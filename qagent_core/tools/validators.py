"""Input validation utilities for QAgent tools.

Provides safe, Agent-friendly validation errors and utility functions
to protect core tools from invalid user inputs without breaking Tool schemas.
"""

from __future__ import annotations

from typing import Any


class ToolValidationError(ValueError):
    """Raised when tool input validation fails.

    Used to produce Agent-safe error dicts instead of raw exceptions.
    """

    pass


def validate_int_range(
    value: Any,
    min_val: int | None = None,
    max_val: int | None = None,
    param_name: str = "value",
) -> int:
    """Validate and convert value to int within [min_val, max_val].

    Args:
        value: Value to validate
        min_val: Minimum allowed value (inclusive), or None
        max_val: Maximum allowed value (inclusive), or None
        param_name: Parameter name for error messages

    Returns:
        Validated integer value

    Raises:
        ToolValidationError: If validation fails
    """
    try:
        int_val = int(value)
    except (ValueError, TypeError) as e:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] {param_name}는 정수여야 합니다: {value}"
        ) from e

    if min_val is not None and int_val < min_val:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] {param_name}는 {min_val} 이상이어야 합니다: {int_val}"
        )

    if max_val is not None and int_val > max_val:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] {param_name}는 {max_val} 이하여야 합니다: {int_val}"
        )

    return int_val


def validate_float_range(
    value: Any,
    min_val: float | None = None,
    max_val: float | None = None,
    param_name: str = "value",
) -> float:
    """Validate and convert value to float within [min_val, max_val].

    Args:
        value: Value to validate
        min_val: Minimum allowed value (inclusive), or None
        max_val: Maximum allowed value (inclusive), or None
        param_name: Parameter name for error messages

    Returns:
        Validated float value

    Raises:
        ToolValidationError: If validation fails
    """
    try:
        float_val = float(value)
    except (ValueError, TypeError) as e:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] {param_name}는 숫자여야 합니다: {value}"
        ) from e

    if min_val is not None and float_val < min_val:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] {param_name}는 {min_val} 이상이어야 합니다: {float_val}"
        )

    if max_val is not None and float_val > max_val:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] {param_name}는 {max_val} 이하여야 합니다: {float_val}"
        )

    return float_val


def validate_choice(
    value: Any,
    choices: list[str] | tuple[str, ...],
    param_name: str = "value",
) -> str:
    """Validate that value is one of the allowed choices.

    Args:
        value: Value to validate
        choices: Allowed choices
        param_name: Parameter name for error messages

    Returns:
        Validated string value

    Raises:
        ToolValidationError: If validation fails
    """
    str_val = str(value).strip()
    if str_val not in choices:
        choices_str = ", ".join(str(c) for c in choices)
        raise ToolValidationError(
            f"[VALIDATION_ERROR] {param_name}은(는) 다음 중 하나여야 합니다: {choices_str} (입력: {str_val})"
        )
    return str_val


def validate_top_n(
    value: Any,
    max_top_n: int = 100,
    default_top_n: int = 10,
) -> int:
    """Validate top_n parameter for result limiting.

    Args:
        value: Value to validate
        max_top_n: Maximum allowed top_n value
        default_top_n: Default value if None or empty

    Returns:
        Validated top_n value

    Raises:
        ToolValidationError: If validation fails
    """
    if value is None or (isinstance(value, float) and str(value) == ""):
        return default_top_n

    try:
        top_n = int(value)
    except (ValueError, TypeError) as e:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] top_n은 정수여야 합니다: {value}"
        ) from e

    if top_n < 1:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] top_n은 1 이상이어야 합니다: {top_n}"
        )

    if top_n > max_top_n:
        raise ToolValidationError(
            f"[VALIDATION_ERROR] top_n은 {max_top_n} 이하여야 합니다: {top_n}"
        )

    return top_n


def validation_error_dict(error: ToolValidationError) -> dict[str, Any]:
    """Convert ToolValidationError to Agent-safe error dict.

    Args:
        error: ToolValidationError instance

    Returns:
        Agent-friendly error dictionary
    """
    msg = str(error)
    if msg.startswith("[VALIDATION_ERROR] "):
        msg = msg.replace("[VALIDATION_ERROR] ", "", 1)

    return {
        "status": "validation_error",
        "error": msg,
        "message": f"입력 검증 실패: {msg}",
    }
