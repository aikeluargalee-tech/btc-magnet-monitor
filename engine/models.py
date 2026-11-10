from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import datetime

@dataclass
class LiquidationCluster:
    price_level: float
    distance_pct: float
    distance_atr: float
    estimated_vol_usd: float
    side: str  # "upper" or "lower"
    cluster_type: str  # e.g., "Modeled Short Liquidity Pool"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class LSCEState:
    """Liquidation Sweep Confirmation Engine (LSCE) State Model."""
    status: str = "UNTESTED"  # UNTESTED, SWEEP_IN_PROGRESS, SWEEP_FAILED_BREAKDOWN, SWEEP_AND_RECLAIM_CONFIRMED
    cluster_tested: str = "N/A"
    sweep_depth_pct: float = 0.0
    reclaim_level: float = 0.0
    spot_absorption: str = "Neutral"
    action_verdict: str = "Wait for sweep confirmation"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MarketMetrics:
    price: float
    daily_vwap: float
    weekly_vwap: float
    ema_20d: float
    ema_50d: float
    ma_200d: float
    
    # Volume & CVD (Candle-aggregated taker volume)
    spot_vol_24h: float
    spot_vol_ma20: float
    spot_vol_ratio: float
    spot_cvd_ratio: float
    spot_cvd_slope_7d: float
    spot_cvd_slope_14d: float
    perp_cvd_slope_24h: float
    perp_cvd_trend: str
    
    # Open Interest & Derivatives
    open_interest: float
    oi_change_1h_pct: float
    oi_change_4h_pct: float
    oi_change_24h_pct: float
    oi_change_3d_pct: float
    funding_rate: float
    funding_rate_annualized: float
    futures_basis_annualized: float
    
    # Volatility & Momentum
    atr: float
    atr_compression_pct: float
    price_change_1h_pct: float
    price_change_24h_pct: float
    
    # Microstructure & Sentiment
    long_short_account_ratio: float
    top_trader_long_short_ratio: float
    taker_buy_sell_ratio: float
    bids_asks_depth_ratio: float

    # Raw swing extremes for stop calculation
    swing_low_4h: float
    swing_high_4h: float
    base_floor: float
    capitulation_wick_low: float

    # Data Quality & Provenance
    data_quality: str = "LIVE"
    spot_data_source: str = "Binance Vision API (Kline Taker Volume Delta)"
    futures_data_source: str = "Binance / Deribit / Kraken Futures"
    etf_net_inflow_m: Optional[float] = None
    whale_inflow_proxy: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RegimeResult:
    # Simplified 5-Regime Radar
    regime: str  # e.g. "Range / Liquidation Magnet", "Spot-Led Expansion", etc.
    regime_id: str  # e.g. "RANGE_LIQUIDATION_MAGNET"
    name: str  # Friendly name
    diagnosis: str  # e.g. "Positioning imbalance and forced liquidations dominate"
    playbook: str  # e.g. "Trade the Magnet (0.5x–0.75x)"
    suitability: str
    sizing_factor: float
    action: str
    rotation: str  # "USDT -> BTC", "BTC -> USDT", "Remain USDT"
    entry_instruction: str
    stop_rule: str
    stop_price: float
    stop_distance_pct: float
    
    # Magnetic Clusters & Multi-Factor Preference (Active in Range / Liquidation Magnet)
    nearest_upper_cluster: Optional[LiquidationCluster]
    nearest_lower_cluster: Optional[LiquidationCluster]
    dominant_magnet: str
    dominant_magnet_reason: str
    
    # Risk Management Rules (Percentage-based, privacy-first)
    risk_budget_ok: bool
    recommended_cash_deploy_pct: float
    target_btc_allocation_pct: float
    target_usdt_reserve_pct: float
    
    matched_criteria: List[str]
    notes: str
    
    # Majority-based scoring telemetry
    majority_score: str = ""
    config: str = ""  # Backward-compatible alias for regime

    # Plain-English Explanations for Beginners (95% User Base)
    plain_english_verdict: str = ""
    why_points: List[str] = field(default_factory=list)
    why_sizing_reason: str = ""
    why_stop_reason: str = ""

    data_quality: str = "LIVE"
    magnet_factors: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    # Institutional Upgrades (LSCE & Dual Imbalance & Disaster Stop)
    immediate_imbalance_ratio: float = 1.0
    total_ladder_lower_vol: float = 0.0
    total_ladder_upper_vol: float = 0.0
    total_ladder_imbalance_ratio: float = 1.0
    lsce_status: str = "UNTESTED"  # UNTESTED, SWEEP_IN_PROGRESS, SWEEP_FAILED_BREAKDOWN, SWEEP_AND_RECLAIM_CONFIRMED
    lsce_detail: str = ""
    disaster_stop_price: float = 0.0
    disaster_stop_distance_pct: float = 0.0
    structural_invalidation_level: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not d.get("config"):
            d["config"] = self.regime
        return d
