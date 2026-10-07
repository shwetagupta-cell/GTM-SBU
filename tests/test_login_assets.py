import tempfile
import unittest
from pathlib import Path

from gtm_tool.page_assets import prepare_login_assets


ROOT = Path(__file__).resolve().parents[1]


class LoginAssetsTests(unittest.TestCase):
    def test_login_can_render_without_external_stylesheet_or_script(self):
        html = prepare_login_assets((ROOT / "gtm_index.html").read_text(), ROOT)
        self.assertNotIn('<link rel="stylesheet"', html)
        self.assertIn((ROOT / "gtm_styles.css").read_text(), html)
        self.assertIn('<section id="authShell" class="auth-shell">', html)
        self.assertIn('<script defer src="/gtm_app.js?v=', html)
        self.assertIn('id="loginEmployeeId"', html)
        self.assertIn('id="loginPassword"', html)

    def test_script_url_changes_when_script_or_server_patch_changes(self):
        html = '<script src="./gtm_app.js"></script>'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "gtm_styles.css").write_text("body { color: black; }")
            (root / "gtm_app.js").write_text("bootstrap();")
            (root / "gtm_server.py").write_text("patch_v1")
            first = prepare_login_assets(html, root)
            (root / "gtm_server.py").write_text("patch_v2")
            second = prepare_login_assets(html, root)
            (root / "gtm_app.js").write_text("newBootstrap();")
            third = prepare_login_assets(html, root)
            self.assertNotEqual(first, second)
            self.assertNotEqual(second, third)
            self.assertEqual(third, prepare_login_assets(html, root))


if __name__ == "__main__":
    unittest.main()
