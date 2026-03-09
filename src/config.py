r"""Config persistence — stores app settings in %APPDATA%\PayslipApp\config.json."""

import json
import os
from pathlib import Path

APP_DATA_DIR = Path(os.environ.get("APPDATA", ".")) / "PayslipApp"
CONFIG_PATH = APP_DATA_DIR / "config.json"

DEFAULT_SUBJECT = "תלוש שכר - {month} {year}"
DEFAULT_BODY = """שלום {name},

מצורף תלוש השכר שלך לחודש {month} {year}.
הקובץ מוגן בסיסמה - מספר תעודת הזהות שלך.

בברכה,
מחלקת שכר"""

DEFAULTS = {
    "subject_template": DEFAULT_SUBJECT,
    "body_template": DEFAULT_BODY,
    "window_width": 1100,
    "window_height": 750,
}


def load_config() -> dict:
    """Load config from disk, falling back to defaults for missing keys."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    config = dict(DEFAULTS)

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config.update(saved)
        except (json.JSONDecodeError, OSError):
            pass

    return config


def save_config(config: dict) -> None:
    """Save config dict to disk."""
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
