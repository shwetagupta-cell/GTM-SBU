import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "gtm_data"
UPLOADS_DIR = DATA_DIR / "uploads"
STATE_FILE = DATA_DIR / "state.json"
ACCOUNTS_FILE = DATA_DIR / "accounts.json"
CONFIG_FILE = DATA_DIR / "config.json"
BUNDLED_PYTHON = Path(
    "/Users/shwetagupta/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
)

DEPARTMENTS = ["Viztown", "Events", "Digital Marketing", "Marketing", "Founder Connect"]
DEFAULT_ADMIN_ID = "1709"


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
    return config


def save_config(config):
    ensure_dirs()
    with CONFIG_FILE.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
