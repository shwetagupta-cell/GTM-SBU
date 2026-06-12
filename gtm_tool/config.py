import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _path_from_env(name, default):
    value = os.environ.get(name)
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


DATA_DIR = _path_from_env("GTM_DATA_DIR", ROOT / "gtm_data")
UPLOADS_DIR = DATA_DIR / "uploads"
STATE_FILE = DATA_DIR / "state.json"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
CONFIG_FILE = DATA_DIR / "config.json"
BUNDLED_PYTHON = Path(
    "/Users/shwetagupta/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
)

DEPARTMENTS = ["Viztown", "Events", "Digital Marketing", "Marketing", "Founder Connect"]
DEFAULT_ADMIN_ID = "1709"
ENABLE_SEED_DATA = os.environ.get("GTM_ENABLE_SEED_DATA", "").strip().lower() in {"1", "true", "yes", "on"}


def ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)


def load_config():
    config = {
        "adminEmployeeIds": [DEFAULT_ADMIN_ID],
        "smtp": {
            "host": "",
            "port": 587,
            "username": "",
            "password": "",
            "fromEmail": "",
            "useTls": True,
        },
    }
    if CONFIG_FILE.exists():
        try:
            with CONFIG_FILE.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except (OSError, json.JSONDecodeError):
            loaded = {}
        if loaded.get("adminEmployeeIds"):
            config["adminEmployeeIds"] = loaded["adminEmployeeIds"]
        config["smtp"].update(loaded.get("smtp", {}))
    admin_ids = os.environ.get("GTM_ADMIN_EMPLOYEE_IDS")
    if admin_ids:
        config["adminEmployeeIds"] = [item.strip() for item in admin_ids.split(",") if item.strip()]
    env_smtp = {
        "host": os.environ.get("SMTP_HOST"),
        "port": os.environ.get("SMTP_PORT"),
        "username": os.environ.get("SMTP_USERNAME"),
        "password": os.environ.get("SMTP_PASSWORD"),
        "fromEmail": os.environ.get("SMTP_FROM_EMAIL"),
    }
    for key, value in env_smtp.items():
        if value not in (None, ""):
            config["smtp"][key] = int(value) if key == "port" else value
    if os.environ.get("SMTP_USE_TLS") not in (None, ""):
        config["smtp"]["useTls"] = os.environ.get("SMTP_USE_TLS", "").strip().lower() not in {"0", "false", "no", "off"}
    return config


def save_config(config):
    ensure_dirs()
    with CONFIG_FILE.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
