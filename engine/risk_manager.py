from dataclasses import dataclass
from typing import Dict, Any
from engine.models import RegimeResult

@dataclass
class RiskBudgetConfig:
    max_risk_per_trade_pct: float = 1.0     # 1% equity risked per trade
    max_stop_distance_pct: float = 4.5      # Refuse trade if required disaster stop > 4.5%
    min_usdt_reserve_pct: float = 20.0      # Always maintain >= 20% dry powder reserve
    max_btc_allocation_pct: float = 80.0    # Never exceed 80% total BTC allocation

class RiskManager:
    """
    Enforces non-negotiable risk rules, sizing caps, and stop compliance.
    Strict Privacy & Data Integrity:
      - Does NOT assume or expose private portfolio dollar balances ($10,000, etc.).
      - Computes strict percentage allocations and sizing multipliers.
      - Enforces that Position Sizing * Stop Distance <= 1.0% portfolio risk.
    """

    def __init__(self, config: RiskBudgetConfig = None):
        self.config = config or RiskBudgetConfig()

    def evaluate_risk(self, result: RegimeResult) -> Dict[str, Any]:
        """Calculates percentage spot deployment and validates stop-loss against risk budget."""
        stop_dist = max(0.01, result.stop_distance_pct)
        stop_valid = stop_dist <= self.config.max_stop_distance_pct

        raw_sizing = result.sizing_factor

        # Strict mathematical risk capping: Sizing * Stop_Distance <= 1.0% Max Risk
        if raw_sizing > 0.0 and stop_dist > 0.0:
            budget_max_sizing = round(self.config.max_risk_per_trade_pct / stop_dist, 2)
            sizing = min(raw_sizing, budget_max_sizing)
        else:
            sizing = 0.0

        target_btc_pct = round(self.config.max_btc_allocation_pct * sizing, 1)
        target_usdt_pct = round(100.0 - target_btc_pct, 1)

        # Cash deployment percentage
        cash_deploy_pct = round(sizing * 100.0, 1)
        effective_risk_pct = round(sizing * stop_dist, 2)

        if not stop_valid:
            trade_action = f"REJECTED / WITHHELD: Structural stop distance ({stop_dist:.2f}%) exceeds maximum risk limit ({self.config.max_stop_distance_pct:.2f}%). Stand aside in 100% USDT cash."
            advisory = f"WARNING: Risk threshold exceeded. Stop distance {stop_dist:.2f}% > {self.config.max_stop_distance_pct:.2f}%."
        elif result.rotation == "USDT -> BTC" and sizing > 0.0:
            trade_action = f"Deploy {cash_deploy_pct:.0f}% of your available USDT cash to buy spot BTC (Strictly capped at {effective_risk_pct:.2f}% total portfolio risk)."
            advisory = f"Approved: Risk capped at {effective_risk_pct:.2f}% (<= {self.config.max_risk_per_trade_pct:.2f}% risk budget). Stop distance: {stop_dist:.2f}%."
        elif result.rotation == "BTC -> USDT":
            sell_pct = 50 if raw_sizing == 0.0 else round((1.0 - raw_sizing) * 100)
            trade_action = f"Harvest / Sell {sell_pct}% of your BTC holdings into USDT cash."
            advisory = "Defensive rotation: Move to stablecoin cash."
        else:
            trade_action = "Maintain 100% USDT cash reserve. Strictly zero new buying."
            advisory = "Standby / Cash Preservation (0.00% Active Risk — no spot position open)."

        return {
            "risk_budget_ok": stop_valid and sizing > 0 if result.rotation == "USDT -> BTC" else stop_valid,
            "max_stop_distance_pct": self.config.max_stop_distance_pct,
            "recommended_cash_deploy_pct": cash_deploy_pct,
            "effective_risk_budget_pct": effective_risk_pct,
            "target_btc_allocation_pct": target_btc_pct,
            "target_usdt_reserve_pct": target_usdt_pct,
            "actionable_trade_instruction": trade_action,
            "risk_advisory": advisory,
            "privacy_notice": "Position sizing is expressed in percentages to protect private portfolio balances."
        }
