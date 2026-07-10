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
from gtm_tool.report_cf_patch import install_excel_patch, install_runtime_patch  # noqa: E402

install()
install_excel_patch()

from gtm_tool.http_handler import GTMAppHandler  # noqa: E402

install_runtime_patch()

# Keep the live service responsive. The heavier dashboard patch is intentionally
# not loaded at startup because it reparses uploaded workbooks and can block
# Render before the first page response is sent.


def install_login_startup_patch(handler_cls):
    if getattr(handler_cls, "_login_startup_patch_installed", False):
        return
    original_do_get = handler_cls.do_GET
    old_bootstrap = '''async function bootstrap() {
  bindEvents();
  try {
    await refreshDashboard();
    setLoggedIn(true);
  } catch (error) {
    setLoggedIn(false);
    els.loginNotice.textContent = "Use your employee ID and password to continue.";
  }
}

bootstrap();'''
    new_bootstrap = '''async function bootstrap() {
  bindEvents();
  setLoggedIn(false);
  els.loginNotice.textContent = "Use your employee ID and password to continue.";
}

bootstrap();'''

    def do_get_with_login_startup_patch(self):
        parsed = urlparse(self.path)
        if parsed.path == "/gtm_app.js":
            script = (ROOT / "gtm_app.js").read_text(encoding="utf-8")
            script = script.replace(old_bootstrap, new_bootstrap)
            body = script.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return original_do_get(self)

    handler_cls.do_GET = do_get_with_login_startup_patch
    handler_cls._login_startup_patch_installed = True


install_login_startup_patch(GTMAppHandler)


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8010"))
    server = ReusableThreadingHTTPServer((host, port), GTMAppHandler)
    print(f"GTM Performance Tool running on http://127.0.0.1:{port}")
    server.serve_forever()
