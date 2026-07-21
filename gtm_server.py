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

    def safe_filename(value, fallback="upload"):
        cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in str(value or fallback))
        cleaned = "-".join(part for part in cleaned.split("-") if part)
        return cleaned[:80] or fallback

    def build_upload_pdf(file_id=""):
        from io import BytesIO

        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=28, leftMargin=28, topMargin=26, bottomMargin=26)
        styles = getSampleStyleSheet()
        story = []
        logo_path = ROOT / "assets" / "flipspaces-logo.png"
        if logo_path.exists():
            story.append(Image(str(logo_path), width=1.55 * inch, height=0.18 * inch, kind="proportional"))
            story.append(Spacer(1, 10))
        uploads = [
            item
            for item in DATA_SERVICE.state.get("uploadedFiles", [])
            if not item.get("deleted") and (not file_id or item.get("fileId") == file_id)
        ]
        title = "Uploaded Sheet PDF" if file_id else "Uploaded Sheets Summary PDF"
        story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
        story.append(Paragraph("SME Performance Management 2026 - 27", styles["Normal"]))
        story.append(Spacer(1, 12))
        if not uploads:
            story.append(Paragraph("No uploaded sheet was found for this request.", styles["Normal"]))
        for upload in uploads:
            story.append(Paragraph(f"<b>{upload.get('fileName') or 'Uploaded Sheet'}</b>", styles["Heading2"]))
            rows = [
                ["Field", "Value"],
                ["Upload Type", str(upload.get("uploadType", "")).replace("_", " ").title()],
                ["Records", str(upload.get("recordCount", 0))],
                ["Uploaded At", str(upload.get("uploadedAt", ""))],
                ["File ID", str(upload.get("fileId", ""))],
                ["Stored Path", str(upload.get("storedPath", ""))],
                ["Status", "Active"],
            ]
            table = Table(rows, colWidths=[1.6 * inch, 5.6 * inch], hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f6e9e4")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2f3848")),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dfe3ea")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fbfbfc")]),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 14))
        doc.build(story)
        return buffer.getvalue(), safe_filename(uploads[0].get("fileName") if len(uploads) == 1 else "uploaded-sheets")

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
        if parsed.path == "/api/admin/upload.pdf":
            session = self.require_admin()
            if not session:
                return
            query = parse_qs(parsed.query)
            pdf, filename = build_upload_pdf((query.get("fileId", [""])[0] or "").strip())
            return send_pdf(self, pdf, f"{filename}.pdf")
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
