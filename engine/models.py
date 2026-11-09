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
    cluster_type: str  # "Short Liquidation Magnet" or "Long Liquidation Magnet"

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
    
    # Volume & CVD
    spot_vol_24h: float
    spot_vol_ma20: float
    spot_vol_ratio: float  # spot_vol_24h / spot_vol_ma20
    spot_cvd_ratio: float  # taker buy / sell volume ratio (spot)
    spot_cvd_slope_7d: float
    spot_cvd_slope_14d: float
    perp_cvd_slope_24h: float
    perp_cvd_trend: str  # "positive", "negative", "surging", "lagging", "lower_lows"
    
    # Open Interest
    open_interest: float
    oi_change_1h_pct: float
    oi_change_4h_pct: float
    oi_change_24h_pct: float
    oi_change_3d_pct: float
    
    # Funding & Basis
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
    whale_inflow_proxy: float
    etf_net_inflow_m: float

    # Raw swing extremes for stop calculation
    swing_low_4h: float
    swing_high_4h: float
    base_floor: float
    capitulation_wick_low: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RegimeResult:
    config: str  # "Config A" through "Config J"
    name: str
    diagnosis: str
    regime_type: str  # "Range", "Trend", "Cascade", "Trap", etc.
    suitability: str  # "Core Operating Zone", "Secondary / Confirmatory", "Restricted / Cash"
    sizing_factor: float
    action: str
    rotation: str  # "USDT -> BTC", "BTC -> USDT", "Remain USDT"
    entry_instruction: str
    stop_rule: str
    stop_price: float
    stop_distance_pct: float
    
    # Magnetic Clusters & Multi-Factor Preference
    nearest_upper_cluster: Optional[LiquidationCluster]
    nearest_lower_cluster: Optional[LiquidationCluster]
    dominant_magnet: str
    dominant_magnet_reason: str
    
    # Risk Management Rules
    risk_budget_ok: bool
    max_spot_allocation_pct: float
    current_recommended_allocation_pct: float
    
    matched_criteria: List[str]
    notes: str
    magnet_factors: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return data
