import hashlib
import json
import os
import secrets
import smtplib
from email.message import EmailMessage

from services.config_service import ACCOUNTS_FILE, CONTACTS_FILE, load_app_config
from services.utils import clean_string, normalize_emp_code, normalize_name


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
    with ACCOUNTS_FILE.open("w", encoding="utf-8") as handle:
        json.dump(accounts, handle, indent=2)


def load_contacts():
    if not CONTACTS_FILE.exists():
        return []
    with CONTACTS_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_known_people():
    known = {}
    for item in load_contacts() + load_accounts():
        employee_id = normalize_emp_code(item.get("employeeId"))
        name = clean_string(item.get("name"))
        existing_by_id = known.get(f"id:{employee_id}", {}) if employee_id else {}
        existing_by_name = known.get(f"name:{normalize_name(name)}", {}) if name else {}
        merged = dict(existing_by_id or existing_by_name or {})
        merged.update(item)
        if not clean_string(merged.get("email")):
            merged["email"] = clean_string(existing_by_id.get("email") or existing_by_name.get("email"))
        if employee_id:
            known[f"id:{employee_id}"] = merged
        if name:
            known[f"name:{normalize_name(name)}"] = merged
    return known


def sync_accounts_for_employees(employees):
    accounts = load_accounts()
    changed = False
    account_map = {normalize_emp_code(item.get("employeeId")): item for item in accounts}
    for employee in employees.values():
        account = account_map.get(employee.employee_id)
        if not account:
            password_data = hash_password(f"SME{employee.employee_id}")
            account = {
                "employeeId": employee.employee_id,
                "name": employee.name,
                "designation": employee.designation,
                "salt": password_data["salt"],
                "passwordHash": password_data["hash"],
                "mustChangePassword": True,
            }
            accounts.append(account)
            account_map[employee.employee_id] = account
            changed = True
        else:
            if employee.name and account.get("name") != employee.name:
                account["name"] = employee.name
                changed = True
            if employee.designation and account.get("designation") != employee.designation:
                account["designation"] = employee.designation
                changed = True
        employee.must_change_password = bool(account.get("mustChangePassword", True))
    if changed:
        save_accounts(accounts)
    return account_map


def update_password(employee_id, new_password):
    accounts = load_accounts()
    for account in accounts:
        if normalize_emp_code(account.get("employeeId")) == employee_id:
            password_data = hash_password(new_password)
            account["salt"] = password_data["salt"]
            account["passwordHash"] = password_data["hash"]
            account["mustChangePassword"] = False
            save_accounts(accounts)
            return True
    return False


def send_reset_otp_email(email, employee_name, otp):
    config = load_app_config()
    smtp = config.get("smtp", {})
    smtp = {
        "host": smtp.get("host") or os.environ.get("SMTP_HOST", ""),
        "port": smtp.get("port") or int(os.environ.get("SMTP_PORT", "587")),
        "username": smtp.get("username") or os.environ.get("SMTP_USERNAME", ""),
        "password": smtp.get("password") or os.environ.get("SMTP_PASSWORD", ""),
        "fromEmail": smtp.get("fromEmail") or os.environ.get("SMTP_FROM_EMAIL", ""),
        "useTls": smtp.get("useTls", True) if smtp.get("host") else os.environ.get("SMTP_USE_TLS", "true").lower() != "false",
    }
    if not smtp.get("host") or not smtp.get("username") or not smtp.get("fromEmail"):
        return {"ok": False, "error": "SMTP settings are not configured yet. OTP has been printed in the server log."}

    message = EmailMessage()
    message["Subject"] = "Flipspaces Incentive Dashboard OTP"
    message["From"] = smtp["fromEmail"]
    message["To"] = email
    message.set_content(
        f"Hello {employee_name},\n\nYour OTP for the Incentive Dashboard reset request is {otp}.\n\nRegards,\nFlipspaces"
    )

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
