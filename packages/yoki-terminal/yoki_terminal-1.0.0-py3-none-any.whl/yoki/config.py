import json
from pathlib import Path

CONFIG_PATH = Path.home() / ".yoki_config.json"

DEFAULT_CONFIG = {"api_key": ""}

def load_api_key() -> str:
    """Return the saved API key, or empty string if none."""
    if CONFIG_PATH.exists():
        try:
            return json.load(open(CONFIG_PATH)).get("api_key", "")
        except Exception:
            return ""
    return ""

def set_api_key(api_key: str):
    """Save API key to config file."""
    config = {"api_key": api_key}
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)
