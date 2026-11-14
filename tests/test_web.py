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
        for token in ("refreshLiveScan", "sanitizeLiveNode", "LIVE SPOT FEED ACTIVE", "renderAgeBanner"):
            self.assertIn(token, self.index)
        self.assertNotIn("STALE DATA", self.index)

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
        self.assertIn("pwa-v8", sw)
        self.assertIn("'./entry.html'", sw)
        self.assertIn("'./text.html'", sw)

    def test_text_terminal_page_generated_and_clean(self):
        import re
        text_path = os.path.join(self.tmp, "text.html")
        app_path = os.path.join(self.tmp, "app.html")
        self.assertTrue(os.path.exists(text_path), "text.html was not generated")
        self.assertTrue(os.path.exists(app_path), "app.html was not generated")
        with open(text_path, "r", encoding="utf-8") as fh:
            text_html = fh.read()
        with open(app_path, "r", encoding="utf-8") as fh:
            app_html = fh.read()
        with open(os.path.join(self.tmp, "regimes.html"), "r", encoding="utf-8") as fh:
            regimes_html = fh.read()

        self.assertEqual(app_html, text_html, "app.html must match vA text.html")

        # Text terminal & index share ONE clean Blind Telemetry button + optional local watermarks
        for token in (
            "panel-1", "copyBlindPrompt", "copy-blind-btn", "BLIND_PROMPT_TEXT",
            "wb-buy", "wb-sell", "wb-clear", "panel-2", "panel-3", "verdict-guide", "verdict-1", "verdict-2",
            "Verdict 1 vs Verdict 2",
            "app-brand-header", "5-Regime Radar", "Observable Positioning Mechanics",
            "BTC MAGNET MONITOR :: 5-REGIME RADAR", "Bidirectional Liquidity Telemetry Terminal",
            "MODE: 5-REGIME MAGNET RADAR (BIDIRECTIONAL)", "quick-nav", "min-height: 44px",
            "IS_NATIVE_APP", "LIVE_BASE", "serviceWorker", "AdMob", "index.html?desktop=1",
            "Radar Signal:", "Bidirectional Magnet Playbook:", "Bidirectional Patience &amp; Risk Rules:",
            "TIER", "EST.POOL", "p3-conf-fresh"
        ):
            self.assertIn(token, text_html)

        self.assertIn("Verdict 2 &bull; Built-In Radar Engine", self.index)
        self.assertIn("window.location.replace('./entry.html'", self.index)
        self.assertIn("p.get('desktop') === '1'", self.index)
        self.assertIn('src="./assets/app-logo.png?v=9"', text_html)
        self.assertIn('src="./assets/app-logo.png?v=9"', self.index)
        self.assertIn('href="entry.html"', text_html)

        entry_path = os.path.join(self.tmp, "entry.html")
        self.assertTrue(os.path.exists(entry_path), "entry.html was not generated")
        with open(entry_path, "r", encoding="utf-8") as fh:
            entry_html = fh.read()
        for token in (
            'id="entry-hero-video"',
            'src="./assets/media/entry-hero.mp4"',
            'id="entry-badger-video"',
            'src="./assets/media/entry-badger.mp4"',
            'id="verdict1-showcase"',
            "Why &amp; How This App Helps You",
            "Copy Telemetry for AI",
            "toggleEntryAudio('entry-badger-video', 'entry-badger-sound-btn')",
            'id="enter-monitor-btn"',
            'href="text.html"',
            'id="entry-data-slot"',
            'id="entry-pressure-meter"',
            "Bull vs. Bear Pressure Meter",
            "data-api.binance.vision/api/v3/depth?symbol=BTCUSDT",
            "Order-Book Depth",
            "Aggressive Flow (24H CVD)",
            "Crowd Leverage Skew (L/S)",
            "hideMonitorOverlaysOnEntry",
            'id="entry-native-ad-anchor"',
            "initEntryNativeAd",
            "backdrop-filter: blur(",
            ".entry-wrapper",
            "rgba(168, 85, 247",
        ):
            self.assertIn(token, entry_html, f"Missing {token} in entry.html")
        self.assertNotIn("querySelector('.entry-wrap')", entry_html)

        self.assertLess(
            entry_html.index('id="entry-badger-card"'),
            entry_html.index('id="entry-native-ad-anchor"'),
            "Entry native ad slot must sit below Honey Badger video card",
        )
        self.assertLess(
            entry_html.index('id="entry-native-ad-anchor"'),
            entry_html.index('id="verdict1-showcase"'),
            "Entry native ad slot must sit above Verdict 1 showcase card",
        )

        # Verify fallback honesty when ls_ratio_available is false on entry.html
        import copy as _copy
        no_ls_payload = _copy.deepcopy(self.payload)
        no_ls_payload["metrics"]["ls_ratio_available"] = False
        no_ls_payload["metrics"]["long_short_account_ratio"] = 0.0
        no_ls_entry = WebGenerator(output_dir=self.tmp)._render_entry_page(no_ls_payload)
        self.assertIn("DATA UNAVAILABLE", no_ls_entry)
        self.assertNotIn("cdn.tailwindcss.com", entry_html)
        self.assertNotIn("fonts.googleapis.com", entry_html)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "assets", "media", "entry-hero.mp4")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "assets", "media", "entry-badger.mp4")))

        def _strip_prompt_payloads(doc: str) -> str:
            cleaned = re.sub(r"<textarea[^>]*>.*?</textarea>", "", doc, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r'<div id="blind-preview-pre"[^>]*>.*?</div>', "", cleaned, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r'<pre[^>]*id="prompt-box-pre"[^>]*>.*?</pre>', "", cleaned, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r"<script[^>]*>.*?</script>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
            return cleaned

        for surface_name, html_doc in (
            ("index.html", self.index),
            ("entry.html", entry_html),
            ("text.html", text_html),
            ("app.html", app_html),
            ("regimes.html", regimes_html),
        ):
            visible = _strip_prompt_payloads(html_doc)
            for jargon in (
                "MANDATE: DIBSE", "10% USDT", "10% BTC", "80% Core", "80% core",
                "Active Sandbox", "DIBSE", "NO LEVERAGE", "SPOT-ONLY",
                "Spot-Only", "No Leverage", "WARNING: TELEMETRY STALE", "STALE DATA",
            ):
                self.assertNotIn(jargon, visible, f"{surface_name} visible HTML retained jargon {jargon!r}")

        for surface_name, html_doc in (("index.html", self.index), ("text.html", text_html)):
            self.assertIn('id="copy-blind-btn"', html_doc, surface_name)
            self.assertIn('id="wb-buy"', html_doc, surface_name)
            self.assertIn('id="wb-sell"', html_doc, surface_name)
            self.assertIn('id="verdict-1"', html_doc, surface_name)
            self.assertIn('id="verdict-2"', html_doc, surface_name)
            self.assertIn("Verdict 1", html_doc, surface_name)
            self.assertIn("Verdict 2", html_doc, surface_name)
            for removed_btn in (
                "copy-prompt-btn", "COPY FULL AUDIT PROMPT", "Copy Full Audit Prompt",
                "copyTelemetryPrompt", "llm-prompt-data", "let PROMPT_TEXT",
                "Method 1", "Method 2", "method-1", "method-2",
            ):
                self.assertNotIn(removed_btn, html_doc, f"{surface_name} retained {removed_btn}")
            for banned_ind in ("20D EMA", "50D EMA", "200D SMA", "Daily ATR", "1H ATR", "ATR Compress"):
                self.assertNotIn(banned_ind, html_doc, f"{surface_name} retained lagged indicator {banned_ind}")

        self.assertIn("Bidirectional Liquidity Protocol", regimes_html)
        for banned_reg in ("20D EMA", "50D EMA", "200D SMA", "1% equity risk-budget"):
            self.assertNotIn(banned_reg, regimes_html)

        for removed in ("view-switcher", "[HUD]", "[JSON]", "[DELTA]", "[PROMPT]"):
            self.assertNotIn(removed, text_html)
        self.assertNotIn("panel-4", text_html)
        self.assertNotIn("Recommended Rotation", text_html)
        self.assertNotIn("cdn.tailwindcss.com", text_html)
        self.assertNotIn("fonts.googleapis.com", text_html)

    def test_multi_language_i18n_bundle_and_surfaces(self):
        from web.i18n import AI_PROMPT_DIRECTIVES, SUPPORTED_LANGS, TRANSLATIONS

        i18n_path = os.path.join(self.tmp, "i18n.js")
        self.assertTrue(os.path.exists(i18n_path), "dist/i18n.js should be generated")
        with open(i18n_path, "r", encoding="utf-8") as f:
            i18n_js = f.read()

        self.assertIn("window.BtcMagnetI18n", i18n_js)
        self.assertIn("localizeBlindPrompt", i18n_js)
        self.assertIn("btc-lang-flag", i18n_js)
        self.assertIn("<svg", i18n_js)
        for lang in ("en", "zh", "id", "ko", "ja", "fr", "es"):
            self.assertIn(lang, SUPPORTED_LANGS)
            if lang != "en":
                self.assertIn(lang, AI_PROMPT_DIRECTIVES)
                self.assertIn("[RESPONSE LANGUAGE DIRECTIVE]", AI_PROMPT_DIRECTIVES[lang])
                self.assertIn(lang, i18n_js)
                self.assertTrue(len(TRANSLATIONS.get(lang, {})) >= 20, f"Expected translations for {lang}")

        with open(os.path.join(self.tmp, "sw.js"), "r", encoding="utf-8") as f:
            sw_js = f.read()
        self.assertIn("'./i18n.js'", sw_js)

        for fname in ("entry.html", "text.html", "app.html", "index.html", "regimes.html"):
            with open(os.path.join(self.tmp, fname), "r", encoding="utf-8") as f:
                doc = f.read()
            self.assertIn('src="./i18n.js"', doc, f"{fname} missing ./i18n.js script tag")
            self.assertIn("data-i18n-switcher", doc, f"{fname} missing language switcher mount")
            if fname in ("index.html", "text.html", "app.html"):
                self.assertIn("localizeBlindPrompt", doc, f"{fname} missing localizeBlindPrompt hook")

    def test_text_telemetry_linter_and_stale_injection(self):
        import copy
        gen = WebGenerator(output_dir=self.tmp)
        bad_risk_payload = copy.deepcopy(self.payload)
        bad_risk_payload["risk"]["portfolio_risk_pct"] = 2.5
        with self.assertRaises(AssertionError):
            gen._verify_text_telemetry(bad_risk_payload)

        bad_skew_payload = copy.deepcopy(self.payload)
        bad_skew_payload["regime"]["immediate_imbalance_ratio"] = 999.0
        bad_skew_payload["regime"]["nearest_lower_cluster"] = {"estimated_vol_usd": 10000000.0}
        bad_skew_payload["regime"]["nearest_upper_cluster"] = {"estimated_vol_usd": 5000000.0}
        with self.assertRaises(AssertionError):
            gen._verify_text_telemetry(bad_skew_payload)

        sweep_payload = copy.deepcopy(self.payload)
        sweep_payload["regime"]["lsce_status"] = "SWEEP_IN_PROGRESS"
        sweep_payload["timestamp"] = "2020-01-01T00:00:00Z"
        sweep_html = gen._render_text_page(sweep_payload)
        self.assertIn("PIERCING / ACTIVE SWEEP", sweep_html)
        self.assertIn('id="static-stale-banner" style="display: none;"', sweep_html)
        self.assertNotIn("WARNING: TELEMETRY STALE", sweep_html)

    def test_manifest_includes_maskable_and_icons(self):
        with open(os.path.join(self.tmp, "manifest.json"), "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        self.assertEqual(manifest.get("start_url"), "./entry.html")
        purposes = [i.get("purpose") for i in manifest.get("icons", [])]
        self.assertIn("maskable", purposes)
        self.assertIn("any", purposes)


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
            for name in ("index.html", "entry.html", "text.html", "app.html", "regimes.html", "privacy.html"):
                with open(os.path.join(dist, name), "r", encoding="utf-8") as fh:
                    html = fh.read()
                for needle in ("src=\"https://cdn.tailwindcss.com", "href=\"https://fonts.googleapis.com", "href=\"https://fonts.gstatic.com"):
                    self.assertNotIn(needle, html, f"{name} still loads {needle}")
                if name not in ("entry.html", "text.html", "app.html"):
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


class TestBrandingAndAndroidIcons(unittest.TestCase):
    def test_master_fullsize_icon_and_web_icons_match_1024_512(self):
        master = os.path.join(ROOT, "branding", "app-icon-fullsize.png")
        self.assertTrue(os.path.exists(master), "branding/app-icon-fullsize.png missing")
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")
        with Image.open(master) as im:
            self.assertEqual(im.size, (1024, 1024))
        for rel, expected in (
            ("icon-512.png", (512, 512)),
            ("icon-maskable-512.png", (512, 512)),
            ("icon-192.png", (192, 192)),
            (os.path.join("assets", "app-logo.png"), (512, 512)),
        ):
            with Image.open(os.path.join(ROOT, rel)) as im:
                self.assertEqual(im.size, expected, rel)

    def test_android_icon_generator_replaces_capacitor_defaults(self):
        try:
            import PIL  # noqa: F401
        except ImportError:
            self.skipTest("Pillow not installed")
        from scripts.generate_android_assets import apply_android_resources
        work = tempfile.mkdtemp()
        try:
            stale_files = []
            for rel in (
                os.path.join("drawable-anydpi-v24", "ic_launcher_foreground.xml"),
                os.path.join("drawable-v24", "ic_launcher_foreground.xml"),
                os.path.join("drawable-v24", "$ic_launcher_foreground__0.xml"),
                os.path.join("drawable", "ic_launcher_background.xml"),
            ):
                stale_path = os.path.join(work, rel)
                os.makedirs(os.path.dirname(stale_path), exist_ok=True)
                with open(stale_path, "w", encoding="utf-8") as fh:
                    fh.write("<vector/>")
                stale_files.append(stale_path)
            apply_android_resources(ROOT, res_dir=work)
            for stale_path in stale_files:
                self.assertFalse(os.path.exists(stale_path), stale_path)
            self.assertTrue(os.path.exists(os.path.join(work, "mipmap-anydpi-v26", "ic_launcher.xml")))
            self.assertTrue(os.path.exists(os.path.join(work, "mipmap-xxxhdpi", "ic_launcher.png")))
            self.assertTrue(os.path.exists(os.path.join(work, "mipmap-xxxhdpi", "ic_launcher_foreground.png")))
            self.assertTrue(os.path.exists(os.path.join(work, "drawable-port-xxhdpi", "splash.png")))
        finally:
            shutil.rmtree(work, ignore_errors=True)


class TestScalabilityAndNativeAd(unittest.TestCase):
    def test_configure_android_native_copies_files_and_patches_gradle_idempotently(self):
        from scripts.configure_android_native import (
            ADMOB_DEP_LINE,
            APP_PACKAGE,
            apply_android_native,
            ensure_admob_gradle_dependency,
        )

        work = tempfile.mkdtemp()
        try:
            app_dir = os.path.join(work, "app")
            os.makedirs(os.path.join(app_dir, "src", "main", "res"), exist_ok=True)
            gradle_path = os.path.join(app_dir, "build.gradle")
            with open(gradle_path, "w", encoding="utf-8") as fh:
                fh.write(
                    "dependencies {\n"
                    "    implementation project(':capacitor-android')\n"
                    "}\n"
                )

            apply_android_native(ROOT, android_dir=work)

            pkg_dir = os.path.join(app_dir, "src", "main", "java", *APP_PACKAGE.split("."))
            self.assertTrue(os.path.isfile(os.path.join(pkg_dir, "MainActivity.java")))
            self.assertTrue(os.path.isfile(os.path.join(pkg_dir, "MagnetNativeAdPlugin.java")))
            self.assertTrue(os.path.isfile(os.path.join(app_dir, "src", "main", "res", "layout", "native_ad_card.xml")))
            for drawable_name in ("native_ad_card_bg.xml", "native_ad_badge_bg.xml", "native_ad_cta_bg.xml"):
                self.assertTrue(
                    os.path.isfile(os.path.join(app_dir, "src", "main", "res", "drawable", drawable_name)),
                    drawable_name,
                )

            with open(gradle_path, "r", encoding="utf-8") as fh:
                gradle_text = fh.read()
            self.assertIn(ADMOB_DEP_LINE.strip(), gradle_text)

            with open(os.path.join(pkg_dir, "MainActivity.java"), "r", encoding="utf-8") as fh:
                main_act = fh.read()
            self.assertIn("OnBackPressedCallback", main_act)
            self.assertIn("/entry.html", main_act)

            # Second run must be idempotent
            self.assertFalse(ensure_admob_gradle_dependency(gradle_path))
            apply_android_native(ROOT, android_dir=work)
            with open(gradle_path, "r", encoding="utf-8") as fh:
                self.assertEqual(fh.read().count("com.google.android.gms:play-services-ads"), 1)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_generated_pages_use_30s_cdn_bucket_cooldown_header_check_and_native_ad_slot(self):
        import json
        from web.generator import WebGenerator

        regime_path = os.path.join(ROOT, "data", "regime.json")
        if not os.path.isfile(regime_path):
            self.skipTest("data/regime.json missing")
        with open(regime_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)

        work = tempfile.mkdtemp()
        try:
            WebGenerator(work).generate(payload)
            with open(os.path.join(work, "text.html"), "r", encoding="utf-8") as fh:
                text_html = fh.read()
            with open(os.path.join(work, "index.html"), "r", encoding="utf-8") as fh:
                index_html = fh.read()

            # Text terminal: header Check button + cooldown + 30s bucket + smart poll + clear overdue
            for token in (
                'id="hdr-check-btn"',
                'onclick="refreshLiveScan(true)"',
                "scheduleNextTextPoll",
                "Math.floor(nowMs / 30000)",
                "lastManualCheckMs + 25000",
                "Scan ${ageM}m ago • next in",
                "MagnetNativeAd",
                "ca-app-pub-3940256099942544/2247696110",
                "syncNativeAdSlot",
                "attachNativeListener",
            ):
                self.assertIn(token, text_html, f"Missing {token} in text.html")

            import re
            self.assertIsNone(
                re.search(r"addListener\s*\([\s\S]{0,400}?\)\s*\.catch\s*\(", text_html),
                "Capacitor native addListener returns {remove} synchronously; chaining .catch() throws TypeError",
            )

            self.assertIn('id="native-ad-anchor"', text_html)
            self.assertIn('id="verdict-guide"', text_html)
            self.assertLess(
                text_html.index('id="native-ad-anchor"'),
                text_html.index('id="verdict-guide"'),
                "Native ad slot must appear directly above Bridge Verdict 1 vs Verdict 2 panel",
            )
            self.assertNotIn("?t=' + Date.now()", text_html)
            self.assertNotIn("cache: 'no-store'", text_html)

            # Desktop dashboard: 30s bucket + smart poll + clear overdue
            for token in (
                "scheduleNextScanPoll",
                "Math.floor(lastAutoScanCheckMs / 30000)",
                "Scan ${ageMin}m ago • next in",
            ):
                self.assertIn(token, index_html, f"Missing {token} in index.html")
            self.assertNotIn("?t=' + Date.now()", index_html)
            self.assertNotIn("cache: 'no-store'", index_html)
            self.assertNotIn("setInterval(refreshLiveScan", index_html)
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_workflows_configure_native_ad_and_half_hour_skip_window(self):
        import datetime

        radar_path = os.path.join(ROOT, ".github", "workflows", "radar.yml")
        apk_wf_path = os.path.join(ROOT, ".github", "workflows", "build-android-apk.yml")
        with open(radar_path, "r", encoding="utf-8") as fh:
            radar_yml = fh.read()
        with open(apk_wf_path, "r", encoding="utf-8") as fh:
            apk_yml = fh.read()

        self.assertIn("same_window", radar_yml)
        self.assertIn("age < 360 or (same_window and age < 1500)", radar_yml)
        self.assertIn("python scripts/configure_android_native.py", apk_yml)
        self.assertIn("res/layout/native_ad_card.xml", apk_yml)
        self.assertIn("Lcom/aikeluargalee/btcmagnet/MagnetNativeAdPlugin;", apk_yml)

        def should_skip(last_dt: datetime.datetime, now_dt: datetime.datetime) -> bool:
            age = (now_dt - last_dt).total_seconds()
            same_window = (now_dt.date(), now_dt.hour, now_dt.minute // 30) == (
                last_dt.date(),
                last_dt.hour,
                last_dt.minute // 30,
            )
            return age < 360 or (same_window and age < 1500)

        # 04:10:52 push must NOT skip 04:32:00 cron (different 30m window and age > 6m)
        self.assertFalse(
            should_skip(
                datetime.datetime(2026, 11, 12, 4, 10, 52, tzinfo=datetime.timezone.utc),
                datetime.datetime(2026, 11, 12, 4, 32, 0, tzinfo=datetime.timezone.utc),
            )
        )
        # 04:31:00 push MUST skip 04:32:00 cron (same window, age = 60s)
        self.assertTrue(
            should_skip(
                datetime.datetime(2026, 11, 12, 4, 31, 0, tzinfo=datetime.timezone.utc),
                datetime.datetime(2026, 11, 12, 4, 32, 0, tzinfo=datetime.timezone.utc),
            )
        )
        # 04:29:00 push MUST skip 04:32:00 cron (age = 180s < 360s)
        self.assertTrue(
            should_skip(
                datetime.datetime(2026, 11, 12, 4, 29, 0, tzinfo=datetime.timezone.utc),
                datetime.datetime(2026, 11, 12, 4, 32, 0, tzinfo=datetime.timezone.utc),
            )
        )


if __name__ == "__main__":
    unittest.main()
