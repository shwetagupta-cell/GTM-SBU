import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
RESET_LOGS_FILE = DATA_DIR / "password_reset_logs.json"
ACCOUNTS_FILE = ROOT / "accounts.json"
CONTACTS_FILE = ROOT / "employee_contacts.json"
APP_CONFIG_FILE = ROOT / "app_config.json"
DOWNLOADS_DIR = Path("/Users/shwetagupta/Downloads")
BUNDLED_PYTHON = Path(
    "/Users/shwetagupta/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
)

DEFAULT_DATASETS = {
    "misWorkbook": str(DATA_DIR / "master_mis.xlsx"),
    "ytdWorkbook": str(DATA_DIR / "ytd_cash_flow.xlsx"),
    "closureWorkbook": str(DATA_DIR / "deal_closure.xlsx"),
    "employeeSheet": str(DOWNLOADS_DIR / "Employee YTD Incentive.xlsx"),
    "teamSheet": str(DOWNLOADS_DIR / "Team Sheet .xlsx"),
}

DATASET_LABELS = {
    "misWorkbook": "MIS Incentive Monthly Employee Data",
    "ytdWorkbook": "YTD Cash Flow",
    "closureWorkbook": "Closure Deal Mapping",
    "employeeSheet": "Employee YTD Incentive Sheet",
    "teamSheet": "Team Structure Sheet",
}


def ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)


def load_app_config():
    config = {
        "datasets": dict(DEFAULT_DATASETS),
        "smtp": {
            "host": "",
            "port": 587,
            "username": "",
            "password": "",
            "fromEmail": "",
            "useTls": True,
        },
        "adminEmployeeIds": ["1448"],
    }
    if APP_CONFIG_FILE.exists():
        try:
            with APP_CONFIG_FILE.open("r", encoding="utf-8") as handle:
                loaded = json.load(handle)
        except (OSError, json.JSONDecodeError):
            loaded = {}
        loaded_datasets = loaded.get("datasets", {})
        for key, fallback in DEFAULT_DATASETS.items():
            config["datasets"][key] = loaded_datasets.get(key) or fallback
        config["smtp"].update(loaded.get("smtp", {}))
        if loaded.get("adminEmployeeIds"):
            config["adminEmployeeIds"] = loaded["adminEmployeeIds"]
    return config


def save_app_config(config):
    ensure_dirs()
    with APP_CONFIG_FILE.open("w", encoding="utf-8") as handle:
        json.dump(config, handle, indent=2)
