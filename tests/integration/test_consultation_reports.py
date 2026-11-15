"""Consultation drafts, optimistic concurrency and frozen report artifacts."""

import io
import json
import zipfile

import pytest
from pypdf import PdfReader

from test_api_contract import api as api_fixture
from test_legacy_contract_restored import request, payslip, drain, complete_report
from agent.tests.test_content_reports import content_fixture
from agent.schemas.public.consultation import ConsultationNotes
from agent.config import AgentSettings
from agent.services.facts import template_explanation
from agent.services.reports import render_pdf

api = api_fixture


def test_draft_without_results_and_concurrent_edits(api):
    c, app, wid, cid = api
    path = f"/cases/{cid}/consultation-draft"
    empty = request(c, "GET", path)
    assert empty["version"] == 0 and empty["notes"]["purpose"] == ""
    body = {"expectedVersion": 0, "notes": {"purpose": "  급여 확인  "}, "documentIds": []}
    saved = request(c, "PUT", path, body)
    assert saved["version"] == 1 and saved["notes"]["purpose"] == "급여 확인"
    request(c, "PUT", path, body, 409)
    assert request(c, "GET", path) == saved
    # An independently logged-in user must not retrieve the draft.
    request(
        c,
        "POST",
        "/auth/signup",
        {"email": "other@example.com", "password": "password1234", "name": "other"},
        201,
    )
    other = request(c, "POST", "/auth/login", {"email": "other@example.com", "password": "password1234"})
    request(c, "GET", path, status=404, headers={"Authorization": "Bearer " + other["accessToken"]})
    request(c, "DELETE", f"/cases/{cid}", status=204)
    request(c, "GET", path, status=404)


@pytest.mark.parametrize(
    "notes",
    [
        {"purpose": "x" * 1001},
        {"startDate": "2026-11-02", "endDate": "2026-11-01"},
        {"startDate": "2026-02-30"},
        {"events": [{"date": None, "text": "x"}] * 21},
        {"questions": ["x" * 301]},
        {"questions": ["x"] * 21},
        {"events": [{"text": "x" * 501}]},
        {"secretField": "unexpected"},
    ],
)
def test_invalid_notes_preserve_previous_draft(api, notes):
    c, _, _, cid = api
    path = f"/cases/{cid}/consultation-draft"
    request(c, "PUT", path, {"expectedVersion": 0, "notes": notes, "documentIds": []}, 422)
    assert request(c, "GET", path)["version"] == 0


def test_notes_pinned_before_async_generation_and_zip_matches_pdf(api):
    c, app, _, cid = api
    path = f"/cases/{cid}/consultation-draft"
    notes = {
        "displayName": "상담자",
        "purpose": "급여 차이를 확인하고 싶습니다",
        "desiredHelp": "준비자료 확인",
        "facts": "사용자가 확인한 사실",
        "unknowns": "휴게시간 미확인",
        "questions": ["어떤 자료가 필요한가요?"],
        "events": [{"date": None, "text": "지급 약속"}, {"date": "2026-10-01", "text": "입사 경위"}],
    }
    saved = request(c, "PUT", path, {"expectedVersion": 0, "notes": notes, "documentIds": []})
    payslip(c, cid)
    drain(app)
    body = {"includeOriginalDocuments": False, "documentIds": [], "draftVersion": saved["version"]}
    created = request(
        c, "POST", f"/cases/{cid}/reports", body, 202, headers={"Idempotency-Key": "consultation-once"}
    )
    # Editing the draft after acceptance must not change the queued report.
    request(
        c, "PUT", path, {"expectedVersion": 1, "notes": {"purpose": "나중에 수정한 내용"}, "documentIds": []}
    )
    assert (
        request(
            c, "POST", f"/cases/{cid}/reports", body, 202, headers={"Idempotency-Key": "consultation-once"}
        )
        == created
    )
    request(c, "POST", f"/cases/{cid}/reports", body, 409)
    ready = complete_report(app, c, cid, created["reportId"])
    assert ready["draftVersion"] == 1 and ready["templateVersion"] == "report-v3"
    pdf = c.get(f"/api/v1/cases/{cid}/reports/{created['reportId']}/pdf").content
    reader = PdfReader(io.BytesIO(pdf))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert "근로·급여 상담 준비서" in text and notes["purpose"] in text
    assert "나중에 수정한 내용" not in text and notes["questions"][0] in text
    assert text.index("입사 경위") < text.index("지급 약속")
    bundle = c.get(f"/api/v1/cases/{cid}/reports/{created['reportId']}/originals").content
    with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
        assert archive.read("summary.pdf") == pdf
        assert json.loads(archive.read("report_context.json"))["consultation"]["purpose"] == notes["purpose"]


def test_invalid_document_selection_cannot_be_saved(api):
    c, _, _, cid = api
    request(
        c,
        "PUT",
        f"/cases/{cid}/consultation-draft",
        {"expectedVersion": 0, "notes": {}, "documentIds": [99999]},
        422,
    )


def test_maximum_notes_paginate_without_truncation():
    result, display, _ = content_fixture()
    notes = ConsultationNotes(
        purpose="상담 내용 " * 150,
        facts="확인한 사실 " * 200,
        events=[{"text": "긴 경위 " * 95, "date": None} for _ in range(20)],
        questions=["긴 질문 " * 55 for _ in range(19)] + ["마지막 질문도 출력되어야 합니다"],
    )
    pdf = render_pdf(result, template_explanation(result), AgentSettings(), result.created_at, display, notes)
    reader = PdfReader(io.BytesIO(pdf))
    text = "\n".join(page.extract_text() for page in reader.pages)
    assert len(reader.pages) > 3 and "마지막 질문도 출력되어야 합니다" in text
    assert "사용자가 작성한 경위와 상담 질문" in text
