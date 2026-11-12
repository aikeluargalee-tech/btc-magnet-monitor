from dataclasses import dataclass
from typing import Dict, Any
from engine.models import RegimeResult


@dataclass
class RiskBudgetConfig:
    active_sandbox_pct: float = 20.0   # 10% USDT Sleeve + 10% BTC Sleeve
    usdt_sleeve_pct: float = 10.0      # Loop A capital sleeve
    btc_sleeve_pct: float = 10.0       # Loop B capital sleeve
    untouched_core_pct: float = 80.0   # Long-term untouched core reserve


class RiskManager:
    """
    Enforces Dual-Inventory Bidirectional Swing Engine (DIBSE) Sleeve & Risk Invariants:
      - Permanent Dual-Asset Sandbox: 10% USDT Sleeve + 10% BTC Sleeve (20% Active | 80% Core).
      - Zero Leverage, Zero Margin, Zero Stop-Losses (Asymmetric Self-Healing Inventory).
      - Percentage-only allocation rules (never exposes private wallet dollar balances).
    """

    def __init__(self, config: RiskBudgetConfig = None):
        self.config = config or RiskBudgetConfig()

    def evaluate_risk(self, result: RegimeResult) -> Dict[str, Any]:
        """Evaluates dual-sleeve DIBSE deployment with zero forced stop-loss exposure."""
        if result.regime_id == "DATA_INCOMPLETE":
            return {
                "risk_budget_ok": False,
                "active_sandbox_pct": self.config.active_sandbox_pct,
                "usdt_sleeve_pct": self.config.usdt_sleeve_pct,
                "btc_sleeve_pct": self.config.btc_sleeve_pct,
                "untouched_core_pct": self.config.untouched_core_pct,
                "recommended_cash_deploy_pct": 0.0,
                "portfolio_risk_pct": 0.0,
                "effective_risk_budget_pct": 0.0,
                "target_btc_allocation_pct": self.config.btc_sleeve_pct,
                "target_usdt_reserve_pct": self.config.usdt_sleeve_pct,
                "actionable_trade_instruction": "DATA UNAVAILABLE — Hold both 10% USDT & 10% BTC sleeves passively.",
                "risk_advisory": "Standby: Verified primary exchange telemetry required before rotating sleeves.",
                "privacy_notice": "Position sizing is expressed in percentages to protect private portfolio balances.",
            }

        sizing = max(0.0, min(1.0, float(result.sizing_factor or 0.0)))
        dibse_sig = getattr(result, "dibse_signal", "HOLD BOTH SLEEVES")

        if dibse_sig == "LOOP A: USDT -> BTC" and sizing > 0.0:
            sleeve_pct = round(sizing * 100.0, 0)
            eq_pct = round(sizing * self.config.usdt_sleeve_pct, 1)
            target_btc = round(self.config.btc_sleeve_pct + eq_pct, 1)
            target_usdt = round(self.config.usdt_sleeve_pct - eq_pct, 1)
            deploy_pct = round(sizing * 100.0, 1)
            trade_action = (
                f"LOOP A (USDT -> BTC): Deploy {sleeve_pct:.0f}% of your 10% USDT Sleeve ({eq_pct:.1f}% total equity) "
                f"at support washout reclaim. Take profit strictly > P_buy. "
                f"If underwater: HOLDING SPOT BTC INVENTORY (WAIT FOR > P_BUY)."
            )
            advisory = (
                f"DIBSE Loop A ({sleeve_pct:.0f}% USDT Sleeve = {eq_pct:.1f}% equity | 80% Core Untouched | Zero Stop-Losses)."
            )
        elif dibse_sig == "LOOP B: BTC -> USDT" and sizing > 0.0:
            sleeve_pct = round(sizing * 100.0, 0)
            eq_pct = round(sizing * self.config.btc_sleeve_pct, 1)
            target_btc = round(self.config.btc_sleeve_pct - eq_pct, 1)
            target_usdt = round(self.config.usdt_sleeve_pct + eq_pct, 1)
            deploy_pct = round(sizing * 100.0, 1)
            trade_action = (
                f"LOOP B (BTC -> USDT): Rotate {sleeve_pct:.0f}% of your 10% BTC Sleeve ({eq_pct:.1f}% total equity) "
                f"into USDT on upper squeeze/resistance. Rebuy strictly < P_sell. "
                f"If bypassed higher: HOLDING SPOT USDT INVENTORY (WAIT FOR < P_SELL)."
            )
            advisory = (
                f"DIBSE Loop B ({sleeve_pct:.0f}% BTC Sleeve = {eq_pct:.1f}% equity | 80% Core Untouched | Zero Stop-Buys)."
            )
        else:
            target_btc = self.config.btc_sleeve_pct
            target_usdt = self.config.usdt_sleeve_pct
            deploy_pct = 0.0
            trade_action = (
                "HOLD BOTH SLEEVES: Keep permanent 10% USDT Sleeve + 10% BTC Sleeve balanced "
                "(80% Core Reserve untouched) until Loop A lower reclaim or Loop B upper squeeze triggers."
            )
            advisory = (
                "DIBSE Balanced Standby: 10% USDT + 10% BTC Active Sandbox | 80% Core Untouched | Zero Stop-Losses."
            )

        return {
            "risk_budget_ok": True,
            "active_sandbox_pct": self.config.active_sandbox_pct,
            "usdt_sleeve_pct": self.config.usdt_sleeve_pct,
            "btc_sleeve_pct": self.config.btc_sleeve_pct,
            "untouched_core_pct": self.config.untouched_core_pct,
            "recommended_cash_deploy_pct": deploy_pct,
            "portfolio_risk_pct": 0.0,
            "effective_risk_budget_pct": 0.0,
            "target_btc_allocation_pct": target_btc,
            "target_usdt_reserve_pct": target_usdt,
            "actionable_trade_instruction": trade_action,
            "risk_advisory": advisory,
            "privacy_notice": "Position sizing is expressed in percentages to protect private portfolio balances.",
        }
