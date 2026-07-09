import os
import sys
from http.server import ThreadingHTTPServer

from gtm_tool.config import BUNDLED_PYTHON


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

install()

from gtm_tool.http_handler import GTMAppHandler  # noqa: E402

# Keep the live service responsive. The dashboard patch is intentionally not
# loaded at startup because it reparses uploaded workbooks and can block Render
# before the first page response is sent.


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8010"))
    server = ReusableThreadingHTTPServer((host, port), GTMAppHandler)
    print(f"GTM Performance Tool running on http://127.0.0.1:{port}")
    server.serve_forever()
