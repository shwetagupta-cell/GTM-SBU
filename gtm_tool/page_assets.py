import hashlib


def prepare_login_assets(html, root):
    # Keep the login form paintable even when a separate asset request stalls.
    stylesheet = (root / "gtm_styles.css").read_text(encoding="utf-8")
    html = html.replace(
        '<link rel="stylesheet" href="./gtm_styles.css" />',
        '<style id="app-styles">\n' + stylesheet + '\n</style>',
    )
    script = (root / "gtm_app.js").read_bytes()
    server = (root / "gtm_server.py").read_bytes()
    version = hashlib.sha256(script + server).hexdigest()[:16]
    return html.replace(
        '<script src="./gtm_app.js"></script>',
        f'<script defer src="/gtm_app.js?v={version}"></script>',
    )
