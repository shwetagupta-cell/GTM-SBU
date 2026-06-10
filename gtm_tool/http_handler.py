import io
import json
import secrets
import time
from email.parser import BytesParser
from email.policy import compat32
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler
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

from gtm_tool.auth_service import find_account, load_accounts, send_reset_otp_email, update_password, verify_password
from gtm_tool.config import DEFAULT_ADMIN_ID, ROOT, load_config, save_config
from gtm_tool.data_service import DATA_SERVICE
from services.utils import clean_string


SESSION_COOKIE = "gtm_session"
SESSIONS = {}
RESET_OTP_STORE = {}
OTP_TTL_SECONDS = 10 * 60


def _account_map():
    return {item.get("employeeId"): item for item in load_accounts()}


class GTMAppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_json(self, payload, status=HTTPStatus.OK, set_cookie=None, clear_cookie=False):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if set_cookie:
            secure = "; Secure" if self.headers.get("X-Forwarded-Proto", "").lower() == "https" else ""
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}={set_cookie}; Path=/; HttpOnly; SameSite=Lax{secure}")
        if clear_cookie:
            self.send_header("Set-Cookie", f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0")
        self.end_headers()
        self.wfile.write(body)

    def send_csv(self, content, filename="gtm-report.csv"):
        body = content.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
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

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        return json.loads(body.decode("utf-8") or "{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.path = "/gtm_index.html"
            return super().do_GET()
        if parsed.path == "/api/me":
            return self.handle_me(parsed)
        if parsed.path in {"/api/admin/report.csv", "/api/report.csv"}:
            return self.handle_report()
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
        if parsed.path == "/api/admin/employees":
            return self.handle_upsert_employee()
        if parsed.path == "/api/admin/employees/delete":
            return self.handle_delete_employee()
        if parsed.path == "/api/admin/employees/undo":
            return self.handle_undo_employee()
        if parsed.path == "/api/admin/kpi/update":
            return self.handle_update_kpi()
        if parsed.path == "/api/admin/project/update":
            return self.handle_update_project()
        if parsed.path == "/api/admin/status/update":
            return self.handle_update_status()
        if parsed.path == "/api/admin/upload-workbook":
            return self.handle_upload_workbook()
        if parsed.path == "/api/admin/delete-upload":
            return self.handle_delete_upload()
        return self.send_json({"error": "Unknown endpoint"}, status=HTTPStatus.NOT_FOUND)

    def handle_me(self, parsed):
        session = self.require_session()
        if not session:
            return
        query = parse_qs(parsed.query)
        target_employee_id = clean_string(query.get("employeeId", [""])[0])
        search = clean_string(query.get("search", [""])[0])
        start_date = clean_string(query.get("startDate", [""])[0])
        end_date = clean_string(query.get("endDate", [""])[0])
        period_label = clean_string(query.get("period", [""])[0])
        payload = DATA_SERVICE.dashboard_payload(
            session["employeeId"],
            target_employee_id=target_employee_id,
            admin_mode=bool(session.get("adminMode")),
            search=search,
            start_date=start_date,
            end_date=end_date,
            period_label=period_label,
        )
        return self.send_json(payload)

    def handle_report(self):
        session = self.require_session()
        if not session:
            return
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        employee_id = clean_string(query.get("employeeId", [""])[0])
        start_date = clean_string(query.get("startDate", [""])[0])
        end_date = clean_string(query.get("endDate", [""])[0])
        period_label = clean_string(query.get("period", [""])[0])
        if not session.get("adminMode") and not employee_id:
            employee_id = session["employeeId"]
        return self.send_csv(
            DATA_SERVICE.export_csv(
                viewer_id=session["employeeId"],
                admin_mode=bool(session.get("adminMode")),
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                period_label=period_label,
            )
        )

    def handle_login(self):
        payload = self.read_json()
        employee_id = clean_string(payload.get("employeeId"))
        password = clean_string(payload.get("password"))
        login_type = clean_string(payload.get("loginType") or "employee").lower()
        account = find_account(employee_id)
        if not account or not verify_password(password, account["salt"], account["passwordHash"]):
            return self.send_json({"error": "Invalid employee ID or password"}, status=HTTPStatus.UNAUTHORIZED)
        if clean_string(account.get("status", "active")).lower() != "active":
            return self.send_json({"error": "This user is inactive. Please contact Admin."}, status=HTTPStatus.UNAUTHORIZED)
        employee_id = clean_string(account.get("employeeId"))
        config = load_config()
        admin_mode = login_type == "admin"
        if admin_mode and employee_id not in config.get("adminEmployeeIds", []):
            return self.send_json({"error": "This account does not have admin access"}, status=HTTPStatus.UNAUTHORIZED)
        if not admin_mode and employee_id not in DATA_SERVICE.state["employees"]:
            return self.send_json({"error": "Employee not found in GTM master data"}, status=HTTPStatus.UNAUTHORIZED)
        token = secrets.token_urlsafe(24)
        SESSIONS[token] = {"employeeId": employee_id, "adminMode": admin_mode}
        return self.send_json(
            DATA_SERVICE.dashboard_payload(employee_id, admin_mode=admin_mode),
            set_cookie=token,
        )

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
        account = _account_map().get(session["employeeId"])
        if not account or not verify_password(clean_string(payload.get("currentPassword")), account["salt"], account["passwordHash"]):
            return self.send_json({"error": "Current password is incorrect"}, status=HTTPStatus.BAD_REQUEST)
        new_password = clean_string(payload.get("newPassword"))
        confirm_password = clean_string(payload.get("confirmPassword"))
        if len(new_password) < 6:
            return self.send_json({"error": "New password must be at least 6 characters"}, status=HTTPStatus.BAD_REQUEST)
        if new_password != confirm_password:
            return self.send_json({"error": "New password and confirm password do not match"}, status=HTTPStatus.BAD_REQUEST)
        update_password(session["employeeId"], new_password)
        DATA_SERVICE.reload()
        return self.send_json({"ok": True, "message": "Password updated successfully"})

    def handle_request_reset_otp(self):
        payload = self.read_json()
        employee_id = clean_string(payload.get("employeeId"))
        employee_name = clean_string(payload.get("employeeName") or payload.get("name"))
        email = clean_string(payload.get("email")).lower()
        employee = DATA_SERVICE.state["employees"].get(employee_id) if employee_id else None
        if not employee and email:
            employee = next(
                (item for item in DATA_SERVICE.state["employees"].values() if clean_string(item.get("email")).lower() == email),
                None,
            )
        if not employee:
            return self.send_json({"error": "Employee not found"}, status=HTTPStatus.BAD_REQUEST)
        employee_id = clean_string(employee.get("employeeId"))
        if employee_name and clean_string(employee.get("name")).lower() != employee_name.lower():
            return self.send_json({"error": "Employee name does not match this record"}, status=HTTPStatus.BAD_REQUEST)
        expected = clean_string(employee.get("email", "")).lower()
        if not email or (expected and expected != email):
            return self.send_json({"error": "The email does not match this employee record"}, status=HTTPStatus.BAD_REQUEST)
        otp = f"{secrets.randbelow(1000000):06d}"
        RESET_OTP_STORE[employee_id] = {"otp": otp, "email": email, "expiresAt": time.time() + OTP_TTL_SECONDS, "attempts": 0, "verified": False}
        result = send_reset_otp_email(email, employee.get("name", employee_id), otp)
        print(f"GTM reset OTP for {employee_id} ({email}): {otp}")
        return self.send_json({"ok": True, "employeeId": employee_id, "message": "OTP sent successfully." if result.get("ok") else result.get("error")})

    def handle_verify_reset_otp(self):
        payload = self.read_json()
        employee_id = clean_string(payload.get("employeeId"))
        record = RESET_OTP_STORE.get(employee_id)
        if not record or record.get("email") != clean_string(payload.get("email")).lower():
            return self.send_json({"error": "Request OTP first before verifying."}, status=HTTPStatus.BAD_REQUEST)
        if time.time() > record.get("expiresAt", 0):
            RESET_OTP_STORE.pop(employee_id, None)
            return self.send_json({"error": "OTP expired. Please request a new OTP."}, status=HTTPStatus.BAD_REQUEST)
        record["attempts"] = int(record.get("attempts", 0)) + 1
        if record["attempts"] > 5:
            RESET_OTP_STORE.pop(employee_id, None)
            return self.send_json({"error": "Too many OTP attempts. Please request a new OTP."}, status=HTTPStatus.BAD_REQUEST)
        if record.get("otp") != clean_string(payload.get("otp")):
            return self.send_json({"error": "OTP is incorrect"}, status=HTTPStatus.BAD_REQUEST)
        record["verified"] = True
        return self.send_json({"ok": True, "message": "OTP verified. Create your new password."})

    def handle_reset_password(self):
        payload = self.read_json()
        employee_id = clean_string(payload.get("employeeId"))
        record = RESET_OTP_STORE.get(employee_id)
        if not record or record.get("email") != clean_string(payload.get("email")).lower():
            return self.send_json({"error": "Request OTP first before resetting your password"}, status=HTTPStatus.BAD_REQUEST)
        if time.time() > record.get("expiresAt", 0):
            RESET_OTP_STORE.pop(employee_id, None)
            return self.send_json({"error": "OTP expired. Please request a new OTP."}, status=HTTPStatus.BAD_REQUEST)
        if record.get("otp") != clean_string(payload.get("otp")):
            return self.send_json({"error": "OTP is incorrect"}, status=HTTPStatus.BAD_REQUEST)
        if not record.get("verified"):
            return self.send_json({"error": "Verify OTP before creating a new password"}, status=HTTPStatus.BAD_REQUEST)
        new_password = clean_string(payload.get("newPassword"))
        confirm_password = clean_string(payload.get("confirmPassword"))
        if len(new_password) < 6:
            return self.send_json({"error": "New password must be at least 6 characters"}, status=HTTPStatus.BAD_REQUEST)
        if new_password != confirm_password:
            return self.send_json({"error": "New password and confirm password do not match"}, status=HTTPStatus.BAD_REQUEST)
        update_password(employee_id, new_password)
        DATA_SERVICE.reload()
        RESET_OTP_STORE.pop(employee_id, None)
        return self.send_json({"ok": True, "message": "Password reset successfully"})

    def handle_upsert_employee(self):
        session = self.require_admin()
        if not session:
            return
        payload = self.read_json()
        try:
            employee = DATA_SERVICE.upsert_employee(payload)
        except ValueError as error:
            return self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        if "adminAccess" in payload:
            config = load_config()
            admin_ids = set(config.get("adminEmployeeIds", []))
            admin_ids.add(DEFAULT_ADMIN_ID)
            employee_id = clean_string(employee.get("employeeId"))
            if payload.get("adminAccess"):
                admin_ids.add(employee_id)
            elif employee_id != DEFAULT_ADMIN_ID:
                admin_ids.discard(employee_id)
            config["adminEmployeeIds"] = sorted(admin_ids)
            save_config(config)
        return self.send_json({"ok": True, "employee": employee})

    def handle_delete_employee(self):
        session = self.require_admin()
        if not session:
            return
        payload = self.read_json()
        deleted = DATA_SERVICE.delete_employee(clean_string(payload.get("employeeId")))
        if not deleted:
            return self.send_json({"error": "Employee not found"}, status=HTTPStatus.NOT_FOUND)
        return self.send_json({"ok": True})

    def handle_undo_employee(self):
        session = self.require_admin()
        if not session:
            return
        employee = DATA_SERVICE.undo_delete_employee()
        if not employee:
            return self.send_json({"error": "Nothing to undo"}, status=HTTPStatus.BAD_REQUEST)
        return self.send_json({"ok": True, "employee": employee})

    def handle_update_kpi(self):
        session = self.require_admin()
        if not session:
            return
        try:
            updated = DATA_SERVICE.update_kpi(self.read_json())
        except ValueError as error:
            return self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        return self.send_json({"ok": True, "kpi": updated})

    def handle_update_project(self):
        session = self.require_admin()
        if not session:
            return
        try:
            updated = DATA_SERVICE.update_project(self.read_json())
        except ValueError as error:
            return self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        return self.send_json({"ok": True, "project": updated})

    def handle_update_status(self):
        session = self.require_admin()
        if not session:
            return
        try:
            updated = DATA_SERVICE.update_disbursal_status(self.read_json())
        except ValueError as error:
            return self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        return self.send_json({"ok": True, "status": updated})

    def handle_upload_workbook(self):
        session = self.require_admin()
        if not session:
            return
        form = _MultipartForm(self.rfile, self.headers)
        workbook = form["workbook"] if "workbook" in form else None
        if workbook is None or not getattr(workbook, "filename", ""):
            return self.send_json({"error": "Upload an Excel workbook first"}, status=HTTPStatus.BAD_REQUEST)
        if not workbook.filename.lower().endswith(".xlsx"):
            return self.send_json({"error": "Workbook must be an .xlsx file"}, status=HTTPStatus.BAD_REQUEST)
        replace_file_id = clean_string(form.getvalue("replaceFileId", ""))
        upload_type = clean_string(form.getvalue("uploadType", ""))
        try:
            uploaded = DATA_SERVICE.apply_workbook_upload(workbook.filename, workbook.file.read(), upload_type, replace_file_id)
        except ValueError as error:
            return self.send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        return self.send_json({"ok": True, "upload": uploaded})

    def handle_delete_upload(self):
        session = self.require_admin()
        if not session:
            return
        payload = self.read_json()
        deleted = DATA_SERVICE.delete_upload(clean_string(payload.get("fileId")))
        if not deleted:
            return self.send_json({"error": "Upload record not found"}, status=HTTPStatus.NOT_FOUND)
        return self.send_json({"ok": True})
