import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from web.generator import WebGenerator  # noqa: E402


def _sample_payload():
    with open(os.path.join(ROOT, "data", "regime.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


class TestGeneratedSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.payload = _sample_payload()
        WebGenerator(output_dir=cls.tmp).generate(cls.payload)
        with open(os.path.join(cls.tmp, "index.html"), "r", encoding="utf-8") as fh:
            cls.index = fh.read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_data_age_banner_and_swappable_root_present(self):
        self.assertIn('id="data-age-banner"', self.index)
        self.assertIn('id="app-root"', self.index)
        self.assertIn('data-scan-ts="%s"' % self.payload["timestamp"], self.index)

    def test_live_refresh_logic_present(self):
        for token in ("refreshLiveScan", "sanitizeLiveNode", "STALE DATA", "renderAgeBanner"):
            self.assertIn(token, self.index)

    def test_price_feed_prefers_non_geoblocked_endpoint(self):
        self.assertLess(
            self.index.index("data-api.binance.vision/api/v3/ticker/price"),
            self.index.index("api.binance.com/api/v3/ticker/price"),
        )

    def test_negative_drift_keeps_minus_sign(self):
        self.assertIn("(up ? '+' : '-') + '$'", self.index)

    def test_privacy_policy_discloses_direct_connections(self):
        with open(os.path.join(self.tmp, "privacy.html"), "r", encoding="utf-8") as fh:
            privacy = fh.read()
        for token in ("data-api.binance.vision", "aikeluargalee-tech.github.io", "cdn.tailwindcss.com", "IP address"):
            self.assertIn(token, privacy)

    def test_service_worker_does_not_cache_errors(self):
        with open(os.path.join(self.tmp, "sw.js"), "r", encoding="utf-8") as fh:
            sw = fh.read()
        self.assertIn("res.ok && res.status === 200", sw)
        self.assertIn("pwa-v6", sw)

    def test_text_terminal_page_generated_and_clean(self):
        text_path = os.path.join(self.tmp, "text.html")
        self.assertTrue(os.path.exists(text_path), "text.html was not generated")
        with open(text_path, "r", encoding="utf-8") as fh:
            text_html = fh.read()
        for token in ("panel-1", "copyPrompt", "PROMPT_TEXT", "panel-2", "panel-3", "panel-4", "method-1", "method-2"):
            self.assertIn(token, text_html)
        self.assertNotIn("cdn.tailwindcss.com", text_html)
        self.assertNotIn("fonts.googleapis.com", text_html)


class TestOfflineBundler(unittest.TestCase):
    def test_bundler_removes_every_cdn_reference(self):
        work = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(work, "assets"))
            shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(work, "scripts"))
            dist = os.path.join(work, "dist")
            WebGenerator(output_dir=dist).generate(_sample_payload())
            with open(os.path.join(dist, "tailwind.css"), "w", encoding="utf-8") as fh:
                fh.write("/* stand-in for the real build */" + ("a{}" * 4000))
            proc = subprocess.run(
                [sys.executable, os.path.join("scripts", "bundle_offline_assets.py")],
                cwd=work, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            for name in ("index.html", "app.html", "regimes.html", "privacy.html"):
                with open(os.path.join(dist, name), "r", encoding="utf-8") as fh:
                    html = fh.read()
                for needle in ("src=\"https://cdn.tailwindcss.com", "href=\"https://fonts.googleapis.com", "href=\"https://fonts.gstatic.com"):
                    self.assertNotIn(needle, html, f"{name} still loads {needle}")
                self.assertIn('href="tailwind.css"', html)
            self.assertTrue(os.path.exists(os.path.join(dist, "fonts", "fonts.css")))
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_bundler_fails_when_tailwind_css_missing(self):
        work = tempfile.mkdtemp()
        try:
            shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(work, "assets"))
            shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(work, "scripts"))
            WebGenerator(output_dir=os.path.join(work, "dist")).generate(_sample_payload())
            proc = subprocess.run(
                [sys.executable, os.path.join("scripts", "bundle_offline_assets.py")],
                cwd=work, capture_output=True, text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
        finally:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
