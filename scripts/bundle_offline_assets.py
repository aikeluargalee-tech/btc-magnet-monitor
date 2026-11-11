"""Make the generated site fully self-contained for the Android app.

Run AFTER `python main.py` and AFTER the Tailwind CLI has produced dist/tailwind.css.

What it does
  1. Copies the bundled fonts (assets/fonts) into dist/fonts and writes dist/fonts/fonts.css.
  2. Rewrites every dist/*.html so it loads /tailwind.css and /fonts/fonts.css from the app itself instead of
     cdn.tailwindcss.com / fonts.googleapis.com / fonts.gstatic.com.
  3. FAILS THE BUILD if any third-party CDN load is left behind, so the app can never silently
     depend on (or leak the user's IP address to) a CDN.
"""
import glob
import os
import re
import shutil
import sys

DIST = "dist"
FONT_SRC = os.path.join("assets", "fonts")
FONT_DST = os.path.join(DIST, "fonts")

FONTS_CSS = """/* Self-hosted fonts (variable, latin subset) - bundled inside the app, no network needed. */
@font-face {
  font-family: 'Inter';
  font-style: normal;
  font-display: swap;
  font-weight: 100 900;
  src: url('./inter-latin-wght-normal.woff2') format('woff2-variations');
}
@font-face {
  font-family: 'JetBrains Mono';
  font-style: normal;
  font-display: swap;
  font-weight: 100 800;
  src: url('./jetbrains-mono-latin-wght-normal.woff2') format('woff2-variations');
}
"""

TAILWIND_TAG = re.compile(r'<script[^>]*src="https://cdn\.tailwindcss\.com[^"]*"[^>]*>\s*</script>')
FONT_TAGS = [
    re.compile(r'<link[^>]*href="https://fonts\.googleapis\.com[^"]*"[^>]*>'),
    re.compile(r'<link[^>]*href="https://fonts\.gstatic\.com[^"]*"[^>]*>'),
]
FORBIDDEN_HOSTS = r"(?:cdn\.tailwindcss\.com|fonts\.googleapis\.com|fonts\.gstatic\.com)"
# Matches real loads (script/link/img src/href, CSS @import / url()), NOT plain-text mentions such as the privacy policy disclosure.
FORBIDDEN_LOAD = re.compile(
    r"""(?:(?:src|href)\s*=\s*["']?https?://%s|@import\s+(?:url\()?["']?https?://%s|url\(\s*["']?https?://%s)""" % ((FORBIDDEN_HOSTS,) * 3),
    re.IGNORECASE,
)


def fail(msg: str) -> None:
    print(f"ERROR: {msg}")
    sys.exit(1)


def main() -> None:
    css_path = os.path.join(DIST, "tailwind.css")
    if not os.path.exists(css_path) or os.path.getsize(css_path) < 5000:
        fail("dist/tailwind.css is missing or suspiciously small - Tailwind build did not run correctly.")

    os.makedirs(FONT_DST, exist_ok=True)
    fonts = glob.glob(os.path.join(FONT_SRC, "*.woff2"))
    if len(fonts) < 2:
        fail(f"expected 2 bundled .woff2 fonts in {FONT_SRC}, found {len(fonts)}")
    for f in fonts:
        shutil.copy(f, FONT_DST)
    with open(os.path.join(FONT_DST, "fonts.css"), "w", encoding="utf-8") as fh:
        fh.write(FONTS_CSS)

    links = '<link rel="stylesheet" href="tailwind.css">\n  <link rel="stylesheet" href="fonts/fonts.css">'
    rewritten = 0
    for path in glob.glob(os.path.join(DIST, "*.html")):
        with open(path, "r", encoding="utf-8") as fh:
            html = fh.read()
        new = TAILWIND_TAG.sub(links, html, count=1)
        for pat in FONT_TAGS:
            new = pat.sub("", new)
        if new != html:
            rewritten += 1
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new)

    # Hard guarantee: no CDN loads may survive in any shipped HTML.
    for path in glob.glob(os.path.join(DIST, "*.html")):
        with open(path, "r", encoding="utf-8") as fh:
            html = fh.read()
        hit = FORBIDDEN_LOAD.search(html)
        if hit:
            fail(f"{path} still loads a third-party CDN resource: {hit.group(0)}")

    print(f"OK: bundled Tailwind CSS ({os.path.getsize(css_path) // 1024} KB) and {len(fonts)} fonts; rewrote {rewritten} HTML files; no CDN references remain.")


if __name__ == "__main__":
    main()
