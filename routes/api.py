import io
import json
import secrets
from datetime import datetime, timedelta
from email.parser import BytesParser
from email.policy import compat32
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse


# ---------------------------------------------------------------------------
# Replacement for cgi.FieldStorage (removed in Python 3.13)
# ---------------------------------------------------------------------------
class _MultipartField:
    def __init__(self, filename, data):
        self.filename = filename
        self.file = io.BytesIO(data)
        self._data = data

    @property
    def value(self):
        return self._data.decode("utf-8", errors="replace")


class _MultipartForm:
    def __init__(self, fp, headers):
        self._fields: dict = {}
        content_type = headers.get("Content-Type", "")
        content_length = int(headers.get("Content-Length", 0))
        body = fp.read(content_length)
        raw = (f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n").encode() + body
        msg = BytesParser(policy=compat32).parsebytes(raw)
        if msg.is_multipart():
            for part in msg.get_payload():
                disp = part.get("Content-Disposition", "")
                name = filename = ""
                for seg in disp.split(";"):
                    seg = seg.strip()
                    if seg.startswith("name="):
                        name = seg[5:].strip('"')
                    elif seg.startswith("filename="):
                        filename = seg[9:].strip('"')
                if name:
                    data = part.get_payload(decode=True) or b""
                    self._fields[name] = _MultipartField(filename, data)

    def __contains__(self, key):
        return key in self._fields

    def __getitem__(self, key):
        return self._fields[key]

    def getvalue(self, key, default=""):
        field = self._fields.get(key)
        return field.value if field is not None else default
# ---------------------------------------------------------------------------

from services.auth_service import (
    build_known_people,
    load_accounts,
    send_reset_otp_email,
    update_password,
    verify_password,
)
from services.config_service import RESET_LOGS_FILE, ROOT, ensure_dirs, load_app_config
from services.data_service import DATA_SERVICE
from services.utils import clean_string, normalize_emp_code


SESSION_COOKIE = "sme_session"
SESSIONS = {}
RESET_OTP_STORE = {}
RESET_TTL_MINUTES = 15


def _append_reset_log(entry):
    ensure_dirs()
    logs = []
    if RESET_LOGS_FILE.exists():
        try:
            logs = json.loads(RESET_LOGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logs = []
    logs.append(entry)
    RESET_LOGS_FILE.write_text(json.dumps(logs[-500:], indent=2), encoding="utf-8")


def _purge_expired_reset_tokens():
    now = datetime.utcnow()
    for employee_id, record in list(RESET_OTP_STORE.items()):
        expires_at = record.get("expiresAt")
        if not expires_at:
            continue
        if now > datetime.fromisoformat(expires_at):
            RESET_OTP_STORE.pop(employee_id, None)


def _account_map():
    return {normalize_emp_code(item.get("employeeId")): item for item in load_accounts()}


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/me":
            return self.handle_me(parsed)
        if parsed.path == "/api/project-detail":
            return self.handle_project_detail(parsed)
        if parsed.path == "/api/admin/search-employees":
            return self.handle_employee_search(parsed)
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/login":
            return self.handle_login()
        if parsed.path == "/api/logout":
            return self.handle_logout()
        if parsed.path == "/api/change-password":
            return self.handle_change_password()
        if parsed.path == "/api/request-reset-otp":
            return self.handle_request_reset_otp()
        if parsed.path == "/api/verify-reset-otp":
            return self.handle_verify_reset_otp()
        if parsed.path == "/api/reset-password":
            return self.handle_reset_password()
        if parsed.path == "/api/admin/upload-datasets":
            return self.handle_upload_datasets()
        if parsed.path == "/api/admin/delete-datasets":
            return self.handle_delete_datasets()
        if parsed.path == "/api/admin/delete-dataset":
            return self.handle_delete_dataset()
        if parsed.path == "/api/admin/reload-dashboard":
            return self.handle_reload_dashboard()
        return self.send_json({"error": "Unknown endpoint"}, status=HTTPStatus.NOT_FOUND)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        return json.loads(body.decode("utf-8") or "{}")

    def send_json(self, payload, status=HTTPStatus.OK, set_cookie=None, clear_cookie=False):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie:
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}={set_cookie}; Path=/; HttpOnly; SameSite=Lax")
        if clear_cookie:
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
        self.end_headers()
        self.wfile.write(body)

    def current_session(self):
        cookie_header = self.headers.get("Cookie")
        if not cookie_header:
            return None
        cookie = SimpleCookie()
        cookie.load(cookie_header)
        token = cookie.get(SESSION_COOKIE)
        if not token:
            return None
        return SESSIONS.get(token.value)

    def require_session(self):
        session = self.current_session()
        if not session:
            self.send_json({"error": "Please log in first"}, status=HTTPStatus.UNAUTHORIZED)
            return None
        return session

    def require_admin(self):
        session = self.require_session()
        if not session:
            return None
        if not session.get("adminMode"):
            self.send_json({"error": "Admin access is required"}, status=HTTPStatus.FORBIDDEN)
            return None
        return session

    def handle_me(self, parsed):
        session = self.require_session()
        if not session:
            return
        query = parse_qs(parsed.query)
        if clean_string(query.get("refresh", [""])[0]) == "1":
            DATA_SERVICE.reload()
        target_employee_id = clean_string(query.get("employeeId", [""])[0])
        payload = DATA_SERVICE.dashboard_payload(session["employeeId"], target_employee_id, bool(session.get("adminMode")))
        if not payload:
            return self.send_json({"error": "No dashboard data found for this account"}, status=HTTPStatus.NOT_FOUND)
        return self.send_json(payload)

    def handle_employee_search(self, parsed):
        session = self.require_admin()
        if not session:
            return
        query = parse_qs(parsed.query)
        term = clean_string(query.get("term", [""])[0])
        page = clean_string(query.get("page", ["1"])[0]) or "1"
        per_page = clean_string(query.get("perPage", ["10"])[0]) or "10"
        return self.send_json(DATA_SERVICE.search_employees(term=term, page=page, per_page=per_page))

    def handle_project_detail(self, parsed):
        session = self.require_session()
        if not session:
            return
        query = parse_qs(parsed.query)
        target_employee_id = clean_string(query.get("employeeId", [""])[0])
        project_id = clean_string(query.get("projectId", [""])[0])
        month = clean_string(query.get("month", [""])[0])
        payload = DATA_SERVICE.project_detail(
            session["employeeId"],
            target_employee_id,
            project_id,
            month,
            bool(session.get("adminMode")),
        )
        if not payload:
            return self.send_json({"error": "Project detail not found"}, status=HTTPStatus.NOT_FOUND)
        return self.send_json(payload)

    def handle_login(self):
        payload = self.read_json()
        employee_id = normalize_emp_code(payload.get("employeeId"))
        password = str(payload.get("password", "")).strip()
        login_type = clean_string(payload.get("loginType") or "employee").lower()
        account = _account_map().get(employee_id)
        if not account or not verify_password(password, account["salt"], account["passwordHash"]):
            return self.send_json({"error": "Invalid employee ID or password"}, status=HTTPStatus.UNAUTHORIZED)

        config = load_app_config()
        is_admin = login_type == "admin"
        if is_admin and employee_id not in config.get("adminEmployeeIds", []):
            return self.send_json({"error": "This account does not have admin access"}, status=HTTPStatus.UNAUTHORIZED)

        if not is_admin and employee_id not in DATA_SERVICE.state["employees"]:
            return self.send_json({"error": "This employee does not exist in the uploaded dashboard data"}, status=HTTPStatus.UNAUTHORIZED)

        session_token = secrets.token_urlsafe(24)
        session_data = {"employeeId": employee_id, "adminMode": is_admin}
        SESSIONS[session_token] = session_data
        dashboard = DATA_SERVICE.dashboard_payload(employee_id, admin_mode=is_admin)
        return self.send_json(dashboard, set_cookie=session_token)

    def handle_logout(self):
        session = self.current_session()
        if session:
            for token, stored in list(SESSIONS.items()):
                if stored == session:
                    SESSIONS.pop(token, None)
        return self.send_json({"ok": True}, clear_cookie=True)

    def handle_change_password(self):
        session = self.require_session()
        if not session:
            return
        payload = self.read_json()
        current_password = str(payload.get("currentPassword", "")).strip()
        new_password = str(payload.get("newPassword", "")).strip()
        confirm_password = str(payload.get("confirmPassword", "")).strip()
        account = _account_map().get(session["employeeId"])
        if not account or not verify_password(current_password, account["salt"], account["passwordHash"]):
            return self.send_json({"error": "Current password is incorrect"}, status=HTTPStatus.BAD_REQUEST)
        if len(new_password) < 6:
            return self.send_json({"error": "New password must be at least 6 characters"}, status=HTTPStatus.BAD_REQUEST)
        if new_password != confirm_password:
            return self.send_json({"error": "New password and confirm password do not match"}, status=HTTPStatus.BAD_REQUEST)
        update_password(session["employeeId"], new_password)
        DATA_SERVICE.reload()
        return self.send_json({"ok": True, "message": "Password updated successfully"})

    def handle_request_reset_otp(self):
        _purge_expired_reset_tokens()
        payload = self.read_json()
        email = clean_string(payload.get("email")).lower()
        employee_id = normalize_emp_code(payload.get("employeeId"))
        employees = DATA_SERVICE.state["employees"]
        if not employee_id and email:
            matches = []
            for candidate in employees.values():
                candidate_email = clean_string(candidate.email).lower()
                known_person = build_known_people().get(f"id:{candidate.employee_id}", {})
                known_email = clean_string(known_person.get("email")).lower()
                if email and email in {candidate_email, known_email}:
                    matches.append(candidate)
            if len(matches) == 1:
                employee_id = matches[0].employee_id
        employees = DATA_SERVICE.state["employees"]
        employee = employees.get(employee_id)
        if not employee:
            return self.send_json({"error": "Employee not found in the uploaded data"}, status=HTTPStatus.BAD_REQUEST)
        known_person = build_known_people().get(f"id:{employee_id}", {})
        expected_email = clean_string(known_person.get("email") or employee.email).lower()
        if not expected_email:
            return self.send_json({"error": "No email is configured for this employee"}, status=HTTPStatus.BAD_REQUEST)
        if email != expected_email:
            return self.send_json({"error": "The email does not match this employee record"}, status=HTTPStatus.BAD_REQUEST)
        otp = f"{secrets.randbelow(1000000):06d}"
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=RESET_TTL_MINUTES)
        RESET_OTP_STORE[employee_id] = {
            "otp": otp,
            "email": email,
            "requestedAt": now.isoformat(timespec="seconds"),
            "expiresAt": expires_at.isoformat(timespec="seconds"),
            "verified": False,
        }
        email_result = send_reset_otp_email(email, employee.name, otp)
        print(f"Password reset OTP for {employee_id} ({email}): {otp}")
        _append_reset_log(
            {
                "employeeId": employee_id,
                "email": email,
                "requestedAt": now.isoformat(timespec="seconds"),
                "expiresAt": expires_at.isoformat(timespec="seconds"),
                "status": "requested",
            }
        )
        message = "OTP sent successfully." if email_result.get("ok") else email_result.get("error")
        return self.send_json({"ok": True, "message": message, "delivered": bool(email_result.get("ok"))})

    def handle_verify_reset_otp(self):
        _purge_expired_reset_tokens()
        payload = self.read_json()
        employee_id = normalize_emp_code(payload.get("employeeId"))
        email = clean_string(payload.get("email")).lower()
        otp = clean_string(payload.get("otp"))
        record = RESET_OTP_STORE.get(employee_id)
        if not record or record.get("email") != email:
            return self.send_json({"error": "Request OTP first before verification"}, status=HTTPStatus.BAD_REQUEST)
        if datetime.utcnow() > datetime.fromisoformat(record["expiresAt"]):
            RESET_OTP_STORE.pop(employee_id, None)
            _append_reset_log(
                {"employeeId": employee_id, "email": email, "status": "expired", "checkedAt": datetime.utcnow().isoformat(timespec="seconds")}
            )
            return self.send_json({"error": "OTP has expired. Request a new one."}, status=HTTPStatus.BAD_REQUEST)
        if record.get("otp") != otp:
            return self.send_json({"error": "OTP is incorrect"}, status=HTTPStatus.BAD_REQUEST)
        record["verified"] = True
        _append_reset_log(
            {"employeeId": employee_id, "email": email, "status": "verified", "checkedAt": datetime.utcnow().isoformat(timespec="seconds")}
        )
        return self.send_json({"ok": True, "message": "OTP verified successfully"})

    def handle_reset_password(self):
        _purge_expired_reset_tokens()
        payload = self.read_json()
        employee_id = normalize_emp_code(payload.get("employeeId"))
        email = clean_string(payload.get("email")).lower()
        otp = clean_string(payload.get("otp"))
        new_password = str(payload.get("newPassword", "")).strip()
        confirm_password = str(payload.get("confirmPassword", "")).strip()
        record = RESET_OTP_STORE.get(employee_id)
        if not record or record.get("email") != email:
            return self.send_json({"error": "Request OTP first before resetting your password"}, status=HTTPStatus.BAD_REQUEST)
        if datetime.utcnow() > datetime.fromisoformat(record["expiresAt"]):
            RESET_OTP_STORE.pop(employee_id, None)
            _append_reset_log(
                {"employeeId": employee_id, "email": email, "status": "expired", "checkedAt": datetime.utcnow().isoformat(timespec="seconds")}
            )
            return self.send_json({"error": "OTP has expired. Request a new one."}, status=HTTPStatus.BAD_REQUEST)
        if record.get("otp") != otp:
            return self.send_json({"error": "OTP is incorrect"}, status=HTTPStatus.BAD_REQUEST)
        if not record.get("verified"):
            return self.send_json({"error": "Verify the OTP before resetting your password"}, status=HTTPStatus.BAD_REQUEST)
        if len(new_password) < 6:
            return self.send_json({"error": "New password must be at least 6 characters"}, status=HTTPStatus.BAD_REQUEST)
        if new_password != confirm_password:
            return self.send_json({"error": "New password and confirm password do not match"}, status=HTTPStatus.BAD_REQUEST)
        update_password(employee_id, new_password)
        DATA_SERVICE.reload()
        RESET_OTP_STORE.pop(employee_id, None)
        _append_reset_log(
            {"employeeId": employee_id, "email": email, "status": "completed", "checkedAt": datetime.utcnow().isoformat(timespec="seconds")}
        )
        return self.send_json({"ok": True, "message": "Password reset successfully"})

    def handle_upload_datasets(self):
        session = self.require_admin()
        if not session:
            return

        form = _MultipartForm(self.rfile, self.headers)
        uploads = {}
        for field_name in ("misWorkbook", "ytdWorkbook", "closureWorkbook", "employeeSheet", "teamSheet"):
            field = form[field_name] if field_name in form else None
            if field is None or not getattr(field, "filename", ""):
                continue
            if not field.filename.lower().endswith(".xlsx"):
                return self.send_json({"error": f"{field_name} must be an .xlsx file"}, status=HTTPStatus.BAD_REQUEST)
            current_status = next((item for item in DATA_SERVICE.state["datasets"] if item.get("key") == field_name), None)
            if current_status and current_status.get("fileName") == Path(field.filename).name:
                return self.send_json(
                    {"error": f"{field.filename} is already the active file for {field_name}. Delete or replace it with a new file name."},
                    status=HTTPStatus.BAD_REQUEST,
                )
            uploads[field_name] = {"filename": field.filename, "bytes": field.file.read()}

        if not uploads:
            return self.send_json({"error": "Upload at least one Excel file before refreshing"}, status=HTTPStatus.BAD_REQUEST)

        DATA_SERVICE.save_uploaded_datasets(uploads)
        dashboard = DATA_SERVICE.dashboard_payload(session["employeeId"], admin_mode=True)
        return self.send_json({"ok": True, "message": "Dashboard data refreshed successfully.", "dashboard": dashboard})

    def handle_delete_datasets(self):
        session = self.require_admin()
        if not session:
            return
        DATA_SERVICE.clear()
        dashboard = DATA_SERVICE.dashboard_payload(session["employeeId"], admin_mode=True)
        return self.send_json(
            {
                "ok": True,
                "message": "Existing uploaded dashboard data has been cleared. Upload fresh Excel sheets to rebuild it.",
                "dashboard": dashboard,
            }
        )

    def handle_delete_dataset(self):
        session = self.require_admin()
        if not session:
            return
        payload = self.read_json()
        dataset_key = clean_string(payload.get("datasetKey"))
        if not dataset_key:
            return self.send_json({"error": "Dataset key is required"}, status=HTTPStatus.BAD_REQUEST)
        DATA_SERVICE.delete_uploaded_dataset(dataset_key)
        dashboard = DATA_SERVICE.dashboard_payload(session["employeeId"], admin_mode=True)
        return self.send_json({"ok": True, "message": "Selected file deleted successfully.", "dashboard": dashboard})

    def handle_reload_dashboard(self):
        session = self.require_admin()
        if not session:
            return
        DATA_SERVICE.reload()
        dashboard = DATA_SERVICE.dashboard_payload(session["employeeId"], admin_mode=True)
        return self.send_json({"ok": True, "message": "Dashboard reloaded from the latest uploaded files.", "dashboard": dashboard})
