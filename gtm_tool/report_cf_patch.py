import csv
import io

from gtm_tool.config import DEFAULT_ADMIN_ID
from services.utils import clean_string, normalize_name, parse_number


PROJECT_ID_KEYS = ("project_id", "poject_id", "project_code", "projectid", "project_no", "project_number")
PROJECT_NAME_KEYS = ("project_name", "project", "client_name", "customer_name", "account_name")
CASHFLOW_KEYS = (
    "cashflow",
    "cash_flow",
    "cashflow_value",
    "cash_flow_value",
    "monthly_cashflow",
    "monthly_cash_flow",
    "monthly_cf",
    "cf",
    "c_f",
    "cf_value",
    "project_cf",
    "actual_cf",
    "cashflow_cf",
    "cash_flow_cf",
    "collection",
    "collections",
    "collection_value",
    "cash_collection",
    "cash_collected",
    "cashflow_mtd",
    "cf_mtd",
    "cash_flow_for_the_month",
    "cashflow_for_the_month",
)


def _scan_cashflow_value(row, excel_service):
    direct = excel_service._first_value(row, *CASHFLOW_KEYS)
    if not excel_service._is_blank(direct):
        return direct
    for column, value in row.items():
        if excel_service._is_blank(value):
            continue
        column_name = clean_string(column).lower().replace("-", "_").replace(" ", "_")
        compact = column_name.replace("_", "")
        if column_name in {"project_name", "project_id", "poject_id", "status", "approval_status", "remarks"}:
            continue
        if (
            column_name == "cf"
            or column_name.endswith("_cf")
            or column_name.startswith("cf_")
            or compact == "cf"
            or "cashflow" in compact
            or ("cash" in compact and "flow" in compact)
            or "collection" in compact
        ):
            return value
    return None


def _project_cf_lookup(path, excel_service):
    lookup = {}
    try:
        pd = excel_service._load_pandas()
        workbook = pd.ExcelFile(path)
    except Exception:
        return lookup
    month_sheets = [name for name in workbook.sheet_names if excel_service._month_from_text(name)]
    for sheet_name in month_sheets:
        try:
            frame = excel_service._frame_from_sheet(path, sheet_name, ["project"])
        except Exception:
            continue
        for _, row in frame.iterrows():
            cashflow_raw = _scan_cashflow_value(row, excel_service)
            if cashflow_raw is None:
                continue
            period_label = excel_service._period_from_value(
                excel_service._first_value(row, "month", "period", "billing_month"),
                sheet_name,
            )
            project_id = clean_string(excel_service._first_value(row, *PROJECT_ID_KEYS))
            project_name = clean_string(excel_service._first_value(row, *PROJECT_NAME_KEYS))
            if period_label and project_id:
                lookup[(period_label, "id", project_id.lower())] = cashflow_raw
            if period_label and project_name:
                lookup[(period_label, "name", normalize_name(project_name))] = cashflow_raw
    return lookup


def install_excel_patch():
    from gtm_tool import excel_service

    if getattr(excel_service, "_report_cf_patch_installed", False):
        return
    original_parse_project_workbook = excel_service.parse_project_workbook

    def parse_project_workbook_with_cf(path):
        parsed = original_parse_project_workbook(path)
        if parsed.get("uploadType") != "project_cf" or not parsed.get("projects"):
            return parsed
        lookup = _project_cf_lookup(path, excel_service)
        if not lookup:
            return parsed
        for project in parsed.get("projects", []):
            period_label = clean_string(project.get("periodLabel"))
            project_id = clean_string(project.get("projectId"))
            project_name = clean_string(project.get("projectName"))
            cashflow_raw = None
            if period_label and project_id:
                cashflow_raw = lookup.get((period_label, "id", project_id.lower()))
            if cashflow_raw is None and period_label and project_name:
                cashflow_raw = lookup.get((period_label, "name", normalize_name(project_name)))
            if cashflow_raw is None:
                continue
            cashflow_value = parse_number(cashflow_raw)
            project["cashflowValue"] = cashflow_value
            project["incentiveBaseValue"] = cashflow_value
        return parsed

    excel_service.parse_project_workbook = parse_project_workbook_with_cf
    excel_service._report_cf_patch_installed = True


def export_csv_two_tables(self, viewer_id="", admin_mode=False, employee_id="", start_date="", end_date="", period_label=""):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    accessible = self._accessible_employee_ids(viewer_id or DEFAULT_ADMIN_ID, admin_mode=admin_mode)
    selected_ids = [employee_id] if employee_id else accessible
    for selected_id in selected_ids:
        if selected_id == DEFAULT_ADMIN_ID and not employee_id:
            continue
        dashboard = self.employee_dashboard(selected_id, selected_period=period_label, start_date=start_date, end_date=end_date)
        if not dashboard:
            continue
        writer.writerow(["Employee ID", dashboard.get("employeeId", "")])
        writer.writerow(["Employee Name", dashboard.get("name", "")])
        writer.writerow(["Business Unit", dashboard.get("businessUnit", "")])
        writer.writerow(["Department", dashboard.get("department", "")])
        writer.writerow(["Grade", dashboard.get("grade", "")])
        writer.writerow(["Designation", dashboard.get("designation", "")])
        writer.writerow([])
        for label in dashboard.get("periodOrder", []):
            if period_label and label != period_label:
                continue
            summary = dashboard.get("periods", {}).get(label)
            if not summary:
                continue
            writer.writerow(["Month", summary.get("displayPeriod", label)])
            writer.writerow(["Disbursal Status", summary.get("disbursalStatus", "Pending")])
            writer.writerow(["NPS Score", summary.get("npsScore", 0)])
            writer.writerow(["NPS Disbursal %", summary.get("disbursalPercent", 0)])
            writer.writerow([])
            writer.writerow(["TABLE 1: KPI / KRA / POINTS SUMMARY"])
            writer.writerow(["KRA", "KPI", "Target", "Achievement", "Achievement %", "Score / Points", "Weightage", "Final KPI Score", "NPS Score", "Action"])
            for kpi in summary.get("kpis", []):
                writer.writerow([
                    kpi.get("kraCategory", ""),
                    kpi.get("kpiName", ""),
                    kpi.get("target", ""),
                    kpi.get("achieved", ""),
                    kpi.get("achievementPercent", ""),
                    kpi.get("score", ""),
                    kpi.get("weightage", ""),
                    kpi.get("finalWeightedScore", ""),
                    summary.get("npsScore", ""),
                    kpi.get("action", ""),
                ])
            writer.writerow(["Final KPI Score", summary.get("finalScore", 0)])
            writer.writerow([])
            writer.writerow(["TABLE 2: PROJECT / CASH FLOW / INCENTIVE DETAILS"])
            writer.writerow([
                "Project Name",
                "Project ID",
                "Month",
                "Project Value",
                "Cashflow / CF",
                "Incentive Base",
                "Share %",
                "Department %",
                "Team Share %",
                "My Share %",
                "Team Count",
                "Accrued Value",
                "NPS Score",
                "Disbursal %",
                "Final Disbursal Amount",
                "Per Employee Incentive",
                "Source Status",
                "Remarks / Details",
            ])
            totals = {key: 0.0 for key in ("projectValue", "cashflowValue", "incentiveBaseValue", "accruedValue", "finalDisbursalValue", "perEmployeeIncentive")}
            projects = summary.get("projects", [])
            if projects:
                for project in projects:
                    for key in totals:
                        totals[key] += parse_number(project.get(key))
                    writer.writerow([
                        project.get("projectName", ""),
                        project.get("projectId", ""),
                        project.get("periodLabel", label),
                        project.get("projectValue", 0),
                        project.get("cashflowValue", 0),
                        project.get("incentiveBaseValue", 0),
                        project.get("sharePercent", ""),
                        project.get("departmentPercent", ""),
                        project.get("teamSharePercent", ""),
                        project.get("mySharePercent", ""),
                        project.get("teamCount", ""),
                        project.get("accruedValue", 0),
                        summary.get("npsScore", ""),
                        project.get("npsDisbursalPercent", summary.get("disbursalPercent", "")),
                        project.get("finalDisbursalValue", 0),
                        project.get("perEmployeeIncentive", 0),
                        project.get("sourceStatus", ""),
                        project.get("assignedRole", ""),
                    ])
            else:
                writer.writerow(["No mapped project rows for this employee and month", "", label, 0, 0, 0])
            writer.writerow([
                "TOTAL",
                "",
                label,
                round(totals["projectValue"], 2),
                round(totals["cashflowValue"], 2),
                round(totals["incentiveBaseValue"], 2),
                "",
                "",
                "",
                "",
                "",
                round(totals["accruedValue"], 2),
                summary.get("npsScore", ""),
                summary.get("disbursalPercent", ""),
                round(totals["finalDisbursalValue"], 2),
                round(totals["perEmployeeIncentive"], 2),
                "",
                "",
            ])
            writer.writerow([])
        writer.writerow([])
    return buffer.getvalue()


def install_runtime_patch():
    from gtm_tool import data_service

    if getattr(data_service.GTMDataService, "_report_cf_export_patch_installed", False):
        return
    data_service.GTMDataService.export_csv = export_csv_two_tables
    data_service.GTMDataService._report_cf_export_patch_installed = True
