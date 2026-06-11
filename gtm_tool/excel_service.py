from services.utils import clean_string, normalize_emp_code, normalize_name, parse_number, slugify


GRADE_COLUMNS = [16, 17, 18, 19]
MONTH_NAMES = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def _load_pandas():
    import pandas as pd

    return pd


def _normalize_headers(values):
    return [slugify(value).replace("-", "_") for value in values]


def _month_from_text(value):
    text = clean_string(value).lower().replace("-", " ").replace("_", " ")
    for part in text.split():
        if part in MONTH_NAMES:
            return MONTH_NAMES[part]
    return None


def _period_from_value(value, sheet_name=""):
    text = clean_string(value) or clean_string(sheet_name)
    parts = text.replace("-", " ").replace("_", " ").split()
    month = None
    year = None
    for part in parts:
        lowered = part.lower()
        if lowered in MONTH_NAMES:
            month = MONTH_NAMES[lowered]
        elif part.isdigit() and len(part) == 4:
            year = int(part)
        elif part.isdigit() and len(part) == 2:
            year = 2000 + int(part)
    if month and year:
        return f"{year}-{month:02d}"
    return ""


def _first_value(row, *keys):
    for key in keys:
        value = row.get(key)
        if clean_string(value):
            return value
    return ""


def _best_header_row(dataframe, required_terms):
    for idx in range(min(len(dataframe.index), 8)):
        cells = _normalize_headers(dataframe.iloc[idx].tolist())
        if all(any(term in cell for cell in cells) for term in required_terms):
            return idx
    return 0


def _frame_from_sheet(path, sheet_name, required_terms):
    pd = _load_pandas()
    raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
    header_row = _best_header_row(raw, required_terms)
    headers = [clean_string(value) for value in raw.iloc[header_row].tolist()]
    frame = raw.iloc[header_row + 1 :].copy().fillna("").infer_objects(copy=False)
    frame.columns = _normalize_headers(headers)
    return frame


def _normalize_department(value, fallback=""):
    text = clean_string(value).upper()
    mapping = {
        "DIGITAL MARKETING": "Digital Marketing",
        "VIZTOWN": "Viztown",
        "EVENTS": "Events",
        "PARTNERSHIPS": "Marketing",
        "FOUNDER'S OFFICE": "Founder Connect",
    }
    if text in mapping:
        return mapping[text]

    source = " ".join([clean_string(value).lower(), clean_string(fallback).lower()])
    if "event" in source:
        return "Events"
    if "viz" in source or " vt " in f" {source} ":
        return "Viztown"
    if "digital" in source or " dm " in f" {source} ":
        return "Digital Marketing"
    if "founder" in source or "fo" in source:
        return "Founder Connect"
    if any(token in source for token in ("marketing", "business development", "bd", "partnership")):
        return "Marketing"
    if "operation" in source or "ops" in source:
        return "Operations"
    if "design" in source:
        return "Design"
    return clean_string(value).title() or clean_string(fallback).title() or "Marketing"


def _role_from_designation(designation, level=""):
    lowered = " ".join([clean_string(designation).lower(), clean_string(level).lower()])
    if any(token in lowered for token in ("vice president", "vp", "avp", "founder", "chief", "head")):
        return "india_head"
    if any(token in lowered for token in ("general manager", "gm", "national", "vertical")):
        return "national_vertical_head"
    if any(token in lowered for token in ("regional", "agm", "dgm", "assistant general manager", "deputy general manager")):
        return "regional_head"
    return "manager"


def _disbursal_type_from_designation(designation):
    lowered = clean_string(designation).lower()
    if any(token in lowered for token in ("vice president", "vp", "avp", "founder", "chief")):
        return "annually"
    if any(token in lowered for token in ("operations", "designer", "design")):
        return "monthly"
    return "quarterly"


def _project_incentive_percent_for_role(role):
    defaults = {
        "india_head": 3.0,
        "national_vertical_head": 2.5,
        "regional_head": 2.0,
        "manager": 1.5,
    }
    return defaults.get(role, 2.0)


def _parse_grade_weights(header_row, data_row):
    grade_weights = {}
    for column in GRADE_COLUMNS:
        grade_key = clean_string(header_row[column] if len(header_row) > column else "").upper()
        if not grade_key:
            continue
        weight = parse_number(data_row[column] if len(data_row) > column else 0)
        if weight <= 0:
            continue
        grade_weights[grade_key] = max(weight, grade_weights.get(grade_key, 0))
    return grade_weights


def _framework_row(section_name, match_key, source, header_row, data_row, display_order):
    kra_name = clean_string(data_row[2] if len(data_row) > 2 else "")
    kpi_name = clean_string(data_row[3] if len(data_row) > 3 else "")
    if not kpi_name:
        return None
    return {
        "frameworkId": slugify(f"{source}-{match_key}-{kra_name}-{kpi_name}"),
        "displayOrder": display_order,
        "source": source,
        "matchKey": match_key,
        "sectionName": section_name,
        "kraCategory": kra_name,
        "kpiName": kpi_name,
        "target": parse_number(data_row[4] if len(data_row) > 4 else 0),
        "achieved": parse_number(data_row[5] if len(data_row) > 5 else 0),
        "definition": clean_string(data_row[8] if len(data_row) > 8 else ""),
        "measurement": clean_string(data_row[9] if len(data_row) > 9 else ""),
        "periodicity": clean_string(data_row[10] if len(data_row) > 10 else "") or "Monthly",
        "scoreBands": {
            "5": clean_string(data_row[11] if len(data_row) > 11 else ""),
            "4": clean_string(data_row[12] if len(data_row) > 12 else ""),
            "3": clean_string(data_row[13] if len(data_row) > 13 else ""),
            "2": clean_string(data_row[14] if len(data_row) > 14 else ""),
            "1": clean_string(data_row[15] if len(data_row) > 15 else ""),
        },
        "gradeWeights": _parse_grade_weights(header_row, data_row),
    }


def _parse_nps_rules(rows, scheme_lookup=None, sheet_key=""):
    scheme_lookup = scheme_lookup or {}
    current_scheme = ""
    rules = []
    for row in rows:
        row_values = [clean_string(value) for value in row]
        for value in row_values:
            if value.startswith("Incentive Disbursal Scheme"):
                current_scheme = scheme_lookup.get(value, value.split("(")[-1].replace(")", "").strip().lower())
                break
        if not current_scheme:
            continue
        nps_range = clean_string(row[12] if len(row) > 12 else "")
        disbursal = parse_number(row[13] if len(row) > 13 else 0)
        if not nps_range or disbursal <= 0:
            continue
        rules.append(
            {
                "source": sheet_key,
                "scheme": current_scheme,
                "npsRange": nps_range,
                "disbursal": disbursal,
            }
        )
    return rules


def parse_gtm_logic_workbook(path):
    pd = _load_pandas()
    workbook = pd.ExcelFile(path)
    frameworks = []
    incentive_rules = []

    if "KPI FRAMEWORK" in workbook.sheet_names:
        raw = pd.read_excel(path, sheet_name="KPI FRAMEWORK", header=None).fillna("")
        rows = raw.values.tolist()
        current_department = ""
        header_row = []
        display_order = 0
        for index, row in enumerate(rows):
            first = clean_string(row[0] if len(row) > 0 else "")
            second = clean_string(row[1] if len(row) > 1 else "")
            fourth = clean_string(row[3] if len(row) > 3 else "")
            if first and index + 1 < len(rows):
                next_row = rows[index + 1]
                if clean_string(next_row[1] if len(next_row) > 1 else "").lower() == "weight":
                    current_department = _normalize_department(first)
                    header_row = next_row
                    continue
            if second.lower() != "x" or not current_department or not fourth:
                continue
            framework = _framework_row(current_department, current_department, "gtm", header_row, row, display_order)
            if framework:
                framework["department"] = current_department
                frameworks.append(framework)
                display_order += 1

    if "Incentive Calculation - GTM" in workbook.sheet_names:
        raw = pd.read_excel(path, sheet_name="Incentive Calculation - GTM", header=None).fillna("")
        incentive_rules = _parse_nps_rules(
            raw.values.tolist(),
            scheme_lookup={
                "Incentive Disbursal Scheme (Quarterly)": "quarterly",
                "Incentive Disbursal Scheme (Annually)": "annually",
            },
            sheet_key="gtm",
        )

    return {
        "uploadType": "gtm_logic",
        "frameworks": frameworks,
        "incentiveRules": incentive_rules,
        "recordCount": len(frameworks),
    }


def parse_sbu_logic_workbook(path):
    pd = _load_pandas()
    workbook = pd.ExcelFile(path)
    frameworks = []
    incentive_rules = []

    if "SBU KPIs (Updated)" in workbook.sheet_names:
        raw = pd.read_excel(path, sheet_name="SBU KPIs (Updated)", header=None).fillna("")
        rows = raw.values.tolist()
        section_meta = {
            "OPS": ("SBU Ops", "sbu_ops"),
            "SALES": ("SBU Sales", "sbu_sales"),
            "DESIGN (PRE-SALES)": ("SBU Design Pre-Sales", "sbu_design_pre"),
            "DESIGN (POST-SALES)": ("SBU Design Post-Sales", "sbu_design_post"),
        }
        active_section_name = ""
        active_match_key = ""
        header_row = []
        display_order = 0

        for row in rows:
            marker = clean_string(row[0] if len(row) > 0 else "")
            marker_upper = marker.upper()
            header_check = clean_string(row[2] if len(row) > 2 else "")
            if marker_upper == "GTM":
                active_section_name = ""
                active_match_key = ""
                header_row = []
                continue
            section_key = next((key for key in section_meta if marker_upper.startswith(key)), "")
            if section_key:
                active_section_name, active_match_key = section_meta[section_key]
                header_row = []
                continue
            if not active_match_key:
                continue
            if header_check == "KRA":
                header_row = row
                continue
            if not header_row:
                continue
            if not clean_string(row[2] if len(row) > 2 else "") or not clean_string(row[3] if len(row) > 3 else ""):
                continue
            framework = _framework_row(active_section_name, active_match_key, "sbu", header_row, row, display_order)
            if framework:
                frameworks.append(framework)
                display_order += 1

    sheet_schemes = {
        "Incentive Calculation- Ops": "sbu_ops",
        "Incentive Calculation- Sales": "sbu_sales",
        "Incentive Calculation- Design": "sbu_design",
    }
    for sheet_name, sheet_key in sheet_schemes.items():
        if sheet_name not in workbook.sheet_names:
            continue
        raw = pd.read_excel(path, sheet_name=sheet_name, header=None).fillna("")
        incentive_rules.extend(
            _parse_nps_rules(
                raw.values.tolist(),
                scheme_lookup={
                    "Incentive Disbursal Scheme (Monthly)": "monthly",
                    "Incentive Disbursal Scheme (Quarterly)": "quarterly",
                    "Incentive Disbursal Scheme (Annually)": "annually",
                },
                sheet_key=sheet_key,
            )
        )

    return {
        "uploadType": "sbu_logic",
        "frameworks": frameworks,
        "incentiveRules": incentive_rules,
        "recordCount": len(frameworks),
    }


def parse_team_workbook(path):
    frame = _frame_from_sheet(path, "Sheet1", ["emp_code", "employee_name", "reports_to"])
    employees = []
    for _, row in frame.iterrows():
        employee_id = normalize_emp_code(row.get("emp_code"))
        name = clean_string(row.get("employee_name"))
        if not employee_id or not name:
            continue
        level = clean_string(row.get("l1_l2_l3") or row.get("grade")).upper()
        grade_band = clean_string(row.get("grade"))
        designation = clean_string(row.get("actual_designation") or row.get("designation"))
        source_department = clean_string(row.get("department"))
        current_sbu = clean_string(row.get("current_sbu"))
        new_sbu = clean_string(row.get("new_sbu_as_per_aop"))
        business_unit = "SBU" if "sbu" in f"{current_sbu} {new_sbu}".lower() else "GTM"
        normalized_department = _normalize_department(new_sbu, source_department or current_sbu)

        if business_unit == "SBU":
            descriptor = f"{source_department} {designation} {current_sbu} {new_sbu}".lower()
            if "design" in descriptor:
                if any(token in descriptor for token in ("pre sales", "pre-sales", "presales", "pre sale", "pre-sale")):
                    logic_key = "sbu_design_pre"
                else:
                    logic_key = "sbu_design_post"
            elif "operation" in descriptor or "ops" in descriptor:
                logic_key = "sbu_ops"
            else:
                logic_key = "sbu_sales"
        else:
            logic_key = normalized_department

        role = _role_from_designation(designation, level)
        employees.append(
            {
                "employeeId": employee_id,
                "name": name,
                "email": clean_string(row.get("email_id")).lower(),
                "grade": level or "L3",
                "gradeBand": grade_band,
                "designation": designation,
                "location": clean_string(row.get("current_location")),
                "department": normalized_department,
                "sourceDepartment": source_department,
                "currentSbu": current_sbu,
                "newSbu": new_sbu,
                "businessUnit": business_unit,
                "logicKey": logic_key,
                "reportingName": clean_string(row.get("reports_to")),
                "reportingTo": "",
                "managerName": clean_string(row.get("reports_to")),
                "managerDesignation": "",
                "hierarchyRole": role,
                "disbursalType": _disbursal_type_from_designation(designation),
                "projectIncentivePercent": _project_incentive_percent_for_role(role),
                "departmentPercent": 100.0,
                "teamSharePercent": 100.0,
                "npsScore": 4.5,
                "status": "active",
            }
        )

    name_map = {normalize_name(item["name"]): item["employeeId"] for item in employees}
    designation_map = {normalize_name(item["name"]): item["designation"] for item in employees}
    for item in employees:
        manager_key = normalize_name(item.get("reportingName"))
        item["reportingTo"] = name_map.get(manager_key, "")
        item["managerDesignation"] = designation_map.get(manager_key, "")

    return {
        "uploadType": "team_master",
        "employees": employees,
        "recordCount": len(employees),
    }


def parse_project_workbook(path):
    pd = _load_pandas()
    workbook = pd.ExcelFile(path)

    monthly_projects = []
    month_sheets = [name for name in workbook.sheet_names if _month_from_text(name)]
    for sheet_name in month_sheets:
        frame = _frame_from_sheet(path, sheet_name, ["project"])
        for _, row in frame.iterrows():
            project_id = clean_string(_first_value(row, "project_id", "poject_id", "project_code"))
            project_name = clean_string(_first_value(row, "project_name", "project", "client_name", "customer_name"))
            employee_id = normalize_emp_code(_first_value(row, "employee_id", "emp_code", "employee_code", "employeeid"))
            employee_name = clean_string(_first_value(row, "employee_name", "employee", "name", "sales_person", "owner"))
            if not (project_id or project_name) or not (employee_id or employee_name):
                continue
            period_label = _period_from_value(_first_value(row, "month", "period", "billing_month"), sheet_name)
            monthly_projects.append(
                {
                    "periodLabel": period_label,
                    "projectId": project_id or project_name,
                    "projectName": project_name or project_id,
                    "projectValue": parse_number(_first_value(row, "cashflow", "cash_flow", "project_value", "project_value_", "value", "amount")),
                    "employeeId": employee_id,
                    "mappedEmployees": [employee_name] if employee_name else [],
                    "assignedRole": clean_string(_first_value(row, "assigned_role", "role", "designation")),
                    "sourceStatus": clean_string(_first_value(row, "approval_status", "status")) or "Pending",
                    "sourceScore": parse_number(row.get("score")),
                    "sourceIncentivePercent": parse_number(_first_value(row, "incentive", "incentive_percent", "incentive_")),
                    "sourceIncentiveAmount": parse_number(_first_value(row, "incentive_amount", "incentive_value")),
                    "remarks": clean_string(row.get("remarks")),
                }
            )
    if monthly_projects:
        return {
            "uploadType": "project_cf",
            "projects": monthly_projects,
            "recordCount": len(monthly_projects),
        }

    pv_frame = _frame_from_sheet(path, "PV", ["project_name", "poject_id", "project_value"])
    map_frame = _frame_from_sheet(path, "Mapping ", ["project_name", "poject_id", "project_value", "employee"])

    project_values = {}
    for _, row in pv_frame.iterrows():
        project_id = clean_string(row.get("poject_id") or row.get("project_id"))
        project_name = clean_string(row.get("project_name"))
        if not project_id and not project_name:
            continue
        key = project_id or project_name
        project_values[key] = {
            "projectId": project_id,
            "projectName": project_name,
            "projectValue": parse_number(row.get("project_value")),
        }

    projects = []
    for _, row in map_frame.iterrows():
        project_id = clean_string(row.get("poject_id") or row.get("project_id"))
        project_name = clean_string(row.get("project_name"))
        if not project_id and not project_name:
            continue
        key = project_id or project_name
        values = project_values.get(key, {})
        employees = []
        for value in row.tolist()[3:]:
            candidate = clean_string(value)
            if candidate:
                employees.append(candidate)
        if not employees:
            continue
        projects.append(
            {
                "projectId": project_id or values.get("projectId", ""),
                "projectName": project_name or values.get("projectName", ""),
                "projectValue": parse_number(row.get("project_value")) or values.get("projectValue", 0),
                "mappedEmployees": employees,
            }
        )

    return {
        "uploadType": "project_cf",
        "projects": projects,
        "recordCount": len(projects),
    }


def parse_workbook(path, upload_type=""):
    forced = clean_string(upload_type).lower()
    if forced in {"kpi_logic", "gtm_logic"}:
        return parse_gtm_logic_workbook(path)
    if forced == "sbu_logic":
        return parse_sbu_logic_workbook(path)
    if forced == "team_master":
        return parse_team_workbook(path)
    if forced == "project_cf":
        return parse_project_workbook(path)

    pd = _load_pandas()
    workbook = pd.ExcelFile(path)
    sheet_names = {clean_string(name) for name in workbook.sheet_names}
    if any(_month_from_text(name) for name in sheet_names):
        return parse_project_workbook(path)
    if "SBU KPIs (Updated)" in sheet_names:
        return parse_sbu_logic_workbook(path)
    if "KPI FRAMEWORK" in sheet_names:
        return parse_gtm_logic_workbook(path)
    if {"PV", "Mapping "} <= sheet_names:
        return parse_project_workbook(path)
    return parse_team_workbook(path)
