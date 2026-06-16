import base64
import csv
import io
import json
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from gtm_tool.auth_service import sync_accounts, upsert_account
from gtm_tool.config import DEPARTMENTS, DEFAULT_ADMIN_ID, ENABLE_SEED_DATA, ROOT, STATE_FILE, UPLOADS_DIR, ensure_dirs, load_config
from gtm_tool.excel_service import parse_workbook
from services.utils import clean_string, month_label, normalize_name, parse_number, slugify


SEED_DATA_DIR = ROOT / "gtm_seed_data"
DEFAULT_TEAM_PATH = SEED_DATA_DIR / "Demo GTM AND SBU Sheet 25 May.xlsx"
DEFAULT_GTM_LOGIC_PATH = SEED_DATA_DIR / "GTM - KPIs & Incentive Structure-2.xlsx"
DEFAULT_SBU_LOGIC_PATH = SEED_DATA_DIR / "SME SBU INCENTIVES 2026-27 (UPDATED).xlsx"
DEFAULT_PROJECT_PATH = SEED_DATA_DIR / "PROJECT_INCENTIVE_DISBURSAL.xlsx"

SEED_UPLOADS = {
    "team_master": ("seed-team-master", DEFAULT_TEAM_PATH),
    "gtm_logic": ("seed-gtm-logic", DEFAULT_GTM_LOGIC_PATH),
    "sbu_logic": ("seed-sbu-logic", DEFAULT_SBU_LOGIC_PATH),
    "project_cf": ("seed-project-cf", DEFAULT_PROJECT_PATH),
}


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


def _normalize_disbursal_type(value):
    text = clean_string(value).lower()
    mapping = {"annual": "annually", "annually": "annually", "quarterly": "quarterly", "monthly": "monthly"}
    return mapping.get(text, "quarterly")


def _fy_periods(base=None):
    base = base or datetime.now()
    start_year = base.year if base.month >= 4 else base.year - 1
    periods = []
    for month in range(4, 13):
        periods.append(f"{start_year}-{month:02d}")
    for month in range(1, 4):
        periods.append(f"{start_year + 1}-{month:02d}")
    return periods


def _current_period():
    now = datetime.now()
    return f"{now.year}-{now.month:02d}"


def _display_period(period_label):
    text = clean_string(period_label)
    try:
        return datetime.strptime(text, "%Y-%m").strftime("%b %Y")
    except ValueError:
        return month_label(text)


def _period_sort_key(period_label):
    try:
        return datetime.strptime(clean_string(period_label), "%Y-%m")
    except ValueError:
        return datetime.max


def _admin_employee():
    return {
        "employeeId": DEFAULT_ADMIN_ID,
        "name": "Shweta",
        "email": "shweta.gupta@flipspaces.com",
        "grade": "L1",
        "gradeBand": "F10",
        "designation": "Admin",
        "location": "Mumbai",
        "department": "Marketing",
        "sourceDepartment": "Marketing",
        "currentSbu": "GTM Admin",
        "newSbu": "GTM Admin",
        "businessUnit": "GTM",
        "logicKey": "Marketing",
        "reportingName": "",
        "reportingTo": "",
        "managerName": "",
        "managerDesignation": "",
        "hierarchyRole": "india_head",
        "disbursalType": "annually",
        "sharePercent": 100.0,
        "projectIncentivePercent": 3.0,
        "mySharePercent": 3.0,
        "departmentPercent": 100.0,
        "teamSharePercent": 100.0,
        "npsScore": 4.8,
        "status": "active",
    }


def _make_seed_upload(file_id, file_name, path, upload_type):
    return {
        "fileId": file_id,
        "fileName": file_name,
        "storedPath": _portable_path(path),
        "uploadedAt": _now(),
        "uploadType": upload_type,
        "recordCount": 0,
        "deleted": False,
        "seeded": True,
    }


def _portable_path(path):
    path = Path(path)
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _resolve_stored_path(path_value):
    cleaned_path = clean_string(path_value)
    if not cleaned_path:
        return Path()
    path = Path(cleaned_path)
    if not path:
        return path
    if path.exists():
        return path
    if not path.is_absolute():
        root_path = ROOT / path
        if root_path.exists():
            return root_path
    for _, seed_path in SEED_UPLOADS.values():
        if path.name == seed_path.name and seed_path.exists():
            return seed_path
    return path


def _restore_upload_file(upload):
    stored_path = _resolve_stored_path(upload.get("storedPath", ""))
    if stored_path.exists():
        return stored_path

    encoded = clean_string(upload.get("fileData"))
    if not encoded:
        return stored_path

    file_id = clean_string(upload.get("fileId")) or uuid.uuid4().hex
    file_name = clean_string(upload.get("fileName")) or "upload.xlsx"
    target_dir = UPLOADS_DIR / file_id
    target_dir.mkdir(parents=True, exist_ok=True)
    restored_path = target_dir / file_name
    restored_path.write_bytes(base64.b64decode(encoded.encode("ascii")))
    upload["fileId"] = file_id
    upload["storedPath"] = _portable_path(restored_path)
    return restored_path


def _public_upload(upload):
    return {key: value for key, value in upload.items() if key != "fileData"}


def _parse_achievement_band(text):
    value = clean_string(text).replace(" ", "").replace("%", "")
    if not value:
        return None
    if value.startswith(">="):
        threshold = parse_number(value[2:])
        return ("gte", threshold)
    if value.startswith(">"):
        threshold = parse_number(value[1:])
        return ("gt", threshold)
    if value.startswith("<"):
        threshold = parse_number(value[1:])
        return ("lt", threshold)
    if "-" in value:
        lower, upper = value.split("-", 1)
        return ("range", parse_number(lower), parse_number(upper))
    threshold = parse_number(value)
    return ("gte", threshold)


def _score_from_framework(row, framework):
    target = parse_number(row.get("target"))
    achieved = parse_number(row.get("achieved"))
    kpi_name = clean_string(row.get("kpiName")).lower()
    achievement_percent = (achieved / target * 100) if target else 0
    if kpi_name == "cac %":
        achievement_percent = (target / achieved * 100) if achieved else 0

    bands = framework.get("scoreBands") or {}
    if clean_string(bands.get("5")).lower() == "actual csat rating":
        if achieved >= 4.5:
            return 5
        if achieved >= 4.0:
            return 4
        if achieved >= 3.5:
            return 3
        if achieved >= 3.0:
            return 2
        return 1

    if "<t" in clean_string(bands.get("5")).lower():
        delta = achieved - target
        if delta < 0:
            return 5
        if delta <= 7:
            return 4
        if delta <= 14:
            return 3
        if delta <= 21:
            return 2
        return 1

    if "+2" in clean_string(bands.get("5")):
        delta = achieved - target
        if delta > 0.02:
            return 5
        if 0 <= delta <= 0.02:
            return 4
        if -0.02 <= delta < 0:
            return 3
        if -0.05 <= delta < -0.02:
            return 2
        return 1

    if kpi_name in {"csat", "tsat"} and achieved:
        if achieved >= 4.5:
            return 5
        if achieved >= 4.0:
            return 4
        if achieved >= 3.5:
            return 3
        if achieved >= 3.0:
            return 2
        return 1

    for score in ("5", "4", "3", "2", "1"):
        band = _parse_achievement_band(bands.get(score, ""))
        if not band:
            continue
        kind = band[0]
        if kind == "gt" and achievement_percent > band[1]:
            return int(score)
        if kind == "gte" and achievement_percent >= band[1]:
            return int(score)
        if kind == "lt":
            compare_value = achieved if target and target > 1 else achievement_percent
            if compare_value < band[1]:
                return int(score)
        if kind == "range" and band[1] <= achievement_percent <= band[2]:
            return int(score)
    return 0


def _default_nps_rules():
    base = [
        {"min": 3.5, "max": 4, "disbursal": 80},
        {"min": 4, "max": 4.5, "disbursal": 90},
        {"min": 4.5, "max": 5.01, "disbursal": 100},
    ]
    return {"monthly": base, "quarterly": base, "annually": base}


def _parse_incentive_rules(rows):
    rules = {"monthly": [], "quarterly": [], "annually": []}
    for row in rows:
        scheme = _normalize_disbursal_type(row.get("scheme"))
        range_text = clean_string(row.get("npsRange"))
        disbursal_value = parse_number(row.get("disbursal"))
        if not range_text or disbursal_value <= 0:
            continue
        disbursal_percent = int(round(disbursal_value * 100 if disbursal_value <= 1 else disbursal_value))
        if range_text.startswith("3.5"):
            rules[scheme].append({"min": 3.5, "max": 4, "disbursal": disbursal_percent})
        elif range_text.startswith("4 to"):
            rules[scheme].append({"min": 4, "max": 4.5, "disbursal": disbursal_percent})
        elif "4.5" in range_text:
            rules[scheme].append({"min": 4.5, "max": 5.01, "disbursal": disbursal_percent})
    for key, default_rows in _default_nps_rules().items():
        if not rules[key]:
            rules[key] = default_rows
    return rules


def _nps_disbursal_from_rules(rules, scheme, score):
    scheme = _normalize_disbursal_type(scheme)
    for row in rules.get(scheme, []):
        if row["min"] <= score < row["max"]:
            return row["disbursal"]
    return 0


def _within_date_range(period_label, start_date="", end_date=""):
    try:
        period_date = datetime.strptime(clean_string(period_label), "%Y-%m")
    except ValueError:
        return True
    if start_date:
        try:
            if period_date < datetime.strptime(start_date[:10], "%Y-%m-%d").replace(day=1):
                return False
        except ValueError:
            pass
    if end_date:
        try:
            if period_date > datetime.strptime(end_date[:10], "%Y-%m-%d").replace(day=1):
                return False
        except ValueError:
            pass
    return True


def _name_tokens(value):
    return [token for token in normalize_name(value).split() if len(token) > 1]


def _similar_token(left, right):
    if not left or not right:
        return False
    return left == right or left.startswith(right) or right.startswith(left) or SequenceMatcher(None, left, right).ratio() >= 0.86


def _project_name_matches_employee(mapped_name, employee_name):
    mapped_tokens = _name_tokens(mapped_name)
    employee_tokens = _name_tokens(employee_name)
    if not mapped_tokens or not employee_tokens:
        return False
    if normalize_name(mapped_name) == normalize_name(employee_name):
        return True
    return all(any(_similar_token(mapped_token, employee_token) for employee_token in employee_tokens) for mapped_token in mapped_tokens)


class GTMDataService:
    def __init__(self):
        self.state = {}
        self._clear_match_caches()
        self.reload()

    def _clear_match_caches(self):
        self._project_resolution_cache = {}
        self._active_employee_match_cache = None

    def _default_state(self):
        return {
            "schemaVersion": 3,
            "uploadedFiles": self._seed_uploads() if ENABLE_SEED_DATA else [],
            "employeeOverrides": {},
            "kpiOverrides": {},
            "projectOverrides": {},
            "monthlyStatuses": {},
            "deletedEmployeeStack": [],
            "employees": [],
            "frameworks": [],
            "kpis": [],
            "projects": [],
            "incentiveRules": _default_nps_rules(),
            "loadedAt": _now(),
        }

    def _seed_uploads(self):
        return [
            _make_seed_upload(file_id, seed_path.name, seed_path, upload_type)
            for upload_type, (file_id, seed_path) in SEED_UPLOADS.items()
        ]

    def _needs_bootstrap(self, raw):
        return raw.get("schemaVersion") != 3

    def _ensure_seed_uploads(self, raw_state):
        uploads = raw_state.setdefault("uploadedFiles", [])
        if not ENABLE_SEED_DATA:
            raw_state["uploadedFiles"] = [
                upload for upload in uploads if not upload.get("seeded") and not clean_string(upload.get("fileId")).startswith("seed-")
            ]
            return

        active_types = set()
        by_file_id = {item.get("fileId"): item for item in uploads}
        seed_by_file_id = {file_id: (upload_type, seed_path) for upload_type, (file_id, seed_path) in SEED_UPLOADS.items()}

        for upload in uploads:
            if upload.get("deleted"):
                continue
            seed_record = seed_by_file_id.get(upload.get("fileId"))
            if seed_record and seed_record[1].exists():
                upload["uploadType"] = seed_record[0]
                upload["fileName"] = seed_record[1].name
                upload["storedPath"] = _portable_path(seed_record[1])
                upload["seeded"] = True
                stored_path = seed_record[1]
            else:
                stored_path = _restore_upload_file(upload)
            if stored_path.exists():
                upload["storedPath"] = _portable_path(stored_path)
                active_types.add(upload.get("uploadType"))

        for upload_type, (file_id, seed_path) in SEED_UPLOADS.items():
            if upload_type in active_types or not seed_path.exists():
                continue
            existing = by_file_id.get(file_id)
            if existing:
                if existing.get("deleted"):
                    continue
                existing.update(
                    {
                        "fileName": seed_path.name,
                        "storedPath": _portable_path(seed_path),
                        "uploadType": upload_type,
                        "deleted": False,
                        "seeded": True,
                    }
                )
            else:
                uploads.append(_make_seed_upload(file_id, seed_path.name, seed_path, upload_type))

    def _frameworks_for_employee(self, employee, frameworks):
        logic_key = clean_string(employee.get("logicKey"))
        business_unit = clean_string(employee.get("businessUnit"))
        if business_unit == "SBU":
            return [item for item in frameworks if item.get("source") == "sbu" and item.get("matchKey") == logic_key]
        return [item for item in frameworks if item.get("source") == "gtm" and item.get("matchKey") == employee.get("department")]

    def _weightage_for_grade(self, framework, grade):
        weights = {clean_string(key).upper(): parse_number(value) for key, value in (framework.get("gradeWeights") or {}).items()}
        grade_key = clean_string(grade).upper()
        if weights.get(grade_key):
            return weights[grade_key]
        for fallback in ("L4", "L3", "L2", "L1"):
            if weights.get(fallback):
                return weights[fallback]
        return 0.0

    def _merge_employee(self, employee, override):
        merged = dict(employee)
        for key, value in override.items():
            if value not in (None, ""):
                merged[key] = value
        return merged

    def _latest_active_uploads(self, raw_state):
        latest_by_type = {}
        for upload in raw_state.get("uploadedFiles", []):
            if upload.get("deleted"):
                continue
            upload_type = clean_string(upload.get("uploadType"))
            if not upload_type:
                continue
            current = latest_by_type.get(upload_type)
            if not current or clean_string(upload.get("uploadedAt")) >= clean_string(current.get("uploadedAt")):
                latest_by_type[upload_type] = upload
        return sorted(latest_by_type.values(), key=lambda item: clean_string(item.get("uploadedAt")))

    def _build_from_uploads(self, raw_state):
        self._ensure_seed_uploads(raw_state)
        employees = {DEFAULT_ADMIN_ID: _admin_employee()}
        frameworks = []
        projects = []
        incentive_rows = []
        parsed_upload_types = set()
        cached_incentive_rules = raw_state.get("incentiveRules", _default_nps_rules())

        for upload in self._latest_active_uploads(raw_state):
            stored_path = _restore_upload_file(upload)
            if not stored_path.exists():
                continue
            upload["storedPath"] = _portable_path(stored_path)
            parsed = parse_workbook(stored_path, upload.get("uploadType", ""))
            upload["recordCount"] = parsed.get("recordCount", 0)
            upload["uploadType"] = parsed.get("uploadType") or upload.get("uploadType")
            if upload["uploadType"] == "team_master":
                parsed_upload_types.add("team_master")
                for employee in parsed.get("employees", []):
                    current = employees.get(employee["employeeId"], {})
                    employees[employee["employeeId"]] = {**current, **employee}
            elif upload["uploadType"] in {"gtm_logic", "sbu_logic"}:
                parsed_upload_types.add(upload["uploadType"])
                frameworks.extend(parsed.get("frameworks", []))
                incentive_rows.extend(parsed.get("incentiveRules", []))
            elif upload["uploadType"] == "project_cf":
                parsed_upload_types.add("project_cf")
                projects = parsed.get("projects", [])

        if "team_master" not in parsed_upload_types:
            for employee in raw_state.get("employees", []):
                employee_id = clean_string(employee.get("employeeId"))
                if not employee_id or employee_id == DEFAULT_ADMIN_ID:
                    continue
                employees[employee_id] = dict(employee)
        if not {"gtm_logic", "sbu_logic"} & parsed_upload_types:
            frameworks = list(raw_state.get("frameworks", []))
        elif "gtm_logic" not in parsed_upload_types or "sbu_logic" not in parsed_upload_types:
            existing_frameworks = list(raw_state.get("frameworks", []))
            parsed_sources = {"gtm" if item == "gtm_logic" else "sbu" for item in parsed_upload_types if item in {"gtm_logic", "sbu_logic"}}
            frameworks.extend([item for item in existing_frameworks if item.get("source") not in parsed_sources])
        if "project_cf" not in parsed_upload_types:
            projects = list(raw_state.get("projects", []))

        for employee_id, override in raw_state.get("employeeOverrides", {}).items():
            if employee_id not in employees:
                employees[employee_id] = {
                    "employeeId": employee_id,
                    "name": clean_string(override.get("name")) or employee_id,
                    "email": clean_string(override.get("email")).lower(),
                    "grade": clean_string(override.get("grade")) or "L3",
                    "gradeBand": clean_string(override.get("gradeBand")),
                    "designation": clean_string(override.get("designation")) or "Employee",
                    "location": clean_string(override.get("location")) or "Mumbai",
                    "department": clean_string(override.get("department")) or "Marketing",
                    "sourceDepartment": clean_string(override.get("sourceDepartment")),
                    "currentSbu": clean_string(override.get("currentSbu")),
                    "newSbu": clean_string(override.get("newSbu")),
                    "businessUnit": clean_string(override.get("businessUnit")) or "GTM",
                    "logicKey": clean_string(override.get("logicKey")) or clean_string(override.get("department")) or "Marketing",
                    "reportingName": clean_string(override.get("reportingName")),
                    "reportingTo": clean_string(override.get("reportingTo")),
                    "managerName": clean_string(override.get("managerName")),
                    "managerDesignation": clean_string(override.get("managerDesignation")),
                    "hierarchyRole": clean_string(override.get("hierarchyRole")) or "manager",
                    "disbursalType": _normalize_disbursal_type(override.get("disbursalType")),
                    "sharePercent": parse_number(override.get("sharePercent")) or 100.0,
                    "projectIncentivePercent": parse_number(override.get("projectIncentivePercent")) or 1.5,
                    "mySharePercent": parse_number(override.get("mySharePercent")) or parse_number(override.get("projectIncentivePercent")) or 1.5,
                    "departmentPercent": parse_number(override.get("departmentPercent")) or 100.0,
                    "teamSharePercent": parse_number(override.get("teamSharePercent")) or 100.0,
                    "npsScore": parse_number(override.get("npsScore")) or 4.5,
                    "status": clean_string(override.get("status")) or "active",
                }
            employees[employee_id] = self._merge_employee(employees[employee_id], override)

        name_to_id = {normalize_name(item.get("name")): item["employeeId"] for item in employees.values()}
        designation_map = {normalize_name(item.get("name")): item.get("designation", "") for item in employees.values()}
        for employee in employees.values():
            manager_name = clean_string(employee.get("reportingName") or employee.get("managerName"))
            manager_key = normalize_name(manager_name)
            employee["reportingTo"] = employee.get("reportingTo") or name_to_id.get(manager_key, "")
            employee["managerName"] = manager_name
            employee["managerDesignation"] = employee.get("managerDesignation") or designation_map.get(manager_key, "")
            employee["email"] = clean_string(employee.get("email")).lower()
            employee["grade"] = clean_string(employee.get("grade")).upper() or "L3"
            employee["department"] = clean_string(employee.get("department")) or "Marketing"
            employee["location"] = clean_string(employee.get("location")) or "Mumbai"
            employee["designation"] = clean_string(employee.get("designation")) or "Employee"
            employee["businessUnit"] = clean_string(employee.get("businessUnit")) or "GTM"
            employee["logicKey"] = clean_string(employee.get("logicKey")) or employee.get("department")
            employee["disbursalType"] = _normalize_disbursal_type(employee.get("disbursalType"))
            employee["sharePercent"] = parse_number(employee.get("sharePercent")) or 100.0
            employee["projectIncentivePercent"] = parse_number(employee.get("projectIncentivePercent")) or 1.5
            employee["mySharePercent"] = parse_number(employee.get("mySharePercent")) or employee["projectIncentivePercent"]
            employee["departmentPercent"] = parse_number(employee.get("departmentPercent")) or 100.0
            employee["teamSharePercent"] = parse_number(employee.get("teamSharePercent")) or 100.0
            employee["npsScore"] = parse_number(employee.get("npsScore")) or 4.5
            employee["status"] = clean_string(employee.get("status")).lower() or "active"

        periods = set(_fy_periods())
        for project in projects:
            if clean_string(project.get("periodLabel")):
                periods.add(clean_string(project.get("periodLabel")))
        for store in (raw_state.get("kpiOverrides", {}), raw_state.get("projectOverrides", {}), raw_state.get("monthlyStatuses", {})):
            for key in store.keys():
                parts = clean_string(key).split("|")
                if len(parts) >= 2:
                    periods.add(parts[1])
        periods = sorted(periods, key=_period_sort_key)

        kpis = []
        for employee in employees.values():
            if employee.get("status") != "active":
                continue
            applicable_frameworks = self._frameworks_for_employee(employee, frameworks)
            for period_label in periods:
                for framework in applicable_frameworks:
                    record_key = f"{employee['employeeId']}|{period_label}|{framework['frameworkId']}"
                    override = raw_state.get("kpiOverrides", {}).get(record_key, {})
                    weightage = self._weightage_for_grade(framework, employee.get("grade"))
                    kpis.append(
                        {
                            "recordId": slugify(record_key),
                            "recordKey": record_key,
                            "employeeId": employee["employeeId"],
                            "periodLabel": period_label,
                            "periodType": "monthly",
                            "kraCategory": framework.get("kraCategory", ""),
                            "kpiName": framework.get("kpiName", ""),
                            "frameworkId": framework.get("frameworkId", ""),
                            "displayOrder": framework.get("displayOrder", 0),
                            "target": parse_number(override.get("target")) if override.get("target") not in (None, "") else parse_number(framework.get("target")),
                            "achieved": parse_number(override.get("achieved")) if override.get("achieved") not in (None, "") else parse_number(framework.get("achieved")),
                            "weightage": weightage,
                            "npsScore": parse_number(override.get("npsScore")) or employee.get("npsScore", 4.5),
                            "uploadedFileId": framework.get("sourceFileId", ""),
                            "notes": clean_string(override.get("notes")),
                        }
                    )

        return {
            "schemaVersion": 3,
            "uploadedFiles": raw_state.get("uploadedFiles", []),
            "employeeOverrides": raw_state.get("employeeOverrides", {}),
            "kpiOverrides": raw_state.get("kpiOverrides", {}),
            "projectOverrides": raw_state.get("projectOverrides", {}),
            "monthlyStatuses": raw_state.get("monthlyStatuses", {}),
            "deletedEmployeeStack": raw_state.get("deletedEmployeeStack", []),
            "employees": list(employees.values()),
            "frameworks": frameworks,
            "kpis": kpis,
            "projects": projects,
            "incentiveRules": _parse_incentive_rules(incentive_rows) if incentive_rows else cached_incentive_rules,
            "loadedAt": _now(),
        }

    def reload(self):
        ensure_dirs()
        if not STATE_FILE.exists():
            raw = self._build_from_uploads(self._default_state())
            STATE_FILE.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        else:
            raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if self._needs_bootstrap(raw):
                raw = self._build_from_uploads(self._default_state())
            else:
                raw = self._build_from_uploads(raw)
            STATE_FILE.write_text(json.dumps(raw, indent=2), encoding="utf-8")

        employees = {item["employeeId"]: item for item in raw.get("employees", [])}
        sync_accounts(employees)
        self.state = {
            "schemaVersion": raw.get("schemaVersion", 3),
            "employees": employees,
            "kpis": raw.get("kpis", []),
            "uploadedFiles": raw.get("uploadedFiles", []),
            "frameworks": raw.get("frameworks", []),
            "projects": raw.get("projects", []),
            "incentiveRules": raw.get("incentiveRules", _default_nps_rules()),
            "employeeOverrides": raw.get("employeeOverrides", {}),
            "kpiOverrides": raw.get("kpiOverrides", {}),
            "projectOverrides": raw.get("projectOverrides", {}),
            "monthlyStatuses": raw.get("monthlyStatuses", {}),
            "deletedEmployeeStack": raw.get("deletedEmployeeStack", []),
            "loadedAt": raw.get("loadedAt", _now()),
        }
        self._clear_match_caches()

    def persist(self):
        ensure_dirs()
        STATE_FILE.write_text(
            json.dumps(
                {
                    "schemaVersion": self.state["schemaVersion"],
                    "uploadedFiles": self.state["uploadedFiles"],
                    "employeeOverrides": self.state["employeeOverrides"],
                    "kpiOverrides": self.state["kpiOverrides"],
                    "projectOverrides": self.state["projectOverrides"],
                    "monthlyStatuses": self.state["monthlyStatuses"],
                    "deletedEmployeeStack": self.state["deletedEmployeeStack"],
                    "employees": list(self.state["employees"].values()),
                    "kpis": self.state["kpis"],
                    "frameworks": self.state["frameworks"],
                    "projects": self.state["projects"],
                    "incentiveRules": self.state["incentiveRules"],
                    "loadedAt": _now(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        self.reload()

    def _accessible_employee_ids(self, viewer_id, admin_mode=False):
        if admin_mode:
            return [item["employeeId"] for item in self.state["employees"].values() if item.get("status") == "active"]
        accessible = {viewer_id}
        queue = [viewer_id]
        while queue:
            manager_id = queue.pop(0)
            children = [
                item["employeeId"]
                for item in self.state["employees"].values()
                if item.get("status") == "active" and item.get("reportingTo") == manager_id
            ]
            for child_id in children:
                if child_id in accessible:
                    continue
                accessible.add(child_id)
                queue.append(child_id)
        return sorted(accessible)

    def employee_search(self, viewer_id, admin_mode=False, term=""):
        term = clean_string(term).lower()
        accessible = set(self._accessible_employee_ids(viewer_id, admin_mode))
        admin_ids = set(load_config().get("adminEmployeeIds", []))
        items = []
        for employee in self.state["employees"].values():
            if employee.get("status") != "active" or employee["employeeId"] not in accessible:
                continue
            haystack = " ".join(
                [
                    employee.get("employeeId", ""),
                    employee.get("name", ""),
                    employee.get("department", ""),
                    employee.get("designation", ""),
                    employee.get("email", ""),
                    employee.get("businessUnit", ""),
                ]
            ).lower()
            if term and term not in haystack:
                continue
            items.append(
                {
                    "employeeId": employee["employeeId"],
                    "name": employee.get("name", employee["employeeId"]),
                    "department": employee.get("department", ""),
                    "designation": employee.get("designation", ""),
                    "grade": employee.get("grade", ""),
                    "location": employee.get("location", ""),
                    "hierarchyRole": employee.get("hierarchyRole", "manager"),
                    "disbursalType": employee.get("disbursalType", "quarterly"),
                    "sharePercent": employee.get("sharePercent", 100),
                    "projectIncentivePercent": employee.get("projectIncentivePercent", 1.5),
                    "mySharePercent": employee.get("mySharePercent", employee.get("projectIncentivePercent", 1.5)),
                    "departmentPercent": employee.get("departmentPercent", 100),
                    "teamSharePercent": employee.get("teamSharePercent", 100),
                    "npsScore": employee.get("npsScore", 4.5),
                    "email": employee.get("email", ""),
                    "businessUnit": employee.get("businessUnit", "GTM"),
                    "adminAccess": employee["employeeId"] in admin_ids,
                }
            )
        return sorted(items, key=lambda item: (item["name"], item["employeeId"]))

    def upsert_employee(self, payload):
        employee_id = clean_string(payload.get("employeeId"))
        if not employee_id:
            raise ValueError("Employee ID is required")
        override = dict(self.state["employeeOverrides"].get(employee_id, {}))
        override.update(
            {
                "employeeId": employee_id,
                "name": clean_string(payload.get("name")) or override.get("name", ""),
                "email": clean_string(payload.get("email")).lower() or override.get("email", ""),
                "grade": clean_string(payload.get("grade")).upper() or override.get("grade", ""),
                "location": clean_string(payload.get("location")) or override.get("location", ""),
                "department": clean_string(payload.get("department")) or override.get("department", ""),
                "designation": clean_string(payload.get("designation")) or override.get("designation", ""),
                "reportingTo": clean_string(payload.get("reportingTo")) or override.get("reportingTo", ""),
                "reportingName": clean_string(payload.get("reportingName")) or override.get("reportingName", ""),
                "managerName": clean_string(payload.get("managerName")) or override.get("managerName", ""),
                "managerDesignation": clean_string(payload.get("managerDesignation")) or override.get("managerDesignation", ""),
                "hierarchyRole": clean_string(payload.get("hierarchyRole")).lower() or override.get("hierarchyRole", "manager"),
                "businessUnit": clean_string(payload.get("businessUnit")) or override.get("businessUnit", "GTM"),
                "logicKey": clean_string(payload.get("logicKey")) or override.get("logicKey", clean_string(payload.get("department"))),
                "disbursalType": _normalize_disbursal_type(payload.get("disbursalType") or override.get("disbursalType")),
                "sharePercent": parse_number(payload.get("sharePercent"))
                if payload.get("sharePercent") not in (None, "")
                else parse_number(override.get("sharePercent")) or 100.0,
                "projectIncentivePercent": parse_number(payload.get("projectIncentivePercent"))
                if payload.get("projectIncentivePercent") not in (None, "")
                else parse_number(override.get("projectIncentivePercent")) or 1.5,
                "mySharePercent": parse_number(payload.get("mySharePercent"))
                if payload.get("mySharePercent") not in (None, "")
                else parse_number(override.get("mySharePercent")) or parse_number(override.get("projectIncentivePercent")) or 1.5,
                "departmentPercent": parse_number(payload.get("departmentPercent"))
                if payload.get("departmentPercent") not in (None, "")
                else parse_number(override.get("departmentPercent")) or 100.0,
                "teamSharePercent": parse_number(payload.get("teamSharePercent"))
                if payload.get("teamSharePercent") not in (None, "")
                else parse_number(override.get("teamSharePercent")) or 100.0,
                "npsScore": parse_number(payload.get("npsScore")) or parse_number(override.get("npsScore")) or 4.5,
                "status": clean_string(payload.get("status")).lower() or override.get("status", "active"),
            }
        )
        self.state["employeeOverrides"][employee_id] = override
        self.persist()
        upsert_account(
            employee_id,
            override.get("name", employee_id),
            designation=override.get("designation", ""),
            department=override.get("department", ""),
            email=override.get("email", ""),
            login_id=employee_id,
            temp_password=clean_string(payload.get("tempPassword")),
            status=override.get("status", "active"),
        )
        self.reload()
        return self.state["employees"].get(employee_id, override)

    def delete_employee(self, employee_id):
        employee_id = clean_string(employee_id)
        employee = self.state["employees"].get(employee_id)
        if not employee or employee_id == DEFAULT_ADMIN_ID:
            return False
        self.state["deletedEmployeeStack"].append(
            {"employeeId": employee_id, "override": dict(self.state["employeeOverrides"].get(employee_id, {}))}
        )
        current = dict(self.state["employeeOverrides"].get(employee_id, {}))
        current["status"] = "inactive"
        self.state["employeeOverrides"][employee_id] = current
        self.persist()
        return True

    def undo_delete_employee(self):
        if not self.state["deletedEmployeeStack"]:
            return None
        item = self.state["deletedEmployeeStack"].pop()
        employee_id = item.get("employeeId")
        override = dict(item.get("override", {}))
        override["status"] = "active"
        self.state["employeeOverrides"][employee_id] = override
        self.persist()
        return self.state["employees"].get(employee_id)

    def _framework_map(self):
        return {item.get("frameworkId"): item for item in self.state["frameworks"]}

    def _kpi_metrics(self, row):
        framework = self._framework_map().get(row.get("frameworkId"), {})
        target = parse_number(row.get("target"))
        achieved = parse_number(row.get("achieved"))
        kpi_name = clean_string(row.get("kpiName")).lower()
        if kpi_name == "cac %":
            achievement_percent = (target / achieved * 100) if achieved else 0
        else:
            achievement_percent = (achieved / target * 100) if target else 0
        score = _score_from_framework(row, framework) if framework else 0
        weighted_score = score * parse_number(row.get("weightage"))
        action = "Above Target" if achievement_percent > 100 else "On Track" if achievement_percent >= 80 else "Needs Improvement"
        return {
            **row,
            "achievementPercent": round(achievement_percent, 2),
            "score": score,
            "finalWeightedScore": round(weighted_score, 2),
            "action": action,
        }

    def _active_employees_for_project_matching(self):
        if self._active_employee_match_cache is None:
            self._active_employee_match_cache = [
                {
                    "employeeId": employee["employeeId"],
                    "name": employee.get("name", ""),
                    "nameTokens": _name_tokens(employee.get("name")),
                }
                for employee in self.state["employees"].values()
                if employee.get("status") == "active"
            ]
        return self._active_employee_match_cache

    def _resolve_project_employee_ids(self, mapped_names):
        cache_key = tuple(normalize_name(name) for name in mapped_names if normalize_name(name))
        if cache_key in self._project_resolution_cache:
            return list(self._project_resolution_cache[cache_key])
        employees = self._active_employees_for_project_matching()
        resolved_ids = []
        seen = set()
        for mapped_name in mapped_names:
            mapped_key = normalize_name(mapped_name)
            if not mapped_key:
                continue
            matches = [
                employee
                for employee in employees
                if _project_name_matches_employee(mapped_name, employee.get("name"))
            ]
            if not matches:
                mapped_tokens = _name_tokens(mapped_name)
                if len(mapped_tokens) == 1:
                    matches = [
                        employee
                        for employee in employees
                        if any(_similar_token(mapped_tokens[0], token) for token in employee.get("nameTokens", []))
                    ]
                elif mapped_tokens:
                    matches = [
                        employee
                        for employee in employees
                        if employee.get("nameTokens") and _similar_token(mapped_tokens[0], employee["nameTokens"][0])
                    ]
            if len(matches) != 1:
                continue
            employee_id = matches[0]["employeeId"]
            if employee_id not in seen:
                seen.add(employee_id)
                resolved_ids.append(employee_id)
        self._project_resolution_cache[cache_key] = tuple(resolved_ids)
        return resolved_ids

    def _project_rows_for_employee(self, employee, period_label, disbursal_percent):
        employee_name_key = normalize_name(employee.get("name"))
        employee_id_key = clean_string(employee.get("employeeId"))
        items = []
        all_projects = self.state.get("projects", [])
        month_projects = [item for item in all_projects if clean_string(item.get("periodLabel")) == clean_string(period_label)]
        candidate_projects = month_projects if month_projects else [item for item in all_projects if not clean_string(item.get("periodLabel"))]
        for project in candidate_projects:
            mapped = [clean_string(name) for name in project.get("mappedEmployees", []) if clean_string(name)]
            normalized = [normalize_name(name) for name in mapped]
            resolved_employee_ids = self._resolve_project_employee_ids(mapped)
            project_employee_id = clean_string(project.get("employeeId"))
            if project_employee_id:
                if project_employee_id != employee_id_key:
                    continue
            elif resolved_employee_ids:
                if employee_id_key not in resolved_employee_ids:
                    continue
            elif employee_name_key not in normalized:
                continue
            override_key = f"{employee['employeeId']}|{period_label}|{project.get('projectId') or project.get('projectName')}"
            override = self.state.get("projectOverrides", {}).get(override_key, {})
            share_percent = parse_number(override.get("sharePercent")) if override.get("sharePercent") not in (None, "") else parse_number(employee.get("sharePercent"))
            department_percent = parse_number(override.get("departmentPercent")) if override.get("departmentPercent") not in (None, "") else parse_number(employee.get("departmentPercent"))
            team_share_percent = parse_number(override.get("teamSharePercent")) if override.get("teamSharePercent") not in (None, "") else (
                100.0 / max(len(resolved_employee_ids) or len(normalized), 1)
            )
            my_share_percent = parse_number(employee.get("mySharePercent")) or parse_number(employee.get("projectIncentivePercent"))
            project_value = parse_number(project.get("projectValue"))
            cashflow_value = parse_number(project.get("cashflowValue"))
            if project.get("incentiveBaseValue") not in (None, ""):
                incentive_base_value = parse_number(project.get("incentiveBaseValue"))
            elif project.get("cashflowValue") not in (None, ""):
                incentive_base_value = cashflow_value
            else:
                incentive_base_value = project_value
            accrued_value = (
                incentive_base_value
                * (share_percent / 100.0)
                * (department_percent / 100.0)
                * (team_share_percent / 100.0)
                * (my_share_percent / 100.0)
            )
            final_disbursal = accrued_value * (disbursal_percent / 100.0)
            items.append(
                {
                    "projectId": clean_string(project.get("projectId")),
                    "projectName": clean_string(project.get("projectName")),
                    "periodLabel": clean_string(project.get("periodLabel")) or period_label,
                    "assignedRole": clean_string(project.get("assignedRole")),
                    "sourceStatus": clean_string(project.get("sourceStatus")),
                    "projectValue": round(project_value, 2),
                    "cashflowValue": round(cashflow_value, 2),
                    "incentiveBaseValue": round(incentive_base_value, 2),
                    "sharePercent": round(share_percent, 2),
                    "departmentPercent": round(department_percent, 2),
                    "teamSharePercent": round(team_share_percent, 2),
                    "mySharePercent": round(my_share_percent, 2),
                    "accruedValue": round(accrued_value, 2),
                    "npsDisbursalPercent": round(disbursal_percent, 2),
                    "finalDisbursalValue": round(final_disbursal, 2),
                }
            )
        return sorted(items, key=lambda item: item.get("projectName", ""))

    def _period_summary(self, employee, period_label, rows):
        rows = [self._kpi_metrics(item) for item in rows]
        total_weightage = sum(parse_number(item.get("weightage")) for item in rows)
        total_weighted_score = sum(parse_number(item.get("finalWeightedScore")) for item in rows)
        final_score = total_weighted_score / total_weightage if total_weightage else 0
        nps_score = round(sum(parse_number(item.get("score")) for item in rows) / len(rows), 2) if rows else parse_number(employee.get("npsScore"))
        rows = [{**item, "npsScore": nps_score} for item in rows]
        disbursal_percent = _nps_disbursal_from_rules(self.state.get("incentiveRules", _default_nps_rules()), employee.get("disbursalType"), nps_score)
        projects = self._project_rows_for_employee(employee, period_label, disbursal_percent)
        accrued_total = sum(item["accruedValue"] for item in projects)
        disbursal_total = sum(item["finalDisbursalValue"] for item in projects)
        for row in rows:
            row_share = (parse_number(row.get("finalWeightedScore")) / total_weighted_score) if total_weighted_score else 0
            row["incentiveAmount"] = round(disbursal_total * row_share, 2)
        status_key = f"{employee['employeeId']}|{period_label}"
        return {
            "periodLabel": period_label,
            "displayPeriod": _display_period(period_label),
            "periodType": "monthly",
            "finalScore": round(final_score, 2),
            "performancePercent": round((final_score / 5) * 100 if final_score else 0, 2),
            "npsScore": nps_score,
            "averageNps": nps_score,
            "disbursalPercent": disbursal_percent,
            "projectValue": round(sum(item["projectValue"] for item in projects), 2),
            "projectIncentivePercent": round(parse_number(employee.get("projectIncentivePercent")), 2),
            "accruedRs": round(accrued_total, 2),
            "finalDisbursal": round(disbursal_total, 2),
            "disbursalStatus": self.state.get("monthlyStatuses", {}).get(status_key, "Pending"),
            "kpis": sorted(rows, key=lambda item: (parse_number(item.get("displayOrder")), item.get("kraCategory", ""), item.get("kpiName", ""))),
            "projects": projects,
        }

    def employee_dashboard(self, employee_id, selected_period="", start_date="", end_date=""):
        employee = self.state["employees"].get(employee_id)
        if not employee or employee.get("status") != "active":
            return None
        admin_ids = set(load_config().get("adminEmployeeIds", []))
        grouped = {}
        for row in self.state["kpis"]:
            if row.get("employeeId") != employee_id:
                continue
            grouped.setdefault(row.get("periodLabel", _current_period()), []).append(row)
        order = [label for label in sorted(grouped.keys(), key=_period_sort_key) if _within_date_range(label, start_date, end_date)]
        periods = {label: self._period_summary(employee, label, grouped[label]) for label in order}
        chosen = selected_period if selected_period in periods else (order[-1] if order else _current_period())
        latest = periods.get(chosen) or (periods[order[-1]] if order else None)
        return {
            "employeeId": employee["employeeId"],
            "name": employee.get("name", employee["employeeId"]),
            "email": employee.get("email", ""),
            "grade": employee.get("grade", ""),
            "designation": employee.get("designation", ""),
            "department": employee.get("department", ""),
            "location": employee.get("location", ""),
            "businessUnit": employee.get("businessUnit", "GTM"),
            "logicKey": employee.get("logicKey", employee.get("department", "")),
            "sharePercent": employee.get("sharePercent", 100),
            "projectIncentivePercent": employee.get("projectIncentivePercent", 1.5),
            "mySharePercent": employee.get("mySharePercent", employee.get("projectIncentivePercent", 1.5)),
            "departmentPercent": employee.get("departmentPercent", 100),
            "teamSharePercent": employee.get("teamSharePercent", 100),
            "npsScore": employee.get("npsScore", 4.5),
            "disbursalType": employee.get("disbursalType", "quarterly"),
            "isManagerView": any(item.get("reportingTo") == employee_id for item in self.state["employees"].values()),
            "hierarchy": {
                "reportingTo": employee.get("reportingTo", ""),
                "managerName": employee.get("managerName", ""),
                "designation": employee.get("managerDesignation", ""),
            },
            "periodOrder": order,
            "periods": periods,
            "selectedPeriod": chosen,
            "latestSummary": latest,
            "mustChangePassword": bool(employee.get("mustChangePassword", True)),
            "adminAccess": employee_id in admin_ids,
        }

    def _employee_summary_for_admin(self, employee, selected_period="", start_date="", end_date=""):
        grouped = {}
        for row in self.state["kpis"]:
            if row.get("employeeId") != employee["employeeId"]:
                continue
            grouped.setdefault(row.get("periodLabel", _current_period()), []).append(row)
        order = [label for label in sorted(grouped.keys(), key=_period_sort_key) if _within_date_range(label, start_date, end_date)]
        chosen = selected_period if selected_period in grouped else (order[-1] if order else _current_period())
        return self._period_summary(employee, chosen, grouped.get(chosen, []))

    def admin_dashboard(self, selected_period="", start_date="", end_date=""):
        total_accrued = 0.0
        total_disbursal = 0.0
        departments = {}
        status_counts = {"Pending": 0, "In Process": 0, "Disbursed": 0}
        for employee in self.state["employees"].values():
            if employee.get("status") != "active" or employee["employeeId"] == DEFAULT_ADMIN_ID:
                continue
            latest = self._employee_summary_for_admin(employee, selected_period=selected_period, start_date=start_date, end_date=end_date)
            if not latest:
                continue
            total_accrued += latest["accruedRs"]
            total_disbursal += latest["finalDisbursal"]
            departments.setdefault(employee.get("department") or "Unassigned", []).append(latest["npsScore"])
            status_counts[latest["disbursalStatus"]] = status_counts.get(latest["disbursalStatus"], 0) + 1
        return {
            "enabled": True,
            "totalEmployees": len([item for item in self.state["employees"].values() if item.get("status") == "active" and item["employeeId"] != DEFAULT_ADMIN_ID]),
            "totalAccrued": round(total_accrued, 2),
            "totalDisbursal": round(total_disbursal, 2),
            "dataUpdated": self.state["loadedAt"],
            "disbursalStatus": " | ".join(f"{key}: {value}" for key, value in status_counts.items()),
            "departmentPerformance": [
                {
                    "department": department,
                    "averagePerformance": round(sum(values) / len(values), 2) if values else 0,
                    "headcount": len(values),
                }
                for department, values in sorted(departments.items())
            ],
            "uploadHistory": [
                _public_upload(item)
                for item in sorted(self.state["uploadedFiles"], key=lambda item: item.get("uploadedAt", ""), reverse=True)
            ],
        }

    def dashboard_payload(self, viewer_id, target_employee_id="", admin_mode=False, search="", start_date="", end_date="", period_label=""):
        viewer = self.state["employees"].get(viewer_id) or _admin_employee()
        employee_options = self.employee_search(viewer_id, admin_mode, search)
        allowed_ids = {item["employeeId"] for item in employee_options}
        default_target = viewer_id
        if admin_mode:
            non_admin_options = [item["employeeId"] for item in employee_options if item["employeeId"] != viewer_id]
            default_target = non_admin_options[0] if non_admin_options else viewer_id
        target_id = target_employee_id if target_employee_id in allowed_ids else default_target
        return {
            "viewer": {
                "employeeId": viewer.get("employeeId", viewer_id),
                "name": viewer.get("name", viewer_id),
                "designation": viewer.get("designation", ""),
                "department": viewer.get("department", ""),
                "grade": viewer.get("grade", ""),
                "location": viewer.get("location", ""),
                "businessUnit": viewer.get("businessUnit", "GTM"),
                "isAdmin": admin_mode,
            },
            "viewedEmployee": self.employee_dashboard(target_id, selected_period=period_label, start_date=start_date, end_date=end_date),
            "employees": employee_options,
            "admin": self.admin_dashboard(selected_period=period_label, start_date=start_date, end_date=end_date) if admin_mode else {"enabled": False},
            "departments": DEPARTMENTS + ["Operations", "Design"],
            "loadedAt": self.state["loadedAt"],
            "currentPeriod": _current_period(),
            "periodOptions": _fy_periods(),
        }

    def update_kpi(self, payload):
        record_id = clean_string(payload.get("recordId"))
        row = next((item for item in self.state["kpis"] if item.get("recordId") == record_id), None)
        if not row:
            raise ValueError("KPI record not found")
        record_key = row.get("recordKey")
        override = dict(self.state["kpiOverrides"].get(record_key, {}))
        override["target"] = parse_number(payload.get("target")) if payload.get("target") is not None else row.get("target")
        override["achieved"] = parse_number(payload.get("achieved")) if payload.get("achieved") is not None else row.get("achieved")
        override["notes"] = clean_string(payload.get("notes")) or row.get("notes", "")
        self.state["kpiOverrides"][record_key] = override
        self.persist()
        updated = next((item for item in self.state["kpis"] if item.get("recordId") == record_id), None)
        return self._kpi_metrics(updated) if updated else None

    def update_project(self, payload):
        employee_id = clean_string(payload.get("employeeId"))
        period_label = clean_string(payload.get("periodLabel")) or _current_period()
        project_id = clean_string(payload.get("projectId"))
        if not employee_id or not project_id:
            raise ValueError("Employee and project are required")
        key = f"{employee_id}|{period_label}|{project_id}"
        override = dict(self.state["projectOverrides"].get(key, {}))
        override["sharePercent"] = parse_number(payload.get("sharePercent"))
        override["departmentPercent"] = parse_number(payload.get("departmentPercent"))
        override["teamSharePercent"] = parse_number(payload.get("teamSharePercent"))
        self.state["projectOverrides"][key] = override
        self.persist()
        return override

    def update_disbursal_status(self, payload):
        employee_id = clean_string(payload.get("employeeId"))
        period_label = clean_string(payload.get("periodLabel")) or _current_period()
        status = clean_string(payload.get("status")) or "Pending"
        if not employee_id:
            raise ValueError("Employee is required")
        self.state["monthlyStatuses"][f"{employee_id}|{period_label}"] = status
        self.persist()
        return {"employeeId": employee_id, "periodLabel": period_label, "status": status}

    def apply_workbook_upload(self, file_name, data_bytes, upload_type="", replace_file_id=""):
        upload_type = clean_string(upload_type).lower()
        if upload_type not in {"team_master", "gtm_logic", "sbu_logic", "project_cf", "kpi_logic"}:
            raise ValueError("Select a valid upload type")
        file_id = uuid.uuid4().hex
        target_dir = UPLOADS_DIR / file_id
        target_dir.mkdir(parents=True, exist_ok=True)
        stored_path = target_dir / file_name
        stored_path.write_bytes(data_bytes)
        parsed = parse_workbook(stored_path, upload_type)
        parsed_upload_type = parsed.get("uploadType", upload_type)
        if replace_file_id:
            self.delete_upload(replace_file_id, persist=False)
        for item in self.state.get("uploadedFiles", []):
            if item.get("deleted") or item.get("uploadType") != parsed_upload_type:
                continue
            item["deleted"] = True
            item.pop("fileData", None)
        self.state["uploadedFiles"].append(
            {
                "fileId": file_id,
                "fileName": file_name,
                "storedPath": _portable_path(stored_path),
                "uploadedAt": _now(),
                "uploadType": parsed_upload_type,
                "recordCount": parsed.get("recordCount", 0),
                "deleted": False,
                "seeded": False,
                "fileData": base64.b64encode(data_bytes).decode("ascii"),
            }
        )
        self.persist()
        uploaded_public = _public_upload(self.state["uploadedFiles"][-1])
        self.reload()
        return uploaded_public

    def delete_upload(self, file_id, persist=True):
        deleted = False
        for item in self.state["uploadedFiles"]:
            if item.get("fileId") == file_id and not item.get("deleted"):
                item["deleted"] = True
                item.pop("fileData", None)
                deleted = True
        if persist:
            self.persist()
            if deleted:
                self.reload()
        return deleted

    def export_csv(self, viewer_id="", admin_mode=False, employee_id="", start_date="", end_date="", period_label=""):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "Employee ID",
                "Employee Name",
                "Business Unit",
                "Department",
                "Grade",
                "Designation",
                "Location",
                "Reporting To",
                "Manager Name",
                "Manager Designation",
                "Period Label",
                "Period",
                "KRA",
                "KPI",
                "Target",
                "Achieved",
                "Achievement %",
                "Score",
                "Weightage",
                "Weighted Score",
                "NPS Score",
                "NPS Disbursal %",
                "Project Value",
                "Cashflow",
                "Incentive Base",
                "Share %",
                "Department %",
                "Team Share %",
                "My Share %",
                "Accrued Rs",
                "Final Disbursal",
                "Disbursal Status",
            ]
        )
        accessible = self._accessible_employee_ids(viewer_id or DEFAULT_ADMIN_ID, admin_mode=admin_mode)
        selected_ids = [employee_id] if employee_id else accessible
        for selected_id in selected_ids:
            if selected_id == DEFAULT_ADMIN_ID and not employee_id:
                continue
            dashboard = self.employee_dashboard(selected_id, selected_period=period_label, start_date=start_date, end_date=end_date)
            if not dashboard:
                continue
            for label in dashboard.get("periodOrder", []):
                if period_label and label != period_label:
                    continue
                summary = dashboard["periods"][label]
                project_rows = summary.get("projects") or [{}]
                kpi_rows = summary.get("kpis") or [{}]
                for kpi in kpi_rows:
                    project = project_rows[0] if project_rows else {}
                    writer.writerow(
                        [
                            dashboard["employeeId"],
                            dashboard["name"],
                            dashboard.get("businessUnit", ""),
                            dashboard.get("department", ""),
                            dashboard.get("grade", ""),
                            dashboard.get("designation", ""),
                            dashboard.get("location", ""),
                            dashboard.get("hierarchy", {}).get("reportingTo", ""),
                            dashboard.get("hierarchy", {}).get("managerName", ""),
                            dashboard.get("hierarchy", {}).get("designation", ""),
                            label,
                            summary["displayPeriod"],
                            kpi.get("kraCategory", ""),
                            kpi.get("kpiName", ""),
                            kpi.get("target", ""),
                            kpi.get("achieved", ""),
                            kpi.get("achievementPercent", ""),
                            kpi.get("score", ""),
                            kpi.get("weightage", ""),
                            kpi.get("finalWeightedScore", ""),
                            summary["npsScore"],
                            summary["disbursalPercent"],
                            project.get("projectValue", summary.get("projectValue", 0)),
                            project.get("cashflowValue", ""),
                            project.get("incentiveBaseValue", ""),
                            project.get("sharePercent", dashboard.get("sharePercent", "")),
                            project.get("departmentPercent", dashboard.get("departmentPercent", "")),
                            project.get("teamSharePercent", dashboard.get("teamSharePercent", "")),
                            project.get("mySharePercent", dashboard.get("mySharePercent", dashboard.get("projectIncentivePercent", ""))),
                            summary["accruedRs"],
                            summary["finalDisbursal"],
                            summary["disbursalStatus"],
                        ]
                    )
        return buffer.getvalue()


DATA_SERVICE = GTMDataService()
