"""Source-preserving lookup of the packaged Ministry of Employment and Labor notice.

This directory is independent of a user's workplaces. A name candidate is never
treated as a confirmed site without an exact complete address match.
"""
import json
import re
import sqlite3
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from pydantic import ValidationError

from app.db import dump, load
from app.errors import ApiError
from app.outputs import SafetyDisclosureDatasetDTO, SafetyDisclosureSourceRecord

DEFAULT_DATASET_PATH = Path(__file__).resolve().parent.parent / 'assets' / 'safety_disclosures' / '2025.json'

SAFETY_SCHEMA = '''
CREATE TABLE IF NOT EXISTS safety_disclosure_datasets (
 id TEXT PRIMARY KEY, data_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS safety_disclosures (
 id TEXT PRIMARY KEY,
 dataset_id TEXT NOT NULL REFERENCES safety_disclosure_datasets(id),
 ordinal INTEGER NOT NULL, data_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS safety_disclosures_dataset ON safety_disclosures(dataset_id,ordinal);
'''


class SafetyDisclosureDatasetError(RuntimeError):
    """Only the sanitized code is exposed to startup logs or callers."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


def normalize_company_name(value):
    text = re.sub(r'\s+', '', unicodedata.normalize('NFKC', value)).casefold()
    return text.replace('(주)', '').replace('주식회사', '')


def normalize_address(value):
    # Preserve site numbers, punctuation and parenthetical site qualifications.
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC', value)).casefold()


def _read_dataset(asset_path):
    try:
        body = json.loads(Path(asset_path).read_text(encoding='utf-8-sig'))
    except FileNotFoundError:
        raise SafetyDisclosureDatasetError('SAFETY_DISCLOSURE_DATASET_MISSING') from None
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise SafetyDisclosureDatasetError('SAFETY_DISCLOSURE_DATASET_INVALID') from None
    try:
        metadata = SafetyDisclosureDatasetDTO.model_validate(body['dataset'])
        records = [SafetyDisclosureSourceRecord.model_validate(item) for item in body['records']]
        published = date.fromisoformat(metadata.publicationDate)
        if (metadata.recordCount != len(records) or not records
                or len({item.id for item in records}) != len(records)
                or published.year != metadata.publicationYear
                or metadata.referenceYear > metadata.publicationYear):
            raise ValueError('invalid dataset consistency')
        for url in (metadata.sourceUrl, metadata.listPdfUrl, metadata.releasePdfUrl):
            parsed = urlparse(url)
            if parsed.scheme != 'https' or parsed.hostname not in ('www.moel.go.kr', 'moel.go.kr'):
                raise ValueError('invalid source provenance')
        for item in records:
            if not normalize_company_name(item.companyName) or not normalize_address(item.address):
                raise ValueError('missing identity')
            if any(not normalize_company_name(alias) for alias in item.companyNames):
                raise ValueError('missing source alias')
    except (KeyError, TypeError, ValueError, ValidationError):
        raise SafetyDisclosureDatasetError('SAFETY_DISCLOSURE_DATASET_INVALID') from None
    return metadata.model_dump(mode='json'), [item.model_dump(mode='json') for item in records]


def initialize_safety_disclosures(db, asset_path=DEFAULT_DATASET_PATH):
    """Validate before writing; seed atomically and keep one active packaged dataset.

    Source IDs supplied by the reproducible PDF extractor remain stable. Repeated
    startup replaces the same snapshot without duplicating records or aliases.
    """
    metadata, records = _read_dataset(asset_path)
    # SQLite executescript commits implicitly, so schema creation precedes the
    # separate write transaction that replaces the complete dataset snapshot.
    with db.connect(snapshot=False) as con:
        con.executescript(SAFETY_SCHEMA)
    with db.connect(write=True) as con:
        con.execute('DELETE FROM safety_disclosures')
        con.execute('DELETE FROM safety_disclosure_datasets')
        con.execute('INSERT INTO safety_disclosure_datasets(id,data_json) VALUES(?,?)',
                    (metadata['id'], dump(metadata)))
        con.executemany('INSERT INTO safety_disclosures(id,dataset_id,ordinal,data_json) VALUES(?,?,?,?)',
                        [(item['id'], metadata['id'], ordinal, dump(item))
                         for ordinal, item in enumerate(records)])
    return metadata


def _unavailable():
    return ApiError(503, 'SAFETY_DISCLOSURE_DATASET_UNAVAILABLE',
                    '산업재해 공표 자료를 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.')


class SafetyDisclosureDirectory:
    def __init__(self, db):
        self.db = db

    def search(self, q, address=None, page=1, size=5):
        query = normalize_company_name(q)
        if not query:
            raise ApiError(422, 'INVALID_SAFETY_DISCLOSURE_QUERY', '검색할 사업장 이름을 입력해 주세요.')
        full_address = normalize_address(address or '')
        try:
            with self.db.connect() as con:
                row = con.execute('SELECT id,data_json FROM safety_disclosure_datasets').fetchone()
                if row is None:
                    raise _unavailable()
                metadata = SafetyDisclosureDatasetDTO.model_validate(load(row['data_json'])).model_dump(mode='json')
                records = [SafetyDisclosureSourceRecord.model_validate(load(item['data_json'])).model_dump(mode='json')
                           for item in con.execute(
                    'SELECT data_json FROM safety_disclosures WHERE dataset_id=? ORDER BY ordinal', (row['id'],))]
        except (sqlite3.DatabaseError, ValueError, TypeError):
            raise _unavailable() from None
        if len(records) != metadata.get('recordCount'):
            raise _unavailable()
        matches = []
        for item in records:
            names = {normalize_company_name(value) for value in [item['companyName'], *item['companyNames']]}
            if query in names:
                level = ('NAME_AND_ADDRESS' if full_address and full_address == normalize_address(item['address'])
                         else 'NAME_ONLY')
            elif any(query in name for name in names):
                level = 'PARTIAL'
            else:
                continue
            matches.append({**item, 'matchLevel': level})
        rank = {'NAME_AND_ADDRESS': 0, 'NAME_ONLY': 1, 'PARTIAL': 2}
        matches.sort(key=lambda item: rank[item['matchLevel']])
        status = ('MATCHED' if any(item['matchLevel'] == 'NAME_AND_ADDRESS' for item in matches)
                  else 'REVIEW_REQUIRED' if matches else 'NOT_FOUND')
        return {'status': status, 'items': matches[(page - 1) * size:page * size],
                'page': page, 'size': size, 'total': len(matches), 'dataset': metadata}
