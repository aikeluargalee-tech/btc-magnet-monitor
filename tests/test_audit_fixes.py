import os
import sys
import json
import tempfile
import unittest
from dataclasses import asdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.models import MarketMetrics, LiquidationCluster
from engine.classifier import RegimeClassifier
from engine.risk_manager import RiskManager
from web.generator import WebGenerator


def _make_sample_inputs(
    price: float = 73509.29,
    daily_vwap: float = 73755.83,
    basis: float = -1.12,
    depth: float = 0.23,
    ls_ratio: float = 1.85,
    oi_hist_ok: bool = True,
    ls_avail: bool = True,
):
    metrics = MarketMetrics(
        price=price,
        daily_vwap=daily_vwap,
        weekly_vwap=74195.38,
        spot_vol_24h=16007.12,
        spot_vol_ma20=14501.22,
        spot_vol_ratio=1.10,
        spot_cvd_ratio=1.01,
        spot_cvd_slope_7d=562.87,
        spot_cvd_slope_14d=3269.15,
        perp_cvd_slope_24h=2522.56,
        perp_cvd_trend="positive",
        open_interest=9327.2,
        oi_change_1h_pct=-0.15,
        oi_change_4h_pct=-0.35,
        oi_change_24h_pct=-0.85,
        oi_change_3d_pct=1.20,
        funding_rate=0.000066,
        funding_rate_annualized=7.27,
        futures_basis_annualized=basis,
        price_change_1h_pct=-0.10,
        price_change_24h_pct=-1.17,
        long_short_account_ratio=ls_ratio,
        top_trader_long_short_ratio=ls_ratio,
        taker_buy_sell_ratio=1.01,
        bids_asks_depth_ratio=depth,
        swing_low_4h=72727.27,
        swing_high_4h=74474.00,
        base_floor=72727.27,
        base_ceiling=74474.00,
        capitulation_wick_low=72727.27,
        euphoria_wick_high=74474.00,
        closed_4h_bar_close_time="2026-11-11T12:00:00+00:00",
        data_quality="LIVE",
        spot_data_source="Binance Public Market-Data REST (data-api.binance.vision/api/v3 Live Klines & Depth)",
        futures_data_source="OKX Live Public Stats & Deribit/Kraken Perps",
        etf_net_inflow_m=None,
        whale_inflow_proxy=None,
        oi_scope="Single-venue perpetual subset (not total market OI)",
        ls_ratio_available=ls_avail,
        oi_history_available=oi_hist_ok,
        ls_ratio_percentile_72h=54.2 if ls_avail else None,
    )
    clusters = [
        LiquidationCluster(
            price_level=73900.0,
            distance_pct=0.53,
            distance_atr=None,
            estimated_vol_usd=18500000.0,
            side="upper",
            cluster_type="Modeled Short Liquidity Pool (Algorithmic Estimate)",
        ),
        LiquidationCluster(
            price_level=73450.0,
            distance_pct=0.08,
            distance_atr=None,
            estimated_vol_usd=72400000.0,
            side="lower",
            cluster_type="Modeled Long Liquidity Pool (Algorithmic Estimate)",
        ),
    ]
    return metrics, clusters


class TestAuditFixesAndRegressions(unittest.TestCase):
    """Regression suite covering Qwen audit fixes, cadence/next-update, and distinctive panel borders."""

    def test_narrative_vs_metrics_consistency_no_hardcoded_stale_numbers(self):
        metrics, clusters = _make_sample_inputs(
            price=71000.0,
            daily_vwap=71234.50,
            basis=-0.85,
            depth=0.31,
            ls_ratio=1.82,
        )
        # Conflicted state forces TRANSITION_MIXED conflict branch
        regime = RegimeClassifier().classify(metrics, clusters)
        self.assertEqual(regime.regime_id, "TRANSITION_MIXED")
        self.assertEqual(len(regime.matched_criteria), 4)
        self.assertIn("4/4", regime.majority_score)

        joined = " ".join(regime.matched_criteria + regime.why_points + [regime.plain_english_verdict])
        self.assertIn("71,234.50", joined)
        self.assertIn("-0.85%", joined)
        self.assertIn("0.31", joined)
        for stale in ("-1.3%", "0.19", "74,963", "Over 70%"):
            self.assertNotIn(stale, joined)

    def test_verify_text_telemetry_rejects_stale_prose(self):
        metrics, clusters = _make_sample_inputs(daily_vwap=71234.50, basis=-0.85, depth=0.31)
        regime = RegimeClassifier().classify(metrics, clusters)
        risk = RiskManager().evaluate_risk(regime)
        payload = {
            "timestamp": "2026-11-11T15:30:00+00:00",
            "symbol": "BTCUSDT",
            "regime": asdict(regime),
            "metrics": asdict(metrics),
            "risk": risk,
        }
        payload["regime"]["why_points"] = ["Price trapped below VWAP ($74,963) with -1.3% basis."]
        with tempfile.TemporaryDirectory() as tmp:
            gen = WebGenerator(output_dir=tmp)
            with self.assertRaises(AssertionError):
                gen._verify_text_telemetry(payload)

    def test_canonical_ladder_and_prompt_parity_across_all_surfaces(self):
        metrics, clusters = _make_sample_inputs()
        regime = RegimeClassifier().classify(metrics, clusters)
        risk = RiskManager().evaluate_risk(regime)
        payload = {
            "timestamp": "2026-11-11T15:30:00+00:00",
            "symbol": "BTCUSDT",
            "regime": asdict(regime),
            "metrics": asdict(metrics),
            "risk": risk,
        }
        with tempfile.TemporaryDirectory() as tmp:
            gen = WebGenerator(output_dir=tmp)
            gen.generate(payload)

            with open(os.path.join(tmp, "index.html"), encoding="utf-8") as f:
                index_html = f.read()
            with open(os.path.join(tmp, "text.html"), encoding="utf-8") as f:
                text_html = f.read()
            with open(os.path.join(tmp, "regimes.html"), encoding="utf-8") as f:
                regimes_html = f.read()

            full_prompt = gen._build_llm_prompt(payload)
            blind_prompt = gen._build_blind_llm_prompt(payload)

        # Canonical ladder prices match identically on all outputs
        for row in payload["regime"]["liquidation_ladder"]:
            px_str = f"${row['price']:,.0f}"
            self.assertIn(px_str, index_html)
            self.assertIn(px_str, text_html)
            self.assertIn(px_str, full_prompt)
            self.assertIn(px_str, blind_prompt)

        # Blind prompt avoids anchoring on engine verdict/sizing while enforcing DIBSE & Modeled Estimate tags
        self.assertIn("(Modeled Estimate)", blind_prompt)
        self.assertIn("DIBSE BLIND SPOT TELEMETRY AUDIT", blind_prompt)
        self.assertIn("5-REGIME RADAR REFERENCE DEFINITIONS", blind_prompt)
        self.assertIn("INSTITUTIONAL RISK OFFICER", blind_prompt)
        self.assertIn("LOOP A", blind_prompt)
        self.assertIn("LOOP B", blind_prompt)
        self.assertIn("[ACTIVE INVENTORY WATERMARKS]:", blind_prompt)
        self.assertIn("SINGLE-VENUE", blind_prompt.upper() + " " + payload["metrics"]["oi_scope"].upper())
        self.assertNotIn("DIBSE ENGINE CALL", blind_prompt)
        self.assertNotIn("EXECUTIVE TRADING DIRECTIVE", blind_prompt)
        self.assertNotIn("Recommend Cash Deploy", blind_prompt)
        for banned in ("20D EMA", "50D EMA", "200D SMA", "1H ATR", "ATR Compression"):
            self.assertNotIn(banned, blind_prompt)
        self.assertIn("[DIBSE ENGINE CALL & BIDIRECTIONAL SLEEVE DIRECTIVE]:", full_prompt)
        self.assertIn("(Modeled Estimate)", full_prompt)
        self.assertIn('id="copy-blind-btn"', index_html)
        self.assertIn('id="copy-blind-btn"', text_html)
        self.assertIn('id="verdict2-ai-reminder"', index_html)
        self.assertIn('id="verdict2-ai-reminder"', text_html)
        self.assertIn('id="wb-details"', index_html)
        self.assertIn('id="wb-details"', text_html)
        self.assertNotIn('id="copy-prompt-btn"', index_html)
        self.assertNotIn('id="copy-prompt-btn"', text_html)

        # T2 & T5 fixes in text.html
        self.assertIn('id="live-24h-change"', text_html)
        self.assertIn('id="live-ticker-status"', text_html)
        self.assertIn(" BTC ", text_html)
        self.assertNotIn("Live WebSocket Feed", text_html)
        self.assertNotIn("Binance Vision (Spot)", text_html)

        # Requirement 1: Update cadence & Next Scheduled Update on index.html and text.html
        for token in ("Every 30 Minutes", 'id="next-update-time"', 'id="next-update-countdown"', 'id="subhdr-next-update"'):
            self.assertIn(token, index_html)
        for token in ("Every 30 Minutes", 'id="hdr-next-upd"', 'id="hdr-countdown"', 'id="p1-next-upd"', 'id="p1-countdown"'):
            self.assertIn(token, text_html)

        # Requirement 2: Distinctive colored panel & sub-card borders
        for token in ("border-emerald-500/60", "border-cyan-500/60", "border-violet-500/60", "border-sky-500/60", "border-purple-500/60"):
            self.assertIn(token, index_html)
        for token in ("panel-box-hero", "panel-box-cyan", "panel-box-sky", "panel-box-purple", "panel-box-gold", "sub-card-indigo", "sub-card-amber", "sub-card-rose", "sub-card-teal"):
            self.assertIn(token, text_html)

        # Preserve prior constraint: no Panel 4 in text.html
        self.assertNotIn("panel-4", text_html)
        self.assertNotIn("Recommended Rotation", text_html)

        # Methodology documentation sections on regimes.html (T4 & T6)
        self.assertIn('id="methodology-pools"', regimes_html)
        self.assertIn('id="methodology-lsce"', regimes_html)

    def test_fallback_honesty_when_oi_or_ls_unavailable(self):
        metrics, clusters = _make_sample_inputs(oi_hist_ok=False, ls_avail=False, ls_ratio=1.0)
        regime = RegimeClassifier().classify(metrics, clusters)
        risk = RiskManager().evaluate_risk(regime)
        payload = {
            "timestamp": "2026-11-11T15:30:00+00:00",
            "symbol": "BTCUSDT",
            "regime": asdict(regime),
            "metrics": {k: v for k, v in asdict(metrics).items() if k != "liquidation_clusters"},
            "risk": risk,
        }
        with tempfile.TemporaryDirectory() as tmp:
            gen = WebGenerator(output_dir=tmp)
            gen.generate(payload)
            with open(os.path.join(tmp, "text.html"), encoding="utf-8") as f:
                text_html = f.read()
            with open(os.path.join(tmp, "index.html"), encoding="utf-8") as f:
                index_html = f.read()
            blind_prompt = gen._build_blind_llm_prompt(payload)
        self.assertGreaterEqual(text_html.count("DATA UNAVAILABLE"), 2)
        self.assertGreaterEqual(index_html.count("DATA UNAVAILABLE"), 2)
        self.assertIn("DATA UNAVAILABLE", blind_prompt)

    def test_text_auto_refresh_and_workflow_backup_schedule(self):
        metrics, clusters = _make_sample_inputs()
        regime = RegimeClassifier().classify(metrics, clusters)
        risk = RiskManager().evaluate_risk(regime)
        payload = {
            "timestamp": "2026-11-11T15:32:00+00:00",
            "symbol": "BTCUSDT",
            "regime": asdict(regime),
            "metrics": {k: v for k, v in asdict(metrics).items() if k != "liquidation_clusters"},
            "risk": risk,
        }
        with tempfile.TemporaryDirectory() as tmp:
            WebGenerator(output_dir=tmp).generate(payload)
            with open(os.path.join(tmp, "text.html"), encoding="utf-8") as f:
                text_html = f.read()
        for token in ("refreshLiveScan(true)", "renderTextStaleState", "sanitizeTextNode", 'id="text-live-payload"', 'id="verdict-guide"', "panel-box-violet"):
            self.assertIn(token, text_html)
        for removed in ("view-switcher", "[HUD]", "[JSON]", "[DELTA]", "[PROMPT]"):
            self.assertNotIn(removed, text_html)

        radar_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".github", "workflows", "radar.yml")
        with open(radar_path, encoding="utf-8") as f:
            radar_yml = f.read()
        for cron_expr in ("2,32 * * * *", "8,38 * * * *", "15,45 * * * *", "23,53 * * * *"):
            self.assertIn(cron_expr, radar_yml)
        self.assertIn("needs.build.outputs.skip != 'true'", radar_yml)

    def test_section5_sidecar_macro_anchors_and_045_cluster_clearance(self):
        from engine.fetcher import MarketDataFetcher

        fetcher = MarketDataFetcher()
        # Craft 40 closed 4H klines where an offset bin lands only +0.02% ($12) above spot ($61,289.62)
        spot = 61289.62
        near_low = 61300.0 / 1.008  # target_liq = 61,300.0 (+0.02% from spot)
        closed_4h = []
        for i in range(40):
            h = 64000.0 + (i * 50.0)
            l = near_low if i == 0 else (58500.0 + (i * 40.0))
            c = 61200.0 + (i * 15.0)
            v = 1200.0 + (i * 10.0)
            closed_4h.append([i * 14400000, c, h, l, c, v, (i + 1) * 14400000 - 1, 0, 0, v * 0.5])

        clusters = fetcher._calc_liquidation_clusters(spot, closed_4h, total_oi=85000.0)
        for c in clusters:
            self.assertGreaterEqual(
                c.distance_pct,
                0.45,
                f"Cluster {c.side} at ${c.price_level} is too close ({c.distance_pct}% < 0.45% micro-straddle floor)",
            )

        # Verify 30D macro anchors (30D VWAP, 30D Volume Profile POCs, 30D Realized Vol)
        closed_daily = []
        for d in range(35):
            # Two distinct volume clusters around $61,000 and $65,000
            px = 61000.0 + (d % 5) * 120.0 if d < 20 else 65000.0 + (d % 4) * 110.0
            vol = 28000.0 if d in (10, 25) else 12000.0
            closed_daily.append([d * 86400000, px, px * 1.01, px * 0.99, px, vol, (d + 1) * 86400000 - 1, 0, 0, vol * 0.5])

        macro = fetcher._calc_30d_macro_anchors(closed_daily, closed_4h)
        self.assertIsNotNone(macro["vwap_30d"])
        self.assertGreater(macro["vwap_30d"], 50000.0)
        self.assertIsNotNone(macro["vpoc_30d_primary"])
        self.assertIsNotNone(macro["vpoc_30d_secondary"])
        self.assertGreaterEqual(
            abs(macro["vpoc_30d_primary"] - macro["vpoc_30d_secondary"]) / macro["vpoc_30d_primary"],
            0.015,
        )
        self.assertIsNotNone(macro["realized_vol_30d_pct"])
        self.assertGreater(macro["realized_vol_30d_pct"], 0.0)

        # Verify Section 5 in blind prompt and Feed 5 in text.html
        metrics, sample_clusters = _make_sample_inputs()
        metrics.coinbase_spot_price = 73425.17
        metrics.okx_spot_price = 73505.00
        metrics.coinbase_premium_usd = -84.12
        metrics.coinbase_premium_bps = -11.44
        metrics.vwap_30d = 70221.00
        metrics.vpoc_30d_primary = 75931.00
        metrics.vpoc_30d_secondary = 64748.00
        metrics.realized_vol_30d_pct = 46.78
        metrics.implied_vol_dvol_pct = 47.70
        metrics.variance_premium_pts = 0.92

        regime = RegimeClassifier().classify(metrics, sample_clusters)
        risk = RiskManager().evaluate_risk(regime)
        payload = {
            "timestamp": "2026-11-24T00:32:00+00:00",
            "symbol": "BTCUSDT",
            "regime": asdict(regime),
            "metrics": asdict(metrics),
            "risk": risk,
        }
        with tempfile.TemporaryDirectory() as tmp:
            gen = WebGenerator(output_dir=tmp)
            gen.generate(payload)
            blind_prompt = gen._build_blind_llm_prompt(payload)
            with open(os.path.join(tmp, "text.html"), encoding="utf-8") as fh:
                text_html = fh.read()

        self.assertIn("SECTION 5 • CROSS-VENUE & MACRO CONTEXT", blind_prompt)
        self.assertIn("Coinbase Premium: -84.12 USD / -11.44 bps", blind_prompt)
        self.assertIn("30D VWAP $70,221.00", blind_prompt)
        self.assertIn("Primary $75,931 / Secondary $64,748", blind_prompt)
        self.assertIn("Deribit Implied DVOL 47.70% vs 30D Realized Vol 46.78%", blind_prompt)
        self.assertIn("Feed 5 &bull; Cross-Venue &amp; Macro Sidecar:", text_html)
        self.assertIn("-84.12 USD (-11.4 bps)", text_html)


if __name__ == "__main__":
    unittest.main()
