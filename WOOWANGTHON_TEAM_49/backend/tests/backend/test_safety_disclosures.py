"""Source-backed safety disclosure matching; name matches are never safety verdicts."""
import json
from pathlib import Path

import pytest

from app.db import Database
from app.errors import ApiError
from app.safety_disclosures import (
    SafetyDisclosureDatasetError,
    SafetyDisclosureDirectory,
    initialize_safety_disclosures,
)


def make_asset(path, records=None):
    records = records if records is not None else [
        {
            'id': 'source-1', 'categoryCode': 'A', 'categoryLabel': '공표 대상 구분 A',
            'companyName': '㈜한빛 정밀', 'companyNames': ['㈜한빛 정밀'],
            'address': '경기도 시흥시 공단로 10', 'industry': '금속 가공업',
            'occurrenceYear': 2024, 'sourcePage': 3,
        },
        {
            'id': 'source-2', 'categoryCode': 'B', 'categoryLabel': '공표 대상 구분 B',
            'companyName': '한빛정밀(주) 부산공장', 'companyNames': ['한빛정밀(주) 부산공장'],
            'address': '부산광역시 사하구 공단길 20', 'industry': None,
            'occurrenceYear': None, 'sourcePage': 7,
        },
        {
            'id': 'source-3', 'categoryCode': 'C', 'categoryLabel': '공표 대상 구분 C',
            'companyName': '(주)한빛정밀 / 주식회사 원도급건설 (아파트 신축현장)',
            'companyNames': ['(주)한빛정밀', '주식회사 원도급건설 (아파트 신축현장)'],
            'address': '충청남도 아산시 현장로 30', 'industry': '건설업',
            'occurrenceYear': 2023, 'sourcePage': 11,
        },
        {
            'id': 'source-4', 'categoryCode': 'A', 'categoryLabel': '공표 대상 구분 A',
            'companyName': '한빛-정밀', 'companyNames': ['한빛-정밀'],
            'address': '경기도 시흥시 공단로 10', 'industry': None,
            'occurrenceYear': None, 'sourcePage': 4,
        },
        {
            'id': 'source-5', 'categoryCode': 'A', 'categoryLabel': '공표 대상 구분 A',
            'companyName': '다른회사', 'companyNames': ['다른회사'],
            'address': '경기도 시흥시 공단로 10', 'industry': None,
            'occurrenceYear': None, 'sourcePage': 5,
        },
    ]
    dataset = {
        'id': 'safety-2025-test', 'title': '2025년 산업재해 발생건수 등 공표',
        'publicationDate': '2025-12-31', 'publicationYear': 2025,
        'referenceYear': 2024, 'noticeNumber': '제2025-999호',
        'sourceUrl': 'https://www.moel.go.kr/test/notice',
        'listPdfUrl': 'https://www.moel.go.kr/test/list.pdf',
        'releasePdfUrl': 'https://www.moel.go.kr/test/release.pdf',
        'scopeNote': '공표 대상 사업장 명단이며 모든 사업장의 안전성을 판정하지 않습니다.',
        'recordCount': len(records),
    }
    path.write_text(json.dumps({'dataset': dataset, 'records': records}, ensure_ascii=False), encoding='utf-8')
    return dataset, records


@pytest.fixture
def disclosure_source(tmp_path):
    source = tmp_path / 'source.json'
    dataset, records = make_asset(source)
    return source, dataset, records


@pytest.fixture
def directory(tmp_path, disclosure_source):
    source, _, _ = disclosure_source
    db = Database(tmp_path / 'data' / 'app.sqlite3')
    db.initialize()
    initialize_safety_disclosures(db, source)
    return SafetyDisclosureDirectory(db)


@pytest.mark.parametrize('query', ['한빛정밀', '(주) 한빛 정밀', '주식회사 한빛정밀', '㈜한빛정밀'])
def test_company_markers_and_whitespace_normalize_without_losing_source(directory, query, disclosure_source):
    _, dataset, records = disclosure_source
    result = directory.search(query, address='경기도 시흥시 공단로 10')
    assert result['status'] == 'MATCHED'
    item = next(item for item in result['items'] if item['id'] == 'source-1')
    assert item['matchLevel'] == 'NAME_AND_ADDRESS'
    for field in ('companyName', 'address', 'categoryCode', 'categoryLabel', 'sourcePage', 'occurrenceYear'):
        assert item[field] == records[0][field]
    for field, value in dataset.items():
        assert result['dataset'][field] == value


def test_name_only_and_wrong_address_require_review_and_do_not_hide_candidates(directory):
    name_only = directory.search('한빛정밀')
    wrong_address = directory.search('한빛정밀', address='서울특별시 종로구 다른길 999')
    assert name_only['status'] == wrong_address['status'] == 'REVIEW_REQUIRED'
    assert {item['id'] for item in name_only['items']} == {item['id'] for item in wrong_address['items']}
    assert next(item for item in wrong_address['items'] if item['id'] == 'source-1')['matchLevel'] == 'NAME_ONLY'
    assert all(item['matchLevel'] != 'NAME_AND_ADDRESS' for item in wrong_address['items'])


def test_partial_address_cannot_establish_identity(directory):
    result = directory.search('한빛정밀', address='경기도 시흥시')
    assert result['status'] == 'REVIEW_REQUIRED'
    assert next(item for item in result['items'] if item['id'] == 'source-1')['matchLevel'] == 'NAME_ONLY'


def test_branch_and_site_names_remain_part_of_company_identity(directory):
    result = directory.search('한빛정밀', address='부산광역시 사하구 공단길 20')
    branch = next(item for item in result['items'] if item['id'] == 'source-2')
    assert branch['matchLevel'] == 'PARTIAL'
    assert result['status'] == 'REVIEW_REQUIRED'
    exact_branch = directory.search('주식회사 한빛정밀 부산공장', address='부산광역시 사하구 공단길 20')
    assert exact_branch['status'] == 'MATCHED'
    assert exact_branch['items'][0]['id'] == 'source-2'
    site = directory.search('원도급건설', address='충청남도 아산시 현장로 30')
    assert site['status'] == 'REVIEW_REQUIRED'
    assert site['items'][0]['matchLevel'] == 'PARTIAL'


def test_each_source_party_alias_is_searchable_without_rewriting_verbatim_site(directory):
    result = directory.search('원도급건설 (아파트 신축현장)', address='충청남도 아산시 현장로 30')
    assert result['status'] == 'MATCHED'
    assert result['items'][0]['companyName'] == '(주)한빛정밀 / 주식회사 원도급건설 (아파트 신축현장)'
    assert result['items'][0]['sourcePage'] == 11


def test_punctuation_is_not_silently_removed_for_exact_identity(directory):
    result = directory.search('한빛-정밀', address='경기도 시흥시 공단로 10')
    assert result['status'] == 'MATCHED'
    assert [item['id'] for item in result['items']] == ['source-4']
    result = directory.search('한빛정밀', address='경기도 시흥시 공단로 10')
    assert not any(item['id'] == 'source-4' and item['matchLevel'] == 'NAME_AND_ADDRESS' for item in result['items'])


def test_substring_with_exact_address_still_requires_review(directory):
    result = directory.search('한빛', address='경기도 시흥시 공단로 10', size=20)
    assert result['status'] == 'REVIEW_REQUIRED'
    assert result['items']
    assert all(item['matchLevel'] == 'PARTIAL' for item in result['items'])


def test_complete_address_can_ignore_spacing_without_ignoring_site_number(directory):
    result = directory.search('한빛정밀', address=' 경기도  시흥시\n공단로10 ')
    assert result['status'] == 'MATCHED'
    result = directory.search('한빛정밀', address='경기도 시흥시 공단로 100')
    assert result['status'] == 'REVIEW_REQUIRED'


def test_global_match_status_and_total_are_independent_of_requested_page(directory):
    first = directory.search('한빛정밀', address='충청남도 아산시 현장로 30', size=1)
    assert first['total'] >= 3
    records = []
    for page in range(1, first['total'] + 1):
        result = directory.search('한빛정밀', address='충청남도 아산시 현장로 30', page=page, size=1)
        assert result['status'] == 'MATCHED'
        assert result['total'] == first['total']
        assert result['page'] == page and result['size'] == 1
        records.extend(result['items'])
    assert len({item['id'] for item in records}) == first['total']
    assert any(item['matchLevel'] != 'NAME_AND_ADDRESS' for item in records)
    assert directory.search('한빛정밀', address='충청남도 아산시 현장로 30', page=100)['items'] == []
    assert directory.search('한빛정밀', address='충청남도 아산시 현장로 30', page=100)['status'] == 'MATCHED'


def test_not_found_still_identifies_dataset_and_scope(directory, disclosure_source):
    _, dataset, _ = disclosure_source
    result = directory.search('공표명단에없는회사', address='경기도 시흥시 공단로 10')
    assert result['status'] == 'NOT_FOUND'
    assert result['total'] == 0 and result['items'] == []
    assert result['dataset']['id'] == dataset['id']
    assert result['dataset']['scopeNote'] == dataset['scopeNote']


def test_initialization_is_idempotent_and_persists_across_restart(tmp_path, disclosure_source):
    source, _, records = disclosure_source
    db_path = tmp_path / 'persistent' / 'app.sqlite3'
    db = Database(db_path)
    db.initialize()
    initialize_safety_disclosures(db, source)
    initialize_safety_disclosures(db, source)
    restarted = Database(db_path)
    restarted.initialize()
    result = SafetyDisclosureDirectory(restarted).search('한빛', size=20)
    assert result['total'] == 4
    assert len({item['id'] for item in result['items']}) == 4
    with restarted.connect() as con:
        assert con.execute('SELECT COUNT(*) FROM safety_disclosures').fetchone()[0] == len(records)
        assert con.execute('SELECT COUNT(*) FROM safety_disclosure_datasets').fetchone()[0] == 1


def test_same_site_in_multiple_source_categories_retains_each_source_record(tmp_path, disclosure_source):
    source, _, records = disclosure_source
    first = records[0]
    second = {**first, 'id': 'another-category', 'categoryCode': 'B', 'categoryLabel': '다른 공표 구분', 'sourcePage': 12}
    make_asset(source, records=[first, second])
    db = Database(tmp_path / 'duplicates' / 'app.sqlite3')
    db.initialize()
    initialize_safety_disclosures(db, source)
    result = SafetyDisclosureDirectory(db).search('한빛정밀', address=first['address'])
    assert result['total'] == 2
    assert {item['categoryCode'] for item in result['items']} == {'A', 'B'}
    assert {item['sourcePage'] for item in result['items']} == {3, 12}


def test_incomplete_persisted_snapshot_is_unavailable_instead_of_not_found(directory):
    with directory.db.connect(write=True) as con:
        con.execute('DELETE FROM safety_disclosures WHERE id=?', ('source-1',))
    with pytest.raises(ApiError) as caught:
        directory.search('공표명단에없는회사')
    assert caught.value.status == 503
    assert caught.value.code == 'SAFETY_DISCLOSURE_DATASET_UNAVAILABLE'


@pytest.mark.parametrize(('table', 'invalid_json'), [
    ('safety_disclosure_datasets', 'null'),
    ('safety_disclosure_datasets', '{}'),
    ('safety_disclosures', '{}'),
    ('safety_disclosures', '{malformed'),
])
def test_malformed_persisted_data_is_unavailable_instead_of_not_found(directory, table, invalid_json):
    with directory.db.connect(write=True) as con:
        con.execute(f'UPDATE {table} SET data_json=?', (invalid_json,))
    with pytest.raises(ApiError) as caught:
        directory.search('공표명단에없는회사')
    assert caught.value.status == 503
    assert caught.value.code == 'SAFETY_DISCLOSURE_DATASET_UNAVAILABLE'


@pytest.mark.parametrize(('content', 'code'), [
    (None, 'SAFETY_DISCLOSURE_DATASET_MISSING'),
    ('{invalid json', 'SAFETY_DISCLOSURE_DATASET_INVALID'),
    ('{"dataset":{},"records":[]}', 'SAFETY_DISCLOSURE_DATASET_INVALID'),
])
def test_missing_or_corrupt_source_fails_explicitly(tmp_path, content, code):
    db = Database(tmp_path / 'broken' / 'app.sqlite3')
    db.initialize()
    source = tmp_path / 'broken.json'
    if content is not None:
        source.write_text(content, encoding='utf-8')
    with pytest.raises(SafetyDisclosureDatasetError) as caught:
        initialize_safety_disclosures(db, source)
    assert caught.value.code == code
    assert str(source) not in str(caught.value)


def test_invalid_replacement_cannot_erase_previous_valid_snapshot(tmp_path, disclosure_source):
    source, _, records = disclosure_source
    db = Database(tmp_path / 'previous' / 'app.sqlite3')
    db.initialize()
    initialize_safety_disclosures(db, source)
    body = json.loads(source.read_text(encoding='utf-8'))
    body['dataset']['recordCount'] = 999
    source.write_text(json.dumps(body, ensure_ascii=False), encoding='utf-8')
    with pytest.raises(SafetyDisclosureDatasetError):
        initialize_safety_disclosures(db, source)
    result = SafetyDisclosureDirectory(db).search('한빛', size=20)
    assert result['total'] == 4
    with db.connect() as con:
        assert con.execute('SELECT COUNT(*) FROM safety_disclosures').fetchone()[0] == len(records)


def test_api_authentication_and_validation(client, auth):
    path = '/api/v1/safety-disclosures'
    assert client.get(path, params={'q': '한빛정밀'}).status_code == 401
    for params in ({}, {'q': ''}, {'q': '   '}, {'q': '회사', 'page': 0},
                   {'q': '회사', 'size': 21}, {'q': '회사', 'address': '가' * 1001}):
        response = client.get(path, params=params, headers=auth)
        assert response.status_code == 422, (params, response.text)


def test_api_wraps_results_and_never_claims_unlisted_company_is_safe(client, auth, disclosure_source):
    source, _, _ = disclosure_source
    initialize_safety_disclosures(client.app.state.db, source)
    client.app.state.safety_disclosures = SafetyDisclosureDirectory(client.app.state.db)
    response = client.get('/api/v1/safety-disclosures', params={'q': '공표명단에없는테스트회사zz'}, headers=auth)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['code'] == 200
    result = body['data']
    assert result['status'] == 'NOT_FOUND' and result['items'] == [] and result['total'] == 0
    assert result['dataset']['scopeNote']
    assert result['dataset']['sourceUrl'].startswith('https://')


def test_api_match_exposes_source_record_and_dataset_provenance(client, auth, disclosure_source):
    source, dataset, records = disclosure_source
    initialize_safety_disclosures(client.app.state.db, source)
    client.app.state.safety_disclosures = SafetyDisclosureDirectory(client.app.state.db)
    response = client.get('/api/v1/safety-disclosures', headers=auth,
                          params={'q': '한빛정밀', 'address': records[0]['address'], 'size': 1})
    assert response.status_code == 200, response.text
    result = response.json()['data']
    assert result['status'] == 'MATCHED' and result['size'] == 1
    assert result['items'][0]['matchLevel'] == 'NAME_AND_ADDRESS'
    assert result['items'][0]['companyName'] == records[0]['companyName']
    assert result['items'][0]['sourcePage'] == records[0]['sourcePage']
    assert result['dataset']['listPdfUrl'] == dataset['listPdfUrl']


def test_api_unavailable_dataset_reports_503_without_empty_fallback(client, auth):
    client.app.state.safety_disclosures = None
    response = client.get('/api/v1/safety-disclosures', params={'q': '한빛정밀'}, headers=auth)
    assert response.status_code == 503, response.text
    result = response.json()['data']
    assert result['errorCode'] == 'SAFETY_DISCLOSURE_DATASET_UNAVAILABLE'
    assert 'items' not in result and 'total' not in result


def test_startup_with_missing_dataset_remains_explicitly_unavailable(tmp_path, monkeypatch, caplog):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app
    from tests.backend.conftest import register

    def missing_dataset(_db):
        raise SafetyDisclosureDatasetError('SAFETY_DISCLOSURE_DATASET_MISSING')

    monkeypatch.setattr('app.main.initialize_safety_disclosures', missing_dataset)
    settings = Settings(_env_file=None, data_dir=tmp_path / 'startup', workers_enabled=False)
    with TestClient(create_app(settings)) as client:
        headers = register(client)
        response = client.get('/api/v1/safety-disclosures', params={'q': '회사'}, headers=headers)
        assert response.status_code == 503
        assert response.json()['data']['errorCode'] == 'SAFETY_DISCLOSURE_DATASET_UNAVAILABLE'
    assert 'SAFETY_DISCLOSURE_DATASET_MISSING' in caplog.text
    assert str(tmp_path) not in caplog.text


def test_bundled_source_has_complete_record_metadata():
    asset = Path(__file__).resolve().parents[2] / 'assets' / 'safety_disclosures' / '2025.json'
    source = json.loads(asset.read_text(encoding='utf-8'))
    dataset, records = source['dataset'], source['records']
    assert dataset['publicationYear'] == 2026
    assert dataset['publicationDate'] == '2026-01-29'
    assert dataset['referenceYear'] == 2025
    assert dataset['recordCount'] == len(records) == 376
    expected_category_counts = {
        'FATALITIES_GE_2': 11,
        'FATALITY_RATE': 329,
        'MAJOR_INDUSTRIAL_ACCIDENT': 7,
        'CONCEALMENT': 2,
        'NON_REPORTING': 9,
        'CONTRACTOR_COMBINED': 2,
        'LEGACY_ACCIDENT_RATE': 16,
    }
    category_counts = {}
    for record in records:
        code = record['categoryCode']
        category_counts[code] = category_counts.get(code, 0) + 1
    assert category_counts == expected_category_counts
    assert len({record['id'] for record in records}) == len(records)
    for key in ('id', 'title', 'publicationDate', 'noticeNumber', 'sourceUrl', 'listPdfUrl', 'releasePdfUrl', 'scopeNote'):
        assert dataset[key]
    for record in records:
        assert record['categoryCode'] and record['categoryLabel']
        assert record['companyName'] and record['companyNames']
        assert all(isinstance(alias, str) and alias.strip() for alias in record['companyNames'])
        assert record['address']
        assert isinstance(record['sourcePage'], int) and 1 <= record['sourcePage'] <= 28
        assert record['industry'] is None or isinstance(record['industry'], str)
        assert record['occurrenceYear'] is None or isinstance(record['occurrenceYear'], int)
