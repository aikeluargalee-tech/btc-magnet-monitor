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
    config: str  # "Config A" through "Config J", or "DATA_INCOMPLETE"
    name: str
    diagnosis: str
    regime_type: str
    suitability: str
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
    
    # Risk Management Rules (Percentage-based, privacy-first)
    risk_budget_ok: bool
    recommended_cash_deploy_pct: float
    target_btc_allocation_pct: float
    target_usdt_reserve_pct: float
    
    matched_criteria: List[str]
    notes: str
    data_quality: str = "LIVE"
    magnet_factors: Dict[str, str] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
