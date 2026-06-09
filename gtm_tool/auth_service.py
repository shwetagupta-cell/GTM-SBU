import hashlib
import json
import secrets
import smtplib
from email.message import EmailMessage

from gtm_tool.config import ACCOUNTS_FILE, load_config


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


def sync_accounts(employees):
    accounts = load_accounts()
    changed = False
    account_map = {item.get("employeeId"): item for item in accounts}
    for employee in employees.values():
        account = account_map.get(employee["employeeId"])
        if not account:
            password_data = hash_password(f"GTM{employee['employeeId']}")
            account = {
                "employeeId": employee["employeeId"],
                "name": employee["name"],
                "designation": employee.get("designation", ""),
                "salt": password_data["salt"],
                "passwordHash": password_data["hash"],
                "mustChangePassword": True,
            }
            accounts.append(account)
            account_map[employee["employeeId"]] = account
            changed = True
        else:
            if account.get("name") != employee["name"]:
                account["name"] = employee["name"]
                changed = True
            if account.get("designation") != employee.get("designation", ""):
                account["designation"] = employee.get("designation", "")
                changed = True
        employee["mustChangePassword"] = bool(account.get("mustChangePassword", True))
    if changed:
        save_accounts(accounts)
    return account_map


def update_password(employee_id, new_password):
    accounts = load_accounts()
    for account in accounts:
        if account.get("employeeId") != employee_id:
            continue
        password_data = hash_password(new_password)
        account["salt"] = password_data["salt"]
        account["passwordHash"] = password_data["hash"]
        account["mustChangePassword"] = False
        save_accounts(accounts)
        return True
    return False


def send_reset_otp_email(email, employee_name, otp):
    config = load_config()
    smtp = config.get("smtp", {})
    if not smtp.get("host") or not smtp.get("username") or not smtp.get("fromEmail"):
        return {"ok": False, "error": "SMTP is not configured. OTP has been printed in the server log."}

    message = EmailMessage()
    message["Subject"] = "GTM Performance Tool OTP"
    message["From"] = smtp["fromEmail"]
    message["To"] = email
    message.set_content(
        f"Hello {employee_name},\n\nYour OTP for the GTM Performance Tool reset request is {otp}.\n\nRegards,\nGTM Performance Team"
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
