from services.utils import clean_string, normalize_name


def _add_people(value, people, seen, split_people):
    for name in split_people(value):
        normalized = normalize_name(name)
        if normalized and normalized not in seen:
            seen.add(normalized)
            people.append(name)


def mapped_people_from_row(row, split_people):
    """Read named and unlabeled employee columns from a project row."""
    people = []
    seen = set()
    employee_columns = {
        "team_members",
        "team_member",
        "mapped_employees",
        "mapped_employee",
        "employees",
        "employee_names",
        "employee_name",
        "employee",
        "sales_person",
        "owner",
    }
    person_columns = {f"person_{index}" for index in range(1, 9)}
    stop_columns = {
        "month",
        "period",
        "billing_month",
        "cashflow",
        "cash_flow",
        "monthly_cashflow",
        "monthly_cash_flow",
        "cash_flow_value",
        "approval_status",
        "status",
        "score",
        "incentive",
        "incentive_percent",
        "incentive_amount",
        "incentive_value",
        "remarks",
    }

    for key in [*employee_columns, *person_columns]:
        _add_people(row.get(key), people, seen, split_people)

    # Monthly project sheets often label only the first assignment column as
    # Employee. Blank headers to its right are normalized as item columns.
    assignment_started = False
    for column, value in row.items():
        column_name = clean_string(column).lower()
        if column_name in employee_columns or column_name in person_columns:
            assignment_started = True
            continue
        if not assignment_started:
            continue
        if column_name in stop_columns:
            break
        if column_name != "item" and not column_name.startswith("item_"):
            continue
        _add_people(value, people, seen, split_people)

    return people


def install():
    from gtm_tool import excel_service

    excel_service._mapped_people_from_row = lambda row: mapped_people_from_row(
        row, excel_service._split_people
    )
