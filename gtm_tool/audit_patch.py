import json
import uuid
from datetime import datetime, timedelta, timezone

from gtm_tool.config import STATE_FILE
from services.utils import clean_string


IST = timezone(timedelta(hours=5, minutes=30))


def _now():
    return datetime.now(IST).isoformat(timespec="seconds")


def _actor_from_service(service, payload=None):
    payload = payload or {}
    actor = payload.get("_auditActor") or getattr(service, "_current_audit_actor", {}) or {}
    actor_id = clean_string(actor.get("employeeId"))
    actor_name = clean_string(actor.get("name")) or actor_id or "Unknown Admin"
    return {"employeeId": actor_id, "name": actor_name}


def _record_audit(service, action, summary, actor=None, **metadata):
    entry = {
        "auditId": uuid.uuid4().hex,
        "changedAt": _now(),
        "changedById": clean_string((actor or {}).get("employeeId")),
        "changedByName": clean_string((actor or {}).get("name")) or clean_string((actor or {}).get("employeeId")) or "Unknown Admin",
        "action": clean_string(action),
        "summary": clean_string(summary),
    }
    for key, value in metadata.items():
        if value not in (None, ""):
            entry[key] = value
    audit_log = service.state.setdefault("auditLog", [])
    audit_log.insert(0, entry)
    del audit_log[500:]


def install_audit_patch(handler_cls, service):
    if getattr(service, "_audit_patch_installed", False):
        return

    original_build_from_uploads = service.__class__._build_from_uploads
    original_persist = service.__class__.persist
    original_reload = service.__class__.reload
    original_admin_dashboard = service.__class__.admin_dashboard
    original_upsert_employee = service.__class__.upsert_employee
    original_delete_employee = service.__class__.delete_employee
    original_undo_delete_employee = service.__class__.undo_delete_employee
    original_update_kpi = service.__class__.update_kpi
    original_update_project = service.__class__.update_project
    original_update_status = service.__class__.update_disbursal_status
    original_upload = service.__class__.apply_workbook_upload
    original_delete_upload = service.__class__.delete_upload
    original_read_json = handler_cls.read_json

    def _read_audit_from_disk():
        if not STATE_FILE.exists():
            return []
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8")).get("auditLog", [])
        except Exception:
            return []

    def build_from_uploads_with_audit(self, raw_state):
        audit_log = raw_state.get("auditLog", [])
        built = original_build_from_uploads(self, raw_state)
        built["auditLog"] = audit_log[:500]
        return built

    def reload_with_audit(self):
        audit_log = _read_audit_from_disk()
        original_reload(self)
        self.state["auditLog"] = audit_log[:500]

    def persist_with_audit(self, reload_state=True):
        audit_log = list(self.state.get("auditLog", []))[:500]
        original_persist(self, reload_state=False)
        try:
            raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            raw = {}
        raw["auditLog"] = audit_log
        STATE_FILE.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        if reload_state:
            self.reload()

    def admin_dashboard_with_audit(self, *args, **kwargs):
        payload = original_admin_dashboard(self, *args, **kwargs)
        payload["auditLog"] = list(self.state.get("auditLog", []))[:80]
        return payload

    def upsert_employee_with_audit(self, payload):
        actor = _actor_from_service(self, payload)
        employee_id = clean_string(payload.get("employeeId"))
        result = original_upsert_employee(self, payload)
        _record_audit(
            self,
            "employee_update",
            f"Saved employee {result.get('name') or employee_id}",
            actor=actor,
            employeeId=employee_id,
            targetName=result.get("name", ""),
        )
        self.persist()
        return result

    def delete_employee_with_audit(self, employee_id):
        employee_id = clean_string(employee_id)
        employee = dict(self.state.get("employees", {}).get(employee_id, {}))
        actor = _actor_from_service(self)
        result = original_delete_employee(self, employee_id)
        if result:
            _record_audit(
                self,
                "employee_delete",
                f"Marked employee {employee.get('name') or employee_id} inactive",
                actor=actor,
                employeeId=employee_id,
                targetName=employee.get("name", ""),
            )
            self.persist()
        return result

    def undo_delete_employee_with_audit(self):
        actor = _actor_from_service(self)
        result = original_undo_delete_employee(self)
        if result:
            _record_audit(
                self,
                "employee_undo_delete",
                f"Restored employee {result.get('name') or result.get('employeeId')}",
                actor=actor,
                employeeId=result.get("employeeId", ""),
                targetName=result.get("name", ""),
            )
            self.persist()
        return result

    def update_kpi_with_audit(self, payload):
        actor = _actor_from_service(self, payload)
        updated = original_update_kpi(self, payload)
        _record_audit(
            self,
            "kpi_update",
            f"Updated KPI {updated.get('kpiName', '')}",
            actor=actor,
            employeeId=updated.get("employeeId", ""),
            periodLabel=updated.get("periodLabel", ""),
            kpi=updated.get("kpiName", ""),
            after={"target": updated.get("target"), "achieved": updated.get("achieved"), "score": updated.get("score")},
        )
        self.persist(reload_state=False)
        return updated

    def update_project_with_audit(self, payload):
        actor = _actor_from_service(self, payload)
        employee_id = clean_string(payload.get("employeeId"))
        period_label = clean_string(payload.get("periodLabel"))
        project_id = clean_string(payload.get("projectId"))
        updated = original_update_project(self, payload)
        _record_audit(
            self,
            "project_update",
            f"Updated project incentive {project_id}",
            actor=actor,
            employeeId=employee_id,
            periodLabel=period_label,
            projectId=project_id,
            after=dict(updated),
        )
        self.persist(reload_state=False)
        return updated

    def update_status_with_audit(self, payload):
        actor = _actor_from_service(self, payload)
        updated = original_update_status(self, payload)
        _record_audit(
            self,
            "disbursal_status_update",
            f"Updated disbursal status to {updated.get('status')}",
            actor=actor,
            employeeId=updated.get("employeeId", ""),
            periodLabel=updated.get("periodLabel", ""),
            after={"status": updated.get("status"), "scope": updated.get("scope", "employee")},
        )
        self.persist(reload_state=False)
        return updated

    def upload_with_audit(self, file_name, data_bytes, upload_type="", replace_file_id="", actor=None):
        actor = actor or _actor_from_service(self)
        try:
            uploaded = original_upload(self, file_name, data_bytes, upload_type, replace_file_id, actor=actor)
        except TypeError:
            uploaded = original_upload(self, file_name, data_bytes, upload_type, replace_file_id)
        _record_audit(
            self,
            "workbook_upload",
            f"Uploaded {file_name}",
            actor=actor,
            fileId=uploaded.get("fileId", ""),
            uploadType=uploaded.get("uploadType", upload_type),
            fileName=uploaded.get("fileName", file_name),
            recordCount=uploaded.get("recordCount", 0),
            replacedFileId=replace_file_id,
        )
        self.persist()
        return uploaded

    def delete_upload_with_audit(self, file_id, persist=True, actor=None):
        actor = actor or _actor_from_service(self)
        upload = next((item for item in self.state.get("uploadedFiles", []) if item.get("fileId") == file_id), {})
        try:
            deleted = original_delete_upload(self, file_id, persist=persist, actor=actor)
        except TypeError:
            deleted = original_delete_upload(self, file_id, persist=persist)
        if deleted:
            _record_audit(
                self,
                "workbook_delete",
                f"Deleted uploaded file {upload.get('fileName') or file_id}",
                actor=actor,
                fileId=file_id,
                uploadType=upload.get("uploadType", ""),
                fileName=upload.get("fileName", ""),
            )
            if persist:
                self.persist()
        return deleted

    def actor_wrapper(original):
        def wrapped(self, *args, **kwargs):
            session = self.current_session()
            if session and session.get("adminMode"):
                employee = service.state.get("employees", {}).get(session["employeeId"], {})
                service._current_audit_actor = {
                    "employeeId": session["employeeId"],
                    "name": employee.get("name", session["employeeId"]),
                }
            try:
                return original(self, *args, **kwargs)
            finally:
                service._current_audit_actor = {}
        return wrapped

    def read_json_with_actor(self):
        payload = original_read_json(self)
        session = self.current_session()
        if session and session.get("adminMode"):
            employee = service.state.get("employees", {}).get(session["employeeId"], {})
            payload["_auditActor"] = {
                "employeeId": session["employeeId"],
                "name": employee.get("name", session["employeeId"]),
            }
        return payload

    service.__class__._build_from_uploads = build_from_uploads_with_audit
    service.__class__.persist = persist_with_audit
    service.__class__.reload = reload_with_audit
    service.__class__.admin_dashboard = admin_dashboard_with_audit
    service.__class__.upsert_employee = upsert_employee_with_audit
    service.__class__.delete_employee = delete_employee_with_audit
    service.__class__.undo_delete_employee = undo_delete_employee_with_audit
    service.__class__.update_kpi = update_kpi_with_audit
    service.__class__.update_project = update_project_with_audit
    service.__class__.update_disbursal_status = update_status_with_audit
    service.__class__.apply_workbook_upload = upload_with_audit
    service.__class__.delete_upload = delete_upload_with_audit
    handler_cls.read_json = read_json_with_actor
    for method_name in (
        "handle_upsert_employee",
        "handle_delete_employee",
        "handle_undo_employee",
        "handle_update_kpi",
        "handle_update_project",
        "handle_update_status",
        "handle_upload_workbook",
        "handle_delete_upload",
    ):
        setattr(handler_cls, method_name, actor_wrapper(getattr(handler_cls, method_name)))
    service.state.setdefault("auditLog", _read_audit_from_disk())
    service._audit_patch_installed = True
