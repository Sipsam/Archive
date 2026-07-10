from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from qagent_core.agent import (
    OpenAIKeyMissingError,
    choose_effective_openai_api,
    normalize_api_mode,
    normalize_reasoning_effort,
    run_generative_agent,
)
from qagent_core.config import (
    AGENT_API_KEY,
    AGENT_CORS_ORIGINS,
    AGENT_DATA_DIR,
    DEFAULT_MODEL,
    DEFAULT_REASONING_EFFORT,
    MAX_AGENT_ITERATIONS,
    get_secret,
)
from qagent_core.data_io import DataLoadError, load_data_folder
from qagent_core.guardrails import (
    GuardrailViolation,
    mask_sensitive_output,
    validate_agent_request,
)
from qagent_core.rag import append_rag_to_prompt, retrieve_rag_context
from qagent_core.runtime import safe_error_message, safe_for_log
from qagent_core.tools import AnalysisContext, build_tool_functions
from qagent_core.utils import apply_lol_patch_version_mapping, normalize_master_tables


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "lol_assignment_dataset"


class AgentRunRequest(BaseModel):
    """Request body for running the balance analysis Agent.

    Args:
        query: User question or analysis instruction.
        model: OpenAI model name. Defaults to ``OPENAI_MODEL``.
        reasoning_effort: Reasoning effort passed to OpenAI when supported.
        context: Optional caller metadata. It is appended to the user prompt as
            JSON and must not contain secrets.
        stream: Reserved flag. Streaming responses are not implemented yet.

    Raises:
        FastAPI returns HTTP 422 when field validation fails.

    Security:
        Do not send OpenAI keys or other secrets in this body. External caller
        authentication uses ``AGENT_API_KEY`` through headers instead.
    """

    query: str = Field(...)
    model: str = Field(default=DEFAULT_MODEL)
    reasoning_effort: str = Field(default=DEFAULT_REASONING_EFFORT)
    context: dict[str, Any] = Field(default_factory=dict)
    stream: bool = False


class AgentRunMetadata(BaseModel):
    """Metadata returned with an Agent response."""

    model: str
    reasoning_effort: str
    api_mode: str
    elapsed_ms: int
    data_dir: str
    rag_status: str = "disabled"
    rag_sources: list[dict[str, Any]] = Field(default_factory=list)
    guardrail_warnings: list[str] = Field(default_factory=list)
    execution_nodes: list[str] = Field(default_factory=list)


class AgentRunResponse(BaseModel):
    """Response body for a completed Agent run."""

    answer: str
    tool_trace: list[dict[str, Any]]
    metadata: AgentRunMetadata


class ErrorResponse(BaseModel):
    """Error response shape used by documented API failures."""

    error: str
    message: str


def _configured_cors_origins() -> list[str]:
    """Return the explicit CORS allow-list from ``AGENT_CORS_ORIGINS``.

    Returns:
        A list of origins. Empty means CORS middleware is not installed.
    """
    return [
        origin.strip() for origin in AGENT_CORS_ORIGINS.split(",") if origin.strip()
    ]


app = FastAPI(
    title="QAgent API",
    version="1.0.0",
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return schema validation errors as documented 400 responses."""
    _ = request
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": {
                "error": "invalid_request",
                "message": "Request body failed schema validation.",
                "fields": safe_for_log(exc.errors()),
            }
        },
    )


cors_origins = _configured_cors_origins()
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["POST", "GET"],
        allow_headers=["Authorization", "X-API-Key", "Content-Type"],
    )


def verify_agent_api_key(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Validate the external API authentication key.

    Args:
        authorization: Optional ``Authorization: Bearer <key>`` header.
        x_api_key: Optional ``X-API-Key`` header.

    Returns:
        ``None`` when authentication succeeds.

    Raises:
        HTTPException: 503 when ``AGENT_API_KEY`` is not configured, or 401 when
        the caller does not present the configured key.

    Security:
        This key is separate from ``OPENAI_API_KEY`` and is never echoed back.
    """
    expected = get_secret("AGENT_API_KEY") or AGENT_API_KEY
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "agent_api_key_missing",
                "message": "AGENT_API_KEY is not configured.",
            },
        )

    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization.split(" ", 1)[1].strip()
    provided = bearer or (x_api_key or "").strip()
    if provided != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "message": "Invalid API key."},
        )


def load_default_analysis_context() -> tuple[AnalysisContext, Path]:
    """Load the dataset used by external API calls.

    Returns:
        ``(AnalysisContext, data_dir)`` for the configured or default dataset.

    Raises:
        DataLoadError: Required CSV files are missing or invalid.

    Security:
        The API does not accept arbitrary file paths from request bodies. Set
        ``AGENT_DATA_DIR`` server-side when a different dataset is needed.
    """
    data_dir = Path(AGENT_DATA_DIR).expanduser() if AGENT_DATA_DIR else DEFAULT_DATA_DIR
    loaded = load_data_folder(data_dir)
    characters, skills, equipment_sets, patch_notes = normalize_master_tables(
        loaded["characters"],
        loaded["skills"],
        loaded["equipment_sets"],
        loaded["patch_notes"],
    )
    battles = apply_lol_patch_version_mapping(loaded["battle_logs"])
    return (
        AnalysisContext(
            battles=battles,
            characters=characters,
            skills=skills,
            equipment_sets=equipment_sets,
            patch_notes=patch_notes,
        ),
        data_dir,
    )


def build_api_user_goal(payload: AgentRunRequest) -> str:
    """Build the Agent prompt from an API request.

    Args:
        payload: Validated request body.

    Returns:
        A prompt string containing the query and optional sanitized context.

    Security:
        The context is sanitized and length-limited for logging hygiene, but
        callers should still avoid sending secrets.
    """
    if not payload.context:
        return payload.query.strip()
    safe_context = safe_for_log(payload.context, max_string_length=500)
    context_json = json.dumps(safe_context, ensure_ascii=False, default=str)
    return f"{payload.query.strip()}\n\nAdditional caller context JSON:\n{context_json[:4000]}"


@app.get("/health")
def health() -> dict[str, Literal["ok"]]:
    """Return a lightweight process health response."""
    return {"status": "ok"}


@app.post("/api/agent/run", response_model=AgentRunResponse)
def run_agent_endpoint(
    payload: AgentRunRequest,
    request: Request,
    _: None = Depends(verify_agent_api_key),
) -> AgentRunResponse:
    """Run the QAgent analysis Agent for an authenticated external caller.

    Args:
        payload: Validated request body.
        request: FastAPI request object, currently used only for future
            observability hooks.
        _: Authentication dependency result.

    Returns:
        Agent answer, sanitized tool trace, and metadata.

    Raises:
        HTTPException: 400 for unsupported options, 401/503 for auth setup,
        503 for missing OpenAI key, 500 for sanitized execution failures.

    Security:
        Requires ``AGENT_API_KEY``. ``OPENAI_API_KEY``, system prompts, and raw
        internal messages are not returned.
    """
    _ = request
    execution_nodes = ["input_validation"]
    try:
        validated = validate_agent_request(
            query=payload.query,
            model=payload.model,
            reasoning_effort=payload.reasoning_effort,
            context=payload.context,
        )
    except GuardrailViolation as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": error.code, "message": str(error)},
        )

    if payload.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "stream_not_supported",
                "message": "Streaming is not implemented for this endpoint.",
            },
        )

    started = time.monotonic()
    reasoning_effort = normalize_reasoning_effort(validated.reasoning_effort)
    api_mode = normalize_api_mode("auto")
    effective_api = choose_effective_openai_api(
        api_mode, reasoning_effort, validated.model
    )
    rag_result = retrieve_rag_context(validated.query, project_root=PROJECT_ROOT)
    execution_nodes.append("rag_search")
    if rag_result.status == "ok":
        execution_nodes.append("rag_context_attached")
    guardrail_warnings = list(validated.warnings)
    if any(hit.injection_signals for hit in rag_result.hits):
        guardrail_warnings.append("rag_injection_signals_detected")

    try:
        context, data_dir = load_default_analysis_context()
        execution_nodes.append("dataset_load")
        tool_functions = build_tool_functions(context)
        execution_nodes.append("tool_registry_build")
        user_goal = append_rag_to_prompt(
            build_api_user_goal(
                AgentRunRequest(
                    query=validated.query,
                    model=validated.model,
                    reasoning_effort=validated.reasoning_effort,
                    context=validated.context,
                    stream=payload.stream,
                )
            ),
            rag_result,
        )
        execution_nodes.append("agent_run")
        answer, trace, _messages = run_generative_agent(
            model=validated.model,
            user_goal=user_goal,
            tool_functions=tool_functions,
            max_turns=MAX_AGENT_ITERATIONS,
            reasoning_effort=reasoning_effort,
            api_mode=api_mode,
        )
    except OpenAIKeyMissingError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "openai_api_key_missing",
                "message": "OPENAI_API_KEY is not configured.",
            },
        )
    except DataLoadError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "data_load_failed",
                "message": safe_error_message("tool", error),
            },
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "agent_run_failed",
                "message": safe_error_message("api", error),
            },
        )

    elapsed_ms = int((time.monotonic() - started) * 1000)
    execution_nodes.append("output_guardrail")
    return AgentRunResponse(
        answer=mask_sensitive_output(answer),
        tool_trace=safe_for_log(trace),
        metadata=AgentRunMetadata(
            model=validated.model,
            reasoning_effort=reasoning_effort,
            api_mode=effective_api,
            elapsed_ms=elapsed_ms,
            data_dir=str(data_dir),
            rag_status=rag_result.status,
            rag_sources=rag_result.sources_metadata(),
            guardrail_warnings=guardrail_warnings,
            execution_nodes=execution_nodes,
        ),
    )
