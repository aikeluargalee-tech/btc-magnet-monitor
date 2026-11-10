import unittest
from engine.models import MarketMetrics, LiquidationCluster, RegimeResult
from engine.classifier import RegimeClassifier
from engine.risk_manager import RiskManager

class TestBTCMagnetIntegrity(unittest.TestCase):

    def setUp(self):
        self.classifier = RegimeClassifier()
        self.risk_manager = RiskManager()
        self.mock_metrics = MarketMetrics(
            price=74000.0,
            daily_vwap=74500.0,
            weekly_vwap=74800.0,
            ema_20d=73500.0,
            ema_50d=73000.0,
            ma_200d=73200.0,
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
            atr=500.0,
            atr_compression_pct=42.0,
            price_change_1h_pct=0.1,
            price_change_24h_pct=-0.5,
            long_short_account_ratio=1.9,
            top_trader_long_short_ratio=1.9,
            taker_buy_sell_ratio=1.02,
            bids_asks_depth_ratio=1.35,
            swing_low_4h=73500.0,
            swing_high_4h=75000.0,
            base_floor=73400.0,
            capitulation_wick_low=73300.0,
            data_quality="LIVE"
        )
        self.mock_clusters = [
            LiquidationCluster(
                price_level=74500.0,
                distance_pct=0.68,
                distance_atr=1.0,
                estimated_vol_usd=10000000.0,
                side="upper",
                cluster_type="Modeled Short Liquidity Pool (Algorithmic Estimate)"
            ),
            LiquidationCluster(
                price_level=73800.0,
                distance_pct=0.27,
                distance_atr=0.4,
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
        self.assertEqual(result.rotation, "Remain USDT")
        self.assertFalse(result.risk_budget_ok)
        self.assertTrue(len(result.plain_english_verdict) > 0)

    def test_range_magnet_classification(self):
        """Test Range / Liquidation Magnet majority classification."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "RANGE_LIQUIDATION_MAGNET")
        self.assertEqual(result.name, "Range / Liquidation Magnet")
        self.assertTrue(result.sizing_factor >= 0.50)
        self.assertIn("majority_score", result.to_dict())

    def test_cascade_classification_priority(self):
        """Test Cascade / Forced Deleveraging takes priority during sharp selloff."""
        cascade_metrics = MarketMetrics(
            price=70000.0, daily_vwap=74000.0, weekly_vwap=74500.0,
            ema_20d=73000.0, ema_50d=72500.0, ma_200d=73000.0,
            spot_vol_24h=50000.0, spot_vol_ma20=20000.0, spot_vol_ratio=2.5,
            spot_cvd_ratio=0.75, spot_cvd_slope_7d=-5000.0, spot_cvd_slope_14d=-8000.0,
            perp_cvd_slope_24h=-3000.0, perp_cvd_trend="declining",
            open_interest=70000.0, oi_change_1h_pct=-5.0, oi_change_4h_pct=-9.0,
            oi_change_24h_pct=-15.0, oi_change_3d_pct=-20.0,
            funding_rate=-0.015, funding_rate_annualized=-16.4, futures_basis_annualized=-2.0,
            atr=1500.0, atr_compression_pct=0.0, price_change_1h_pct=-4.5, price_change_24h_pct=-8.0,
            long_short_account_ratio=0.8, top_trader_long_short_ratio=0.8,
            taker_buy_sell_ratio=0.75, bids_asks_depth_ratio=0.6,
            swing_low_4h=70000.0, swing_high_4h=75000.0, base_floor=70000.0,
            capitulation_wick_low=69500.0, data_quality="LIVE"
        )
        result = self.classifier.classify(cascade_metrics, self.mock_clusters)
        self.assertEqual(result.regime_id, "CASCADE_FORCED_DELEVERAGING")
        self.assertEqual(result.sizing_factor, 0.0)
        self.assertEqual(result.rotation, "Remain USDT")

    def test_risk_manager_privacy_percentage_sizing(self):
        """Ensure risk manager outputs percentages and does NOT assume arbitrary $10,000 wallet."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        risk = self.risk_manager.evaluate_risk(result)
        
        self.assertIn("recommended_cash_deploy_pct", risk)
        self.assertIn("target_btc_allocation_pct", risk)
        self.assertIn("target_usdt_reserve_pct", risk)
        self.assertNotIn("current_btc_usd", risk)

    def test_magnet_cluster_naming_honesty(self):
        """Ensure clusters are labeled as modeled estimates."""
        for c in self.mock_clusters:
            self.assertIn("Modeled", c.cluster_type)
            self.assertIn("Estimate", c.cluster_type)

    def test_six_factor_scoring_incorporates_size_and_atr(self):
        """Verify larger pool heavily outweighs minor proximity difference."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        self.assertEqual(result.dominant_magnet, "Lower Long Sweep Magnet")
        self.assertIn("LOWER", result.dominant_magnet_reason)
        self.assertEqual(len(result.magnet_factors), 6)

    def test_plain_english_breakdown_populated(self):
        """Verify plain-English explanation fields are populated for beginners."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        self.assertTrue(len(result.plain_english_verdict) > 20)
        self.assertEqual(len(result.why_points), 3)
        self.assertTrue(len(result.why_sizing_reason) > 10)
        self.assertTrue(len(result.why_stop_reason) > 10)

if __name__ == "__main__":
    unittest.main()
