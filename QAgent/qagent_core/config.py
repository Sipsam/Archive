import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Battle Balance Analyst Generative AI Agent"
APP_VERSION = "2.8.0"


def _int_setting(name: str, default: int, minimum: int, maximum: int) -> int:
    """Read a bounded integer setting from the environment.

    Args:
        name: Environment variable name.
        default: Value used when the variable is absent or invalid.
        minimum: Lowest accepted value.
        maximum: Highest accepted value.

    Returns:
        The parsed value clamped to the allowed range.

    Raises:
        No exception is raised for malformed values; the default is used.
    """
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return min(max(value, minimum), maximum)


def _bool_setting(name: str, default: bool) -> bool:
    """Read a boolean setting from the environment.

    Args:
        name: Environment variable name.
        default: Value used when the variable is absent.

    Returns:
        True for common truthy strings, otherwise False.
    """
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float_setting(name: str, default: float, minimum: float, maximum: float) -> float:
    """Read a bounded float setting from the environment.

    Args:
        name: Environment variable name.
        default: Value used when the variable is absent or invalid.
        minimum: Lowest accepted value.
        maximum: Highest accepted value.

    Returns:
        The parsed value clamped to the allowed range.
    """
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return min(max(value, minimum), maximum)


MAX_AGENT_ITERATIONS = _int_setting("MAX_AGENT_ITERATIONS", 18, 1, 50)
MAX_TOOL_CALLS = _int_setting("MAX_TOOL_CALLS", 30, 1, 100)
AGENT_TIMEOUT_SECONDS = _int_setting("AGENT_TIMEOUT_SECONDS", 180, 10, 1800)
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4").strip() or "gpt-5.4"
DEFAULT_REASONING_EFFORT = (
    os.getenv("OPENAI_REASONING_EFFORT", "none").strip() or "none"
)
ENABLE_TOOL_TRACE = _bool_setting("ENABLE_TOOL_TRACE", True)
ENABLE_DEBUG_LOG = _bool_setting("ENABLE_DEBUG_LOG", False)
BALANCE_MIN_SAMPLES = _int_setting("BALANCE_MIN_SAMPLES", 30, 10, 200)
BALANCE_MIN_WIN_RATE = _float_setting("BALANCE_MIN_WIN_RATE", 0.75, 0.5, 0.99)
BALANCE_MIN_WIN_RATE_DIFF = _float_setting("BALANCE_MIN_WIN_RATE_DIFF", 0.20, 0.01, 0.6)
BALANCE_MIN_WILSON_DIFF = _float_setting("BALANCE_MIN_WILSON_DIFF", 0.0, 0.0, 0.3)
BALANCE_FDR_ALPHA = _float_setting("BALANCE_FDR_ALPHA", 0.05, 0.001, 0.25)
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "").strip()
AGENT_DATA_DIR = os.getenv("AGENT_DATA_DIR", "").strip()
AGENT_CORS_ORIGINS = os.getenv("AGENT_CORS_ORIGINS", "").strip()
ENABLE_RAG = _bool_setting("ENABLE_RAG", True)
RAG_INCLUDE_DATA_DOCS = _bool_setting("RAG_INCLUDE_DATA_DOCS", True)
RAG_TOP_K = _int_setting("RAG_TOP_K", 4, 0, 10)
MAX_AGENT_QUERY_CHARS = _int_setting("MAX_AGENT_QUERY_CHARS", 12000, 100, 50000)


def get_secret(name: str) -> str:
    """Read a secret exclusively from the process environment.

    Args:
        name: Environment variable name such as ``OPENAI_API_KEY`` or
            ``AGENT_API_KEY``.

    Returns:
        The stripped secret value, or an empty string when unset.

    Raises:
        No exception is raised for missing values.

    Security:
        This helper must only be used on the server side. Do not pass its return
        value into UI defaults, logs, API responses, or exception messages.
    """
    return os.getenv(name, "").strip()
