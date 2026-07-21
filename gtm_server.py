import os
import sys
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse

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
              .audit-list { display: grid; gap: 12px; max-height: 520px; overflow: auto; padding-right: 4px; }
              .audit-card { display: grid; grid-template-columns: 42px minmax(0, 1fr); gap: 12px; padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: rgba(255, 255, 255, 0.82); box-shadow: 0 10px 24px rgba(24, 33, 47, 0.06); }
              .audit-avatar { width: 42px; height: 42px; display: grid; place-items: center; border-radius: 8px; background: rgba(207, 95, 58, 0.12); color: var(--accent); font-weight: 800; letter-spacing: 0; }
              .audit-card strong { display: block; color: var(--text); font-size: 14px; line-height: 1.35; }
              .audit-card p { margin: 4px 0 0; color: var(--muted); font-size: 12px; }
              .audit-meta { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 10px; color: var(--muted); font-size: 11px; }
              .audit-meta span { display: inline-flex; min-height: 24px; align-items: center; max-width: 100%; padding: 0 9px; border-radius: 999px; background: rgba(24, 33, 47, 0.06); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
              .audit-meta .audit-time { background: rgba(207, 95, 58, 0.12); color: var(--accent); font-weight: 700; }
              @media (max-width: 700px) { .audit-card { grid-template-columns: 1fr; } .audit-avatar { width: 36px; height: 36px; } }
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
    els.auditLog.innerHTML = auditLog.length
      ? auditLog
          .map((entry) => {
            const changed = formatLoadedAt(entry.changedAt);
            const actorName = entry.changedByName || "Unknown Admin";
            const actorInitial = String(actorName).trim().charAt(0).toUpperCase() || "A";
            const actionLabel = String(entry.action || "admin change").replaceAll("_", " ");
            const details = [
              entry.employeeId ? `Employee ${entry.employeeId}` : "",
              entry.periodLabel ? `Month ${entry.periodLabel}` : "",
              entry.projectId ? `Project ${entry.projectId}` : "",
              entry.fileName || entry.fileId || "",
            ].filter(Boolean);
            return `
              <article class="audit-card">
                <span class="audit-avatar">${escapeHtml(actorInitial)}</span>
                <div class="audit-body">
                  <strong>${escapeHtml(entry.summary || entry.action || "Admin change")}</strong>
                  <p>${escapeHtml(actorName)}${entry.changedById ? ` • ID ${escapeHtml(entry.changedById)}` : ""}</p>
                  <div class="audit-meta">
                    <span class="audit-time">${escapeHtml(changed.primary)} ${escapeHtml(changed.secondary)}</span>
                    <span>${escapeHtml(actionLabel)}</span>
                    ${details.map((item) => `<span title="${escapeHtml(item)}">${escapeHtml(item)}</span>`).join("")}
                  </div>
                </div>
              </article>
            `;
          })
          .join("")
      : `<article class="audit-card empty-state">Admin changes will appear here.</article>`;
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
