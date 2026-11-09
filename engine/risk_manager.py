from dataclasses import dataclass
from typing import Dict, Any
from engine.models import RegimeResult

@dataclass
class RiskBudgetConfig:
    max_risk_per_trade_pct: float = 1.0     # 1% equity risked per trade
    max_stop_distance_pct: float = 3.5      # Refuse trade if required stop > 3.5%
    min_usdt_reserve_pct: float = 20.0      # Always maintain >= 20% dry powder reserve
    max_btc_allocation_pct: float = 80.0    # Never exceed 80% total BTC allocation

class RiskManager:
    """
    Enforces non-negotiable risk rules, sizing caps, and stop compliance.
    Strict Privacy & Data Integrity:
      - Does NOT assume or expose private portfolio dollar balances ($10,000, etc.).
      - Computes strict percentage allocations and sizing multipliers.
      - Dollar conversions are executed strictly on the user's private client/mobile app.
    """

    def __init__(self, config: RiskBudgetConfig = None):
        self.config = config or RiskBudgetConfig()

    def evaluate_risk(self, result: RegimeResult) -> Dict[str, Any]:
        """Calculates percentage spot deployment and validates stop-loss against risk budget."""
        stop_dist = max(0.01, result.stop_distance_pct)
        stop_valid = stop_dist <= self.config.max_stop_distance_pct

        sizing = result.sizing_factor
        target_btc_pct = round(self.config.max_btc_allocation_pct * sizing, 1)
        target_usdt_pct = round(100.0 - target_btc_pct, 1)

        # Cash deployment percentage
        cash_deploy_pct = round(sizing * 100.0, 1)

        if not stop_valid:
            trade_action = f"REJECTED / WITHHELD: Structural stop distance ({stop_dist:.2f}%) exceeds maximum risk limit ({self.config.max_stop_distance_pct:.2f}%). Stand aside."
            advisory = f"WARNING: Risk threshold exceeded. Stop distance {stop_dist:.2f}% > {self.config.max_stop_distance_pct:.2f}%."
        elif result.rotation == "USDT -> BTC":
            trade_action = f"Deploy {cash_deploy_pct:.0f}% of your available USDT cash to buy spot BTC."
            advisory = f"Approved: Stop distance {stop_dist:.2f}% is within the {self.config.max_stop_distance_pct:.2f}% risk budget."
        elif result.rotation == "BTC -> USDT":
            sell_pct = 50 if sizing == 0.0 else round((1.0 - sizing) * 100)
            trade_action = f"Harvest / Sell {sell_pct}% of your BTC holdings into USDT cash."
            advisory = "Defensive rotation: Move to stablecoin cash."
        else:
            trade_action = "Maintain 100% USDT cash reserve. Strictly zero new buying."
            advisory = "Defensive stance: Cash preservation."

        return {
            "risk_budget_ok": stop_valid,
            "max_stop_distance_pct": self.config.max_stop_distance_pct,
            "recommended_cash_deploy_pct": cash_deploy_pct,
            "target_btc_allocation_pct": target_btc_pct,
            "target_usdt_reserve_pct": target_usdt_pct,
            "actionable_trade_instruction": trade_action,
            "risk_advisory": advisory,
            "privacy_notice": "Position sizing is expressed in percentages to protect private portfolio balances."
        }
