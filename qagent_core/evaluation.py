"""Deterministic checks for fixture-based Agent quality evaluation."""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping


NUMBER_PATTERN = re.compile(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?:%p|%|전|개)?")
LIST_PREFIX_PATTERN = re.compile(r"(?m)^\s*\d+[.)]\s+")


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    missing_tools: tuple[str, ...]
    forbidden_claims: tuple[str, ...]
    missing_keywords: tuple[str, ...]
    missing_limitations: tuple[str, ...]
    unsupported_numbers: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return not any((
            self.missing_tools,
            self.forbidden_claims,
            self.missing_keywords,
            self.missing_limitations,
            self.unsupported_numbers,
        ))


def _canonical_number(value: str | int | float) -> str | None:
    text = str(value).removesuffix("%p").removesuffix("%").removesuffix("전").removesuffix("개")
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    normalized = number.normalize()
    return format(normalized, "f")


def _numbers_in_value(value: Any) -> set[str]:
    supported: set[str] = set()
    if isinstance(value, bool) or value is None:
        return supported
    if isinstance(value, (int, float)):
        canonical = _canonical_number(value)
        if canonical is not None:
            supported.add(canonical)
        if isinstance(value, float) and abs(value) <= 1:
            percentage = _canonical_number(Decimal(str(value)) * Decimal(100))
            if percentage is not None:
                supported.add(percentage)
        return supported
    if isinstance(value, str):
        for token in NUMBER_PATTERN.findall(value):
            canonical = _canonical_number(token)
            if canonical is not None:
                supported.add(canonical)
        return supported
    if isinstance(value, Mapping):
        for item in value.values():
            supported.update(_numbers_in_value(item))
        return supported
    if isinstance(value, Iterable):
        for item in value:
            supported.update(_numbers_in_value(item))
    return supported


def evaluate_agent_response(
    case: Mapping[str, Any],
    response: str,
    trace: Iterable[Mapping[str, Any]],
) -> EvaluationResult:
    """Evaluate one canned response without making an external LLM request."""
    trace_rows = list(trace)
    called_tools = [str(row.get("tool_name") or row.get("tool") or "") for row in trace_rows]
    lowered = response.casefold()

    missing_tools = tuple(tool for tool in case["expected_tools"] if tool not in called_tools)
    forbidden = tuple(claim for claim in case["forbidden_claims"] if claim.casefold() in lowered)
    missing_keywords = tuple(
        keyword for keyword in case["required_output_keywords"] if keyword.casefold() not in lowered
    )
    missing_limitations = tuple(
        limitation for limitation in case["expected_limitations"] if limitation.casefold() not in lowered
    )

    supported_numbers = _numbers_in_value([
        row.get("result", {}) for row in trace_rows if row.get("success", True)
    ])
    supported_numbers.update(
        number for value in case.get("allowed_numeric_literals", [])
        if (number := _canonical_number(value)) is not None
    )
    response_without_list_numbers = LIST_PREFIX_PATTERN.sub("", response)
    unsupported = []
    for token in NUMBER_PATTERN.findall(response_without_list_numbers):
        canonical = _canonical_number(token)
        if canonical is not None and canonical not in supported_numbers:
            unsupported.append(token)

    return EvaluationResult(
        case_id=str(case["id"]),
        missing_tools=missing_tools,
        forbidden_claims=forbidden,
        missing_keywords=missing_keywords,
        missing_limitations=missing_limitations,
        unsupported_numbers=tuple(dict.fromkeys(unsupported)),
    )
