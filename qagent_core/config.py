import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = "Battle Balance Analyst Generative AI Agent"
APP_VERSION = "2.8.0"


def _int_setting(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return min(max(value, minimum), maximum)


def _bool_setting(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _float_setting(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        value = default
    return min(max(value, minimum), maximum)


MAX_AGENT_ITERATIONS = _int_setting("MAX_AGENT_ITERATIONS", 18, 1, 50)
MAX_TOOL_CALLS = _int_setting("MAX_TOOL_CALLS", 30, 1, 100)
AGENT_TIMEOUT_SECONDS = _int_setting("AGENT_TIMEOUT_SECONDS", 180, 10, 1800)
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4").strip() or "gpt-5.4"
DEFAULT_REASONING_EFFORT = os.getenv("OPENAI_REASONING_EFFORT", "none").strip() or "none"
ENABLE_TOOL_TRACE = _bool_setting("ENABLE_TOOL_TRACE", True)
ENABLE_DEBUG_LOG = _bool_setting("ENABLE_DEBUG_LOG", False)
BALANCE_MIN_SAMPLES = _int_setting("BALANCE_MIN_SAMPLES", 30, 10, 200)
BALANCE_MIN_WIN_RATE = _float_setting("BALANCE_MIN_WIN_RATE", 0.75, 0.5, 0.99)
BALANCE_MIN_WIN_RATE_DIFF = _float_setting("BALANCE_MIN_WIN_RATE_DIFF", 0.20, 0.01, 0.6)
BALANCE_MIN_WILSON_DIFF = _float_setting("BALANCE_MIN_WILSON_DIFF", 0.0, 0.0, 0.3)
BALANCE_FDR_ALPHA = _float_setting("BALANCE_FDR_ALPHA", 0.05, 0.001, 0.25)


def get_secret(name: str) -> str:
    """Read a secret exclusively from the process environment."""
    return os.getenv(name, "").strip()
