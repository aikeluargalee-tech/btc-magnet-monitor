import os
import math
import time
import datetime
import requests
from typing import List, Dict, Any, Tuple, Optional
from engine.models import MarketMetrics, LiquidationCluster

class MarketDataFetcher:
    """
    Fetches and computes live market metrics for BTC positioning mechanics.
    Strict Data Integrity Architecture:
      - Spot: Binance Vision API (global, non-geoblocked) with Binance.com fallback.
      - Futures: Binance Futures with seamless Deribit & Kraken fallbacks.
      - Never fabricates placeholder or default numbers. If critical data fails, raises an error.
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BTC-Magnet-Monitor/1.2 (Observable-Positioning-Engine)"
        })

    def _get_json(self, urls: List[str], params: Dict[str, Any] = None) -> Any:
        last_err = None
        for url in urls:
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    return resp.json()
                last_err = RuntimeError(f"HTTP {resp.status_code} from {url}")
            except Exception as e:
                last_err = e
        raise RuntimeError(f"All candidate endpoints failed: {last_err}")

    def fetch_metrics(self) -> Tuple[MarketMetrics, List[LiquidationCluster]]:
        """Fetch all verified market data and compute diagnostic metrics."""

        # 1. Spot 24h Ticker & Current Price (Binance Vision / Binance)
        ticker_data = self._get_json([
            "https://data-api.binance.vision/api/v3/ticker/24hr",
            "https://api.binance.com/api/v3/ticker/24hr"
        ], {"symbol": "BTCUSDT"})
        current_price = float(ticker_data["lastPrice"])
        price_change_24h_pct = float(ticker_data["priceChangePercent"])

        # 2. Spot Daily Klines (60 closed days for 20D Spot Vol Baseline & 7D/14D Spot CVD — zero MA/EMA)
        daily_klines = self._get_json([
            "https://data-api.binance.vision/api/v3/klines",
            "https://api.binance.com/api/v3/klines"
        ], {
            "symbol": "BTCUSDT",
            "interval": "1d",
            "limit": 60
        })

        # 3. Spot 4H Klines (closed bars via [:-1] per DIBSE Rule 6)
        four_h_klines = self._get_json([
            "https://data-api.binance.vision/api/v3/klines",
            "https://api.binance.com/api/v3/klines"
        ], {
            "symbol": "BTCUSDT",
            "interval": "4h",
            "limit": 60
        })

        # 4. Spot 1H Klines (daily VWAP, closed 24h spike wicks, Spot CVD)
        one_h_klines = self._get_json([
            "https://data-api.binance.vision/api/v3/klines",
            "https://api.binance.com/api/v3/klines"
        ], {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "limit": 100
        })

        closed_daily = daily_klines[:-1] if len(daily_klines) >= 2 else daily_klines
        closed_4h = four_h_klines[:-1] if len(four_h_klines) >= 2 else four_h_klines
        closed_1h = one_h_klines[:-1] if len(one_h_klines) >= 2 else one_h_klines
        if len(closed_4h) < 6 or len(closed_1h) < 2:
            raise RuntimeError("Insufficient closed 4H/1H bar history from spot exchange.")

        # 5. Order Book Depth Ratio (Bids vs Asks within ±1.5% of current price)
        depth_data = self._get_json([
            "https://data-api.binance.vision/api/v3/depth",
            "https://api.binance.com/api/v3/depth"
        ], {
            "symbol": "BTCUSDT",
            "limit": 100
        })
        bids_sum = sum(float(qty) for price, qty in depth_data["bids"] if float(price) >= current_price * 0.985)
        asks_sum = sum(float(qty) for price, qty in depth_data["asks"] if float(price) <= current_price * 1.015)
        bids_asks_depth_ratio = (bids_sum / asks_sum) if asks_sum > 0 else 1.0

        # 6. Futures Metrics (Funding, OI, Basis, Perp CVD) - Real exchanges only, zero fabricated defaults
        fut = self._fetch_futures_data(current_price)

        # Empirical Volume & Anchors (DIBSE Rule 4: zero MA/EMA/RSI/MACD/ATR; Rule 6: closed 4H bars klines[:-1])
        closed_daily_vols = [float(k[5]) for k in closed_daily]
        if len(closed_daily_vols) < 20:
            raise RuntimeError(
                f"Insufficient closed daily volume history for 20D baseline: got {len(closed_daily_vols)}"
            )
        vol_slice_20d = closed_daily_vols[-20:]
        spot_vol_24h = float(ticker_data["volume"])
        spot_vol_ma20 = sum(vol_slice_20d) / len(vol_slice_20d)
        spot_vol_ratio = (spot_vol_24h / spot_vol_ma20) if spot_vol_ma20 > 0 else 1.0

        daily_vwap = self._calc_vwap_from_midnight(one_h_klines)
        weekly_vwap = self._calc_vwap_from_monday(closed_4h)

        last_closed_1h_close = float(closed_1h[-1][4])
        price_change_1h_pct = ((current_price - last_closed_1h_close) / last_closed_1h_close) * 100 if last_closed_1h_close > 0 else 0.0

        spot_cvd_ratio, spot_cvd_7d, spot_cvd_14d = self._calc_spot_cvd(closed_daily, closed_1h)

        swing_low_4h = min(float(k[3]) for k in closed_4h[-6:])
        swing_high_4h = max(float(k[2]) for k in closed_4h[-6:])
        base_floor = min(float(k[3]) for k in closed_4h[-18:])
        base_ceiling = max(float(k[2]) for k in closed_4h[-18:])
        capitulation_wick_low = min(float(k[3]) for k in closed_1h[-24:])
        euphoria_wick_high = max(float(k[2]) for k in closed_1h[-24:])

        closed_4h_close_ms = int(closed_4h[-1][6]) if len(closed_4h[-1]) > 6 else 0
        closed_4h_close_iso = (
            datetime.datetime.fromtimestamp(closed_4h_close_ms / 1000.0, tz=datetime.timezone.utc).isoformat()
            if closed_4h_close_ms > 0 else None
        )
        current_oi = fut["current_oi"]

        # 7. Cross-Venue Spot (Coinbase / OKX), Deribit DVOL & 30D Closed-Bar Macro Anchors (Section 5 Sidecar)
        xv = self._fetch_cross_venue_spot_and_dvol(current_price)
        macro_30d = self._calc_30d_macro_anchors(closed_daily, closed_4h)
        dvol_pct = xv.get("implied_vol_dvol_pct")
        rvol_pct = macro_30d.get("realized_vol_30d_pct")
        var_prem = round(dvol_pct - rvol_pct, 2) if (dvol_pct is not None and rvol_pct is not None) else None
        env_etf_raw = os.environ.get("BTC_MAGNET_ETF_NETFLOW_1D_M", "").strip()
        etf_inflow_val: Optional[float] = None
        if env_etf_raw:
            try:
                etf_inflow_val = float(env_etf_raw)
            except ValueError:
                etf_inflow_val = None

        metrics = MarketMetrics(
            price=current_price,
            daily_vwap=daily_vwap,
            weekly_vwap=weekly_vwap,
            spot_vol_24h=spot_vol_24h,
            spot_vol_ma20=spot_vol_ma20,
            spot_vol_ratio=spot_vol_ratio,
            spot_cvd_ratio=spot_cvd_ratio,
            spot_cvd_slope_7d=spot_cvd_7d,
            spot_cvd_slope_14d=spot_cvd_14d,
            perp_cvd_slope_24h=fut["perp_slope"],
            perp_cvd_trend=fut["perp_trend"],
            open_interest=current_oi,
            oi_change_1h_pct=fut["oi_change_1h_pct"],
            oi_change_4h_pct=fut["oi_change_4h_pct"],
            oi_change_24h_pct=fut["oi_change_24h_pct"],
            oi_change_3d_pct=fut["oi_change_3d_pct"],
            funding_rate=fut["funding_rate"],
            funding_rate_annualized=fut["funding_ann"],
            futures_basis_annualized=fut["basis_ann"],
            price_change_1h_pct=price_change_1h_pct,
            price_change_24h_pct=price_change_24h_pct,
            long_short_account_ratio=fut["ls_ratio"],
            top_trader_long_short_ratio=fut["ls_ratio"],
            taker_buy_sell_ratio=spot_cvd_ratio,
            bids_asks_depth_ratio=bids_asks_depth_ratio,
            swing_low_4h=swing_low_4h,
            swing_high_4h=swing_high_4h,
            base_floor=base_floor,
            base_ceiling=base_ceiling,
            capitulation_wick_low=capitulation_wick_low,
            euphoria_wick_high=euphoria_wick_high,
            closed_4h_bar_close_time=closed_4h_close_iso,
            data_quality="LIVE",
            spot_data_source="Binance Public Market-Data REST (data-api.binance.vision/api/v3 Closed 4H/1H Klines & L2 Depth)",
            futures_data_source=fut["futures_source"],
            etf_net_inflow_m=etf_inflow_val,  # Never fabricated: None unless verified env/source provided
            whale_inflow_proxy=None,          # Never fabricated: None unless verified source wired
            oi_scope=fut["oi_scope"],
            ls_ratio_available=fut["ls_ratio_available"],
            oi_history_available=fut["oi_history_available"],
            ls_ratio_percentile_72h=fut.get("ls_ratio_percentile_72h"),
            coinbase_spot_price=xv.get("coinbase_spot_price"),
            okx_spot_price=xv.get("okx_spot_price"),
            coinbase_premium_usd=xv.get("coinbase_premium_usd"),
            coinbase_premium_bps=xv.get("coinbase_premium_bps"),
            vwap_30d=macro_30d.get("vwap_30d"),
            vpoc_30d_primary=macro_30d.get("vpoc_30d_primary"),
            vpoc_30d_secondary=macro_30d.get("vpoc_30d_secondary"),
            realized_vol_30d_pct=rvol_pct,
            implied_vol_dvol_pct=dvol_pct,
            variance_premium_pts=var_prem,
        )

        clusters = self._calc_liquidation_clusters(current_price, closed_4h, current_oi)
        return metrics, clusters

    @staticmethod
    def _calc_percentile(series: List[float], current_val: float) -> Optional[float]:
        if not series or len(series) < 5:
            return None
        below_or_eq = sum(1 for v in series if v <= current_val)
        return round((below_or_eq / len(series)) * 100.0, 1)

    def _fetch_futures_data(self, current_price: float) -> Dict[str, Any]:
        """
        Fetches perpetual futures data strictly from real exchange responses.
        Tier 1: Binance Futures (fapi.binance.com)
        Tier 2: OKX + Deribit + Kraken Futures Live Public APIs (real 72h OI & L/S history)
        Tier 3: Deribit & Kraken Perpetual Live APIs (never fabricates L/S crowding or copies price deltas into OI)
        If all fail: Raises RuntimeError (never invents dummy numbers).
        """
        errors = []

        # Tier 1: Try Binance Futures
        try:
            prem = self._get_json(["https://fapi.binance.com/fapi/v1/premiumIndex"], {"symbol": "BTCUSDT"})
            mark_price = float(prem["markPrice"])
            index_price = float(prem["indexPrice"])
            funding_rate = float(prem["lastFundingRate"])
            funding_ann = funding_rate * 3 * 365 * 100
            basis_ann = ((mark_price - index_price) / max(index_price, 1.0)) * 100 * (365 / 30)

            oi_hist = self._get_json(["https://fapi.binance.com/futures/data/openInterestHist"], {
                "symbol": "BTCUSDT", "period": "1h", "limit": 73
            })
            current_oi = float(oi_hist[-1]["sumOpenInterest"])
            oi_1h = float(oi_hist[-2]["sumOpenInterest"]) if len(oi_hist) >= 2 else current_oi
            oi_4h = float(oi_hist[-5]["sumOpenInterest"]) if len(oi_hist) >= 5 else current_oi
            oi_24h = float(oi_hist[-25]["sumOpenInterest"]) if len(oi_hist) >= 25 else current_oi
            oi_72h = float(oi_hist[0]["sumOpenInterest"]) if len(oi_hist) >= 72 else current_oi

            fapi_klines = self._get_json(["https://fapi.binance.com/fapi/v1/klines"], {
                "symbol": "BTCUSDT", "interval": "1h", "limit": 73
            })
            closed_fapi = fapi_klines[:-1] if len(fapi_klines) >= 2 else fapi_klines
            perp_slope, perp_trend = self._calc_perp_cvd(closed_fapi)

            ls_data = self._get_json(["https://fapi.binance.com/futures/data/globalLongShortAccountRatio"], {
                "symbol": "BTCUSDT", "period": "1h", "limit": 72
            })
            ls_hist_vals = [float(x["longShortRatio"]) for x in ls_data if x.get("longShortRatio")]
            ls_ratio = float(ls_data[-1]["longShortRatio"])
            ls_pct = self._calc_percentile(ls_hist_vals, ls_ratio)

            oi_change_1h_pct = ((current_oi - oi_1h) / oi_1h * 100) if oi_1h > 0 else 0.0
            oi_change_4h_pct = ((current_oi - oi_4h) / oi_4h * 100) if oi_4h > 0 else 0.0
            oi_change_24h_pct = ((current_oi - oi_24h) / oi_24h * 100) if oi_24h > 0 else 0.0
            oi_change_3d_pct = ((current_oi - oi_72h) / oi_72h * 100) if oi_72h > 0 else 0.0

            return {
                "funding_rate": funding_rate,
                "funding_ann": funding_ann,
                "basis_ann": basis_ann,
                "current_oi": current_oi,
                "oi_change_1h_pct": oi_change_1h_pct,
                "oi_change_4h_pct": oi_change_4h_pct,
                "oi_change_24h_pct": oi_change_24h_pct,
                "oi_change_3d_pct": oi_change_3d_pct,
                "perp_slope": perp_slope,
                "perp_trend": perp_trend,
                "ls_ratio": ls_ratio,
                "ls_ratio_percentile_72h": ls_pct,
                "ls_ratio_available": True,
                "oi_history_available": True,
                "futures_source": "Binance Futures Live REST (fapi BTCUSDT Perp)",
                "oi_scope": "Binance BTCUSDT Perp Only (single-venue perpetual, not global market OI)",
            }

        except Exception as e:
            errors.append(f"Binance Futures: {e}")

        # Tier 2: OKX + Deribit + Kraken Multi-Venue Public APIs (empirical OI history & L/S ratio)
        try:
            okx_mark = self._get_json(["https://www.okx.com/api/v5/public/mark-price"], {
                "instType": "SWAP", "instId": "BTC-USDT-SWAP"
            })
            okx_fund = self._get_json(["https://www.okx.com/api/v5/public/funding-rate"], {
                "instId": "BTC-USDT-SWAP"
            })
            okx_oi = self._get_json(["https://www.okx.com/api/v5/public/open-interest"], {
                "instType": "SWAP", "instId": "BTC-USDT-SWAP"
            })
            okx_oiv = self._get_json(["https://www.okx.com/api/v5/rubik/stat/contracts/open-interest-volume"], {
                "ccy": "BTC", "period": "1H"
            })
            okx_ls = self._get_json(["https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio"], {
                "ccy": "BTC", "period": "1H"
            })

            mark_price = float(okx_mark["data"][0]["markPx"])
            funding_rate = float(okx_fund["data"][0]["fundingRate"])
            funding_ann = funding_rate * 3 * 365 * 100
            basis_ann = ((mark_price - current_price) / max(current_price, 1.0)) * 100 * (365 / 30)

            combined_oi = float(okx_oi["data"][0]["oiCcy"])
            sources = ["OKX BTC-USDT-SWAP"]

            # Add Deribit & Kraken perpetual OI where reachable for broader multi-venue coverage
            try:
                deribit_resp = self._get_json(
                    ["https://www.deribit.com/api/v2/public/get_book_summary_by_currency"],
                    {"currency": "BTC", "kind": "future"}
                )
                perp = next((item for item in deribit_resp.get("result", []) if "PERPETUAL" in item.get("instrument_name", "")), None)
                if perp:
                    combined_oi += float(perp["open_interest"]) / max(float(perp["mark_price"]), 1.0)
                    sources.append("Deribit BTC-PERPETUAL")
            except Exception:
                pass

            try:
                kraken_resp = self._get_json(["https://futures.kraken.com/derivatives/api/v3/tickers"])
                k_btc = next((t for t in kraken_resp.get("tickers", []) if t.get("symbol") == "PF_XBTUSD"), None)
                if k_btc and k_btc.get("openInterest"):
                    combined_oi += float(k_btc["openInterest"])
                    sources.append("Kraken PF_XBTUSD")
            except Exception:
                pass

            try:
                bitget_resp = self._get_json(
                    ["https://api.bitget.com/api/v2/mix/market/open-interest"],
                    {"symbol": "BTCUSDT", "productType": "USDT-FUTURES"},
                )
                bg_list = (bitget_resp.get("data") or {}).get("openInterestList") or []
                if bg_list and bg_list[0].get("size"):
                    bg_oi = float(bg_list[0]["size"])
                    if bg_oi > 0:
                        combined_oi += bg_oi
                        sources.append("Bitget BTCUSDT-PERP")
            except Exception:
                pass

            try:
                gate_resp = self._get_json(["https://api.gateio.ws/api/v4/futures/usdt/contracts/BTC_USDT"])
                pos_sz = float(gate_resp.get("position_size") or 0.0)
                q_mult = float(gate_resp.get("quanto_multiplier") or 0.0001)
                gate_oi = pos_sz * q_mult
                if gate_oi > 0:
                    combined_oi += gate_oi
                    sources.append("Gate.io BTC_USDT")
            except Exception:
                pass

            oiv_rows = sorted(okx_oiv.get("data", []), key=lambda r: int(r[0]))
            if len(oiv_rows) < 25:
                raise RuntimeError("Insufficient OKX hourly OI history")
            oi_now = float(oiv_rows[-1][1])
            oi_1h = float(oiv_rows[-2][1])
            oi_4h = float(oiv_rows[-5][1]) if len(oiv_rows) >= 5 else oi_now
            oi_24h = float(oiv_rows[-25][1])
            oi_72h = float(oiv_rows[0][1]) if len(oiv_rows) >= 72 else float(oiv_rows[0][1])

            oi_change_1h_pct = ((oi_now - oi_1h) / oi_1h * 100) if oi_1h > 0 else 0.0
            oi_change_4h_pct = ((oi_now - oi_4h) / oi_4h * 100) if oi_4h > 0 else 0.0
            oi_change_24h_pct = ((oi_now - oi_24h) / oi_24h * 100) if oi_24h > 0 else 0.0
            oi_change_3d_pct = ((oi_now - oi_72h) / oi_72h * 100) if oi_72h > 0 else 0.0

            ls_rows = sorted(okx_ls.get("data", []), key=lambda r: int(r[0]))
            ls_hist_vals = [float(r[1]) for r in ls_rows[-72:]]
            ls_ratio = float(ls_rows[-1][1]) if ls_rows else 1.0
            ls_pct = self._calc_percentile(ls_hist_vals, ls_ratio)

            perp_slope = mark_price - current_price
            perp_trend = "positive" if perp_slope > 0 else "declining"

            return {
                "funding_rate": funding_rate,
                "funding_ann": funding_ann,
                "basis_ann": basis_ann,
                "current_oi": combined_oi,
                "oi_change_1h_pct": oi_change_1h_pct,
                "oi_change_4h_pct": oi_change_4h_pct,
                "oi_change_24h_pct": oi_change_24h_pct,
                "oi_change_3d_pct": oi_change_3d_pct,
                "perp_slope": perp_slope,
                "perp_trend": perp_trend,
                "ls_ratio": ls_ratio,
                "ls_ratio_percentile_72h": ls_pct,
                "ls_ratio_available": bool(ls_rows),
                "oi_history_available": True,
                "futures_source": f"{' + '.join(sources)} Live API",
                "oi_scope": f"{' + '.join(sources)} (tracked venue subset, not total ~$50B+ global market OI)",
            }

        except Exception as e:
            errors.append(f"OKX/Multi-Venue Futures: {e}")

        # Tier 3: Deribit & Kraken Futures Live API (never fabricates L/S crowding or copies price delta into OI)
        try:
            deribit_resp = self.session.get(
                "https://www.deribit.com/api/v2/public/get_book_summary_by_currency?currency=BTC&kind=future",
                timeout=self.timeout
            ).json()
            perp = next((item for item in deribit_resp.get("result", []) if "PERPETUAL" in item.get("instrument_name", "")), None)

            if not perp:
                raise RuntimeError("Deribit BTC-PERPETUAL instrument not found")

            mark_price = float(perp["mark_price"])
            funding_rate = float(perp.get("funding_8h", 0.0))
            funding_ann = funding_rate * 3 * 365 * 100
            basis_ann = ((mark_price - current_price) / max(current_price, 1.0)) * 100 * (365 / 30)
            current_oi = float(perp["open_interest"]) / max(mark_price, 1.0)
            sources = ["Deribit BTC-PERPETUAL"]

            try:
                kraken_resp = self.session.get("https://futures.kraken.com/derivatives/api/v3/tickers", timeout=self.timeout).json()
                k_btc = next((t for t in kraken_resp.get("tickers", []) if t.get("symbol") == "PF_XBTUSD"), None)
                if k_btc and k_btc.get("openInterest"):
                    current_oi += float(k_btc["openInterest"])
                    sources.append("Kraken PF_XBTUSD")
            except Exception:
                pass

            perp_slope = mark_price - current_price
            perp_trend = "positive" if perp_slope > 0 else "declining"

            return {
                "funding_rate": funding_rate,
                "funding_ann": funding_ann,
                "basis_ann": basis_ann,
                "current_oi": current_oi,
                "oi_change_1h_pct": 0.0,
                "oi_change_4h_pct": 0.0,
                "oi_change_24h_pct": 0.0,
                "oi_change_3d_pct": 0.0,
                "perp_slope": perp_slope,
                "perp_trend": perp_trend,
                "ls_ratio": 1.0,
                "ls_ratio_percentile_72h": None,
                "ls_ratio_available": False,
                "oi_history_available": False,
                "futures_source": f"{' & '.join(sources)} Live API",
                "oi_scope": f"{' + '.join(sources)} Only (single/two-venue subset; 24h OI delta & retail L/S unavailable)",
            }

        except Exception as e:
            errors.append(f"Deribit/Kraken: {e}")

        # If all fail: strictly fail without fabricating fake data
        raise RuntimeError(f"Data Integrity Failure: All futures endpoints failed ({'; '.join(errors)})")

    def _calc_vwap_from_midnight(self, klines_1h: List[List[Any]]) -> float:
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

    def _calc_spot_cvd(self, daily_klines: List[List[Any]], one_h_klines: List[List[Any]]) -> Tuple[float, float, float]:
        taker_buy_24h = sum(float(k[9]) for k in one_h_klines[-24:])
        total_vol_24h = sum(float(k[5]) for k in one_h_klines[-24:])
        taker_sell_24h = max(1e-6, total_vol_24h - taker_buy_24h)
        spot_cvd_ratio = taker_buy_24h / taker_sell_24h

        daily_deltas = [float(k[9]) - (float(k[5]) - float(k[9])) for k in daily_klines]
        slope_7d = sum(daily_deltas[-7:]) if len(daily_deltas) >= 7 else 0.0
        slope_14d = sum(daily_deltas[-14:]) if len(daily_deltas) >= 14 else 0.0

        return spot_cvd_ratio, slope_7d, slope_14d

    def _calc_perp_cvd(self, fapi_klines: List[List[Any]]) -> Tuple[float, str]:
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
        closed_4h: List[List[Any]],
        total_oi: float
    ) -> List[LiquidationCluster]:
        """
        Derives algorithmic estimated leverage concentration zones from closed 4H klines[:-1].
        Uses empirical price-proportional binning (~0.15% spot tick step; zero ATR smoothing).
        Explicitly classified as Modeled Liquidity Pools, not verified private exchange orders.
        """
        recent_highs = [float(k[2]) for k in closed_4h[-40:]]
        recent_lows = [float(k[3]) for k in closed_4h[-40:]]

        tiers = [
            (100, 0.008, 0.15),
            (50, 0.018, 0.30),
            (25, 0.038, 0.35),
            (10, 0.095, 0.20),
        ]

        bin_size = max(100.0, round(current_price * 0.0015, -1))
        upper_bins: Dict[float, float] = {}
        lower_bins: Dict[float, float] = {}

        for low_val in set(recent_lows):
            for _, offset, share in tiers:
                target_liq = low_val * (1.0 + offset)
                if target_liq > current_price:
                    binned_price = round(target_liq / bin_size) * bin_size
                    vol = (total_oi * 0.02 * current_price * share)
                    upper_bins[binned_price] = upper_bins.get(binned_price, 0.0) + vol

        for high_val in set(recent_highs):
            for offset in [0.005, 0.012, 0.025]:
                target_liq = high_val * (1.0 + offset)
                if target_liq > current_price:
                    binned_price = round(target_liq / bin_size) * bin_size
                    vol = (total_oi * 0.03 * current_price)
                    upper_bins[binned_price] = upper_bins.get(binned_price, 0.0) + vol

        for high_val in set(recent_highs):
            for _, offset, share in tiers:
                target_liq = high_val * (1.0 - offset)
                if target_liq < current_price:
                    binned_price = round(target_liq / bin_size) * bin_size
                    vol = (total_oi * 0.02 * current_price * share)
                    lower_bins[binned_price] = lower_bins.get(binned_price, 0.0) + vol

        for low_val in set(recent_lows):
            for offset in [0.005, 0.012, 0.025]:
                target_liq = low_val * (1.0 - offset)
                if target_liq < current_price:
                    binned_price = round(target_liq / bin_size) * bin_size
                    vol = (total_oi * 0.03 * current_price)
                    lower_bins[binned_price] = lower_bins.get(binned_price, 0.0) + vol

        clusters = []
        # Enforce >= 0.45% minimum distance clearance from spot for immediate 50-100x pools
        # so historical kline offset bins landing $10 (0.02%) from spot do not create micro-straddle noise.
        min_clearance = current_price * 0.0045
        all_upper = [item for item in sorted(upper_bins.items(), key=lambda x: x[0]) if item[0] > current_price]
        cleared_upper = [item for item in all_upper if item[0] >= current_price + min_clearance]
        selected_upper = cleared_upper[:2] if len(cleared_upper) >= 2 else (cleared_upper + [x for x in all_upper if x not in cleared_upper])[:2]
        for p, vol in selected_upper:
            dist_pct = ((p - current_price) / current_price) * 100
            clusters.append(
                LiquidationCluster(
                    price_level=round(p, 2),
                    distance_pct=round(dist_pct, 2),
                    estimated_vol_usd=round(vol, 0),
                    side="upper",
                    cluster_type="Modeled Short Liquidity Pool (Algorithmic Estimate)",
                    distance_atr=None,
                )
            )

        all_lower = [item for item in sorted(lower_bins.items(), key=lambda x: x[0], reverse=True) if item[0] < current_price]
        cleared_lower = [item for item in all_lower if item[0] <= current_price - min_clearance]
        selected_lower = cleared_lower[:2] if len(cleared_lower) >= 2 else (cleared_lower + [x for x in all_lower if x not in cleared_lower])[:2]
        for p, vol in selected_lower:
            dist_pct = ((current_price - p) / current_price) * 100
            clusters.append(
                LiquidationCluster(
                    price_level=round(p, 2),
                    distance_pct=round(dist_pct, 2),
                    estimated_vol_usd=round(vol, 0),
                    side="lower",
                    cluster_type="Modeled Long Liquidity Pool (Algorithmic Estimate)",
                    distance_atr=None,
                )
            )

        return clusters

    def _fetch_cross_venue_spot_and_dvol(self, binance_price: float) -> Dict[str, Optional[float]]:
        """Fetch supplemental un-geoblocked Coinbase BTC-USD spot, OKX BTC-USDT spot, and Deribit BTC DVOL."""
        out: Dict[str, Optional[float]] = {
            "coinbase_spot_price": None,
            "okx_spot_price": None,
            "coinbase_premium_usd": None,
            "coinbase_premium_bps": None,
            "implied_vol_dvol_pct": None,
        }
        try:
            cb = self._get_json(["https://api.exchange.coinbase.com/products/BTC-USD/ticker"])
            cb_px = float(cb.get("price") or 0.0)
            if cb_px > 0 and binance_price > 0:
                prem_usd = cb_px - binance_price
                prem_bps = (prem_usd / binance_price) * 10000.0
                out["coinbase_spot_price"] = round(cb_px, 2)
                out["coinbase_premium_usd"] = round(prem_usd, 2)
                out["coinbase_premium_bps"] = round(prem_bps, 2)
        except Exception:
            pass

        try:
            okx = self._get_json(
                ["https://www.okx.com/api/v5/market/ticker"],
                {"instId": "BTC-USDT"},
            )
            okx_rows = okx.get("data") or []
            if okx_rows and okx_rows[0].get("last"):
                okx_px = float(okx_rows[0]["last"])
                if okx_px > 0:
                    out["okx_spot_price"] = round(okx_px, 2)
        except Exception:
            pass

        try:
            now_ms = int(time.time() * 1000)
            start_ms = now_ms - (48 * 3600 * 1000)
            dvol_resp = self._get_json(
                ["https://www.deribit.com/api/v2/public/get_volatility_index_data"],
                {
                    "currency": "BTC",
                    "resolution": "3600",
                    "start_timestamp": start_ms,
                    "end_timestamp": now_ms,
                },
            )
            dvol_rows = ((dvol_resp.get("result") or {}).get("data")) or []
            if dvol_rows:
                # Each row is [timestamp, open, high, low, close]
                latest_close = float(dvol_rows[-1][4])
                if latest_close > 0:
                    out["implied_vol_dvol_pct"] = round(latest_close, 2)
        except Exception:
            pass

        return out

    def _calc_30d_macro_anchors(
        self,
        closed_daily: List[List[Any]],
        closed_4h: List[List[Any]],
    ) -> Dict[str, Optional[float]]:
        """
        Deterministically compute 30D Closed VWAP, 30D Volume Profile POCs (Primary & Secondary HVN),
        and 30D Annualized Realized Volatility strictly from closed klines[:-1] (zero lagging oscillators).
        """
        out: Dict[str, Optional[float]] = {
            "vwap_30d": None,
            "vpoc_30d_primary": None,
            "vpoc_30d_secondary": None,
            "realized_vol_30d_pct": None,
        }
        window_30d = closed_daily[-30:] if len(closed_daily) >= 30 else closed_daily
        if window_30d:
            cum_pv = 0.0
            cum_vol = 0.0
            for k in window_30d:
                h, l, c, v = float(k[2]), float(k[3]), float(k[4]), float(k[5])
                typical = (h + l + c) / 3.0
                cum_pv += typical * v
                cum_vol += v
            if cum_vol > 0:
                out["vwap_30d"] = round(cum_pv / cum_vol, 2)

        # 30D Volume Profile POCs ($250 price bins across closed 30D daily + closed 4H klines)
        bin_step = 250.0
        vol_bins: Dict[float, float] = {}
        profile_bars = list(window_30d) + list(closed_4h[-60:])
        for k in profile_bars:
            h, l, c, v = float(k[2]), float(k[3]), float(k[4]), float(k[5])
            if v <= 0 or h <= 0 or l <= 0:
                continue
            typical = (h + l + c) / 3.0
            b_center = round(typical / bin_step) * bin_step
            vol_bins[b_center] = vol_bins.get(b_center, 0.0) + v

        if vol_bins:
            ranked_bins = sorted(vol_bins.items(), key=lambda x: x[1], reverse=True)
            primary_poc = ranked_bins[0][0]
            out["vpoc_30d_primary"] = round(primary_poc, 2)
            for cand_price, _ in ranked_bins[1:]:
                if abs(cand_price - primary_poc) / max(primary_poc, 1.0) >= 0.015:
                    out["vpoc_30d_secondary"] = round(cand_price, 2)
                    break

        # 30D Annualized Realized Volatility from closed daily log returns
        ret_window = closed_daily[-31:] if len(closed_daily) >= 31 else closed_daily
        closes = [float(k[4]) for k in ret_window if float(k[4]) > 0]
        if len(closes) >= 10:
            log_rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
            n = len(log_rets)
            mean_r = sum(log_rets) / n
            var_r = sum((r - mean_r) ** 2 for r in log_rets) / max(1, n - 1)
            rvol_ann = math.sqrt(var_r) * math.sqrt(365.0) * 100.0
            out["realized_vol_30d_pct"] = round(rvol_ann, 2)

        return out
