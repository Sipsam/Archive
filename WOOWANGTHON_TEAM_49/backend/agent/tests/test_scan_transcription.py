"""Scanned pages: model transcript for text, local OCR for coordinates. No network here."""

import io

import pytest
from pypdf import PdfReader, PdfWriter

from agent.config import AgentSettings
from agent.services import local_ocr, scan_transcription
from agent.services.document_ocr import recognize_document
from agent.tests.fixtures_support import pdf_bytes
from app.source_location import bounding_box

ENABLED = {"openai_api_key": "test-key-never-sent", "scan_transcription": True}


def word(text, x, y, width=0.08):
    return {"text": text, "bbox": [x, y, x + width, y + 0.02]}


def ocr_page(text, words=()):
    return [{"text": text, "lines": [{"text": text, "confidence": 30}], "words": list(words)}]


def fake_requests(monkeypatch, answer):
    sent = []

    async def request(data, page_count, settings):
        sent.append((len(PdfReader(io.BytesIO(data)).pages), page_count))
        return answer(page_count)

    monkeypatch.setattr(scan_transcription, "request_pages", request)
    return sent


async def test_disabled_or_keyless_reader_never_requests_a_transcript(monkeypatch):
    monkeypatch.setattr(local_ocr, "recognize_pdf", lambda *args: ocr_page("Scanned net 2,888,000 KRW"))
    sent = fake_requests(monkeypatch, lambda count: pytest.fail("transcription must stay off"))
    scan = pdf_bytes(["Scanned net 2,888,000 KRW"], scanned=True)
    for settings in (AgentSettings(), AgentSettings(scan_transcription=True), AgentSettings(openai_api_key="k")):
        result = await recognize_document(scan, settings)
        assert result["pages"] == ["Scanned net 2,888,000 KRW"]
        assert result["text_sources"] == ["python_ocr"]
        assert result["ocr_pages"][0]["lines"][0]["confidence"] == 30
    assert sent == []


async def test_only_scanned_pages_are_sent_and_their_text_is_replaced(monkeypatch):
    writer = PdfWriter()
    for source in (
        pdf_bytes(["Native net 2,888,000 KRW"]),
        pdf_bytes(["Scanned net 2,888,000 KRW"], scanned=True),
    ):
        writer.add_page(PdfReader(io.BytesIO(source)).pages[0])
    stream = io.BytesIO()
    writer.write(stream)
    words = [word("Scanned", 0.1, 0.1), word("nel", 0.2, 0.1), word("2,888,OOO", 0.3, 0.1), word("KRW", 0.4, 0.1)]
    monkeypatch.setattr(local_ocr, "recognize_pdf", lambda *args: ocr_page("Scanned nel 2,888,OOO KRW", words))
    sent = fake_requests(monkeypatch, lambda count: ["Scanned net 2,888,000 KRW"] * count)

    result = await recognize_document(stream.getvalue(), AgentSettings(**ENABLED))

    assert sent == [(1, 1)]  # the digital page never left the server
    assert result["page_methods"] == ["pdf_text", "python_ocr"]
    assert result["text_sources"] == ["pdf_text", "model_transcription"]
    assert result["pages"][1] == "Scanned net 2,888,000 KRW"
    page = result["ocr_pages"][1]
    # The extraction graph requires the stored page text to equal the page it reads.
    assert page["text"] == result["pages"][1] and page["ocr_text"] == "Scanned nel 2,888,OOO KRW"
    assert page["lines"] == [] and page["words"] == words
    assert result["layout_pages"][1]["blocks"]


@pytest.mark.parametrize("answer", [RuntimeError("network"), [""], ["net"]])
async def test_failed_empty_or_truncated_transcript_keeps_local_ocr_text(monkeypatch, answer):
    def respond(count):
        if isinstance(answer, Exception):
            raise answer
        return answer

    text = "Scanned net 2,888,000 KRW and many more words on the page"
    monkeypatch.setattr(local_ocr, "recognize_pdf", lambda *args: ocr_page(text))
    fake_requests(monkeypatch, respond)
    result = await recognize_document(pdf_bytes([text], scanned=True), AgentSettings(**ENABLED))
    assert result["pages"] == [text]
    assert result["text_sources"] == ["python_ocr"]
    assert result["ocr_pages"][0]["lines"][0]["confidence"] == 30


async def test_long_scans_are_sent_in_small_batches(monkeypatch):
    writer = PdfWriter()
    page = PdfReader(io.BytesIO(pdf_bytes(["Scanned page"], scanned=True))).pages[0]
    for _ in range(scan_transcription.BATCH_PAGES + 1):
        writer.add_page(page)
    stream = io.BytesIO()
    writer.write(stream)
    monkeypatch.setattr(local_ocr, "recognize_pdf", lambda *args: ocr_page("Scanned page"))
    sent = fake_requests(monkeypatch, lambda count: [f"Transcribed page {n}" for n in range(count)])
    result = await recognize_document(stream.getvalue(), AgentSettings(**ENABLED))
    assert sorted(sent) == [(1, 1), (scan_transcription.BATCH_PAGES, scan_transcription.BATCH_PAGES)]
    assert set(result["text_sources"]) == {"model_transcription"}


def test_transcript_tables_become_plain_rows():
    markdown = "# 급여명세서\n<table><tr><th>항목</th><th>금액</th></tr><tr><td>기본급</td><td>3,000,000</td></tr></table>"
    assert scan_transcription.visible_text(markdown) == "# 급여명세서\n항목 금액\n기본급 3,000,000"


def transcribed(blocks):
    return {"layout_pages": [{"page": 1, "blocks": blocks}], "text_sources": ["model_transcription"]}


def test_transcript_quote_is_located_on_misread_ocr_words():
    blocks = [
        {"text": "근 로 시 간", "words": [word("근", 0.1, 0.3, 0.02), word("로", 0.13, 0.3, 0.02), word("시", 0.16, 0.3, 0.02), word("간", 0.19, 0.3, 0.02)]},
        {"text": "1) 월 통상임금: 월 3000,000원 -", "words": [word("1)", 0.1, 0.5, 0.02), word("월", 0.13, 0.5, 0.02), word("통상임금:", 0.16, 0.5, 0.1), word("월", 0.27, 0.5, 0.02), word("3000,000원", 0.3, 0.5, 0.1), word("-", 0.41, 0.5, 0.01)]},
        {"text": "매월분을 다음 달 10 일 지급", "words": [word("매월분을", 0.1, 0.7), word("다음", 0.2, 0.7, 0.04), word("달", 0.25, 0.7, 0.02), word("10", 0.28, 0.7, 0.02), word("일", 0.31, 0.7, 0.02), word("지급", 0.34, 0.7, 0.04)]},
    ]
    recognized = transcribed(blocks)
    box = bounding_box(recognized, 1, "1) 월 통상임금: 월 3,000,000원", "3,000,000원")
    assert box == pytest.approx([0.298, 0.498, 0.104, 0.024])
    # A value that is ambiguous inside its quote marks the whole quote, as on OCR pages.
    whole = bounding_box(recognized, 1, "1) 월 통상임금: 월 3,000,000원", "월")
    assert whole[0] == pytest.approx(0.098) and whole[1] == pytest.approx(0.498) and whole[2] > 0.3
    # Without the transcription marker the exact rule still applies: a misread quote has no box.
    assert bounding_box({"layout_pages": recognized["layout_pages"]}, 1, "1) 월 통상임금: 월 3,000,000원", "3,000,000원") is None


def test_transcript_value_in_the_next_table_cell_is_found_after_its_label():
    blocks = [
        {"text": "업체명 Name of the enterprise 전 화 번호 Phone number", "words": [word("업체명", 0.1, 0.1), word("Name", 0.2, 0.1), word("of", 0.3, 0.1, 0.02), word("the", 0.33, 0.1, 0.03), word("enterprise", 0.37, 0.1), word("전", 0.6, 0.1, 0.02), word("화", 0.63, 0.1, 0.02), word("번호", 0.66, 0.1, 0.04), word("Phone", 0.71, 0.1), word("number", 0.8, 0.1)]},
        {"text": "주식회사 한 빚 정 밀 (가상) 010-0000-0000 (가상)", "words": [word("주식회사", 0.1, 0.2), word("한", 0.19, 0.2, 0.02), word("빚", 0.22, 0.2, 0.02), word("정", 0.25, 0.2, 0.02), word("밀", 0.28, 0.2, 0.02), word("(가상)", 0.31, 0.2, 0.05), word("010-0000-0000", 0.6, 0.2, 0.12), word("(가상)", 0.73, 0.2, 0.05)]},
    ]
    box = bounding_box(transcribed(blocks), 1, "업체명 Name of the enterprise\n주식회사 한빛정밀 (가상)", "주식회사 한빛정밀")
    assert box == pytest.approx([0.098, 0.198, 0.204, 0.024])


def test_transcript_quote_matching_two_places_equally_has_no_box():
    row = lambda y: {"text": "기본급 100", "words": [word("기본급", 0.1, y), word("1OO", 0.3, y)]}  # noqa: E731
    assert bounding_box(transcribed([row(0.1), row(0.5)]), 1, "기본급 100", "100") is None
    assert bounding_box(transcribed([]), 1, "기본급 100", "100") is None
    assert bounding_box(transcribed([row(0.1)]), 1, "전혀 다른 문장입니다", "문장") is None


def test_dropped_repeated_digit_is_restored_only_from_a_matching_ocr_token():
    restore = scan_transcription.restore_digit_runs
    ocr = "예금주 응 우 엔 계 좌 번호 TEST-000-0026 잔액 3,087,727 원 지급 2,000,000"
    text, repairs = restore("계좌번호 TEST-000-026 잔액 3,087,727원 지급 2,00,000", ocr)
    assert text == "계좌번호 TEST-000-0026 잔액 3,087,727원 지급 2,000,000"
    assert repairs == [["2,00,000", "2,000,000"], ["TEST-000-026", "TEST-000-0026"]]
    # Same token, a different digit, several candidates, two plausible amounts, or a time: untouched.
    for transcript, seen in (
        ("TEST-000-0026", "TEST-000-0026"),
        ("TEST-000-026", "TEST-000-1026"),
        ("TEST-000-026", "TEST-000-9026 TEST-000-0026 TEST-0000-026"),
        ("3,000,000", "3,0000,000"),
        ("3,000,000", "33,000,000"),
        ("09:00", "09:000"),
    ):
        assert restore(transcript, seen) == (transcript, [])


async def test_reader_applies_the_digit_repair_and_records_it(monkeypatch):
    ocr = "Account TEST-000-0026 balance 3,087,727 KRW"
    monkeypatch.setattr(local_ocr, "recognize_pdf", lambda *args: ocr_page(ocr))
    fake_requests(monkeypatch, lambda count: ["Account TEST-000-026 balance 3,087,727 KRW"])
    result = await recognize_document(pdf_bytes([ocr], scanned=True), AgentSettings(**ENABLED))
    assert result["pages"] == [ocr]
    assert result["ocr_pages"][0]["transcript_repairs"] == [["TEST-000-026", "TEST-000-0026"]]
    assert result["text_sources"] == ["model_transcription"]


def test_similar_table_rows_are_told_apart_by_a_token_printed_once():
    def row(date, y, start="O9:00"):
        return {
            "text": f"{date} 정 상 근 무 {start} 18:00 8",
            "words": [word(date, 0.1, y), word("정", 0.2, y, 0.02), word("상", 0.23, y, 0.02), word("근", 0.26, y, 0.02), word("무", 0.29, y, 0.02), word(start, 0.4, y), word("18:00", 0.5, y), word("8", 0.6, y, 0.02)],
        }

    recognized = transcribed([row("04/01", 0.1), row("04/02", 0.2), row("04/03", 0.3)])
    # The OCR misread 09:00 in every row, so no row matches exactly and all rows look alike.
    assert bounding_box(recognized, 1, "04/02 정상근무 09:00 18:00 8", "18:00") == pytest.approx([0.498, 0.198, 0.084, 0.024])
    assert bounding_box(recognized, 1, "04/02 정상근무 09:00 18:00 8", "04/02") == pytest.approx([0.098, 0.198, 0.084, 0.024])
    # Without a distinguishing token the rows stay ambiguous.
    assert bounding_box(recognized, 1, "정상근무 09:00 18:00 8", "18:00") is None
