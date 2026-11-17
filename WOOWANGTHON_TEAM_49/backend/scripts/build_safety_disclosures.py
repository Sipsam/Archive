"""Rebuild the public 2025 disclosure snapshot from the two official source PDFs.

Run with a Python environment containing pdfplumber. Inputs are explicit paths;
no OCR, network lookup, inferred accident counts, or business-wide deduplication.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import pdfplumber


CATEGORIES = {
    "FATALITIES_GE_2": ("연간 사망재해자 2명 이상", 11),
    "FATALITY_RATE": ("동규모·동업종 평균 이상 사망만인율", 329),
    "MAJOR_INDUSTRIAL_ACCIDENT": ("중대산업사고 발생", 7),
    "CONCEALMENT": ("산업재해 발생 사실 은폐", 2),
    "NON_REPORTING": ("최근 3년간 산업재해 발생 보고의무 2회 이상 위반", 9),
    "CONTRACTOR_COMBINED": ("원·하청 산업재해 통합공표", 2),
    "LEGACY_ACCIDENT_RATE": ("구 시행령 기준 중대재해·평균 이상 재해율", 16),
}
PDF_BASE = "https://www.moel.go.kr/common/downloadFile.do?bbs_id=12&bbs_seq=18907&file_ext=pdf&file_seq="


def compact(value):
    return " ".join((value or "").split())


def names_from_source(value):
    """Separate explicitly labelled parties, retaining factory/branch qualifiers.

    Site names remain in companyName, and must never become a separate accused
    business. Former company names are aliases only when explicitly in the PDF.
    """
    former = re.findall(r"\(구,\s*([^)]*)\)", value)
    main = re.sub(r"\(구,\s*[^)]*\)", "", value)
    names = []
    for party in re.split(r"\((?:원청|하청)\)", main):
        legal_form = r"(?:주식회사|유한회사|유한|주|유|합|재|사)"
        party = re.split(r"\n\((?!" + legal_form + r"\))", party, maxsplit=1)[0].strip()
        if not party or party.startswith("(") and not re.match(r"^\(" + legal_form + r"\)", party):
            continue
        name = "".join(line.strip() for line in party.splitlines()).strip()
        if name and name not in names:
            names.append(name)
    for old in former:
        name = "".join(line.strip() for line in old.splitlines()).strip()
        if name and name not in names:
            names.append(name)
    if not names:
        raise ValueError("Could not identify a source company name")
    return names


def category_for_table(index):
    if index < 5:
        return "FATALITIES_GE_2"
    if index < 30:
        return "FATALITY_RATE"
    return {
        30: "MAJOR_INDUSTRIAL_ACCIDENT", 31: "MAJOR_INDUSTRIAL_ACCIDENT",
        32: "CONCEALMENT", 33: "NON_REPORTING", 34: "CONTRACTOR_COMBINED",
        35: "LEGACY_ACCIDENT_RATE", 36: "LEGACY_ACCIDENT_RATE", 37: "LEGACY_ACCIDENT_RATE",
    }[index]


def build(list_path, release_path):
    records = []
    category_counts = Counter()
    year = None
    table_index = 0
    with pdfplumber.open(list_path) as document:
        if len(document.pages) != 28:
            raise ValueError("Expected the official 28-page list snapshot")
        for page_number, page in enumerate(document.pages, 1):
            for page_table_index, table in enumerate(page.find_tables(), 1):
                code = category_for_table(table_index)
                before = page.crop((0, 0, page.width, table.bbox[1])).extract_text() or ""
                headings = re.findall(r"^○\s*.*", before, re.MULTILINE)
                year_heading = re.search(r"[‘’'](\d{2})년", headings[-1]) if headings else None
                if year_heading:
                    year = 2000 + int(year_heading.group(1))
                rows = table.extract()
                headers = [compact(value) for value in rows[0]]
                name_index = next(i for i, value in enumerate(headers) if value.startswith("사업장명"))
                address_index = next(i for i, value in enumerate(headers) if "소재지" in value)
                industry_index = next((i for i, value in enumerate(headers) if value == "업종명"), None)
                year_index = next((i for i, value in enumerate(headers) if value == "재해 발생 연도"), None)
                for row_index, row in enumerate(rows[1:], 1):
                    if row[name_index] is None and row[address_index] is None:
                        # Second-level column headers on the accident/combined tables.
                        continue
                    company = (row[name_index] or "").strip()
                    address = compact(row[address_index])
                    if not company or not address:
                        raise ValueError(f"Missing source identity at page {page_number}, row {row_index}")
                    occurrence_year = int(row[year_index]) if year_index is not None else year
                    if code == "NON_REPORTING":
                        occurrence_year = None  # The PDF gives a 2022-2024 period, not one accident year.
                    record = {
                        "id": f"moel-2025-p{page_number:02d}-t{page_table_index:02d}-r{row_index:02d}",
                        "categoryCode": code,
                        "categoryLabel": CATEGORIES[code][0],
                        "companyName": company,
                        "companyNames": names_from_source(company),
                        "address": address,
                        "industry": compact(row[industry_index]) if industry_index is not None else None,
                        "occurrenceYear": occurrence_year,
                        "sourcePage": page_number,
                        "sourceTable": page_table_index,
                        "sourceRow": row_index,
                        "sourceCells": row,
                    }
                    records.append(record)
                    category_counts[code] += 1
                table_index += 1
    expected = {code: count for code, (_, count) in CATEGORIES.items()}
    if table_index != 38 or dict(category_counts) != expected or len(records) != 376:
        raise ValueError(f"Source completeness check failed: {table_index} tables, {category_counts}")
    rate_years = Counter(r["occurrenceYear"] for r in records if r["categoryCode"] == "FATALITY_RATE")
    if rate_years != {2024: 50, 2023: 152, 2022: 84, 2021: 26, 2020: 11, 2019: 6}:
        raise ValueError(f"Source year headings do not reconcile: {rate_years}")
    with pdfplumber.open(release_path) as release:
        if len(release.pages) != 12:
            raise ValueError("Expected the official 12-page release snapshot")
        release_text = "\n".join(page.extract_text() or "" for page in release.pages)
        for term in ("376개", "2026. 1. 29.", "99개소"):
            if term not in release_text:
                raise ValueError(f"Press release provenance check failed: {term}")
    metadata = {
        "id": "moel-2025-20260129",
        "title": "2025년 산업재해 발생건수 등 공표",
        "publicationDate": "2026-01-29",
        "publicationYear": 2026,
        "referenceYear": 2025,
        "noticeNumber": "고용노동부 공고 제2026-60호",
        "sourceUrl": "https://www.moel.go.kr/news/enews/report/enewsView.do?news_seq=18907",
        "listPdfUrl": PDF_BASE + "20260101830",
        "releasePdfUrl": PDF_BASE + "20260101829",
        "scopeNote": "2025년에 법 위반이 확정되어 2026년 1월 29일 발표한 공표자료입니다. "
                     "동일 사업장이 여러 기준에 중복 수록될 수 있으며, 검색 결과가 없다는 것이 "
                     "산업재해나 법 위반 이력이 없음을 뜻하지 않습니다. 사업장명·현장명·소재지를 함께 확인하세요.",
        "recordCount": len(records),
        "categoryCounts": dict(category_counts),
        "listPdfSha256": hashlib.sha256(list_path.read_bytes()).hexdigest(),
        "releasePdfSha256": hashlib.sha256(release_path.read_bytes()).hexdigest(),
        "listPageCount": 28,
        "releasePageCount": 12,
    }
    return {"dataset": metadata, "records": records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list-pdf", required=True, type=Path)
    parser.add_argument("--release-pdf", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("assets/safety_disclosures/2025.json"))
    parser.add_argument("--frontend-copy", type=Path)
    args = parser.parse_args()
    payload = build(args.list_pdf, args.release_pdf)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    if args.frontend_copy:
        args.frontend_copy.parent.mkdir(parents=True, exist_ok=True)
        args.frontend_copy.write_text(content, encoding="utf-8")
    print(json.dumps({"records": len(payload["records"]), "categories": payload["dataset"]["categoryCounts"]}))


if __name__ == "__main__":
    main()
