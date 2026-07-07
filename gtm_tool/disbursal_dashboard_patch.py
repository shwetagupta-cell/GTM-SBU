from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlparse

from gtm_tool.config import ROOT
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
    _install_index_injection(handler_cls)
