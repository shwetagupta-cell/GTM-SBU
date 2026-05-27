from datetime import datetime
from pathlib import Path

from models.entities import EmployeeRecord, ProjectRecord
from services.auth_service import build_known_people, sync_accounts_for_employees
from services.config_service import DATASET_LABELS, DEFAULT_DATASETS, UPLOADS_DIR, load_app_config, save_app_config
from services.excel_service import (
    parse_closure_workbook,
    parse_future_employee_workbook,
    parse_master_workbook,
    parse_team_workbook,
    parse_ytd_workbook,
)
from services.utils import clean_string, month_label, normalize_name, slugify


class DashboardDataService:
    def __init__(self):
        self.state = {"employees": {}, "datasets": [], "loadedAt": None}
        self.reload()

    def reload(self):
        config = load_app_config()
        employees = {}
        known_people = build_known_people()

        team_path = Path(config["datasets"].get("teamSheet", "")).expanduser()
        if team_path.is_file():
            for employee_id, employee in parse_team_workbook(team_path).items():
                employees[employee_id] = employee

        closure_map = self._safe_parse(parse_closure_workbook, config["datasets"].get("closureWorkbook", ""))
        ytd_map = self._safe_parse(parse_ytd_workbook, config["datasets"].get("ytdWorkbook", ""))
        master_employees = self._safe_parse(
            parse_master_workbook,
            config["datasets"].get("misWorkbook", ""),
            closure_map=closure_map or {},
            ytd_map=ytd_map or {},
        )
        future_employees = self._safe_parse(parse_future_employee_workbook, config["datasets"].get("employeeSheet", ""))

        for workbook_employee in master_employees or []:
            employee = self._resolve_employee(employees, known_people, workbook_employee)
            self._merge_employee_projects(employee, workbook_employee)

        for workbook_employee in future_employees or []:
            employee = self._resolve_employee(employees, known_people, workbook_employee)
            self._merge_employee_projects(employee, workbook_employee)

        for employee in employees.values():
            if employee.team_head_id and employee.team_head_id in employees:
                manager = employees[employee.team_head_id]
                if employee.employee_id not in manager.managed_employee_ids:
                    manager.managed_employee_ids.append(employee.employee_id)

        sync_accounts_for_employees(employees)
        self.state = {
            "employees": employees,
            "datasets": self._dataset_status(config),
            "loadedAt": datetime.now().isoformat(timespec="seconds"),
        }

    def _safe_parse(self, parser, dataset_path, **kwargs):
        path = Path(dataset_path or "").expanduser()
        if not path.is_file():
            return None
        return parser(path, **kwargs) if kwargs else parser(path)

    def clear(self):
        config = load_app_config()
        config["datasets"] = dict(DEFAULT_DATASETS)
        save_app_config(config)
        self.reload()

    def _resolve_employee(self, employees, known_people, workbook_employee):
        name_key = f"name:{normalize_name(workbook_employee.name)}"
        matched = None
        for employee in employees.values():
            if normalize_name(employee.name) == normalize_name(workbook_employee.name):
                matched = employee
                break

        if not matched:
            known = known_people.get(name_key, {})
            employee_id = clean_string(known.get("employeeId")) or workbook_employee.employee_id or slugify(workbook_employee.name)
            matched = employees.get(employee_id) or EmployeeRecord(
                employee_id=employee_id,
                name=workbook_employee.name,
                designation=clean_string(known.get("designation") or workbook_employee.designation),
                email=clean_string(known.get("email")),
                location=clean_string(workbook_employee.location),
            )
            employees[matched.employee_id] = matched

        if workbook_employee.name:
            matched.name = workbook_employee.name
        if workbook_employee.designation and not matched.designation:
            matched.designation = workbook_employee.designation
        if workbook_employee.location and not matched.location:
            matched.location = workbook_employee.location
        return matched

    def _merge_employee_projects(self, employee, workbook_employee):
        for month in workbook_employee.month_order:
            if month not in employee.month_order:
                employee.month_order.append(month)

        for incoming in workbook_employee.projects:
            existing = next(
                (
                    project
                    for project in employee.projects
                    if project.project_id == incoming.project_id or normalize_name(project.project_name) == normalize_name(incoming.project_name)
                ),
                None,
            )
            if not existing:
                employee.projects.append(incoming)
                continue

            existing.project_name = incoming.project_name or existing.project_name
            existing.project_value = incoming.project_value or existing.project_value
            existing.future_value = incoming.future_value or existing.future_value
            existing.source_sheet = incoming.source_sheet or existing.source_sheet
            existing.sourcing_type = incoming.sourcing_type or existing.sourcing_type
            if incoming.closure_roles:
                existing.closure_roles = incoming.closure_roles
            if incoming.ytd_meta:
                existing.ytd_meta.update(incoming.ytd_meta)
            existing.monthly_cf.update(incoming.monthly_cf)
            existing.monthly_incentive.update(incoming.monthly_incentive)

    def _dataset_status(self, config):
        status = []
        for key, label in DATASET_LABELS.items():
            path = Path(config["datasets"].get(key, "")).expanduser()
            exists = path.is_file()
            status.append(
                {
                    "key": key,
                    "label": label,
                    "path": str(path),
                    "exists": exists,
                    "fileName": path.name if str(path) else "",
                    "updatedAt": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if exists else "",
                }
            )
        return status

    def employee_ids_for_viewer(self, viewer, admin_mode):
        if admin_mode:
            return sorted(self.state["employees"].keys())
        accessible = [viewer.employee_id]
        accessible.extend(sorted(viewer.managed_employee_ids))
        return list(dict.fromkeys(accessible))

    def _empty_employee_dashboard(self, employee):
        return {
            "employeeId": employee.employee_id,
            "name": employee.name,
            "designation": employee.designation,
            "location": employee.location,
            "email": employee.email,
            "teamHeadName": employee.team_head_name,
            "isTeamHead": employee.is_team_head,
            "mustChangePassword": employee.must_change_password,
            "months": {},
            "monthOrder": [],
            "latestMonth": "",
            "projectCount": 0,
        }

    def employee_dashboard(self, employee):
        months = {}
        for month in employee.month_order:
            entries = []
            total_share = 0.0
            total_cf = 0.0
            future_total = 0.0
            for project in employee.projects:
                current_month_cf = project.monthly_cf.get(month, 0.0)
                if current_month_cf <= 0:
                    continue
                entry = {
                    "projectId": project.project_id,
                    "projectName": project.project_name,
                    "projectValue": project.project_value,
                    "thisMonthCf": current_month_cf,
                    "yourShare": project.monthly_incentive.get(month, 0.0),
                    "futureValueSecured": project.future_value,
                    "closureRoles": project.closure_roles,
                    "sourcingType": project.sourcing_type,
                    "ytdMeta": project.ytd_meta,
                }
                total_share += entry["yourShare"]
                total_cf += entry["thisMonthCf"]
                future_total += entry["futureValueSecured"]
                entries.append(entry)
            entries.sort(key=lambda item: item["yourShare"], reverse=True)
            months[month] = {
                "month": month,
                "totalShare": total_share,
                "totalCf": total_cf,
                "futureTotal": future_total,
                "entries": entries,
            }
        latest_month = employee.month_order[-1] if employee.month_order else ""
        timeline = []
        for index, month in enumerate(employee.month_order):
            month_values = months.get(month, {})
            if not month_values:
                continue
            status = "Current" if month == latest_month else "Past"
            timeline.append(
                {
                    "month": month,
                    "quarter": self._quarter_label(month),
                    "year": self._year_label(month),
                    "incentiveEarned": month_values.get("totalShare", 0.0),
                    "incentiveStatus": status,
                    "futureProjection": month_values.get("futureTotal", 0.0) if status == "Current" else 0.0,
                    "remarks": "Latest uploaded cycle" if status == "Current" else "Historical cycle",
                }
            )
        if latest_month:
            latest_projection = months.get(latest_month, {}).get("futureTotal", 0.0)
            timeline.append(
                {
                    "month": f"{latest_month} Projection",
                    "quarter": self._quarter_label(latest_month),
                    "year": self._year_label(latest_month),
                    "incentiveEarned": 0.0,
                    "incentiveStatus": "Future",
                    "futureProjection": latest_projection,
                    "remarks": "Projected from secured future value",
                }
            )
        return {
            "employeeId": employee.employee_id,
            "name": employee.name,
            "designation": employee.designation,
            "location": employee.location,
            "email": employee.email,
            "teamHeadName": employee.team_head_name,
            "isTeamHead": employee.is_team_head,
            "mustChangePassword": employee.must_change_password,
            "months": months,
            "monthOrder": employee.month_order,
            "latestMonth": latest_month,
            "projectCount": sum(len(item.get("entries", [])) for item in months.values()),
            "incentiveTimeline": timeline,
        }

    def _quarter_label(self, month_label_value):
        lowered = (month_label_value or "").lower()
        if lowered.startswith(("jan", "feb", "mar")):
            return "Q1"
        if lowered.startswith(("apr", "may", "jun")):
            return "Q2"
        if lowered.startswith(("jul", "aug", "sep")):
            return "Q3"
        if lowered.startswith(("oct", "nov", "dec")):
            return "Q4"
        if "-" in month_label_value:
            try:
                month_number = int(month_label_value.split("-")[1])
                return f"Q{((month_number - 1) // 3) + 1}"
            except (ValueError, IndexError):
                return "Unknown"
        return "Unknown"

    def _year_label(self, month_label_value):
        text = month_label_value or ""
        if "-" in text:
            return text.split("-")[0]
        if text[-2:].isdigit():
            return f"20{text[-2:]}"
        return "Unknown"

    def dashboard_payload(self, viewer_id, target_employee_id="", admin_mode=False):
        employees = self.state["employees"]
        viewer = employees.get(viewer_id)
        if not viewer and admin_mode:
            known = build_known_people().get(f"id:{viewer_id}", {})
            viewer = EmployeeRecord(
                employee_id=viewer_id,
                name=clean_string(known.get("name")) or "Admin User",
                designation=clean_string(known.get("designation")) or "Admin",
                email=clean_string(known.get("email")),
            )
        if not viewer:
            return None
        allowed_ids = self.employee_ids_for_viewer(viewer, admin_mode)
        default_target = viewer.employee_id if viewer.employee_id in allowed_ids else (allowed_ids[0] if allowed_ids else viewer.employee_id)
        target_id = target_employee_id if target_employee_id in allowed_ids else default_target
        target = employees.get(target_id)

        summaries = []
        for employee_id in allowed_ids:
            employee = employees[employee_id]
            dashboard = self.employee_dashboard(employee)
            summaries.append(
                {
                    "employeeId": employee.employee_id,
                    "name": employee.name,
                    "designation": employee.designation,
                    "isTeamHead": employee.is_team_head,
                    "latestMonth": dashboard["latestMonth"],
                    "department": employee.location or employee.designation,
                    "email": employee.email,
                    "monthTotals": {month: values["totalShare"] for month, values in dashboard["months"].items()},
                }
            )

        viewed_employee = self.employee_dashboard(target) if target else self._empty_employee_dashboard(viewer)
        return {
            "viewer": {
                "employeeId": viewer.employee_id,
                "name": viewer.name,
                "designation": viewer.designation,
                "isAdmin": admin_mode,
                "isTeamHead": viewer.is_team_head,
            },
            "viewedEmployee": viewed_employee,
            "accessibleEmployees": summaries,
            "admin": {"enabled": admin_mode, "datasets": self.state["datasets"]},
            "loadedAt": self.state["loadedAt"],
        }

    def search_employees(self, term="", page=1, per_page=10):
        page = max(int(page or 1), 1)
        per_page = max(min(int(per_page or 10), 50), 1)
        lowered_term = clean_string(term).lower()
        records = []
        for employee in self.state["employees"].values():
            haystack = " ".join(
                [
                    employee.employee_id,
                    employee.name,
                    employee.designation,
                    employee.location,
                    employee.email,
                ]
            ).lower()
            if lowered_term and lowered_term not in haystack:
                continue
            records.append(
                {
                    "employeeId": employee.employee_id,
                    "name": employee.name,
                    "designation": employee.designation,
                    "department": employee.location or employee.designation,
                    "email": employee.email,
                }
            )
        records.sort(key=lambda item: item["name"])
        total = len(records)
        start = (page - 1) * per_page
        end = start + per_page
        return {
            "items": records[start:end],
            "page": page,
            "perPage": per_page,
            "total": total,
            "totalPages": max((total + per_page - 1) // per_page, 1),
        }

    def project_detail(self, viewer_id, target_employee_id, project_id, month, admin_mode=False):
        payload = self.dashboard_payload(viewer_id, target_employee_id, admin_mode)
        if not payload:
            return None
        for entry in payload["viewedEmployee"]["months"].get(month, {}).get("entries", []):
            if entry["projectId"] == project_id:
                return {
                    "employeeName": payload["viewedEmployee"]["name"],
                    "projectName": entry["projectName"],
                    "month": month,
                    "thisMonthCf": entry["thisMonthCf"],
                    "yourShare": entry["yourShare"],
                    "futureValueSecured": entry["futureValueSecured"],
                    "sourcingType": entry["sourcingType"],
                    "closureRoles": entry["closureRoles"],
                    "ytdMeta": entry["ytdMeta"],
                }
        return None

    def save_uploaded_dataset(self, dataset_key, source_file_name, data_bytes):
        config = load_app_config()
        target_dir = UPLOADS_DIR / dataset_key
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / "current.xlsx"
        target_path.write_bytes(data_bytes)
        config.setdefault("datasets", {})
        config["datasets"][dataset_key] = str(target_path)
        save_app_config(config)

    def save_uploaded_datasets(self, uploads):
        for dataset_key, payload in uploads.items():
            self.save_uploaded_dataset(dataset_key, payload["filename"], payload["bytes"])
        self.reload()

    def delete_uploaded_dataset(self, dataset_key):
        config = load_app_config()
        existing_path = Path(config.get("datasets", {}).get(dataset_key, "")).expanduser()
        if existing_path.is_file():
            existing_path.unlink(missing_ok=True)
        config.setdefault("datasets", {})
        config["datasets"][dataset_key] = ""
        save_app_config(config)
        self.reload()


DATA_SERVICE = DashboardDataService()
