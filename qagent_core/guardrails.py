"""Input, output, and path guardrails shared by UI and API entrypoints."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from qagent_core.config import DEFAULT_MODEL, MAX_AGENT_QUERY_CHARS, get_secret
from qagent_core.runtime import safe_for_log

MODEL_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")
REASONING_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh"}
PROMPT_INJECTION_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"ignore\s+(all\s+)?(previous|prior)\s+(instructions|messages)",
        r"reveal\s+(the\s+)?(system|developer)\s+(prompt|message)",
        r"show\s+(me\s+)?(the\s+)?(system|developer)\s+(prompt|message)",
        r"(exfiltrate|leak|dump)\s+(secrets?|api\s*keys?|tokens?)",
        r"do\s+not\s+use\s+(tools?|rag|retrieval)",
        r"bypass\s+(guardrails?|safety|policy)",
    ]
]
SECRET_LIKE_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9_-]{8,}|RGAPI-[A-Za-z0-9_-]{8,}|Bearer\s+\S+)",
    re.I,
)


@dataclass(frozen=True)
class GuardrailResult:
    """Validation outcome for one user/API request."""

    query: str
    model: str
    reasoning_effort: str
    context: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


class GuardrailViolation(ValueError):
    """Raised when an input cannot be safely processed by the Agent."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def detect_prompt_injection(text: str) -> tuple[str, ...]:
    """Return prompt-injection indicators found in user or retrieved text."""
    findings = []
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text or ""):
            findings.append(pattern.pattern)
    return tuple(findings)


def validate_agent_request(
    *,
    query: str,
    model: str | None = None,
    reasoning_effort: str | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailResult:
    """Validate common Agent request fields before retrieval or LLM calls.

    Raises:
        GuardrailViolation: If the request is empty, oversized, or uses an
            unsupported model/reasoning value.

    Security:
        The caller context is sanitized before it is echoed into prompts or logs.
    """
    normalized_query = str(query or "").strip()
    if not normalized_query:
        raise GuardrailViolation("empty_query", "query must not be empty.")
    if len(normalized_query) > MAX_AGENT_QUERY_CHARS:
        raise GuardrailViolation(
            "query_too_long",
            f"query exceeds {MAX_AGENT_QUERY_CHARS} characters.",
        )

    normalized_model = str(model or DEFAULT_MODEL).strip()
    if not MODEL_NAME_PATTERN.fullmatch(normalized_model):
        raise GuardrailViolation(
            "invalid_model",
            "model may contain only letters, numbers, '.', '_', ':', and '-'.",
        )

    normalized_reasoning = str(reasoning_effort or "none").strip().lower()
    if normalized_reasoning not in REASONING_EFFORTS:
        raise GuardrailViolation(
            "invalid_reasoning_effort",
            f"reasoning_effort must be one of {sorted(REASONING_EFFORTS)}.",
        )

    safe_context = safe_for_log(context or {}, max_string_length=500)
    context_json = json.dumps(safe_context, ensure_ascii=False, default=str)
    if len(context_json) > 8000:
        raise GuardrailViolation("context_too_large", "context JSON is too large.")

    warnings = []
    if detect_prompt_injection(normalized_query):
        warnings.append("prompt_injection_signals_detected")
    return GuardrailResult(
        query=normalized_query,
        model=normalized_model,
        reasoning_effort=normalized_reasoning,
        context=safe_context if isinstance(safe_context, dict) else {},
        warnings=tuple(warnings),
    )


def ensure_path_within_roots(path: Path, allowed_roots: Iterable[Path]) -> Path:
    """Resolve ``path`` and ensure it stays under one of the allowed roots.

    Raises:
        GuardrailViolation: If the resolved path escapes all allowed roots.
    """
    resolved = Path(path).expanduser().resolve()
    roots = [Path(root).expanduser().resolve() for root in allowed_roots]
    if not any(resolved == root or root in resolved.parents for root in roots):
        raise GuardrailViolation("path_not_allowed", "path is outside allowed roots.")
    return resolved


def mask_sensitive_output(text: str) -> str:
    """Redact secret-looking values and configured secrets from LLM output."""
    redacted = SECRET_LIKE_PATTERN.sub("[REDACTED]", str(text or ""))
    for name in ("OPENAI_API_KEY", "AGENT_API_KEY", "RIOT_API_KEY"):
        secret = get_secret(name)
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted
