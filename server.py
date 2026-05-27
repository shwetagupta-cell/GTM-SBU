import os
import sys
from http.server import ThreadingHTTPServer

from services.config_service import BUNDLED_PYTHON


def ensure_bundled_runtime():
    if os.environ.get("SME_BUNDLED_RUNTIME") == "1":
        return
    try:
        import pandas  # noqa: F401
    except Exception:
        if not BUNDLED_PYTHON.exists():
            raise RuntimeError("Bundled Python runtime with pandas was not found.")
        env = os.environ.copy()
        env["SME_BUNDLED_RUNTIME"] = "1"
        os.execve(str(BUNDLED_PYTHON), [str(BUNDLED_PYTHON), __file__, *sys.argv[1:]], env)


ensure_bundled_runtime()

from routes.api import AppHandler  # noqa: E402


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8001"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Incentive Dashboard running on http://127.0.0.1:{port}")
    server.serve_forever()
