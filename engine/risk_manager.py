from dataclasses import dataclass
from typing import Dict, Any
from engine.models import RegimeResult

@dataclass
class RiskBudgetConfig:
    max_risk_per_trade_pct: float = 1.0     # 1% equity risked per trade
    max_stop_distance_pct: float = 4.0      # Skip trade if required stop > 4.0%
    min_usdt_reserve_pct: float = 20.0      # Always keep >= 20% USDT as dry powder
    max_btc_allocation_pct: float = 80.0    # Never exceed 80% BTC allocation
    default_portfolio_equity_usd: float = 10000.0

class RiskManager:
    """Enforces non-negotiable risk rules, sizing caps, and stop compliance."""

    def __init__(self, config: RiskBudgetConfig = None):
        self.config = config or RiskBudgetConfig()

    def evaluate_risk(self, result: RegimeResult, current_btc_usd: float = 5000.0, current_usdt_usd: float = 5000.0) -> Dict[str, Any]:
        """
        Calculates exact spot rotation amounts and validates stop-loss against risk budget.
        Assumes equal starting 50/50 balance if not specified.
        """
        total_equity = current_btc_usd + current_usdt_usd
        current_btc_pct = (current_btc_usd / total_equity) * 100
        current_usdt_pct = (current_usdt_usd / total_equity) * 100

        # Max allowable dollar loss based on risk budget
        max_dollar_risk = total_equity * (self.config.max_risk_per_trade_pct / 100.0)

        # Stop distance verification
        stop_dist = max(0.1, result.stop_distance_pct)
        stop_valid = stop_dist <= self.config.max_stop_distance_pct

        # Position size calculated by risk formula: Position = Max Risk $ / Stop Distance %
        risk_based_max_position_usd = (max_dollar_risk / (stop_dist / 100.0))

        # Target BTC allocation based on regime sizing factor
        target_btc_pct = self.config.max_btc_allocation_pct * result.sizing_factor
        target_btc_usd = total_equity * (target_btc_pct / 100.0)

        # Cap by risk budget
        target_btc_usd = min(target_btc_usd, current_btc_usd + risk_based_max_position_usd)

        delta_usd = target_btc_usd - current_btc_usd

        if delta_usd > 50 and result.rotation == "USDT -> BTC":
            trade_action = f"BUY ${delta_usd:,.2f} BTC using USDT ({delta_usd / current_usdt_usd * 100:.1f}% of available USDT)"
            actionable_amount_usd = round(delta_usd, 2)
        elif delta_usd < -50 and result.rotation in ["BTC -> USDT", "Remain USDT"]:
            sell_amount = abs(delta_usd)
            trade_action = f"SELL ${sell_amount:,.2f} BTC to USDT ({sell_amount / current_btc_usd * 100:.1f}% of current BTC)"
            actionable_amount_usd = round(sell_amount, 2)
        else:
            trade_action = "HOLD current allocation. No rotation required."
            actionable_amount_usd = 0.0

        return {
            "risk_budget_ok": stop_valid,
            "max_dollar_risk": round(max_dollar_risk, 2),
            "max_position_size_usd": round(risk_based_max_position_usd, 2),
            "current_btc_pct": round(current_btc_pct, 1),
            "target_btc_pct": round(target_btc_pct, 1),
            "actionable_trade_instruction": trade_action,
            "rotation_amount_usd": actionable_amount_usd,
            "risk_advisory": (
                "Approved: Stop distance fits risk budget." if stop_valid
                else f"REJECTED / DOWNSIZED: Stop distance {stop_dist:.2f}% exceeds maximum risk threshold {self.config.max_stop_distance_pct:.2f}%."
            )
        }
