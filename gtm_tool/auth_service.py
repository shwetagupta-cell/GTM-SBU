import hashlib
import json
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime

from gtm_tool.config import ACCOUNTS_FILE, ensure_dirs, load_config


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000).hex()
    return {"salt": salt, "hash": digest}


def verify_password(password, salt, password_hash):
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000).hex()
    return secrets.compare_digest(candidate, password_hash)


def load_accounts():
    if not ACCOUNTS_FILE.exists():
        return []
    with ACCOUNTS_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_accounts(accounts):
    ensure_dirs()
    with ACCOUNTS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(accounts, handle, indent=2)


def _now():
    return datetime.utcnow().isoformat(timespec="seconds")


def _send_email(to_email, subject, body):
    config = load_config()
    smtp = config.get("smtp", {})
    if not smtp.get("host") or not smtp.get("username") or not smtp.get("fromEmail"):
        return {"ok": False, "error": "SMTP is not configured."}

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp["fromEmail"]
    message["To"] = to_email
    message.set_content(body)

    try:
        if smtp.get("useTls", True):
            with smtplib.SMTP(smtp["host"], int(smtp.get("port", 587))) as server:
                server.starttls()
                server.login(smtp["username"], smtp.get("password", ""))
                server.send_message(message)
        else:
            with smtplib.SMTP_SSL(smtp["host"], int(smtp.get("port", 465))) as server:
                server.login(smtp["username"], smtp.get("password", ""))
                server.send_message(message)
        return {"ok": True}
    except Exception as error:
        return {"ok": False, "error": str(error)}


def send_new_employee_credentials_email(credentials, to_email="shweta.gupta@flipspaces.com"):
    if not credentials:
        return {"ok": True, "skipped": True}
    lines = [
        "New GTM/SBU employees were detected and login credentials were created:",
        "",
    ]
    for item in credentials:
        lines.append(f"{item['name']} | Employee ID: {item['employeeId']} | Password: {item['password']}")
    result = _send_email(to_email, "New GTM/SBU employee login credentials", "\n".join(lines))
    if not result.get("ok"):
        print("New employee credentials could not be emailed:", result.get("error"))
        for item in credentials:
            print(f"GTM credential {item['employeeId']} {item['name']}: {item['password']}")
    return result


def sync_accounts(employees):
    accounts = load_accounts()
    changed = False
    account_map = {item.get("employeeId"): item for item in accounts}
    new_credentials = []
    for employee in employees.values():
        account = account_map.get(employee["employeeId"])
        if not account:
            default_password = f"GTM{employee['employeeId']}"
            password_data = hash_password(default_password)
            account = {
                "employeeId": employee["employeeId"],
                "loginId": employee.get("loginId") or employee["employeeId"],
                "name": employee["name"],
                "email": employee.get("email", ""),
                "designation": employee.get("designation", ""),
                "department": employee.get("department", ""),
                "status": employee.get("status", "active"),
                "salt": password_data["salt"],
                "passwordHash": password_data["hash"],
                "mustChangePassword": True,
                "createdAt": _now(),
                "updatedAt": _now(),
            }
            accounts.append(account)
            account_map[employee["employeeId"]] = account
            new_credentials.append({"employeeId": employee["employeeId"], "name": employee.get("name", ""), "password": default_password})
            changed = True
        else:
            account_changed = False
            login_id = employee.get("loginId") or employee["employeeId"]
            if account.get("loginId") != login_id:
                account["loginId"] = login_id
                account_changed = True
            if account.get("name") != employee["name"]:
                account["name"] = employee["name"]
                account_changed = True
            if account.get("email") != employee.get("email", ""):
                account["email"] = employee.get("email", "")
                account_changed = True
            if account.get("designation") != employee.get("designation", ""):
                account["designation"] = employee.get("designation", "")
                account_changed = True
            if account.get("department") != employee.get("department", ""):
                account["department"] = employee.get("department", "")
                account_changed = True
            if account.get("status") != employee.get("status", "active"):
                account["status"] = employee.get("status", "active")
                account_changed = True
            if account_changed:
                account["updatedAt"] = _now()
                changed = True
        employee["loginId"] = account.get("loginId") or employee["employeeId"]
        employee["mustChangePassword"] = bool(account.get("mustChangePassword", True))
    if changed:
        save_accounts(accounts)
    if new_credentials:
        send_new_employee_credentials_email(new_credentials)
    return account_map


def find_account(login_id_or_employee_id):
    lookup = str(login_id_or_employee_id or "").strip().lower()
    if not lookup:
        return None
    for account in load_accounts():
        employee_id = str(account.get("employeeId", "")).strip().lower()
        login_id = str(account.get("loginId") or account.get("employeeId") or "").strip().lower()
        if lookup in {employee_id, login_id}:
            return account
    return None


def upsert_account(employee_id, name, designation="", department="", email="", login_id="", temp_password="", status="active"):
    employee_id = str(employee_id or "").strip()
    if not employee_id:
        return None
    accounts = load_accounts()
    account = next((item for item in accounts if item.get("employeeId") == employee_id), None)
    created = False
    if not account:
        password_text = temp_password or f"GTM{employee_id}"
        password_data = hash_password(password_text)
        account = {
            "employeeId": employee_id,
            "salt": password_data["salt"],
            "passwordHash": password_data["hash"],
            "mustChangePassword": True,
            "createdAt": _now(),
        }
        accounts.append(account)
        created = True
    account["loginId"] = (login_id or employee_id).strip()
    account["name"] = name or employee_id
    account["designation"] = designation or account.get("designation", "")
    account["department"] = department or account.get("department", "")
    account["email"] = email or account.get("email", "")
    account["status"] = status or account.get("status", "active")
    if temp_password:
        password_data = hash_password(temp_password)
        account["salt"] = password_data["salt"]
        account["passwordHash"] = password_data["hash"]
        account["mustChangePassword"] = True
    elif created and "mustChangePassword" not in account:
        account["mustChangePassword"] = True
    account["updatedAt"] = _now()
    save_accounts(accounts)
    return account


def update_password(employee_id, new_password):
    accounts = load_accounts()
    for account in accounts:
        if account.get("employeeId") != employee_id:
            continue
        password_data = hash_password(new_password)
        account["salt"] = password_data["salt"]
        account["passwordHash"] = password_data["hash"]
        account["mustChangePassword"] = False
        account["updatedAt"] = _now()
        save_accounts(accounts)
        return True
    return False


def send_reset_otp_email(email, employee_name, otp):
    result = _send_email(
        email,
        "GTM Performance Tool OTP",
        f"Hello {employee_name},\n\nYour OTP for the GTM Performance Tool reset request is {otp}.\n\nRegards,\nGTM Performance Team",
    )
    if not result.get("ok"):
        return {"ok": False, "error": "SMTP is not configured. OTP has been printed in the server log."}
    return result
