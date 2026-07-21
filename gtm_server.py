import base64
import csv
import os
import sys
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from gtm_tool.config import BUNDLED_PYTHON, ROOT


def ensure_bundled_runtime():
    if os.environ.get("GTM_BUNDLED_RUNTIME") == "1":
        return
    try:
        import pandas  # noqa: F401
    except Exception:
        if not BUNDLED_PYTHON.exists():
            raise RuntimeError("Bundled Python runtime with pandas was not found.")
        env = os.environ.copy()
        env["GTM_BUNDLED_RUNTIME"] = "1"
        os.execve(str(BUNDLED_PYTHON), [str(BUNDLED_PYTHON), __file__, *sys.argv[1:]], env)


ensure_bundled_runtime()

from gtm_tool.project_employee_mapping import install  # noqa: E402
from gtm_tool.audit_patch import install_audit_patch  # noqa: E402
from gtm_tool.report_cf_patch import install_excel_patch, install_runtime_patch  # noqa: E402

install()
install_excel_patch()

from gtm_tool.http_handler import GTMAppHandler  # noqa: E402
from gtm_tool.data_service import DATA_SERVICE  # noqa: E402

install_runtime_patch()
install_audit_patch(GTMAppHandler, DATA_SERVICE)

# Keep the live service responsive. The heavier dashboard patch is intentionally
# not loaded at startup because it reparses uploaded workbooks and can block
# Render before the first page response is sent.


def install_live_ui_patch(handler_cls):
    if getattr(handler_cls, "_live_ui_patch_installed", False):
        return

    original_do_get = handler_cls.do_GET

    old_bootstrap = """async function bootstrap() {
  bindEvents();
  try {
    await refreshDashboard();
    setLoggedIn(true);
  } catch (error) {
    setLoggedIn(false);
    els.loginNotice.textContent = "Use your employee ID and password to continue.";
  }
}

bootstrap();
"""
    new_bootstrap = """async function bootstrap() {
  bindEvents();
  setLoggedIn(false);
  els.loginNotice.textContent = "Use your employee ID and password to continue.";
}

bootstrap();
"""

    def send_text(self, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_pdf(self, body, filename):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_excel(self, body, filename):
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def safe_filename(value, fallback="upload"):
        cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in str(value or fallback))
        cleaned = "-".join(part for part in cleaned.split("-") if part)
        return cleaned[:80] or fallback

    def build_report_pdf(csv_text, title, subtitle=""):
        from io import BytesIO

        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A3, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A3), rightMargin=22, leftMargin=22, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()
        styles["Title"].fontSize = 16
        styles["Title"].leading = 19
        styles["Normal"].fontSize = 9
        styles["Normal"].leading = 11
        styles["BodyText"].fontSize = 6.2
        styles["BodyText"].leading = 7.2
        styles["BodyText"].wordWrap = "CJK"
        heading_cell_style = styles["BodyText"].clone("ReportSectionHeading")
        heading_cell_style.fontSize = 8
        heading_cell_style.leading = 9
        heading_cell_style.alignment = TA_CENTER
        heading_cell_style.textColor = colors.HexColor("#a64f34")
        header_cell_style = styles["BodyText"].clone("ReportHeaderCell")
        header_cell_style.fontSize = 6.2
        header_cell_style.leading = 7.1
        header_cell_style.alignment = TA_CENTER
        story = []
        logo_path = ROOT / "assets" / "flipspaces-logo.png"
        if logo_path.exists():
            story.append(Image(str(logo_path), width=1.55 * inch, height=0.18 * inch, kind="proportional"))
            story.append(Spacer(1, 10))
        if title and title not in {"Individual Employee Report", "All Employees Report"}:
            story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
        story.append(Paragraph(subtitle or "SME Performance Management 2026 - 27", styles["Normal"]))
        story.append(Spacer(1, 12))

        rows = [row for row in csv.reader(csv_text.splitlines())]
        if not rows:
            story.append(Paragraph("No report data was found for this date range.", styles["Normal"]))
        section = []

        def flush_section():
            nonlocal section
            if not section:
                return
            max_cols = max(len(row) for row in section)
            normalized = [row + [""] * (max_cols - len(row)) for row in section]
            if max_cols == 1:
                story.append(Paragraph(f"<b>{normalized[0][0]}</b>", styles["Heading2"]))
                story.append(Spacer(1, 6))
                section = []
                return
            usable_width = doc.width
            raw_heading = str(normalized[0][0]).strip()
            first_heading = raw_heading.upper().startswith("TABLE ")
            header_row = normalized[1] if first_heading and len(normalized) > 1 else normalized[0]

            if "Project Name" in header_row and "Cashflow / CF" in header_row:
                weights = [1.45, 1.15, 0.72, 0.92, 0.92, 0.92, 0.55, 0.68, 0.72, 0.62, 0.58, 0.9, 0.62, 0.62, 0.92, 0.92, 0.8, 0.9]
            elif "KRA" in header_row and "KPI" in header_row:
                weights = [1.2, 1.5, 0.65, 0.72, 0.75, 0.62, 0.62, 0.75, 0.58, 0.85]
            elif max_cols == 2:
                weights = [0.9, 2.2]
            else:
                weights = [1] * max_cols
            weights = (weights + [1] * max_cols)[:max_cols]
            total_weight = sum(weights) or max_cols
            col_widths = [usable_width * weight / total_weight for weight in weights]

            wrapped = []
            for row_index, row in enumerate(normalized):
                row_cells = []
                is_heading_row = str(row[0]).strip().upper().startswith("TABLE ") and not any(str(cell).strip() for cell in row[1:])
                for cell_index, cell in enumerate(row):
                    if is_heading_row and cell_index == 0:
                        cell = str(cell).split(":", 1)[1].strip() if ":" in str(cell) else str(cell).replace("TABLE 1", "").replace("TABLE 2", "").strip()
                    cell_style = heading_cell_style if is_heading_row else header_cell_style if row_index == (1 if first_heading else 0) else styles["BodyText"]
                    row_cells.append(Paragraph(str(cell or ""), cell_style))
                wrapped.append(row_cells)

            repeat_rows = 2 if first_heading and max_cols > 1 else 1
            table = Table(wrapped, colWidths=col_widths, repeatRows=repeat_rows, hAlign="LEFT")
            style_commands = [
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2f3848")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dfe3ea")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfbfc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.4),
                ("TOPPADDING", (0, 0), (-1, -1), 2.8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8),
            ]
            if first_heading and max_cols > 1:
                style_commands.extend(
                    [
                        ("SPAN", (0, 0), (-1, 0)),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fff1ec")),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f7f8fa")),
                        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#667085")),
                        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ]
                )
            else:
                style_commands.extend(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f6e9e4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2f3848")),
                    ]
                )
            table.setStyle(
                TableStyle(style_commands)
            )
            story.append(table)
            story.append(Spacer(1, 10))
            section = []

        for row in rows:
            if not any(str(cell).strip() for cell in row):
                flush_section()
                continue
            section.append(row)
        flush_section()
        doc.build(story)
        return buffer.getvalue()

    def uploaded_excel(file_id):
        upload = next(
            (
                item
                for item in DATA_SERVICE.state.get("uploadedFiles", [])
                if item.get("fileId") == file_id and not item.get("deleted")
            ),
            None,
        )
        if not upload:
            return None, ""
        raw_name = str(upload.get("fileName") or file_id or "uploaded-sheet")
        file_stem = raw_name.rsplit(".", 1)[0]
        filename = safe_filename(file_stem, "uploaded-sheet") + ".xlsx"
        stored_path = ROOT / str(upload.get("storedPath", ""))
        if stored_path.exists():
            return stored_path.read_bytes(), filename
        encoded = upload.get("fileData")
        if encoded:
            return base64.b64decode(encoded.encode("ascii")), filename
        return None, ""

    def patch_index_html(html):
        replacements = {
            '              <article class="project-pill"><span>Total Incentive Value</span><strong id="kpiTotalIncentive">Rs 0</strong></article>\n': "",
            "                    <th>Incentive Amount</th>\n": "",
            '                <p class="eyebrow">Project Incentive Disbursal</p>\n': "",
        }
        for old, new in replacements.items():
            html = html.replace(old, new)
        html = html.replace(
            '              <section class="panel inset">\n'
            '                <h3>Upload History</h3>\n'
            '                <div id="uploadHistory" class="upload-list"></div>\n'
            '              </section>\n'
            '            </div>\n',
            '              <section class="panel inset">\n'
            '                <h3>Upload History</h3>\n'
            '                <div id="uploadHistory" class="upload-list"></div>\n'
            '              </section>\n'
            '              <section class="panel inset">\n'
            '                <h3>Change History</h3>\n'
            '                <div id="auditLog" class="audit-list"></div>\n'
            '              </section>\n'
            '            </div>\n',
        )
        html = html.replace(
            "</head>",
            """<style>
              .audit-list { display: grid; gap: 12px; max-height: 560px; overflow: auto; padding-right: 4px; }
              .audit-tabs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
              .audit-tab { min-height: 32px; padding: 0 12px; border: 1px solid var(--line); border-radius: 8px; background: #fff; color: var(--muted); font-size: 12px; font-weight: 800; }
              .audit-tab.is-active { border-color: rgba(207, 95, 58, 0.35); background: rgba(207, 95, 58, 0.1); color: var(--accent); }
              .audit-card { display: grid; gap: 12px; padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: rgba(255, 255, 255, 0.88); box-shadow: 0 10px 24px rgba(24, 33, 47, 0.06); }
              .audit-card-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; border-bottom: 1px solid var(--line); padding-bottom: 10px; }
              .audit-card-head strong { display: block; color: var(--text); font-size: 14px; line-height: 1.35; }
              .audit-card-head p { margin: 4px 0 0; color: var(--muted); font-size: 12px; }
              .audit-badge { display: inline-flex; min-height: 28px; align-items: center; padding: 0 10px; border-radius: 999px; background: rgba(207, 95, 58, 0.12); color: var(--accent); font-size: 11px; font-weight: 800; white-space: nowrap; }
              .audit-field-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
              .audit-field { min-height: 62px; padding: 10px; border: 1px solid rgba(223, 227, 234, 0.9); border-radius: 8px; background: rgba(248, 249, 251, 0.8); min-width: 0; }
              .audit-field span { display: block; margin-bottom: 5px; color: var(--muted); font-size: 10px; font-weight: 900; letter-spacing: 0.12em; text-transform: uppercase; }
              .audit-field strong { display: block; color: var(--text); font-size: 12px; line-height: 1.35; overflow-wrap: anywhere; }
              .audit-field--wide { grid-column: span 2; }
              @media (max-width: 1100px) { .audit-field-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
              @media (max-width: 700px) { .audit-card-head { display: grid; } .audit-field-grid { grid-template-columns: 1fr; } .audit-field--wide { grid-column: auto; } }
            </style>
  </head>""",
        )
        return html

    def patch_app_js(script):
        script = script.replace(old_bootstrap, new_bootstrap)
        replacements = {
            '  uploadHistory: document.getElementById("uploadHistory"),\n': '  uploadHistory: document.getElementById("uploadHistory"),\n  auditLog: document.getElementById("auditLog"),\n',
            '  kpiTotalIncentive: document.getElementById("kpiTotalIncentive"),\n': "",
            '  els.kpiTotalIncentive.textContent = money(summary?.finalDisbursal || 0);\n\n': "",
            '              <td class="kpi-incentive">${money(row.incentiveAmount)}</td>\n': "",
            '          rowElement.querySelector(".kpi-incentive").textContent = money(item.incentiveAmount);\n': "",
            '    const incentiveAmount = totalWeightedScore ? totalIncentive * Number(item.finalWeightedScore || 0) / totalWeightedScore : 0;\n    item.incentiveAmount = roundMetric(incentiveAmount);\n    item.npsScore = npsScore;\n    rowElement.querySelector(".kpi-incentive").textContent = money(item.incentiveAmount);\n': '    item.npsScore = npsScore;\n',
            '    const incentiveAmount = totalWeightedScore ? totalIncentive * Number(item.finalWeightedScore || 0) / totalWeightedScore : 0;\n    item.incentiveAmount = roundMetric(incentiveAmount);\n    rowElement.querySelector(".kpi-incentive").textContent = money(item.incentiveAmount);\n': "",
            '      colspan="11"': '      colspan="10"',
        }
        for old, new in replacements.items():
            script = script.replace(old, new)
        script = script.replace(
            """  const accruedTotal = (currentSummary()?.projects || []).reduce((sum, project) => sum + Number(project.accruedValue || 0), 0);
  const totalIncentive = accruedTotal * disbursalPercent / 100;

  els.kpiTotalScore.textContent = roundMetric(totalScore).toLocaleString("en-IN", { maximumFractionDigits: 2 });
  els.kpiTotalIncentive.textContent = money(totalIncentive);
""",
            """  els.kpiTotalScore.textContent = roundMetric(totalScore).toLocaleString("en-IN", { maximumFractionDigits: 2 });
""",
        )
        script = script.replace(
            """          const incentiveAmount = totalWeightedScore ? totalIncentive * Number(item.finalWeightedScore || 0) / totalWeightedScore : 0;
          item.incentiveAmount = roundMetric(incentiveAmount);
          item.npsScore = npsScore;
          rowElement.querySelector(".kpi-incentive").textContent = money(item.incentiveAmount);
""",
            """          item.npsScore = npsScore;
""",
        )
        script = script.replace(
            """  renderDepartmentOptions();
}

function fillEmployeeForm(employee) {
""",
            """  if (els.auditLog) {
    const auditLog = admin.auditLog || [];
    if (auditLog.length) {
      const auditCategory = (entry) => {
        const action = String(entry.action || "").toLowerCase();
        if (action.includes("employee")) return "employee";
        if (action.includes("kpi")) return "kpi";
        if (action.includes("project")) return "project";
        if (action.includes("workbook")) return "upload";
        if (action.includes("status")) return "status";
        return "other";
      };
      const groups = [
        ["all", "All Changes", auditLog.length],
        ["employee", "Employee", auditLog.filter((entry) => auditCategory(entry) === "employee").length],
        ["kpi", "KPI", auditLog.filter((entry) => auditCategory(entry) === "kpi").length],
        ["project", "Project", auditLog.filter((entry) => auditCategory(entry) === "project").length],
        ["upload", "Uploads", auditLog.filter((entry) => auditCategory(entry) === "upload").length],
        ["status", "Status", auditLog.filter((entry) => auditCategory(entry) === "status").length],
      ];
      const tabs = `<div class="audit-tabs">${groups
        .map(([filter, label, count], index) => `<button class="audit-tab ${index === 0 ? "is-active" : ""}" data-audit-filter="${escapeHtml(filter)}" type="button">${escapeHtml(label)} (${count})</button>`)
        .join("")}</div>`;
      const cards = auditLog
          .map((entry) => {
            const changed = formatLoadedAt(entry.changedAt);
            const actorName = entry.changedByName || "Unknown Admin";
            const actionLabel = String(entry.action || "admin change").replaceAll("_", " ");
            const details = [
              entry.employeeId ? `Employee ${entry.employeeId}` : "",
              entry.periodLabel ? `Month ${entry.periodLabel}` : "",
              entry.projectId ? `Project ${entry.projectId}` : "",
              entry.fileName || entry.fileId || "",
            ].filter(Boolean);
            return `
              <article class="audit-card" data-audit-category="${escapeHtml(auditCategory(entry))}">
                <div class="audit-card-head">
                  <div>
                    <strong>${escapeHtml(entry.summary || entry.action || "Admin change")}</strong>
                    <p>${escapeHtml(actorName)}${entry.changedById ? ` • ID ${escapeHtml(entry.changedById)}` : ""}</p>
                  </div>
                  <span class="audit-badge">${escapeHtml(actionLabel)}</span>
                </div>
                <div class="audit-field-grid">
                  <div class="audit-field audit-field--wide"><span>New Change</span><strong>${escapeHtml(entry.summary || "Admin change")}</strong></div>
                  <div class="audit-field"><span>Date</span><strong>${escapeHtml(changed.primary)}</strong></div>
                  <div class="audit-field"><span>Time</span><strong>${escapeHtml(changed.secondary || "-")}</strong></div>
                  <div class="audit-field"><span>Name</span><strong>${escapeHtml(actorName)}</strong></div>
                  <div class="audit-field"><span>Admin ID</span><strong>${escapeHtml(entry.changedById || "-")}</strong></div>
                  <div class="audit-field"><span>Action</span><strong>${escapeHtml(actionLabel)}</strong></div>
                  <div class="audit-field audit-field--wide"><span>Details</span><strong>${escapeHtml(details.join(" | ") || "-")}</strong></div>
                </div>
              </article>
            `;
          })
          .join("");
      els.auditLog.innerHTML = tabs + cards;
      els.auditLog.querySelectorAll(".audit-tab").forEach((button) => {
        button.addEventListener("click", () => {
          const filter = button.dataset.auditFilter || "all";
          els.auditLog.querySelectorAll(".audit-tab").forEach((tab) => tab.classList.toggle("is-active", tab === button));
          els.auditLog.querySelectorAll(".audit-card").forEach((card) => {
            card.classList.toggle("hidden", filter !== "all" && card.dataset.auditCategory !== filter);
          });
        });
      });
    } else {
      els.auditLog.innerHTML = `<article class="audit-card empty-state">Admin changes will appear here.</article>`;
    }
  }

  renderDepartmentOptions();
}

function fillEmployeeForm(employee) {
""",
        )
        return script

    def do_get_with_live_ui_patch(self):
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/gtm_index.html"}:
            html = (ROOT / "gtm_index.html").read_text(encoding="utf-8")
            return send_text(self, patch_index_html(html), "text/html; charset=utf-8")
        if parsed.path == "/gtm_app.js":
            script = (ROOT / "gtm_app.js").read_text(encoding="utf-8")
            return send_text(self, patch_app_js(script), "text/javascript; charset=utf-8")
        if parsed.path in {"/api/admin/report.pdf", "/api/report.pdf"}:
            session = self.require_session()
            if not session:
                return
            query = parse_qs(parsed.query)
            employee_id = (query.get("employeeId", [""])[0] or "").strip()
            start_date = (query.get("startDate", [""])[0] or "").strip()
            end_date = (query.get("endDate", [""])[0] or "").strip()
            period_label = (query.get("period", [""])[0] or "").strip()
            if start_date or end_date:
                period_label = ""
            if not session.get("adminMode") and not employee_id:
                employee_id = session["employeeId"]
            csv_text = DATA_SERVICE.export_csv(
                viewer_id=session["employeeId"],
                admin_mode=bool(session.get("adminMode")),
                employee_id=employee_id,
                start_date=start_date,
                end_date=end_date,
                period_label=period_label,
            )
            title = "Individual Employee Report" if employee_id else "All Employees Report"
            filters = " | ".join(
                item
                for item in [
                    f"Employee ID: {employee_id}" if employee_id else "All active employees",
                    f"From: {start_date}" if start_date else "",
                    f"Till: {end_date}" if end_date else "",
                    f"Month: {period_label}" if period_label else "",
                ]
                if item
            )
            pdf = build_report_pdf(csv_text, title, filters or "SME Performance Management 2026 - 27")
            return send_pdf(self, pdf, f"{safe_filename(title)}.pdf")
        if parsed.path == "/api/admin/upload.xlsx":
            session = self.require_admin()
            if not session:
                return
            query = parse_qs(parsed.query)
            file_bytes, filename = uploaded_excel((query.get("fileId", [""])[0] or "").strip())
            if not file_bytes:
                return self.send_json({"error": "Uploaded Excel file was not found"}, status=HTTPStatus.NOT_FOUND)
            return send_excel(self, file_bytes, filename)
        return original_do_get(self)

    handler_cls.do_GET = do_get_with_live_ui_patch
    handler_cls._live_ui_patch_installed = True


install_live_ui_patch(GTMAppHandler)


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8010"))
    server = ReusableThreadingHTTPServer((host, port), GTMAppHandler)
    print(f"GTM Performance Tool running on http://127.0.0.1:{port}")
    server.serve_forever()
