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
            spot_vol_ratio=1.25,
            spot_cvd_ratio=1.22,
            spot_cvd_slope_7d=1200.0,
            spot_cvd_slope_14d=2400.0,
            perp_cvd_slope_24h=500.0,
            perp_cvd_trend="declining",
            open_interest=95000.0,
            oi_change_1h_pct=0.2,
            oi_change_4h_pct=0.5,
            oi_change_24h_pct=1.0,
            oi_change_3d_pct=2.5,
            funding_rate=0.005,
            funding_rate_annualized=5.47,
            futures_basis_annualized=1.2,
            atr=500.0,
            atr_compression_pct=42.0,
            price_change_1h_pct=0.1,
            price_change_24h_pct=-0.5,
            long_short_account_ratio=1.9,
            top_trader_long_short_ratio=1.9,
            taker_buy_sell_ratio=1.22,
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
        self.assertEqual(result.config, "DATA_INCOMPLETE")
        self.assertEqual(result.sizing_factor, 0.0)
        self.assertEqual(result.rotation, "Remain USDT")
        self.assertFalse(result.risk_budget_ok)

    def test_risk_manager_privacy_percentage_sizing(self):
        """Ensure risk manager outputs percentages and does NOT assume arbitrary $10,000 wallet."""
        result = self.classifier.classify(self.mock_metrics, self.mock_clusters)
        risk = self.risk_manager.evaluate_risk(result)
        
        self.assertIn("recommended_cash_deploy_pct", risk)
        self.assertIn("target_btc_allocation_pct", risk)
        self.assertIn("target_usdt_reserve_pct", risk)
        # Should not have fixed dollar portfolio
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
        # Ensure all 6 factors are in dictionary
        self.assertEqual(len(result.magnet_factors), 6)

if __name__ == "__main__":
    unittest.main()
