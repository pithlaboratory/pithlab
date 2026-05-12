import os


def _get_env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def require_env(*keys: str) -> str:
    for key in keys:
        value = _get_env(key)
        if value:
            return value
    raise RuntimeError(f"Missing required environment variable. Tried: {', '.join(keys)}")


def optional_env(*keys: str, default: str = "") -> str:
    for key in keys:
        value = _get_env(key)
        if value:
            return value
    return default.strip()


def normalize_mode(value: str) -> str:
    value = value.strip().lower()
    return value if value in {"dev", "staging", "prod"} else "prod"


def normalize_log_level(value: str) -> str:
    value = value.strip().upper()
    return value if value in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"} else "INFO"


TG_TOKEN = require_env("TG_TOKEN", "TGTOKEN")
OPENROUTER_KEY = require_env("OPENROUTER_KEY")

OWNER_CHAT_ID = optional_env("OWNER_CHAT_ID")
GITHUB_TOKEN = optional_env("GITHUB_TOKEN")
TIMEWEB_KEY = optional_env("TIMEWEB_KEY")

PITH_MODE = normalize_mode(optional_env("PITH_MODE", default="prod"))
LOG_LEVEL = normalize_log_level(optional_env("LOG_LEVEL", default="INFO"))