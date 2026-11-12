from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import datetime

@dataclass
class LiquidationCluster:
    price_level: float
    distance_pct: float
    estimated_vol_usd: float
    side: str  # "upper" or "lower"
    cluster_type: str  # e.g., "Modeled Short Liquidity Pool"
    distance_atr: Optional[float] = None  # Deprecated under DIBSE Rule 4 (zero ATR smoothing)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class LSCEState:
    """Bidirectional Liquidation Sweep Confirmation Engine (LSCE) State Model."""
    status: str = "UNTESTED"  # UNTESTED, SWEEP_IN_PROGRESS, SWEEP_FAILED_BREAKDOWN, SWEEP_AND_RECLAIM_CONFIRMED, UPPER_SWEEP_IN_PROGRESS, UPPER_SWEEP_REJECTION_CONFIRMED
    side: str = "NONE"        # LOWER (Loop A), UPPER (Loop B), or NONE
    cluster_tested: str = "N/A"
    sweep_depth_pct: float = 0.0
    reclaim_level: float = 0.0
    spot_absorption: str = "Neutral"
    action_verdict: str = "Monitoring Loop A lower washout & Loop B upper squeeze."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MarketMetrics:
    price: float
    daily_vwap: float
    weekly_vwap: float

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

    # Empirical Return Momentum (zero smoothed oscillators)
    price_change_1h_pct: float
    price_change_24h_pct: float

    # Microstructure & Sentiment
    long_short_account_ratio: float
    top_trader_long_short_ratio: float
    taker_buy_sell_ratio: float
    bids_asks_depth_ratio: float

    # Closed 4H / 1H bar extremes (klines[:-1]) for bidirectional Loop A / Loop B structure
    swing_low_4h: float
    swing_high_4h: float
    base_floor: float
    capitulation_wick_low: float
    base_ceiling: float = 0.0
    euphoria_wick_high: float = 0.0
    closed_4h_bar_close_time: Optional[str] = None

    # Data Quality & Provenance
    data_quality: str = "LIVE"
    spot_data_source: str = "Binance Public Market-Data REST (data-api.binance.vision/api/v3)"
    futures_data_source: str = "Binance / OKX / Deribit / Kraken Public REST"
    etf_net_inflow_m: Optional[float] = None
    whale_inflow_proxy: Optional[float] = None
    oi_scope: str = "Single-Venue Perpetual Contract (venue-level, not total market OI)"
    ls_ratio_available: bool = True
    oi_history_available: bool = True
    ls_ratio_percentile_72h: Optional[float] = None

    # Excluded lagging/smoothed oscillators under DIBSE Rule 4 (kept None intentionally)
    ema_20d: Optional[float] = None
    ema_50d: Optional[float] = None
    ma_200d: Optional[float] = None
    atr: Optional[float] = None
    atr_compression_pct: Optional[float] = None
    atr_percentile_72h: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RegimeResult:
    # Simplified 5-Regime Radar + DIBSE Bidirectional Overlay
    regime: str
    regime_id: str
    name: str
    diagnosis: str
    playbook: str
    suitability: str
    sizing_factor: float
    action: str
    rotation: str  # "USDT -> BTC" (Loop A), "BTC -> USDT" (Loop B), "Hold Both Sleeves"
    entry_instruction: str
    stop_rule: str
    stop_price: float
    stop_distance_pct: float

    # Magnetic Clusters & Multi-Factor Preference
    nearest_upper_cluster: Optional[LiquidationCluster]
    nearest_lower_cluster: Optional[LiquidationCluster]
    dominant_magnet: str
    dominant_magnet_reason: str

    # Risk Management Rules (DIBSE Dual-Sleeve Sandbox, Percentage-based)
    risk_budget_ok: bool
    recommended_cash_deploy_pct: float
    target_btc_allocation_pct: float
    target_usdt_reserve_pct: float

    matched_criteria: List[str]
    notes: str

    # Majority-based scoring telemetry
    majority_score: str = ""
    config: str = ""

    # Plain-English Explanations
    plain_english_verdict: str = ""
    why_points: List[str] = field(default_factory=list)
    why_sizing_reason: str = ""
    why_stop_reason: str = ""

    data_quality: str = "LIVE"
    magnet_factors: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    # Bidirectional Sweep & Dual Imbalance & DIBSE Protocol Fields
    immediate_imbalance_ratio: float = 1.0
    total_ladder_lower_vol: float = 0.0
    total_ladder_upper_vol: float = 0.0
    total_ladder_imbalance_ratio: float = 1.0
    lsce_status: str = "UNTESTED"
    lsce_detail: str = ""
    lsce_side: str = "NONE"
    disaster_stop_price: float = 0.0
    disaster_stop_distance_pct: float = 0.0
    structural_invalidation_level: float = 0.0
    liquidation_ladder: List[Dict[str, Any]] = field(default_factory=list)
    stop_placement_note: str = ""
    dibse_signal: str = "HOLD BOTH SLEEVES"
    dibse_action_headline: str = ""
    loop_a_zone: str = ""
    loop_b_zone: str = ""
    sleeve_allocation: str = "10% USDT Sleeve + 10% BTC Sleeve (20% Active Sandbox | 80% Untouched Core)"
    failure_protocol: str = (
        "Zero Stop-Losses | Loop A underwater -> HOLDING SPOT BTC INVENTORY (WAIT FOR > P_BUY) | "
        "Loop B bypassed -> HOLDING SPOT USDT INVENTORY (WAIT FOR < P_SELL)"
    )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if not d.get("config"):
            d["config"] = self.regime
        return d
