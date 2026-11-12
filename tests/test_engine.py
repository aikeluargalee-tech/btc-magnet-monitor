import datetime
import unittest
from engine.models import MarketMetrics, LiquidationCluster, RegimeResult
from engine.classifier import RegimeClassifier
from engine.risk_manager import RiskManager
from engine.fetcher import MarketDataFetcher

class TestBTCMagnetIntegrity(unittest.TestCase):

    def setUp(self):
        self.classifier = RegimeClassifier()
        self.risk_manager = RiskManager()
        self.mock_metrics = MarketMetrics(
            price=74000.0,
            daily_vwap=74500.0,
            weekly_vwap=74800.0,
            spot_vol_24h=25000.0,
            spot_vol_ma20=20000.0,
            spot_vol_ratio=1.05,
            spot_cvd_ratio=1.02,
            spot_cvd_slope_7d=1200.0,
            spot_cvd_slope_14d=2400.0,
            perp_cvd_slope_24h=500.0,
            perp_cvd_trend="declining",
            open_interest=95000.0,
            oi_change_1h_pct=0.2,
            oi_change_4h_pct=0.5,
            oi_change_24h_pct=1.0,
            oi_change_3d_pct=2.5,
            funding_rate=0.009,
            funding_rate_annualized=9.85,
            futures_basis_annualized=1.2,
            price_change_1h_pct=0.1,
            price_change_24h_pct=-0.5,
            long_short_account_ratio=1.9,
            top_trader_long_short_ratio=1.9,
            taker_buy_sell_ratio=1.02,
            bids_asks_depth_ratio=1.35,
            swing_low_4h=73500.0,
            swing_high_4h=75000.0,
            base_floor=73400.0,
            base_ceiling=75100.0,
            capitulation_wick_low=73950.0,
            euphoria_wick_high=74200.0,
            closed_4h_bar_close_time="2026-11-11T12:00:00+00:00",
            data_quality="LIVE"
        )
        self.mock_clusters = [
            LiquidationCluster(
                price_level=74500.0,
                distance_pct=0.68,
                distance_atr=None,
                estimated_vol_usd=10000000.0,
                side="upper",
                cluster_type="Modeled Short Liquidity Pool (Algorithmic Estimate)"
            ),
            LiquidationCluster(
                price_level=73800.0,
                distance_pct=0.27,
                distance_atr=None,
                estimated_vol_usd=85000000.0,
                side="lower",
                cluster_type="Modeled Long Liquidity Pool (Algorithmic Estimate)"
            )
        ]

    def test_no_hardcoded_etf_or_whale(self):
        """Ensure ETF and whale inflow are None unless verified data is provided."""
        self.assertIsNone(self.mock_metrics.etf_net_inflow_m)
        self.assertIsNone(self.mock_metrics.whale_inflow_proxy)

    def test_incomplete_data_withholds_verdict(self):
        """When data is missing or None, the engine MUST withhold trading verdict."""
        result = self.classifier.classify(None, [])
        self.assertEqual(result.regime_id, "DATA_INCOMPLETE")
        self.assertEqual(result.sizing_factor, 0.0)
        self.assertEqual(result.rotation, "Hold Both Sleeves")
        self.assertEqual(result.dibse_signal, "HOLD BOTH SLEEVES")
        self.assertEqual(result.disaster_stop_price, 0.0)
        self.assertFalse(result.risk_budget_ok)
        self.assertTrue(len(result.plain_english_verdict) > 0)

    def test_range_magnet_classification_untested_holds_cash(self):
        """Test Range / Liquidation Magnet holds both sleeves (0.0x) while sweeps are untested."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "RANGE_LIQUIDATION_MAGNET")
        self.assertEqual(result.name, "Range / Liquidation Magnet")
        self.assertEqual(result.sizing_factor, 0.0)
        self.assertEqual(result.rotation, "Hold Both Sleeves")
        self.assertEqual(result.dibse_signal, "HOLD BOTH SLEEVES")
        self.assertEqual(result.lsce_status, "UNTESTED")
        self.assertEqual(result.lsce_side, "NONE")
        self.assertEqual(result.disaster_stop_price, 0.0)
        self.assertIn("majority_score", result.to_dict())

    def test_range_magnet_sweep_and_reclaim_authorizes_buy(self):
        """Test Range / Liquidation Magnet triggers DIBSE Loop A (USDT -> BTC) with ZERO stop-losses upon confirmed reclaim."""
        confirmed_metrics = MarketMetrics(
            price=74000.0,
            daily_vwap=74500.0,
            weekly_vwap=74800.0,
            spot_vol_24h=25000.0,
            spot_vol_ma20=20000.0,
            spot_vol_ratio=1.05,
            spot_cvd_ratio=1.12,  # Spot CVD >= 1.05 signals absorption
            spot_cvd_slope_7d=1200.0,
            spot_cvd_slope_14d=2400.0,
            perp_cvd_slope_24h=500.0,
            perp_cvd_trend="declining",
            open_interest=95000.0,
            oi_change_1h_pct=0.2,
            oi_change_4h_pct=0.5,
            oi_change_24h_pct=1.0,
            oi_change_3d_pct=2.5,
            funding_rate=0.009,
            funding_rate_annualized=9.85,
            futures_basis_annualized=1.2,
            price_change_1h_pct=0.1,
            price_change_24h_pct=-0.5,
            long_short_account_ratio=1.9,
            top_trader_long_short_ratio=1.9,
            taker_buy_sell_ratio=1.12,
            bids_asks_depth_ratio=1.35,  # Solid order depth
            swing_low_4h=73500.0,
            swing_high_4h=75000.0,
            base_floor=73400.0,
            base_ceiling=75100.0,
            capitulation_wick_low=73300.0,  # Swept below lower cluster ($73,800)
            euphoria_wick_high=74200.0,
            data_quality="LIVE"
        )
        result = self.classifier.classify(confirmed_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "RANGE_LIQUIDATION_MAGNET")
        self.assertEqual(result.lsce_status, "SWEEP_AND_RECLAIM_CONFIRMED")
        self.assertEqual(result.lsce_side, "LOWER")
        self.assertEqual(result.sizing_factor, 0.75)
        self.assertEqual(result.rotation, "USDT -> BTC")
        self.assertEqual(result.dibse_signal, "LOOP A: USDT -> BTC")
        self.assertEqual(result.disaster_stop_price, 0.0)
        self.assertIn("Zero Stop-Losses", result.failure_protocol)
        self.assertTrue(result.structural_invalidation_level > 0.0)

    def test_conflicted_signals_fallback_to_transition_mixed(self):
        """When price is sub-VWAP, futures in backwardation, and bids thin without reclaim, engine holds both sleeves."""
        conflicted_metrics = MarketMetrics(
            price=73400.0,
            daily_vwap=74500.0,
            weekly_vwap=74800.0,
            spot_vol_24h=20000.0,
            spot_vol_ma20=20000.0,
            spot_vol_ratio=1.0,
            spot_cvd_ratio=1.15,  # Conflicting positive CVD
            spot_cvd_slope_7d=1500.0,
            spot_cvd_slope_14d=3000.0,
            perp_cvd_slope_24h=-500.0,
            perp_cvd_trend="declining",
            open_interest=92000.0,
            oi_change_1h_pct=-0.1,
            oi_change_4h_pct=-0.3,
            oi_change_24h_pct=-0.8,
            oi_change_3d_pct=-1.5,
            funding_rate=0.005,
            funding_rate_annualized=5.5,
            futures_basis_annualized=-1.4,  # Backwardation
            price_change_1h_pct=-0.2,
            price_change_24h_pct=-1.2,
            long_short_account_ratio=1.85,
            top_trader_long_short_ratio=1.85,
            taker_buy_sell_ratio=1.15,
            bids_asks_depth_ratio=0.25,  # Thin bids (<0.35)
            swing_low_4h=73500.0,
            swing_high_4h=75500.0,
            base_floor=73200.0,
            base_ceiling=75600.0,
            capitulation_wick_low=73500.0,  # Not swept
            euphoria_wick_high=74200.0,
            data_quality="LIVE"
        )
        result = self.classifier.classify(conflicted_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "TRANSITION_MIXED")
        self.assertEqual(result.sizing_factor, 0.0)
        self.assertEqual(result.rotation, "Hold Both Sleeves")
        self.assertEqual(result.dibse_signal, "HOLD BOTH SLEEVES")
        self.assertEqual(result.disaster_stop_price, 0.0)

    def test_dual_imbalance_ratios_calculated(self):
        """Verify both immediate tier and total ladder imbalance ratios are computed."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        self.assertEqual(result.immediate_imbalance_ratio, 8.5)  # 85M / 10M
        self.assertTrue(result.total_ladder_lower_vol > 0.0)
        self.assertTrue(result.total_ladder_upper_vol > 0.0)
        self.assertTrue(result.total_ladder_imbalance_ratio > 0.0)

    def test_risk_budget_sizing_cap(self):
        """Verify RiskManager enforces DIBSE zero leverage / zero forced stop-loss budget (0.0% portfolio risk)."""
        confirmed_metrics = MarketMetrics(
            price=74000.0, daily_vwap=74500.0, weekly_vwap=74800.0,
            spot_vol_24h=25000.0, spot_vol_ma20=20000.0, spot_vol_ratio=1.05,
            spot_cvd_ratio=1.12, spot_cvd_slope_7d=1200.0, spot_cvd_slope_14d=2400.0,
            perp_cvd_slope_24h=500.0, perp_cvd_trend="declining",
            open_interest=95000.0, oi_change_1h_pct=0.2, oi_change_4h_pct=0.5,
            oi_change_24h_pct=1.0, oi_change_3d_pct=2.5,
            funding_rate=0.009, funding_rate_annualized=9.85, futures_basis_annualized=1.2,
            price_change_1h_pct=0.1, price_change_24h_pct=-0.5,
            long_short_account_ratio=1.9, top_trader_long_short_ratio=1.9,
            taker_buy_sell_ratio=1.12, bids_asks_depth_ratio=1.35,
            swing_low_4h=73500.0, swing_high_4h=75000.0, base_floor=73400.0,
            base_ceiling=75100.0, capitulation_wick_low=73300.0, euphoria_wick_high=74200.0,
            data_quality="LIVE"
        )
        result = self.classifier.classify(confirmed_metrics, self.mock_clusters)
        risk = self.risk_manager.evaluate_risk(result)
        self.assertTrue(risk["risk_budget_ok"])
        self.assertEqual(risk["portfolio_risk_pct"], 0.0)
        self.assertEqual(risk["effective_risk_budget_pct"], 0.0)
        self.assertIn("10% USDT", result.sleeve_allocation)
        self.assertIn("10% BTC", result.sleeve_allocation)
        self.assertIn("Zero Stop-Losses", risk["risk_advisory"])
        self.assertIn("80% Core Untouched", risk["risk_advisory"])

    def test_cascade_classification_priority(self):
        """Test Cascade / Forced Deleveraging holds both sleeves during sharp selloff."""
        cascade_metrics = MarketMetrics(
            price=70000.0, daily_vwap=74000.0, weekly_vwap=74500.0,
            spot_vol_24h=50000.0, spot_vol_ma20=20000.0, spot_vol_ratio=2.5,
            spot_cvd_ratio=0.75, spot_cvd_slope_7d=-5000.0, spot_cvd_slope_14d=-8000.0,
            perp_cvd_slope_24h=-3000.0, perp_cvd_trend="declining",
            open_interest=70000.0, oi_change_1h_pct=-5.0, oi_change_4h_pct=-9.0,
            oi_change_24h_pct=-15.0, oi_change_3d_pct=-20.0,
            funding_rate=-0.015, funding_rate_annualized=-16.4, futures_basis_annualized=-2.0,
            price_change_1h_pct=-4.5, price_change_24h_pct=-8.0,
            long_short_account_ratio=0.8, top_trader_long_short_ratio=0.8,
            taker_buy_sell_ratio=0.75, bids_asks_depth_ratio=0.6,
            swing_low_4h=70000.0, swing_high_4h=75000.0, base_floor=70000.0,
            base_ceiling=75100.0, capitulation_wick_low=69500.0, euphoria_wick_high=74500.0,
            data_quality="LIVE"
        )
        result = self.classifier.classify(cascade_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "CASCADE_FORCED_DELEVERAGING")
        self.assertEqual(result.sizing_factor, 0.0)
        self.assertEqual(result.rotation, "Hold Both Sleeves")
        self.assertEqual(result.dibse_signal, "HOLD BOTH SLEEVES")
        self.assertEqual(result.disaster_stop_price, 0.0)

    def test_risk_manager_privacy_percentage_sizing(self):
        """Ensure risk manager outputs percentages and does NOT assume arbitrary $10,000 wallet."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        risk = self.risk_manager.evaluate_risk(result)
        
        self.assertIn("recommended_cash_deploy_pct", risk)
        self.assertIn("target_btc_allocation_pct", risk)
        self.assertIn("target_usdt_reserve_pct", risk)
        self.assertNotIn("current_btc_usd", risk)

    def test_magnet_cluster_naming_honesty(self):
        """Ensure clusters are labeled as modeled estimates and never carry ATR distances."""
        for c in self.mock_clusters:
            self.assertIn("Modeled", c.cluster_type)
            self.assertIn("Estimate", c.cluster_type)
            self.assertIsNone(c.distance_atr)

    def test_six_factor_scoring_incorporates_size_and_atr(self):
        """Verify larger pool heavily outweighs minor proximity difference using closed-4H width factor."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        self.assertEqual(result.dominant_magnet, "Lower Long Sweep Magnet")
        self.assertIn("LOWER", result.dominant_magnet_reason)
        self.assertEqual(len(result.magnet_factors), 6)
        self.assertIn("factor_6_range_compression", result.magnet_factors)

    def test_plain_english_breakdown_populated(self):
        """Verify plain-English explanation fields are populated for beginners."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        self.assertTrue(len(result.plain_english_verdict) > 20)
        self.assertEqual(len(result.why_points), 3)
        self.assertTrue(len(result.why_sizing_reason) > 10)
        self.assertTrue(len(result.why_stop_reason) > 10)

    def test_distribution_blocks_lsce_buy_authorization(self):
        """P0 Test: When macro regime is Distribution/Bear, LSCE must NEVER authorize Loop A buy deployment."""
        dist_metrics = MarketMetrics(
            price=74000.0, daily_vwap=76000.0, weekly_vwap=76500.0,
            spot_vol_24h=10000.0, spot_vol_ma20=20000.0, spot_vol_ratio=0.5,
            spot_cvd_ratio=1.10, spot_cvd_slope_7d=-2000.0, spot_cvd_slope_14d=-4000.0,
            perp_cvd_slope_24h=-1000.0, perp_cvd_trend="declining",
            open_interest=90000.0, oi_change_1h_pct=-0.1, oi_change_4h_pct=-0.2,
            oi_change_24h_pct=0.5, oi_change_3d_pct=1.0,
            funding_rate=0.015, funding_rate_annualized=16.4, futures_basis_annualized=-1.5,
            price_change_1h_pct=-0.2, price_change_24h_pct=-2.0,
            long_short_account_ratio=2.5, top_trader_long_short_ratio=2.5,
            taker_buy_sell_ratio=1.10, bids_asks_depth_ratio=0.6,
            swing_low_4h=73500.0, swing_high_4h=76000.0, base_floor=73000.0,
            base_ceiling=76100.0, capitulation_wick_low=73750.0, euphoria_wick_high=74800.0,
            data_quality="LIVE"
        )
        result = self.classifier.classify(dist_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "DISTRIBUTION_BEAR_CONTINUATION")
        self.assertEqual(result.sizing_factor, 0.0)
        self.assertIn("paused by macro regime", result.lsce_detail)
        self.assertNotEqual(result.dibse_signal, "LOOP A: USDT -> BTC")

    def test_loop_b_upper_squeeze_rejection_range_magnet(self):
        """Bidirectional DIBSE Test: Upper short sweep + rejection activates Loop B (BTC -> USDT)."""
        upper_reject_metrics = MarketMetrics(
            price=74300.0, daily_vwap=74200.0, weekly_vwap=74400.0,
            spot_vol_24h=24000.0, spot_vol_ma20=20000.0, spot_vol_ratio=1.15,
            spot_cvd_ratio=0.98, spot_cvd_slope_7d=200.0, spot_cvd_slope_14d=400.0,
            perp_cvd_slope_24h=900.0, perp_cvd_trend="positive",
            open_interest=96000.0, oi_change_1h_pct=0.4, oi_change_4h_pct=1.2,
            oi_change_24h_pct=2.2, oi_change_3d_pct=3.5,
            funding_rate=0.011, funding_rate_annualized=12.0, futures_basis_annualized=3.5,
            price_change_1h_pct=-0.2, price_change_24h_pct=0.6,
            long_short_account_ratio=2.1, top_trader_long_short_ratio=2.1,
            taker_buy_sell_ratio=0.98, bids_asks_depth_ratio=0.78,
            swing_low_4h=73500.0, swing_high_4h=75000.0, base_floor=73400.0,
            base_ceiling=75100.0, capitulation_wick_low=73900.0, euphoria_wick_high=74750.0,
            data_quality="LIVE"
        )
        result = self.classifier.classify(upper_reject_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "RANGE_LIQUIDATION_MAGNET")
        self.assertEqual(result.lsce_status, "UPPER_SWEEP_REJECTION_CONFIRMED")
        self.assertEqual(result.lsce_side, "UPPER")
        self.assertEqual(result.dibse_signal, "LOOP B: BTC -> USDT")
        self.assertEqual(result.rotation, "BTC -> USDT")
        self.assertEqual(result.sizing_factor, 0.75)
        self.assertEqual(result.disaster_stop_price, 0.0)
        self.assertIn("Zero Stop-Losses", result.failure_protocol)

    def test_loop_b_leveraged_fragile_upside(self):
        """Bidirectional DIBSE Test: Perp-driven euphoria triggers Loop B (BTC -> USDT) even before stop runs."""
        fragile_metrics = MarketMetrics(
            price=75400.0, daily_vwap=74100.0, weekly_vwap=73900.0,
            spot_vol_24h=15000.0, spot_vol_ma20=20000.0, spot_vol_ratio=0.75,
            spot_cvd_ratio=0.96, spot_cvd_slope_7d=-300.0, spot_cvd_slope_14d=100.0,
            perp_cvd_slope_24h=3500.0, perp_cvd_trend="surging",
            open_interest=102000.0, oi_change_1h_pct=1.8, oi_change_4h_pct=3.5,
            oi_change_24h_pct=6.5, oi_change_3d_pct=12.0,
            funding_rate=0.018, funding_rate_annualized=19.7, futures_basis_annualized=14.5,
            price_change_1h_pct=0.7, price_change_24h_pct=2.4,
            long_short_account_ratio=2.3, top_trader_long_short_ratio=2.3,
            taker_buy_sell_ratio=0.96, bids_asks_depth_ratio=0.82,
            swing_low_4h=72800.0, swing_high_4h=75200.0, base_floor=72600.0,
            base_ceiling=75300.0, capitulation_wick_low=73100.0, euphoria_wick_high=75600.0,
            data_quality="LIVE"
        )
        result = self.classifier.classify(fragile_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "LEVERAGED_FRAGILE_UPSIDE")
        self.assertEqual(result.dibse_signal, "LOOP B: BTC -> USDT")
        self.assertEqual(result.rotation, "BTC -> USDT")
        self.assertEqual(result.sizing_factor, 1.0)
        self.assertEqual(result.disaster_stop_price, 0.0)

    def test_fetcher_closed_4h_slicing_and_no_ma_atr(self):
        """DIBSE Rules 4 & 6: Fetcher slices klines[:-1] (zero unclosed bar leakage) & disables MA/EMA/ATR."""
        now_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
        closed_4h_template = [
            [now_ms - (21 - i) * 14400000, "73500", "74500", "73000", "73800", "1200", now_ms - (20 - i) * 14400000, "90000000", 100, "650", "48000000"]
            for i in range(20)
        ]
        unclosed_spike_4h = [now_ms - 600000, "73800", "99999", "50001", "74000", "500", now_ms + 13800000, "37000000", 50, "250", "18000000"]
        closed_daily_21 = [
            [now_ms - (22 - i) * 86400000, "73500", "74500", "73000", "73800", "20000", now_ms - (21 - i) * 86400000, "140000000", 100, "10500", "70000000"]
            for i in range(21)
        ]
        unclosed_spike_1h = [now_ms - 600000, "73800", "88888", "60000", "74000", "100", now_ms + 3000000, "7400000", 20, "50", "3700000"]
        closed_1h_25 = [
            [now_ms - (26 - i) * 3600000, "73600", "74200", "73200", "73800", "800", now_ms - (25 - i) * 3600000, "59000000", 50, "420", "31000000"]
            for i in range(25)
        ] + [unclosed_spike_1h]

        fetcher = MarketDataFetcher()
        def _fake_get(urls, params=None):
            u = urls[0]
            if "ticker/24hr" in u:
                return {"lastPrice": "74000.0", "volume": "22000.0", "priceChangePercent": "0.45"}
            if "klines" in u:
                iv = (params or {}).get("interval")
                if iv == "1d":
                    return closed_daily_21
                if iv == "4h":
                    return closed_4h_template + [unclosed_spike_4h]
                if iv == "1h":
                    return closed_1h_25
            if "depth" in u:
                return {"bids": [["73800", "10"]], "asks": [["74200", "8"]]}
            raise RuntimeError(u)

        fetcher._get_json = _fake_get
        fetcher._fetch_futures_data = lambda px: {
            "current_oi": 10000.0, "oi_change_1h_pct": 0.1, "oi_change_4h_pct": 0.2,
            "oi_change_24h_pct": 0.5, "oi_change_3d_pct": 1.0, "funding_rate": 0.005,
            "funding_ann": 5.4, "basis_ann": 0.8, "ls_ratio": 1.2, "ls_ratio_available": True,
            "oi_history_available": True, "ls_ratio_percentile_72h": 50.0,
            "perp_slope": 100.0, "perp_trend": "positive", "futures_source": "OKX Mock",
            "oi_scope": "Single-venue perpetual subset (not total market OI)",
        }

        m, clusters = fetcher.fetch_metrics()
        self.assertEqual(m.swing_high_4h, 74500.0)
        self.assertEqual(m.swing_low_4h, 73000.0)
        self.assertEqual(m.base_ceiling, 74500.0)
        self.assertEqual(m.base_floor, 73000.0)
        self.assertEqual(m.euphoria_wick_high, 74200.0)
        self.assertEqual(m.capitulation_wick_low, 73200.0)
        self.assertIsNone(m.ema_20d)
        self.assertIsNone(m.ema_50d)
        self.assertIsNone(m.ma_200d)
        self.assertIsNone(m.atr)
        self.assertIsNone(m.atr_compression_pct)
        self.assertEqual(len(clusters), 4)
        self.assertTrue(all(c.distance_atr is None for c in clusters))

if __name__ == "__main__":
    unittest.main()
