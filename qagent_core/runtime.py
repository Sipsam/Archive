from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

SENSITIVE_KEY_PATTERN = re.compile(r"(api.?key|token|secret|password|authorization)", re.I)
SECRET_VALUE_PATTERN = re.compile(r"(sk-[A-Za-z0-9_-]{8,}|RGAPI-[A-Za-z0-9_-]{8,}|Bearer\s+\S+)", re.I)


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"RUN-{stamp}-{uuid.uuid4().hex[:8]}"


def safe_for_log(value: Any, max_string_length: int = 240, depth: int = 0) -> Any:
    if depth > 4:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        if str(value.get("role", "")).lower() == "user" and "content" in value:
            value = {**value, "content": "[USER_INPUT_REDACTED]"}
        return {
            str(key): "[REDACTED]" if SENSITIVE_KEY_PATTERN.search(str(key))
            else safe_for_log(item, max_string_length, depth + 1)
            for key, item in list(value.items())[:50]
        }
    if isinstance(value, list):
        return [safe_for_log(item, max_string_length, depth + 1) for item in value[:20]]
    if isinstance(value, tuple):
        return [safe_for_log(item, max_string_length, depth + 1) for item in value[:20]]
    if isinstance(value, str):
        redacted = SECRET_VALUE_PATTERN.sub("[REDACTED]", value)
        return redacted if len(redacted) <= max_string_length else redacted[:max_string_length] + "…[TRUNCATED]"
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return str(type(value).__name__)


def input_summary(arguments: dict[str, Any]) -> str:
    safe = safe_for_log(arguments)
    keys = sorted(safe.keys()) if isinstance(safe, dict) else []
    return f"fields={keys}, bytes={len(json.dumps(safe, ensure_ascii=False, default=str))}"


def output_summary(result: Any) -> str:
    if isinstance(result, dict):
        status = result.get("status", "unknown")
        return f"status={status}, fields={sorted(str(key) for key in result.keys())[:20]}"
    return f"type={type(result).__name__}"


def safe_error_message(category: str, error: Exception | None = None) -> str:
    suffix = f" ({type(error).__name__})" if error is not None else ""
    messages = {
        "api": "외부 AI API 요청에 실패했습니다. 인증, 네트워크, 사용 한도와 모델 접근 권한을 확인하세요.",
        "tool": "분석 Tool 실행에 실패했습니다. 입력 조건과 데이터 형식을 확인하세요.",
        "json": "Tool 입력 JSON을 해석하지 못했습니다. Agent가 올바른 인자를 생성하지 않았습니다.",
        "limit": "Agent 실행 안전 제한에 도달했습니다.",
        "timeout": "Agent 실행 제한 시간을 초과했습니다.",
    }
    return messages.get(category, "Agent 실행 중 오류가 발생했습니다.") + suffix
