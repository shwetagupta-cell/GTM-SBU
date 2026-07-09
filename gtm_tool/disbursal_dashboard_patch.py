import csv
import io
from http import HTTPStatus
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from gtm_tool.config import DEFAULT_ADMIN_ID, ROOT
from services.utils import clean_string, normalize_name, parse_number


_SCRIPT_TAG = '    <script src="./gtm_disbursal_status_patch.js"></script>'
_PROJECT_ID_KEYS = ("project_id", "poject_id", "project_code", "projectid", "project_no", "project_number")
_PROJECT_NAME_KEYS = ("project_name", "project", "client_name", "customer_name", "account_name")
_CASHFLOW_KEYS = (
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


def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _format_currency(value):
    amount = round(_safe_float(value))
    return f"Rs {amount:,.0f}"


def _scan_cashflow_value(row, excel_service):
    direct = excel_service._first_value(row, *_CASHFLOW_KEYS)
    if not excel_service._is_blank(direct):
        return direct

    for column, value in row.items():
        if excel_service._is_blank(value):
            continue
        column_name = clean_string(column).lower().replace("-", "_").replace(" ", "_")
        compact = column_name.replace("_", "")
        if column_name in {"status", "approval_status", "source_status", "remarks", "project_name", "project_id"}:
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
                excel_service._first_value(row, "month", "period", "billing_month"), sheet_name
            )
            project_id = clean_string(excel_service._first_value(row, *_PROJECT_ID_KEYS))
            project_name = clean_string(excel_service._first_value(row, *_PROJECT_NAME_KEYS))
            if period_label and project_id:
                lookup[(period_label, "id", project_id.lower())] = cashflow_raw
            if period_label and project_name:
                lookup[(period_label, "name", normalize_name(project_name))] = cashflow_raw
    return lookup


def _install_project_cf_patch():
    from gtm_tool import data_service, excel_service

    if getattr(excel_service, "_project_cf_mapping_patch_installed", False):
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
    excel_service._project_cf_mapping_patch_installed = True

    # Rebuild the in-memory/state cache so already uploaded project sheets pick up the wider CF mapping after deploy.
    try:
        data_service.DATA_SERVICE.reload()
    except Exception as error:
        print(f"Project CF patch reload skipped: {error}")


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
                        project_value = _safe_float(project.get("projectValue"))
                        cashflow_value = _safe_float(project.get("cashflowValue"))
                        incentive_base = _safe_float(project.get("incentiveBaseValue"))
                        accrued_value = _safe_float(project.get("accruedValue"))
                        final_value = _safe_float(project.get("finalDisbursalValue"))
                        per_employee = _safe_float(project.get("perEmployeeIncentive"))
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


def _build_pdf_report(service, viewer_id="", admin_mode=False, employee_id="", start_date="", end_date="", period_label=""):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24,
        title="SME Performance Report",
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    normal_style = styles["BodyText"]
    story = []

    logo_path = Path(ROOT) / "assets" / "flipspaces-logo.png"
    if logo_path.exists():
        story.append(Image(str(logo_path), width=1.25 * inch, height=0.32 * inch, kind="proportional"))
    story.append(Paragraph("SME Performance Report", title_style))
    story.append(Spacer(1, 8))

    accessible = service._accessible_employee_ids(viewer_id or DEFAULT_ADMIN_ID, admin_mode=admin_mode)
    selected_ids = [employee_id] if employee_id else accessible
    wrote_employee = False

    for selected_id in selected_ids:
        if selected_id == DEFAULT_ADMIN_ID and not employee_id:
            continue
        dashboard = service.employee_dashboard(selected_id, selected_period=period_label, start_date=start_date, end_date=end_date)
        if not dashboard:
            continue
        if wrote_employee:
            story.append(PageBreak())
        wrote_employee = True

        story.append(Paragraph(f"{dashboard.get('name', '')} ({dashboard.get('employeeId', '')})", heading_style))
        meta = [
            ["Business Unit", dashboard.get("businessUnit", ""), "Department", dashboard.get("department", "")],
            ["Grade", dashboard.get("grade", ""), "Designation", dashboard.get("designation", "")],
        ]
        story.append(Table(meta, colWidths=[95, 220, 95, 220], hAlign="LEFT", style=[
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9dee8")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f6f8fb")),
            ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f6f8fb")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(Spacer(1, 10))

        for label in dashboard.get("periodOrder", []):
            if period_label and label != period_label:
                continue
            summary = dashboard.get("periods", {}).get(label)
            if not summary:
                continue

            story.append(Paragraph(f"Month-Year: {summary.get('displayPeriod', label)}", heading_style))
            story.append(Paragraph(
                f"Final KPI Score: {summary.get('finalScore', 0)} | NPS Score: {summary.get('npsScore', 0)} | "
                f"Disbursal: {summary.get('disbursalPercent', 0)}% | Status: {summary.get('disbursalStatus', 'Pending')}",
                normal_style,
            ))
            story.append(Spacer(1, 8))

            kpi_rows = [["KRA", "KPI", "Target", "Achievement", "Achievement %", "Score / Points", "Final KPI Score"]]
            for kpi in summary.get("kpis", []):
                kpi_rows.append([
                    kpi.get("kraCategory", ""),
                    kpi.get("kpiName", ""),
                    kpi.get("target", ""),
                    kpi.get("achieved", ""),
                    f"{kpi.get('achievementPercent', '')}%",
                    kpi.get("score", ""),
                    kpi.get("finalWeightedScore", ""),
                ])
            if len(kpi_rows) == 1:
                kpi_rows.append(["No KPI rows available", "", "", "", "", "", ""])
            story.append(Paragraph("Table 1: KPI / KRA / Points Summary", styles["Heading3"]))
            story.append(Table(kpi_rows, repeatRows=1, colWidths=[110, 160, 62, 72, 78, 78, 86], hAlign="LEFT", style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#202938")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9dee8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            story.append(Spacer(1, 10))

            project_rows = [[
                "Project name",
                "Project value",
                "Cashflow / CF",
                "Incentive base",
                "NPS / logic",
                "Final disbursal",
                "Total value",
                "Remarks",
            ]]
            project_total = cashflow_total = incentive_total = final_total = 0.0
            for project in summary.get("projects", []):
                project_value = _safe_float(project.get("projectValue"))
                cashflow_value = _safe_float(project.get("cashflowValue"))
                incentive_base = _safe_float(project.get("incentiveBaseValue"))
                final_value = _safe_float(project.get("finalDisbursalValue"))
                project_total += project_value
                cashflow_total += cashflow_value
                incentive_total += incentive_base
                final_total += final_value
                project_rows.append([
                    project.get("projectName", ""),
                    _format_currency(project_value),
                    _format_currency(cashflow_value),
                    _format_currency(incentive_base),
                    f"NPS {summary.get('npsScore', 0)} / {project.get('npsDisbursalPercent', summary.get('disbursalPercent', 0))}%",
                    _format_currency(final_value),
                    _format_currency(project.get("perEmployeeIncentive", final_value)),
                    project.get("assignedRole") or project.get("sourceStatus", ""),
                ])
            if len(project_rows) == 1:
                project_rows.append(["No mapped projects", "Rs 0", "Rs 0", "Rs 0", "", "Rs 0", "Rs 0", ""])
            project_rows.append([
                "TOTAL",
                _format_currency(project_total),
                _format_currency(cashflow_total),
                _format_currency(incentive_total),
                "",
                _format_currency(final_total),
                _format_currency(final_total),
                "",
            ])
            story.append(Paragraph("Table 2: Project / Cash Flow / Incentive Details", styles["Heading3"]))
            story.append(Table(project_rows, repeatRows=1, colWidths=[150, 82, 82, 88, 90, 90, 80, 110], hAlign="LEFT", style=[
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#202938")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f3eee8")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d9dee8")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            story.append(Spacer(1, 14))

    if not wrote_employee:
        story.append(Paragraph("No report data found for the selected filters.", normal_style))

    doc.build(story)
    return buffer.getvalue()


def _install_pdf_report_patch():
    from gtm_tool import data_service

    if getattr(data_service.GTMDataService, "_pdf_report_patch_installed", False):
        return

    def export_pdf(self, viewer_id="", admin_mode=False, employee_id="", start_date="", end_date="", period_label=""):
        return _build_pdf_report(
            self,
            viewer_id=viewer_id,
            admin_mode=admin_mode,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            period_label=period_label,
        )

    data_service.GTMDataService.export_pdf = export_pdf
    data_service.GTMDataService._pdf_report_patch_installed = True


def _install_index_injection(handler_cls):
    if handler_cls is None or getattr(handler_cls, "_disbursal_patch_script_installed", False):
        return

    original_do_get = handler_cls.do_GET

    def send_pdf(self, content, filename="gtm-report.pdf"):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def handle_pdf_report(self, parsed):
        from gtm_tool.http_handler import DATA_SERVICE

        session = self.require_session()
        if not session:
            return
        query = parse_qs(parsed.query)
        employee_id = clean_string(query.get("employeeId", [""])[0])
        start_date = clean_string(query.get("startDate", [""])[0])
        end_date = clean_string(query.get("endDate", [""])[0])
        period_label = clean_string(query.get("period", [""])[0])
        if not session.get("adminMode") and not employee_id:
            employee_id = session["employeeId"]
        pdf = DATA_SERVICE.export_pdf(
            viewer_id=session["employeeId"],
            admin_mode=bool(session.get("adminMode")),
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            period_label=period_label,
        )
        return send_pdf(self, pdf)

    def do_get_with_disbursal_patch(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/api/admin/report.pdf", "/api/report.pdf"}:
            return handle_pdf_report(self, parsed)
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
    _install_project_cf_patch()
    _install_period_summary_patch()
    _install_report_export_patch()
    _install_pdf_report_patch()
    _install_index_injection(handler_cls)
