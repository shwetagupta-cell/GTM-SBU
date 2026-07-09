import csv
import io
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

from gtm_tool.config import DEFAULT_ADMIN_ID, ROOT
from services.utils import clean_string


_SCRIPT_TAG = '    <script src="./gtm_disbursal_status_patch.js"></script>'


def _install_period_summary_patch():
    from gtm_tool import data_service

    if getattr(data_service.GTMDataService, "_month_status_patch_installed", False):
        return

    original_period_summary = data_service.GTMDataService._period_summary

    def period_summary_with_month_status(self, employee, period_label, rows):
        summary = original_period_summary(self, employee, period_label, rows)
        employee_id = clean_string(employee.get("employeeId"))
        month_status = self.state.get("monthlyDisbursalStatuses", {}).get(period_label)
        employee_status = self.state.get("monthlyStatuses", {}).get(f"{employee_id}|{period_label}")
        summary["disbursalStatus"] = month_status or employee_status or summary.get("disbursalStatus") or "Pending"
        return summary

    data_service.GTMDataService._period_summary = period_summary_with_month_status
    data_service.GTMDataService._month_status_patch_installed = True


def _install_report_export_patch():
    from gtm_tool import data_service

    if getattr(data_service.GTMDataService, "_report_export_patch_installed", False):
        return

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
                writer.writerow([
                    "KRA",
                    "KPI",
                    "Target",
                    "Achievement",
                    "Achievement %",
                    "Score / Points",
                    "Weightage",
                    "Final KPI Score",
                    "NPS Score",
                    "Action",
                ])
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
                    "Cash Flow",
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
                project_total = 0.0
                cashflow_total = 0.0
                incentive_base_total = 0.0
                accrued_total = 0.0
                final_total = 0.0
                per_employee_total = 0.0
                projects = summary.get("projects", [])
                if projects:
                    for project in projects:
                        project_value = float(project.get("projectValue") or 0)
                        cashflow_value = float(project.get("cashflowValue") or 0)
                        incentive_base = float(project.get("incentiveBaseValue") or 0)
                        accrued_value = float(project.get("accruedValue") or 0)
                        final_value = float(project.get("finalDisbursalValue") or 0)
                        per_employee = float(project.get("perEmployeeIncentive") or 0)
                        project_total += project_value
                        cashflow_total += cashflow_value
                        incentive_base_total += incentive_base
                        accrued_total += accrued_value
                        final_total += final_value
                        per_employee_total += per_employee
                        writer.writerow([
                            project.get("projectName", ""),
                            project.get("projectId", ""),
                            project.get("periodLabel", label),
                            project_value,
                            cashflow_value,
                            incentive_base,
                            project.get("sharePercent", ""),
                            project.get("departmentPercent", ""),
                            project.get("teamSharePercent", ""),
                            project.get("mySharePercent", ""),
                            project.get("teamCount", ""),
                            accrued_value,
                            summary.get("npsScore", ""),
                            project.get("npsDisbursalPercent", summary.get("disbursalPercent", "")),
                            final_value,
                            per_employee,
                            project.get("sourceStatus", ""),
                            project.get("assignedRole", ""),
                        ])
                else:
                    writer.writerow(["No mapped project rows for this employee and month", "", label, 0, 0, 0])
                writer.writerow([
                    "TOTAL",
                    "",
                    label,
                    project_total,
                    cashflow_total,
                    incentive_base_total,
                    "",
                    "",
                    "",
                    "",
                    "",
                    accrued_total,
                    summary.get("npsScore", ""),
                    summary.get("disbursalPercent", ""),
                    final_total,
                    per_employee_total,
                    "",
                    "",
                ])
                writer.writerow([])
            writer.writerow([])
        return buffer.getvalue()

    data_service.GTMDataService.export_csv = export_csv_two_tables
    data_service.GTMDataService._report_export_patch_installed = True


def _install_index_injection(handler_cls):
    if handler_cls is None or getattr(handler_cls, "_disbursal_patch_script_installed", False):
        return

    original_do_get = handler_cls.do_GET

    def do_get_with_disbursal_patch(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/gtm_index.html"}:
            index_path = Path(ROOT) / "gtm_index.html"
            html = index_path.read_text(encoding="utf-8")
            if "gtm_disbursal_status_patch.js" not in html:
                html = html.replace(
                    '    <script src="./gtm_app.js"></script>',
                    '    <script src="./gtm_app.js"></script>\n' + _SCRIPT_TAG,
                )
            body = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return original_do_get(self)

    handler_cls.do_GET = do_get_with_disbursal_patch
    handler_cls._disbursal_patch_script_installed = True


def install(handler_cls=None):
    _install_period_summary_patch()
    _install_report_export_patch()
    _install_index_injection(handler_cls)
