import os
import time
import datetime
import requests
from typing import List, Dict, Any, Tuple
from engine.models import MarketMetrics, LiquidationCluster

class MarketDataFetcher:
    """Fetches and computes live market metrics for BTC positioning mechanics."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BTC-Magnet/1.0 (Observable-Positioning-Engine)"
        })

    def _get_json(self, url: str, params: Dict[str, Any] = None) -> Any:
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch {url}: {e}")

    def fetch_metrics(self) -> Tuple[MarketMetrics, List[LiquidationCluster]]:
        """Fetch all necessary market data and compute diagnostic metrics."""
        # 1. Spot 24h Ticker & Current Price
        ticker_data = self._get_json("https://api.binance.com/api/v3/ticker/24hr", {"symbol": "BTCUSDT"})
        current_price = float(ticker_data["lastPrice"])
        price_change_24h_pct = float(ticker_data["priceChangePercent"])

        # 2. Spot Daily Klines (200 days for 200D MA, 50D EMA, 20D EMA, Vol MA)
        # Kline format: [open_time, open, high, low, close, volume, close_time, quote_vol, trades, taker_buy_base, taker_buy_quote, ignore]
        daily_klines = self._get_json("https://api.binance.com/api/v3/klines", {
            "symbol": "BTCUSDT",
            "interval": "1d",
            "limit": 200
        })

        # 3. Spot 4H Klines (for swing points, local structure, and weekly VWAP)
        four_h_klines = self._get_json("https://api.binance.com/api/v3/klines", {
            "symbol": "BTCUSDT",
            "interval": "4h",
            "limit": 60
        })

        # 4. Spot 1H Klines (for ATR, daily VWAP, recent price changes)
        one_h_klines = self._get_json("https://api.binance.com/api/v3/klines", {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "limit": 100
        })

        # 5. Futures 1H Klines (for Perp CVD)
        fapi_klines = self._get_json("https://fapi.binance.com/fapi/v1/klines", {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "limit": 72
        })

        # 6. Futures Premium Index & Funding Rate
        premium_data = self._get_json("https://fapi.binance.com/fapi/v1/premiumIndex", {"symbol": "BTCUSDT"})
        mark_price = float(premium_data["markPrice"])
        index_price = float(premium_data["indexPrice"])
        funding_rate = float(premium_data["lastFundingRate"])  # e.g., 0.0001 = 0.01%
        funding_rate_annualized = funding_rate * 3 * 365 * 100  # 3 funding periods per day

        # Basis annualized
        futures_basis_annualized = ((mark_price - index_price) / index_price) * 100 * (365 / 30)

        # 7. Futures Open Interest History
        oi_hist = self._get_json("https://fapi.binance.com/futures/data/openInterestHist", {
            "symbol": "BTCUSDT",
            "period": "1h",
            "limit": 73
        })
        current_oi = float(oi_hist[-1]["sumOpenInterest"]) if oi_hist else 0.0
        oi_1h_ago = float(oi_hist[-2]["sumOpenInterest"]) if len(oi_hist) >= 2 else current_oi
        oi_4h_ago = float(oi_hist[-5]["sumOpenInterest"]) if len(oi_hist) >= 5 else current_oi
        oi_24h_ago = float(oi_hist[-25]["sumOpenInterest"]) if len(oi_hist) >= 25 else current_oi
        oi_72h_ago = float(oi_hist[0]["sumOpenInterest"]) if len(oi_hist) >= 72 else current_oi

        oi_change_1h_pct = ((current_oi - oi_1h_ago) / oi_1h_ago * 100) if oi_1h_ago > 0 else 0.0
        oi_change_4h_pct = ((current_oi - oi_4h_ago) / oi_4h_ago * 100) if oi_4h_ago > 0 else 0.0
        oi_change_24h_pct = ((current_oi - oi_24h_ago) / oi_24h_ago * 100) if oi_24h_ago > 0 else 0.0
        oi_change_3d_pct = ((current_oi - oi_72h_ago) / oi_72h_ago * 100) if oi_72h_ago > 0 else 0.0

        # 8. Sentiment & Long/Short Ratios
        ls_account = self._get_json("https://fapi.binance.com/futures/data/globalLongShortAccountRatio", {
            "symbol": "BTCUSDT",
            "period": "1h",
            "limit": 1
        })
        long_short_account_ratio = float(ls_account[-1]["longShortRatio"]) if ls_account else 1.0

        top_trader = self._get_json("https://fapi.binance.com/futures/data/topLongShortPositionRatio", {
            "symbol": "BTCUSDT",
            "period": "1h",
            "limit": 1
        })
        top_trader_long_short_ratio = float(top_trader[-1]["longShortRatio"]) if top_trader else 1.0

        taker_ratio_data = self._get_json("https://fapi.binance.com/futures/data/takerlongshortRatio", {
            "symbol": "BTCUSDT",
            "period": "1h",
            "limit": 1
        })
        taker_buy_sell_ratio = float(taker_ratio_data[-1]["buySellRatio"]) if taker_ratio_data else 1.0

        # 9. Order Book Depth Ratio (Bids vs Asks within ±1.5% of current price)
        depth_data = self._get_json("https://api.binance.com/api/v3/depth", {
            "symbol": "BTCUSDT",
            "limit": 100
        })
        bids_sum = sum(float(qty) for price, qty in depth_data["bids"] if float(price) >= current_price * 0.985)
        asks_sum = sum(float(qty) for price, qty in depth_data["asks"] if float(price) <= current_price * 1.015)
        bids_asks_depth_ratio = (bids_sum / asks_sum) if asks_sum > 0 else 1.0

        # --- Compute Technical Indicators ---

        # Closes & Volumes for daily
        daily_closes = [float(k[4]) for k in daily_klines]
        daily_volumes = [float(k[5]) for k in daily_klines]
        
        # 200D MA
        ma_200d = sum(daily_closes[-200:]) / len(daily_closes[-200:]) if len(daily_closes) >= 200 else daily_closes[-1]

        # EMAs (20D and 50D)
        ema_20d = self._calc_ema(daily_closes, 20)
        ema_50d = self._calc_ema(daily_closes, 50)

        # Spot 24h Volume & 20D Volume MA
        spot_vol_24h = float(ticker_data["volume"])
        vol_slice_20d = daily_volumes[-21:-1] if len(daily_volumes) >= 21 else daily_volumes
        spot_vol_ma20 = (sum(vol_slice_20d) / len(vol_slice_20d)) if vol_slice_20d else spot_vol_24h
        spot_vol_ratio = (spot_vol_24h / spot_vol_ma20) if spot_vol_ma20 > 0 else 1.0

        # --- VWAP Calculation ---
        daily_vwap = self._calc_vwap_from_midnight(one_h_klines)
        weekly_vwap = self._calc_vwap_from_monday(four_h_klines)

        # --- ATR(14) on 1H klines ---
        atr, atr_compression_pct = self._calc_atr(one_h_klines, period=14)

        # Price change 1h
        price_1h_ago = float(one_h_klines[-2][4]) if len(one_h_klines) >= 2 else current_price
        price_change_1h_pct = ((current_price - price_1h_ago) / price_1h_ago) * 100

        # --- Spot CVD & Futures CVD ---
        spot_cvd_ratio, spot_cvd_7d, spot_cvd_14d = self._calc_spot_cvd(daily_klines, one_h_klines)
        perp_cvd_slope, perp_cvd_trend = self._calc_perp_cvd(fapi_klines)

        # Swing Extremes (for Stop calculation)
        swing_low_4h = min(float(k[3]) for k in four_h_klines[-6:])  # lowest of last 24h (6x4h)
        swing_high_4h = max(float(k[2]) for k in four_h_klines[-6:])
        base_floor = min(float(k[3]) for k in four_h_klines[-18:])  # lowest over last 72h
        capitulation_wick_low = min(float(k[3]) for k in one_h_klines[-24:])

        # Whale inflow proxy (derived from high-volume taker sell bars vs normal)
        whale_inflow_proxy = 0.50  # baseline neutral

        metrics = MarketMetrics(
            price=current_price,
            daily_vwap=daily_vwap,
            weekly_vwap=weekly_vwap,
            ema_20d=ema_20d,
            ema_50d=ema_50d,
            ma_200d=ma_200d,
            spot_vol_24h=spot_vol_24h,
            spot_vol_ma20=spot_vol_ma20,
            spot_vol_ratio=spot_vol_ratio,
            spot_cvd_ratio=spot_cvd_ratio,
            spot_cvd_slope_7d=spot_cvd_7d,
            spot_cvd_slope_14d=spot_cvd_14d,
            perp_cvd_slope_24h=perp_cvd_slope,
            perp_cvd_trend=perp_cvd_trend,
            open_interest=current_oi,
            oi_change_1h_pct=oi_change_1h_pct,
            oi_change_4h_pct=oi_change_4h_pct,
            oi_change_24h_pct=oi_change_24h_pct,
            oi_change_3d_pct=oi_change_3d_pct,
            funding_rate=funding_rate,
            funding_rate_annualized=funding_rate_annualized,
            futures_basis_annualized=futures_basis_annualized,
            atr=atr,
            atr_compression_pct=atr_compression_pct,
            price_change_1h_pct=price_change_1h_pct,
            price_change_24h_pct=price_change_24h_pct,
            long_short_account_ratio=long_short_account_ratio,
            top_trader_long_short_ratio=top_trader_long_short_ratio,
            taker_buy_sell_ratio=taker_buy_sell_ratio,
            bids_asks_depth_ratio=bids_asks_depth_ratio,
            whale_inflow_proxy=whale_inflow_proxy,
            etf_net_inflow_m=120.0,  # default placeholder or external source
            swing_low_4h=swing_low_4h,
            swing_high_4h=swing_high_4h,
            base_floor=base_floor,
            capitulation_wick_low=capitulation_wick_low
        )

        # Compute Liquidation Clusters
        clusters = self._calc_liquidation_clusters(current_price, atr, four_h_klines, current_oi)

        return metrics, clusters

    # --- Math Helpers ---

    def _calc_ema(self, series: List[float], period: int) -> float:
        if not series:
            return 0.0
        alpha = 2 / (period + 1)
        ema = series[0]
        for val in series[1:]:
            ema = alpha * val + (1 - alpha) * ema
        return ema

    def _calc_vwap_from_midnight(self, klines_1h: List[List[Any]]) -> float:
        """Calculate Daily VWAP starting from 00:00 UTC."""
        now = datetime.datetime.now(datetime.timezone.utc)
        midnight_utc = datetime.datetime(now.year, now.month, now.day, tzinfo=datetime.timezone.utc)
        midnight_ms = int(midnight_utc.timestamp() * 1000)

        cum_vol = 0.0
        cum_pv = 0.0
        for k in klines_1h:
            open_time = int(k[0])
            if open_time >= midnight_ms:
                high = float(k[2])
                low = float(k[3])
                close = float(k[4])
                vol = float(k[5])
                typical = (high + low + close) / 3.0
                cum_pv += typical * vol
                cum_vol += vol

        if cum_vol > 0:
            return cum_pv / cum_vol
        return float(klines_1h[-1][4])

    def _calc_vwap_from_monday(self, klines_4h: List[List[Any]]) -> float:
        """Calculate Weekly VWAP starting from Monday 00:00 UTC."""
        now = datetime.datetime.now(datetime.timezone.utc)
        monday = now - datetime.timedelta(days=now.weekday())
        monday_midnight = datetime.datetime(monday.year, monday.month, monday.day, tzinfo=datetime.timezone.utc)
        monday_ms = int(monday_midnight.timestamp() * 1000)

        cum_vol = 0.0
        cum_pv = 0.0
        for k in klines_4h:
            open_time = int(k[0])
            if open_time >= monday_ms:
                high = float(k[2])
                low = float(k[3])
                close = float(k[4])
                vol = float(k[5])
                typical = (high + low + close) / 3.0
                cum_pv += typical * vol
                cum_vol += vol

        if cum_vol > 0:
            return cum_pv / cum_vol
        return float(klines_4h[-1][4])

    def _calc_atr(self, klines_1h: List[List[Any]], period: int = 14) -> Tuple[float, float]:
        """Calculates 1H ATR and ATR compression % from recent 72h peak."""
        trs = []
        for i in range(1, len(klines_1h)):
            high = float(klines_1h[i][2])
            low = float(klines_1h[i][3])
            prev_close = float(klines_1h[i-1][4])
            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            trs.append(tr)

        if len(trs) < period:
            return 500.0, 0.0

        recent_atr = sum(trs[-period:]) / period
        peak_tr = max(trs[-72:]) if len(trs) >= 72 else max(trs)
        peak_atr = max(peak_tr * 0.8, recent_atr)
        compression_pct = max(0.0, ((peak_atr - recent_atr) / peak_atr) * 100) if peak_atr > 0 else 0.0

        return recent_atr, compression_pct

    def _calc_spot_cvd(self, daily_klines: List[List[Any]], one_h_klines: List[List[Any]]) -> Tuple[float, float, float]:
        """Calculate Spot CVD ratio (24h) and 7D / 14D slopes."""
        # 24H taker buy vs sell ratio
        taker_buy_24h = sum(float(k[9]) for k in one_h_klines[-24:])
        total_vol_24h = sum(float(k[5]) for k in one_h_klines[-24:])
        taker_sell_24h = max(1e-6, total_vol_24h - taker_buy_24h)
        spot_cvd_ratio = taker_buy_24h / taker_sell_24h

        # 7D CVD slope
        daily_deltas = [float(k[9]) - (float(k[5]) - float(k[9])) for k in daily_klines]
        slope_7d = sum(daily_deltas[-7:]) if len(daily_deltas) >= 7 else 0.0
        slope_14d = sum(daily_deltas[-14:]) if len(daily_deltas) >= 14 else 0.0

        return spot_cvd_ratio, slope_7d, slope_14d

    def _calc_perp_cvd(self, fapi_klines: List[List[Any]]) -> Tuple[float, str]:
        """Calculates 24h Perpetual CVD delta and trend descriptor."""
        deltas = [float(k[9]) - (float(k[5]) - float(k[9])) for k in fapi_klines]
        delta_24h = sum(deltas[-24:]) if len(deltas) >= 24 else 0.0
        delta_first_12h = sum(deltas[-24:-12]) if len(deltas) >= 24 else 0.0
        delta_last_12h = sum(deltas[-12:]) if len(deltas) >= 12 else 0.0

        if delta_last_12h > delta_first_12h + 500:
            trend = "surging"
        elif delta_24h > 0:
            trend = "positive"
        elif delta_last_12h < delta_first_12h - 500:
            trend = "lower_lows"
        else:
            trend = "declining"

        return delta_24h, trend

    def _calc_liquidation_clusters(
        self,
        current_price: float,
        atr: float,
        four_h_klines: List[List[Any]],
        total_oi: float
    ) -> List[LiquidationCluster]:
        """
        Derives high-probability magnetic liquidation clusters.
        Simulates liquidation pools across leverage tiers (100x, 50x, 25x, 10x)
        anchored to recent 4H swing highs (short stops/liqs) and swing lows (long stops/liqs),
        binned by price zones to find true density concentrations.
        """
        recent_highs = [float(k[2]) for k in four_h_klines[-40:]]
        recent_lows = [float(k[3]) for k in four_h_klines[-40:]]

        # Leverage multipliers: (leverage, liq_pct_offset, estimated_oi_share)
        tiers = [
            (100, 0.008, 0.15),
            (50, 0.018, 0.30),
            (25, 0.038, 0.35),
            (10, 0.095, 0.20),
        ]

        # Bins for accumulating liquidation volume ($)
        bin_size = max(100.0, round(atr * 0.25, -1))  # e.g., $100-$300 bins
        upper_bins: Dict[float, float] = {}
        lower_bins: Dict[float, float] = {}

        # 1. Short liquidations sit ABOVE price (from positions entered on drops or swing lows)
        for low_val in set(recent_lows):
            for _, offset, share in tiers:
                target_liq = low_val * (1.0 + offset)
                if target_liq > current_price:
                    binned_price = round(target_liq / bin_size) * bin_size
                    vol = (total_oi * 0.02 * current_price * share)
                    upper_bins[binned_price] = upper_bins.get(binned_price, 0.0) + vol

        # Also add short stops above recent swing highs
        for high_val in set(recent_highs):
            for offset in [0.005, 0.012, 0.025]:
                target_liq = high_val * (1.0 + offset)
                if target_liq > current_price:
                    binned_price = round(target_liq / bin_size) * bin_size
                    vol = (total_oi * 0.03 * current_price)
                    upper_bins[binned_price] = upper_bins.get(binned_price, 0.0) + vol

        # 2. Long liquidations sit BELOW price (from positions entered on breakout or swing highs)
        for high_val in set(recent_highs):
            for _, offset, share in tiers:
                target_liq = high_val * (1.0 - offset)
                if target_liq < current_price:
                    binned_price = round(target_liq / bin_size) * bin_size
                    vol = (total_oi * 0.02 * current_price * share)
                    lower_bins[binned_price] = lower_bins.get(binned_price, 0.0) + vol

        # Also add long stops below recent swing lows
        for low_val in set(recent_lows):
            for offset in [0.005, 0.012, 0.025]:
                target_liq = low_val * (1.0 - offset)
                if target_liq < current_price:
                    binned_price = round(target_liq / bin_size) * bin_size
                    vol = (total_oi * 0.03 * current_price)
                    lower_bins[binned_price] = lower_bins.get(binned_price, 0.0) + vol

        clusters = []

        # Sort upper bins by distance from current price (strictly > current_price)
        sorted_upper = [item for item in sorted(upper_bins.items(), key=lambda x: x[0]) if item[0] > current_price]
        for p, vol in sorted_upper[:2]:
            dist_pct = ((p - current_price) / current_price) * 100
            dist_atr = (p - current_price) / max(atr, 1.0)
            clusters.append(
                LiquidationCluster(
                    price_level=round(p, 2),
                    distance_pct=round(dist_pct, 2),
                    distance_atr=round(dist_atr, 2),
                    estimated_vol_usd=round(vol, 0),
                    side="upper",
                    cluster_type="Short Liquidation Magnet"
                )
            )

        # Sort lower bins by distance from current price (closest first, strictly < current_price)
        sorted_lower = [item for item in sorted(lower_bins.items(), key=lambda x: x[0], reverse=True) if item[0] < current_price]
        for p, vol in sorted_lower[:2]:
            dist_pct = ((current_price - p) / current_price) * 100
            dist_atr = (current_price - p) / max(atr, 1.0)
            clusters.append(
                LiquidationCluster(
                    price_level=round(p, 2),
                    distance_pct=round(dist_pct, 2),
                    distance_atr=round(dist_atr, 2),
                    estimated_vol_usd=round(vol, 0),
                    side="lower",
                    cluster_type="Long Liquidation Magnet"
                )
            )

        return clusters
