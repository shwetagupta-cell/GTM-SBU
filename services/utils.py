import re


def clean_string(value) -> str:
    if isinstance(value, float) and value != value:
        return ""
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_emp_code(value) -> str:
    text = clean_string(value)
    if text.lower() == "nan":
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    return text


def normalize_name(value) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean_string(value).lower()).strip()


def slugify(value) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean_string(value).lower()).strip("-") or "item"


def parse_number(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, float) and value != value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = clean_string(value).replace(",", "")
    if not text or text.lower() in {"nan", "na", "#value!"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def month_label(value) -> str:
    text = clean_string(value)
    lowered = text.lower()
    mapping = {
        "nov": "Nov25",
        "november": "Nov25",
        "nov25": "Nov25",
        "dec": "Dec25",
        "december": "Dec25",
        "dec25": "Dec25",
        "jan": "Jan26",
        "january": "Jan26",
        "jan26": "Jan26",
        "feb": "Feb26",
        "february": "Feb26",
        "feb26": "Feb26",
        "mar": "Mar26",
        "march": "Mar26",
        "mar26": "Mar26",
        "apr": "April",
        "april": "April",
        "may": "May",
        "jun": "June",
        "june": "June",
        "jul": "July",
        "july": "July",
        "aug": "August",
        "august": "August",
        "sep": "September",
        "sept": "September",
        "september": "September",
        "oct": "October",
        "october": "October",
    }
    return mapping.get(lowered, text.title())
