import json
import os
import datetime
from typing import Dict, Any, Tuple

class WebGenerator:
    """
    Generates:
      1. dist/regime.json (Static JSON API feed)
      2. dist/index.html (Modern financial dashboard with standalone Regime Panel & AI Telemetry Drawer)
      3. dist/regimes.html (Comprehensive educational subpage explaining all 5 regimes)
    """

    def __init__(self, output_dir: str = "dist"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        # 1. Write raw JSON feed
        json_path = os.path.join(self.output_dir, "regime.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # 2. Render main dashboard HTML (Unified 6-Panel Gold Standard Format)
        html_content = self._render_html(payload)
        html_path = os.path.join(self.output_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 3. Render regimes detailed subpage HTML
        regimes_content = self._render_regimes_subpage(payload)
        regimes_path = os.path.join(self.output_dir, "regimes.html")
        with open(regimes_path, "w", encoding="utf-8") as f:
            f.write(regimes_content)

        # 3b. Render Privacy Policy subpage HTML (Google Play & AdMob Requirement)
        privacy_content = self._render_privacy_page()
        privacy_path = os.path.join(self.output_dir, "privacy.html")
        with open(privacy_path, "w", encoding="utf-8") as f:
            f.write(privacy_content)

        # 3c. Render Mobile Text-Only Terminal (text.html)
        self._verify_text_telemetry(payload)
        text_content = self._render_text_page(payload)
        text_path = os.path.join(self.output_dir, "text.html")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text_content)

        # 4. Render Mobile Cockpit App (app.html) with 100% exact format parity with index.html
        app_path = os.path.join(self.output_dir, "app.html")
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 5. Render manifest.json and sw.js for PWA installation
        try:
            import shutil
            for icon_name in ["icon-192.png", "icon-512.png", "icon-maskable-512.png"]:
                if os.path.exists(icon_name):
                    dst = os.path.join(self.output_dir, icon_name)
                    if os.path.abspath(icon_name) != os.path.abspath(dst):
                        shutil.copy(icon_name, dst)
            if os.path.exists("assets"):
                dst_assets = os.path.join(self.output_dir, "assets")
                if os.path.abspath("assets") != os.path.abspath(dst_assets):
                    shutil.copytree("assets", dst_assets, dirs_exist_ok=True)

            from web.mobile_generator import MobileWebGenerator
            mob_gen = MobileWebGenerator()
            manifest_path = os.path.join(self.output_dir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(mob_gen.render_manifest())

            sw_path = os.path.join(self.output_dir, "sw.js")
            with open(sw_path, "w", encoding="utf-8") as f:
                f.write(mob_gen.render_service_worker())
        except Exception as e:
            print(f"Warning: Mobile generator encountered error: {e}")

        return json_path, html_path

    @staticmethod
    def _compute_scan_id(data: Dict[str, Any]) -> str:
        """Deterministic short scan identifier linking index.html, text.html, regime.json, and AI prompts."""
        import hashlib
        ts = str(data.get("timestamp", ""))
        metrics = data.get("metrics", {}) or {}
        regime = data.get("regime", {}) or {}
        seed = f"{ts}|{metrics.get('price', 0.0)}|{regime.get('regime_id', '')}|{metrics.get('open_interest', 0.0)}"
        digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:6]
        compact_ts = ts.replace("-", "").replace(":", "")[:13] or "SCAN"
        return f"{compact_ts}Z-{digest}"

    @staticmethod
    def _format_pool_m(vol_m: float) -> str:
        """Formats modeled liquidation pool volume without false decimal precision above $10M."""
        if vol_m >= 10.0:
            return f"~${round(vol_m):,.0f}M"
        return f"~${vol_m:.1f}M"

    @staticmethod
    def _get_canonical_ladder(data: Dict[str, Any]) -> list:
        """
        Single source of truth for the 6-tier 10x-100x Modeled Liquidation Ladder across
        index.html, text.html, and exported AI prompts.
        """
        regime = data.get("regime", {}) or {}
        metrics = data.get("metrics", {}) or {}
        existing = regime.get("liquidation_ladder")
        if isinstance(existing, list) and len(existing) == 6:
            return existing

        price = max(1.0, float(metrics.get("price", 0.0) or 1.0))
        atr_safe = max(1.0, float(metrics.get("atr", 500.0) or 500.0))
        sw_h = float(metrics.get("swing_high_4h", price * 1.01) or price * 1.01)
        sw_l = float(metrics.get("swing_low_4h", price * 0.99) or price * 0.99)
        oi = float(metrics.get("open_interest", 0.0) or 0.0)
        ls = float(metrics.get("long_short_account_ratio", 1.0) or 1.0)
        ls_avail = bool(metrics.get("ls_ratio_available", True))

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_p = float(upper_c.get("price_level", round(sw_h * 1.005, 2)) or sw_h * 1.005)
        u_v = float(upper_c.get("estimated_vol_usd", 0.0) or 0.0) / 1e6
        l_p = float(lower_c.get("price_level", round(sw_l * 0.995, 2)) or sw_l * 0.995)
        l_v = float(lower_c.get("estimated_vol_usd", 0.0) or 0.0) / 1e6

        oi_notional_m = max(10.0, (oi * price) / 1e6) if oi > 0 else 2000.0
        long_share = (ls / (1.0 + ls)) if (ls_avail and (1.0 + ls) > 0) else 0.5
        l_w = max(0.50, long_share / 0.50)
        u_w = max(0.50, (1.0 - long_share) / 0.50)

        u_25_v = round(max(1.0, oi_notional_m * 0.032 * u_w), 1)
        u_10_v = round(max(1.0, oi_notional_m * 0.024 * u_w), 1)
        l_25_v = round(max(1.0, oi_notional_m * 0.040 * l_w), 1)
        l_10_v = round(max(1.0, oi_notional_m * 0.028 * l_w), 1)

        def _make_row(tier: str, lev: str, side: str, lvl: float, vol_m: float, dist_ovr=None, atr_ovr=None, is_near: bool = False):
            d_pct = ((lvl - price) / price) * 100.0
            if dist_ovr is not None:
                d_pct = float(dist_ovr) if side == "upper" else -float(dist_ovr)
            d_atr = (lvl - price) / atr_safe
            if atr_ovr is not None:
                d_atr = float(atr_ovr) if side == "upper" else -float(atr_ovr)
            return {
                "tier": tier,
                "leverage": lev,
                "side": side,
                "price": round(lvl, 2),
                "distance_pct": round(d_pct, 2),
                "distance_atr": round(d_atr, 2),
                "estimated_vol_m": round(vol_m, 1),
                "modeled": True,
                "is_nearest": is_near,
            }

        return [
            _make_row("10x Shorts", "10x", "upper", sw_h * 1.025, u_10_v),
            _make_row("25x Shorts", "25x", "upper", sw_h * 1.012, u_25_v),
            _make_row("50-100x Shorts", "50-100x", "upper", u_p, u_v, upper_c.get("distance_pct"), upper_c.get("distance_atr"), True),
            _make_row("100x Longs", "100x", "lower", l_p, l_v, lower_c.get("distance_pct"), lower_c.get("distance_atr"), True),
            _make_row("25x Longs", "25x", "lower", sw_l * 0.988, l_25_v),
            _make_row("10x Longs", "10x", "lower", sw_l * 0.975, l_10_v),
        ]

    @staticmethod
    def _format_utc_sgt(ts_iso: str) -> Tuple[str, str, str]:
        """Returns (utc_time_str, sgt_time_str, date_str) parsed strictly from scan ISO timestamp."""
        import datetime as _dt
        try:
            dt_utc = _dt.datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
            dt_sgt = dt_utc + _dt.timedelta(hours=8)
            return dt_utc.strftime("%H:%M:%S UTC"), dt_sgt.strftime("%H:%M:%S SGT"), dt_utc.strftime("%d %b %Y")
        except Exception:
            t_raw = ts_iso.split("T")[1][:8] if "T" in ts_iso else "00:00:00"
            return f"{t_raw} UTC", "--:--:-- SGT", ts_iso[:10] if len(ts_iso) >= 10 else "Unknown"

    def _build_blind_llm_prompt(self, data: Dict[str, Any]) -> str:
        """Constructs an unanchored, metrics-only prompt with zero engine verdict/sizing bias."""
        metrics = data.get("metrics", {})
        ts = data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
        scan_id = self._compute_scan_id(data)
        ladder = self._get_canonical_ladder(data)

        price = metrics.get("price", 0.0)
        daily_vwap = metrics.get("daily_vwap", 0.0)
        weekly_vwap = metrics.get("weekly_vwap", 0.0)
        ema_20d = metrics.get("ema_20d", 0.0)
        ema_50d = metrics.get("ema_50d", 0.0)
        ma_200d = metrics.get("ma_200d", 0.0)
        swing_high = metrics.get("swing_high_4h", 0.0)
        swing_low = metrics.get("swing_low_4h", 0.0)
        base_floor = metrics.get("base_floor", 0.0)
        cap_wick = metrics.get("capitulation_wick_low", 0.0)

        spot_vol = metrics.get("spot_vol_24h", 0.0)
        spot_vol_ratio = metrics.get("spot_vol_ratio", 1.0)
        spot_cvd_ratio = metrics.get("spot_cvd_ratio", 1.0)
        spot_cvd_7d = metrics.get("spot_cvd_slope_7d", 0.0)
        spot_cvd_14d = metrics.get("spot_cvd_slope_14d", 0.0)
        perp_trend = metrics.get("perp_cvd_trend", "Flat")
        bids_asks_depth = metrics.get("bids_asks_depth_ratio", 1.0)

        oi = metrics.get("open_interest", 0.0)
        oi_24h = metrics.get("oi_change_24h_pct", 0.0)
        oi_1h = metrics.get("oi_change_1h_pct", 0.0)
        oi_4h = metrics.get("oi_change_4h_pct", 0.0)
        oi_3d = metrics.get("oi_change_3d_pct", 0.0)
        oi_hist_ok = metrics.get("oi_history_available", True)
        funding_rate = metrics.get("funding_rate", 0.0) * 100
        funding_ann = metrics.get("funding_rate_annualized", 0.0)
        basis = metrics.get("futures_basis_annualized", 0.0)
        ls_ratio = metrics.get("long_short_account_ratio", 1.0)
        ls_avail = metrics.get("ls_ratio_available", True)
        long_pct = (ls_ratio / (1.0 + ls_ratio)) * 100 if (1.0 + ls_ratio) > 0 else 50.0
        ls_pct_72h = metrics.get("ls_ratio_percentile_72h")
        atr = metrics.get("atr", 0.0)
        atr_comp = metrics.get("atr_compression_pct", 0.0)
        atr_pct_72h = metrics.get("atr_percentile_72h")
        range_width = ((swing_high - swing_low) / max(price, 1.0)) * 100
        spot_src = metrics.get("spot_data_source", "Binance Public Market-Data REST")
        fut_src = metrics.get("futures_data_source", "Perp Public REST")
        oi_scope = metrics.get("oi_scope", "Tracked venue perp subset (not total market OI)")

        oi_delta_line = (
            f"1H: {oi_1h:+.2f}% | 4H: {oi_4h:+.2f}% | 24H: {oi_24h:+.2f}% | 3D: {oi_3d:+.2f}%"
            if oi_hist_ok else "Multi-hour OI history unavailable on current fallback feed"
        )
        ls_line = (
            f"{ls_ratio:.2f} ({long_pct:.1f}% long" + (f", p{ls_pct_72h:.0f} 72h)" if ls_pct_72h is not None else ")")
            if ls_avail else "Unavailable on fallback feed"
        )
        atr_pct_note = f" | 72h Rank: p{atr_pct_72h:.0f}" if atr_pct_72h is not None else ""

        upper_rows = [r for r in ladder if r["side"] == "upper"]
        lower_rows = [r for r in ladder if r["side"] == "lower"]
        upper_lines = "\n".join(
            f"  ▲ {r['tier']:<14} ${r['price']:,.0f} ({r['distance_pct']:+.2f}% / {r['distance_atr']:+.2f} ATR) | {self._format_pool_m(r['estimated_vol_m'])} (Modeled Estimate)"
            for r in upper_rows
        )
        lower_lines = "\n".join(
            f"  ▼ {r['tier']:<14} ${r['price']:,.0f} ({r['distance_pct']:+.2f}% / {r['distance_atr']:+.2f} ATR) | {self._format_pool_m(r['estimated_vol_m'])} (Modeled Estimate)"
            for r in lower_rows
        )

        return f"""================================================================================
BLIND BITCOIN (BTC) MICROSTRUCTURE TELEMETRY AUDIT (UNANCHORED MODE)
Scan ID: {scan_id} | Timestamp: {ts[:19]} UTC | Cadence: Every 30m (:00 & :30 UTC)
Raw Spot Feed: {spot_src}
Raw Futures Feed: {fut_src}
Mandate: SPOT-ONLY ROTATION (BTC / USDT). Zero borrowed leverage. Zero shorting.
Note: System engine verdict and sizing have been intentionally withheld to prevent anchoring bias.
================================================================================

SECTION 1 • RAW PRICE BENCHMARKS & RANGE GEOMETRY
• Current BTC Spot Price: ${price:,.2f}
• Daily VWAP (00:00 UTC): ${daily_vwap:,.2f} [{((price - daily_vwap)/max(daily_vwap,1)*100):+.2f}% vs Spot]
• Weekly VWAP (Monday):   ${weekly_vwap:,.2f} [{((price - weekly_vwap)/max(weekly_vwap,1)*100):+.2f}% vs Spot]
• Moving Averages: 20D EMA: ${ema_20d:,.2f} | 50D EMA: ${ema_50d:,.2f} | 200D SMA: ${ma_200d:,.2f}
• 4-Hour Channel Range: ${swing_low:,.0f} (Floor) to ${swing_high:,.0f} (Ceiling) [Width: {range_width:.2f}%]
• Structural Anchors: 3D Base Floor: ${base_floor:,.2f} | 24H Low: ${cap_wick:,.2f}

SECTION 2 • RAW ORDER FLOW & KLINE TAKER VOLUME DELTA
• 24h Spot Volume: {spot_vol:,.0f} BTC ({spot_vol_ratio:.2f}x 20D MA)
• Spot CVD Ratio (24h kline taker buy/sell): {spot_cvd_ratio:.2f} | Slopes: 7D {spot_cvd_7d:+.0f} | 14D {spot_cvd_14d:+.0f}
• Perp Flow Trend: {perp_trend}
• Order Book Depth Ratio (±1.5% bids/asks): {bids_asks_depth:.2f}

SECTION 3 • RAW DERIVATIVES POSITIONING ({oi_scope})
• Tracked Venue Open Interest: {oi:,.1f} BTC (~${(oi * price) / 1e9:.2f}B notional in tracked contract(s))
• OI Velocity: {oi_delta_line}
• 8-Hour Funding Rate: {funding_rate:+.4f}% ({funding_ann:+.2f}% Ann.)
• Futures Basis (Ann.): {basis:+.2f}%
• Tracked L/S Account Ratio: {ls_line}

SECTION 4 • VOLATILITY & MODELED LIQUIDATION ESTIMATES (ALGORITHMIC ESTIMATE)
• 14-Period 1H ATR: ${atr:,.2f} (Compression vs 72h Peak: {atr_comp:.1f}%{atr_pct_note})
[MODELED UPPER SHORT POOLS — ALGORITHMIC ESTIMATE FROM VENUE OI & 4H SWINGS]:
{upper_lines}
● CURRENT BTC SPOT ANCHOR: ${price:,.2f}
[MODELED LOWER LONG POOLS — ALGORITHMIC ESTIMATE FROM VENUE OI & 4H SWINGS]:
{lower_lines}

BLIND ANALYST TASK:
Without seeing our internal call, form your own independent judgment:
1. Classify the market into one of the 5 Regimes (Spot-Led Expansion, Leveraged/Fragile Upside, Range/Liquidation Magnet, Cascade/Forced Deleveraging, Distribution/Bear) or Transition/Mixed (Default Cash). Cite 3+ metrics.
2. State your independent spot allocation (0.0x to 1.0x), exact invalidation level, and key risks.""".strip()

    def _build_llm_prompt(self, data: Dict[str, Any]) -> str:
        """Constructs an institutional-grade audit prompt strictly bound to scan telemetry."""
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})
        ts = data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
        scan_id = self._compute_scan_id(data)
        ladder = self._get_canonical_ladder(data)

        price = metrics.get("price", 0.0)
        daily_vwap = metrics.get("daily_vwap", 0.0)
        weekly_vwap = metrics.get("weekly_vwap", 0.0)
        ema_20d = metrics.get("ema_20d", 0.0)
        ema_50d = metrics.get("ema_50d", 0.0)
        ma_200d = metrics.get("ma_200d", 0.0)
        swing_high = metrics.get("swing_high_4h", 0.0)
        swing_low = metrics.get("swing_low_4h", 0.0)
        base_floor = metrics.get("base_floor", 0.0)
        cap_wick = metrics.get("capitulation_wick_low", 0.0)

        spot_vol = metrics.get("spot_vol_24h", 0.0)
        spot_vol_ratio = metrics.get("spot_vol_ratio", 1.0)
        spot_cvd_ratio = metrics.get("spot_cvd_ratio", 1.0)
        spot_cvd_7d = metrics.get("spot_cvd_slope_7d", 0.0)
        spot_cvd_14d = metrics.get("spot_cvd_slope_14d", 0.0)
        perp_trend = metrics.get("perp_cvd_trend", "Flat")
        bids_asks_depth = metrics.get("bids_asks_depth_ratio", 1.0)

        oi = metrics.get("open_interest", 0.0)
        oi_24h = metrics.get("oi_change_24h_pct", 0.0)
        oi_1h = metrics.get("oi_change_1h_pct", 0.0)
        oi_4h = metrics.get("oi_change_4h_pct", 0.0)
        oi_3d = metrics.get("oi_change_3d_pct", 0.0)
        oi_hist_ok = metrics.get("oi_history_available", True)
        funding_rate = metrics.get("funding_rate", 0.0) * 100
        funding_ann = metrics.get("funding_rate_annualized", 0.0)
        basis = metrics.get("futures_basis_annualized", 0.0)
        ls_ratio = metrics.get("long_short_account_ratio", 1.0)
        ls_avail = metrics.get("ls_ratio_available", True)
        long_pct = (ls_ratio / (1.0 + ls_ratio)) * 100 if (1.0 + ls_ratio) > 0 else 50.0
        ls_pct_72h = metrics.get("ls_ratio_percentile_72h")

        atr = metrics.get("atr", 0.0)
        atr_comp = metrics.get("atr_compression_pct", 0.0)
        atr_pct_72h = metrics.get("atr_percentile_72h")
        range_width = ((swing_high - swing_low) / max(price, 1.0)) * 100
        spot_src = metrics.get("spot_data_source", "Binance Public Market-Data REST")
        fut_src = metrics.get("futures_data_source", "Perp Public REST")
        oi_scope = metrics.get("oi_scope", "Tracked venue perp subset (not total market OI)")

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_v = upper_c.get("estimated_vol_usd", 0.0) / 1e6
        l_v = lower_c.get("estimated_vol_usd", 0.0) / 1e6

        imm_ratio = regime.get("immediate_imbalance_ratio", round(l_v / max(u_v, 0.1), 1))
        tot_u_vol = regime.get("total_ladder_upper_vol", sum(r["estimated_vol_m"] for r in ladder if r["side"] == "upper"))
        tot_l_vol = regime.get("total_ladder_lower_vol", sum(r["estimated_vol_m"] for r in ladder if r["side"] == "lower"))
        tot_ratio = regime.get("total_ladder_imbalance_ratio", round(tot_l_vol / max(tot_u_vol, 0.1), 2))
        imm_disp = f"~{round(imm_ratio):.0f}x" if imm_ratio >= 10 else f"{imm_ratio:.1f}x"

        lsce_status = regime.get("lsce_status", "UNTESTED")
        lsce_detail = regime.get("lsce_detail", "Monitoring active liquidation zones.")

        disaster_stop = regime.get("disaster_stop_price", regime.get("stop_price", 0.0))
        disaster_stop_dist = regime.get("disaster_stop_distance_pct", regime.get("stop_distance_pct", 0.0))
        structural_inval = regime.get("structural_invalidation_level", swing_low)
        stop_note = regime.get("stop_placement_note", "")
        effective_risk = risk.get("effective_risk_budget_pct", 0.0)

        regime_name = regime.get("name", "Unknown")
        majority = regime.get("majority_score", "")
        diagnosis = regime.get("diagnosis", "")
        dom_magnet = regime.get("dominant_magnet", "")
        dom_reason = regime.get("dominant_magnet_reason", "")
        rotation = regime.get("rotation", "Remain USDT")
        action = regime.get("action", "")
        sizing = regime.get("sizing_factor", 0.0)

        oi_delta_line = (
            f"1H: {oi_1h:+.2f}% | 4H: {oi_4h:+.2f}% | 24H: {oi_24h:+.2f}% | 3D: {oi_3d:+.2f}%"
            if oi_hist_ok else "Multi-hour OI history unavailable on current fallback feed"
        )
        ls_line = (
            f"{ls_ratio:.2f} ({long_pct:.1f}% of tracked accounts are NET LONG"
            + (f"; 72h rank: p{ls_pct_72h:.0f})" if ls_pct_72h is not None else ")")
            if ls_avail else "Unavailable on current fallback feed"
        )
        atr_pct_note = f" | 72h Rank: p{atr_pct_72h:.0f}" if atr_pct_72h is not None else ""
        if sizing == 0.0:
            risk_banner = "STANDBY / CASH PRESERVATION (0.00% Active Risk — no spot trade active)"
        elif risk.get("risk_budget_ok"):
            risk_banner = f"APPROVED (Within 1% Risk Budget) [Portfolio Risk Capped at {effective_risk:.2f}%]"
        else:
            risk_banner = f"CASH PRESERVATION / RISK REDUCED [Portfolio Risk: {effective_risk:.2f}%]"

        upper_rows = [r for r in ladder if r["side"] == "upper"]
        lower_rows = [r for r in ladder if r["side"] == "lower"]
        upper_lines = "\n".join(
            f"  ▲ {r['tier']:<14} ${r['price']:,.0f} ({r['distance_pct']:+.2f}% / {r['distance_atr']:+.2f} ATR) | {self._format_pool_m(r['estimated_vol_m'])} (Modeled Estimate)"
            for r in upper_rows
        )
        lower_lines = "\n".join(
            f"  ▼ {r['tier']:<14} ${r['price']:,.0f} ({r['distance_pct']:+.2f}% / {r['distance_atr']:+.2f} ATR) | {self._format_pool_m(r['estimated_vol_m'])} (Modeled Estimate)"
            + (" [🔥 DOMINANT MAGNET CORE]" if r.get("is_nearest") else "")
            for r in lower_rows
        )

        prompt = f"""================================================================================
INSTITUTIONAL BITCOIN (BTC) ORDER FLOW & LIQUIDATION TELEMETRY AUDIT
System: BTC Magnet Monitor | Scan ID: {scan_id} | Cadence: Every 30m (:00 & :30 UTC)
Raw Spot Feed: {spot_src}
Raw Futures Feed: {fut_src}
Mandate: SPOT-ONLY ROTATION (BTC / USDT). Zero borrowed leverage. Zero shorting.
Timestamp: {ts[:19]} UTC | Status: {data.get('data_status', 'LIVE')}
================================================================================

[EXECUTIVE TRADING DIRECTIVE & SYSTEM CALL]:
• Engine Regime Diagnosis: {regime_name} ({majority})
• Physical Microstructure Diagnosis: {diagnosis}
• Recommended Spot Capital Rotation: {rotation}
• Playbook Execution Protocol: {action}
• Prescribed Position Sizing: {sizing}x ({int(sizing * 100)}% of deployable cash budget)
• Liquidation Sweep Engine (LSCE) Status: {lsce_status}
  └ Details: {lsce_detail}
• Dual Inviolable Stop Architecture:
  ├ Structural Invalidation: 1-Hour candle close below ${structural_inval:,.2f} (Floor breakdown)
  └ Inviolable Disaster Hard Stop: ${disaster_stop:,.2f} ({disaster_stop_dist:.2f}% distance) [Below 200D SMA (${ma_200d:,.0f}) & 25x shelf (${swing_low * 0.988:,.0f})]
  {('└ Placement Note: ' + stop_note) if stop_note else ''}
• Dominant Liquidation Magnet Target: {dom_magnet} ({dom_reason})
• Desk Risk Management Status: {risk_banner}

--------------------------------------------------------------------------------
SECTION 1 • RAW PRICE BENCHMARKS & RANGE GEOMETRY (MACRO STRUCTURE)
--------------------------------------------------------------------------------
• Current BTC Spot Price: ${price:,.2f}
• Daily VWAP (Anchored 00:00 UTC):   ${daily_vwap:,.2f} [Price is {((price - daily_vwap)/max(daily_vwap,1)*100):+.2f}% vs Daily VWAP]
• Weekly VWAP (Anchored Monday):     ${weekly_vwap:,.2f} [Price is {((price - weekly_vwap)/max(weekly_vwap,1)*100):+.2f}% vs Weekly VWAP]
• Moving Averages: 20D EMA: ${ema_20d:,.2f} | 50D EMA: ${ema_50d:,.2f} | 200D SMA: ${ma_200d:,.2f}
• 4-Hour Channel Range: ${swing_low:,.0f} (Floor) to ${swing_high:,.0f} (Ceiling) [Channel Width: {range_width:.2f}%]
• Multi-Day Structural Anchors: 3D Base Floor: ${base_floor:,.2f} | 24H Capitulation Low: ${cap_wick:,.2f}

--------------------------------------------------------------------------------
SECTION 2 • RAW ORDER FLOW & TAKER VOLUME DELTA (KLINE SPOT CVD)
--------------------------------------------------------------------------------
• 24h Spot Volume: {spot_vol:,.0f} BTC (Volume Ratio vs 20D MA: {spot_vol_ratio:.2f}x)
• Spot CVD Ratio (Kline Taker Buy / Sell Volume): {spot_cvd_ratio:.2f} (>1.0 = Spot Bids Leading, <1.0 = Spot Selling)
• Spot CVD Momentum Slopes: 7-Day: {spot_cvd_7d:+.0f} | 14-Day: {spot_cvd_14d:+.0f}
• Perpetual Futures Flow Trend: {perp_trend}
• Order Book Depth Balance (Bids vs Asks within ±1.5%): {bids_asks_depth:.2f}

--------------------------------------------------------------------------------
SECTION 3 • RAW DERIVATIVES POSITIONING ({oi_scope})
--------------------------------------------------------------------------------
• Tracked Venue Open Interest: {oi:,.1f} BTC (~${(oi * price) / 1e9:.2f}B notional in tracked contract(s))
• OI Multi-Timeframe Velocity: {oi_delta_line}
• 8-Hour Funding Rate: {funding_rate:+.4f}% [{funding_ann:+.2f}% Annualized] (Neutral baseline ~+0.0100%)
• Futures Basis (Annualized Contango/Backwardation Spread): {basis:+.2f}%
• Tracked Account Long/Short Ratio: {ls_line}

--------------------------------------------------------------------------------
SECTION 4 • VOLATILITY & MODELED LIQUIDATION LADDER (ALGORITHMIC ESTIMATE)
--------------------------------------------------------------------------------
• 14-Period 1-Hour ATR: ${atr:,.2f} (Compression vs 72h Peak: {atr_comp:.1f}%{atr_pct_note})

[UPPER SHORT LIQUIDATION POOLS (MODELED ESTIMATE ABOVE)]:
{upper_lines}

[ZERO-AXIS EQUILIBRIUM SPOT ANCHOR]:
  ● CURRENT BTC SPOT PRICE: ${price:,.2f} (Microstructure Baseline)

[LOWER LONG LIQUIDATION POOLS (MODELED ESTIMATE BELOW)]:
{lower_lines}

• Dual Imbalance Analysis (Modeled Estimate — wide band sensitivity when denominator ~${u_v:.1f}M is small):
  ├ Immediate Tier Imbalance: Lower 100x pool is {imm_disp} larger than Upper 50-100x pool ({self._format_pool_m(l_v)} vs {self._format_pool_m(u_v)}).
  ├ Total Leverage Ladder Imbalance (10x-100x Modeled Bands): Total Lower ({self._format_pool_m(tot_l_vol)}) vs Total Upper ({self._format_pool_m(tot_u_vol)}) = {tot_ratio:.2f}x skew.
  └ Active LSCE Sweep Confirmation Status: {lsce_status} ({lsce_detail})

================================================================================
INSTRUCTIONS FOR THE AI ANALYST (STRICT AUDIT MANDATE):
You are the Chief Risk Officer and Head of Microstructure at an institutional spot trading desk.
You are strictly bounded by a SPOT-ONLY investment mandate (USDT cash vs BTC spot). No leverage, no futures, no shorting.

Evaluate the live telemetry against the 5-Regime Radar Framework:
1. Spot-Led Expansion: Spot CVD leading, price holding VWAP, funding normal, OI stable. (Action: 0.75x-1.0x Long)
2. Leveraged / Fragile Upside: Price rising but Spot CVD flat/lagging, OI/funding surging. (Action: Trim/Stand aside 0.0x-0.25x)
3. Range / Liquidation Magnet: Price bound in channel, positioning crowded, liquidation clusters dominate. (Action: Trade the Magnet 0.5x-0.75x only upon confirmed LSCE sweep reclaim)
4. Cascade / Forced Deleveraging: Waterfall drop, massive long liquidations, OI crashing. (Action: 0.0x Wait, NEVER buy waterfall)
5. Distribution / Bear Continuation: Price below key VWAPs, Spot CVD negative, weak bounces. (Action: 0.0x Cash)
Default: Transition / Mixed (0.0x cash).

PROVIDE YOUR PROFESSIONAL CRITIQUE IN THIS EXACT 5-PART FORMAT:

1. REGIME VERDICT & INDEPENDENT VOTE:
   - State clearly whether you AGREE, DISAGREE, or call a different regime. Cite at least 3 specific empirical metrics.

2. DUAL LIQUIDATION HEATMAP IMBALANCE AUDIT (MODELED ESTIMATE):
   - Analyze both the Immediate Tier Imbalance ({imm_disp}) and the Total Leverage Ladder Imbalance ({tot_ratio:.2f}x across modeled 10x-100x bands).
   - How does small denominator sensitivity (~${u_v:.1f}M upper vs ~${l_v:.1f}M lower) affect interpretation?

3. SPOT EXECUTION & LSCE SWEEP DIRECTIVE:
   - Critique the engine's suggested action: '{action}' ({sizing}x sizing) under LSCE state '{lsce_status}'.
   - State clearly how a spot trader should execute right now given reclaim thresholds.

4. DUAL INVIOLABLE STOP-LOSS SAFETY CHECK:
   - Audit Structural Invalidation (${structural_inval:,.2f}) vs Disaster Stop (${disaster_stop:,.2f}, {disaster_stop_dist:.2f}% distance, anchored below 200D SMA ${ma_200d:,.0f} & 25x shelf ${swing_low * 0.988:,.0f} vs 10x shelf ${swing_low * 0.975:,.0f}).

5. SPECIFIC INVALIDATION & RED FLAGS:
   - What exact microstructure changes would invalidate this thesis or force an emergency exit to 100% USDT cash?
================================================================================"""
        return prompt.strip()

    def _render_html(self, data: Dict[str, Any], is_mobile: bool = False) -> str:
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})

        regime_id = regime.get("regime_id", "RANGE_LIQUIDATION_MAGNET")
        name = regime.get("name", regime.get("regime", "Range / Liquidation Magnet"))
        diagnosis = regime.get("diagnosis", "")
        playbook = regime.get("playbook", "")
        majority_score = regime.get("majority_score", "4/4 observations confirmed")
        rotation = regime.get("rotation", "Remain USDT")
        sizing = regime.get("sizing_factor", 0.0)
        action = regime.get("action", "")
        stop_rule = regime.get("stop_rule", "")
        stop_price = regime.get("stop_price", 0.0)
        stop_dist = regime.get("stop_distance_pct", 0.0)
        entry_inst = regime.get("entry_instruction", "")
        dom_magnet = regime.get("dominant_magnet", "Neutral")
        dom_reason = regime.get("dominant_magnet_reason", dom_magnet)
        notes = regime.get("notes", "")
        data_quality = regime.get("data_quality", "LIVE")

        plain_verdict = regime.get("plain_english_verdict", "Analyzing current market conditions...")
        why_points = regime.get("why_points", [])
        why_sizing = regime.get("why_sizing_reason", f"Deploying {sizing*100:.0f}% of available cash based on regime risk parameters.")
        why_stop = regime.get("why_stop_reason", f"Safety stop anchored at ${stop_price:,.2f} ({stop_dist:.2f}% distance).")

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}

        # Institutional Upgrades: Dual Imbalance & LSCE & Dual Stops
        imm_ratio = regime.get("immediate_imbalance_ratio", 1.0)
        tot_l_vol = regime.get("total_ladder_lower_vol", 0.0)
        tot_u_vol = regime.get("total_ladder_upper_vol", 0.0)
        tot_ratio = regime.get("total_ladder_imbalance_ratio", 1.0)
        lsce_status = regime.get("lsce_status", "UNTESTED")
        lsce_detail = regime.get("lsce_detail", "")
        disaster_stop = regime.get("disaster_stop_price", stop_price)
        disaster_stop_dist = regime.get("disaster_stop_distance_pct", stop_dist)
        structural_inval = regime.get("structural_invalidation_level", metrics.get("swing_low_4h", 0.0))

        if lsce_status == "SWEEP_AND_RECLAIM_CONFIRMED":
            if sizing > 0 and "USDT -> BTC" in rotation:
                lsce_badge_class = "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
                lsce_badge_icon = "✅"
                lsce_badge_title = f"SWEEP &amp; RECLAIM CONFIRMED (BUY AUTHORIZED {sizing:.2f}x)"
            else:
                lsce_badge_class = "border-amber-500/40 bg-amber-500/15 text-amber-300"
                lsce_badge_icon = "🛡️"
                lsce_badge_title = "LOCAL SWEEP OBSERVED — BUY BLOCKED BY MACRO REGIME"
        elif lsce_status == "SWEEP_IN_PROGRESS":
            lsce_badge_class = "border-amber-500/40 bg-amber-500/15 text-amber-300 animate-pulse"
            lsce_badge_icon = "⚠️"
            lsce_badge_title = "SWEEP IN PROGRESS (DO NOT BUY)"
        elif lsce_status == "SWEEP_FAILED_BREAKDOWN":
            lsce_badge_class = "border-rose-500/40 bg-rose-500/15 text-rose-300"
            lsce_badge_icon = "🚨"
            lsce_badge_title = "SWEEP FAILED / CASCADE RISK (100% CASH)"
        else:
            lsce_badge_class = "border-zinc-700 bg-zinc-800/80 text-zinc-300"
            lsce_badge_icon = "⏸️"
            lsce_badge_title = "UNTESTED (MONITORING / CASH)"

        magnet_factors = regime.get("magnet_factors", {})
        f1 = magnet_factors.get("factor_1_size", "Evaluating cluster size disparity...")
        f2 = magnet_factors.get("factor_2_spot_leadership", "Evaluating spot vs derivatives CVD...")
        f3 = magnet_factors.get("factor_3_crowding_fuel", "Evaluating funding and positioning crowding...")
        f4 = magnet_factors.get("factor_4_regime_structure", "Evaluating regime structure...")
        f5 = magnet_factors.get("factor_5_asymmetry", "Evaluating cluster distance asymmetry...")
        f6 = magnet_factors.get("factor_6_atr_volatility", "Evaluating ATR compression...")

        # Specific styling tokens for the Standout Regime Panel
        if regime_id == "SPOT_LED_EXPANSION":
            regime_border_color = "border-emerald-500/50 shadow-emerald-500/10"
            regime_badge_bg = "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
            regime_icon = "🚀"
            regime_tagline = "Genuine spot buyers in control. Favorable environment for trend-following spot longs."
        elif regime_id == "LEVERAGED_FRAGILE_UPSIDE":
            regime_border_color = "border-orange-500/50 shadow-orange-500/10"
            regime_badge_bg = "bg-orange-500/15 text-orange-300 border-orange-500/30"
            regime_icon = "⚠️"
            regime_tagline = "Advance built on dangerous borrowed futures leverage. High probability of long squeeze."
        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            regime_border_color = "border-rose-500/60 shadow-rose-500/15"
            regime_badge_bg = "bg-rose-500/15 text-rose-300 border-rose-500/30"
            regime_icon = "⚡"
            regime_tagline = "Forced margin liquidation cascade in progress. Strictly avoid buying until selling ceases."
        elif regime_id == "DISTRIBUTION_BEAR_CONTINUATION":
            regime_border_color = "border-rose-500/50 shadow-rose-500/10"
            regime_badge_bg = "bg-rose-500/15 text-rose-300 border-rose-500/30"
            regime_icon = "📉"
            regime_tagline = "Structural seller control. Whales distributing into retail bounces. Cash preservation priority."
        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            regime_border_color = "border-cyan-500/50 shadow-cyan-500/10"
            regime_badge_bg = "bg-cyan-500/15 text-cyan-300 border-cyan-500/30"
            regime_icon = "🧲"
            regime_tagline = "Price bound within defined horizontal channel. Positioning imbalance and liquidation magnets dominate."
        else:
            regime_border_color = "border-amber-500/60 shadow-[0_0_25px_rgba(245,158,11,0.12)]"
            regime_badge_bg = "bg-amber-500/15 text-amber-300 border-amber-500/30"
            regime_icon = "⚖️"
            regime_tagline = "Market indicators conflicting or transitioning between regimes. Capital preservation in cash."

        # Action banner color styling
        if "USDT -> BTC" in rotation:
            action_bg = "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
            action_pill = "Buy Spot (Accumulate)"
        elif "BTC -> USDT" in rotation:
            action_bg = "bg-rose-500/10 border-rose-500/30 text-rose-400"
            action_pill = "Trim Spot / Harvest to Cash"
        else:
            action_bg = "bg-amber-500/10 border-amber-500/30 text-amber-400"
            action_pill = "Hold 100% Cash Reserve"

        ev_border = "border-amber-500/35" if regime_id == "TRANSITION_MIXED" else "border-emerald-500/35"
        # Evidence Cards for the Standout Regime Panel
        evidence_cards_html = "".join([
            f"""<div class='flex items-start gap-2.5 p-3 rounded-xl bg-zinc-950/75 border {ev_border}'>
                 <span class='text-emerald-400 font-bold mt-0.5 text-xs'>✓</span>
                 <span class='text-xs text-zinc-200 leading-relaxed'>{item}</span>
               </div>"""
            for item in regime.get("matched_criteria", [])
        ])

        # Why Points HTML
        why_points_html = "".join([
            f"""<div class='flex items-start gap-3 p-3.5 rounded-xl bg-zinc-950/80 border border-emerald-500/30'>
                 <span class='w-6 h-6 rounded-full bg-emerald-500/15 border border-emerald-500/40 flex items-center justify-center text-xs font-bold text-emerald-400 flex-shrink-0 mt-0.5'>{idx+1}</span>
                 <p class='text-xs sm:text-sm text-zinc-300 leading-relaxed font-normal'>{pt}</p>
               </div>"""
            for idx, pt in enumerate(why_points)
        ])

        ts_iso = str(data.get("timestamp", ""))
        scan_id = self._compute_scan_id(data)
        utc_time_str, sgt_time_str, scan_date_str = self._format_utc_sgt(ts_iso)
        ladder = self._get_canonical_ladder(data)

        price = metrics.get("price", 0.0)
        price_change_24h = metrics.get("price_change_24h_pct", 0.0)
        daily_vwap = metrics.get("daily_vwap", 0.0)
        weekly_vwap = metrics.get("weekly_vwap", 0.0)
        ema_20d = metrics.get("ema_20d", 0.0)
        ema_50d = metrics.get("ema_50d", 0.0)
        ma_200d = metrics.get("ma_200d", 0.0)
        swing_high = metrics.get("swing_high_4h", 0.0)
        swing_low = metrics.get("swing_low_4h", 0.0)
        base_floor = metrics.get("base_floor", 0.0)
        funding_rate = metrics.get("funding_rate", 0.0) * 100
        spot_cvd_ratio = metrics.get("spot_cvd_ratio", 1.0)
        oi_change_24h = metrics.get("oi_change_24h_pct", 0.0)
        oi_change_1h = metrics.get("oi_change_1h_pct", 0.0)
        oi_change_4h = metrics.get("oi_change_4h_pct", 0.0)
        oi_hist_ok = bool(metrics.get("oi_history_available", True))
        basis = metrics.get("futures_basis_annualized", 0.0)
        ls_ratio = metrics.get("long_short_account_ratio", 1.0)
        ls_avail = bool(metrics.get("ls_ratio_available", True))
        ls_pct_72h = metrics.get("ls_ratio_percentile_72h")
        atr_pct_72h = metrics.get("atr_percentile_72h")
        current_oi = metrics.get("open_interest", 0.0)
        spot_source = metrics.get("spot_data_source", "Binance Public Market-Data REST (data-api.binance.vision/api/v3)")
        futures_source = metrics.get("futures_data_source", "Perp Public REST")
        oi_scope = metrics.get("oi_scope", "Tracked venue perpetual subset (not total market OI)")
        stop_note = regime.get("stop_placement_note", "")

        oi_24h_str = f"{oi_change_24h:+.2f}%" if oi_hist_ok else "N/A (Fallback)"
        oi_1h_str = f"{oi_change_1h:+.2f}%" if oi_hist_ok else "N/A"
        oi_4h_str = f"{oi_change_4h:+.2f}%" if oi_hist_ok else "N/A"
        ls_pct_disp = f"{ls_ratio:.2f}" + (f" (p{ls_pct_72h:.0f} 72h)" if ls_pct_72h is not None else "") if ls_avail else "Unavailable"
        atr_pct_disp = f" (p{atr_pct_72h:.0f} 72h)" if atr_pct_72h is not None else ""

        upper_ladders_html = []
        lower_ladders_html = []
        for row in ladder:
            vol_disp = self._format_pool_m(row["estimated_vol_m"])
            if row["side"] == "upper":
                if row.get("is_nearest"):
                    w_bar = min(100, max(15, row["estimated_vol_m"] / 20.0 * 100.0))
                    upper_ladders_html.append(f"""          <!-- Upper Tier: {row['tier']} Nearest Active Pool -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/45">
            <div class="flex items-center gap-2.5 w-48">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">{row['tier']}</span>
              <span class="font-mono font-bold text-rose-300">${row['price']:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-rose-700 to-rose-400 h-full rounded-full" style="width: {w_bar:.0f}%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-rose-400 text-xs w-44">
              {row['distance_pct']:+.2f}% &bull; {vol_disp} <span class="text-[10px] text-zinc-500">(Est.)</span>
            </div>
          </div>""")
                else:
                    w_bar = 35 if row["leverage"] == "10x" else 48
                    upper_ladders_html.append(f"""          <!-- Upper Tier: {row['tier']} -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/50 border border-rose-500/25 hover:border-rose-500/45 transition-colors">
            <div class="flex items-center gap-2.5 w-48">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">{row['tier']}</span>
              <span class="font-mono text-zinc-300">${row['price']:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-rose-900 to-rose-600 h-full rounded-full" style="width: {w_bar}%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-zinc-400 text-xs w-44">
              {row['distance_pct']:+.2f}% &bull; {vol_disp} <span class="text-[10px] text-zinc-500">(Est.)</span>
            </div>
          </div>""")
            else:
                if row.get("is_nearest"):
                    sweep_tag = " <span class='text-[10px] text-rose-300 font-bold'>&laquo; TESTING</span>" if "SWEEP" in lsce_status else ""
                    lower_ladders_html.append(f"""          <!-- Lower Tier: {row['tier']} DOMINANT MAGNET CORE -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 border-2 border-emerald-500/50 shadow-lg shadow-emerald-500/10">
            <div class="flex items-center gap-2.5 w-48">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/25 text-emerald-300 border border-emerald-500/50 flex items-center gap-1">
                <span>🔥</span> {row['tier']}
              </span>
              <span class="font-mono font-extrabold text-emerald-300">${row['price']:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-3 rounded-full overflow-hidden p-0.5">
                <div class="bg-gradient-to-r from-emerald-600 via-emerald-400 to-amber-300 h-full rounded-full animate-pulse" style="width: 100%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-emerald-300 font-bold text-xs w-44">
              {row['distance_pct']:+.2f}% &bull; {vol_disp}{sweep_tag}
            </div>
          </div>""")
                else:
                    w_bar = 55 if row["leverage"] == "25x" else 40
                    lower_ladders_html.append(f"""          <!-- Lower Tier: {row['tier']} -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/50 border border-emerald-500/25 hover:border-emerald-500/45 transition-colors">
            <div class="flex items-center gap-2.5 w-48">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">{row['tier']}</span>
              <span class="font-mono text-zinc-300">${row['price']:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-emerald-900 to-emerald-600 h-full rounded-full" style="width: {w_bar}%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-zinc-400 text-xs w-44">
              {row['distance_pct']:+.2f}% &bull; {vol_disp} <span class="text-[10px] text-zinc-500">(Est.)</span>
            </div>
          </div>""")
        upper_ladder_block = "\n".join(upper_ladders_html)
        lower_ladder_block = "\n".join(lower_ladders_html)

        imm_disp = f"~{round(imm_ratio):.0f}x" if imm_ratio >= 10 else f"{imm_ratio:.1f}x"

        # Build raw & blind prompts for clipboard
        llm_prompt = self._build_llm_prompt(data)
        llm_prompt_escaped = llm_prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        blind_prompt = self._build_blind_llm_prompt(data)
        blind_prompt_escaped = blind_prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Unified PWA meta and styling tags (applies to both index.html and app.html)
        page_title = "BTC Magnet Monitor — 5-Regime Radar &amp; AI Telemetry Cockpit"
        body_padding = "pb-16"

        pwa_meta_tags = """  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="BTC Magnet">
  <meta name="theme-color" content="#09090b">
  <link rel="manifest" href="manifest.json?v=7">
  <link rel="icon" type="image/png" sizes="192x192" href="icon-192.png?v=7">
  <link rel="icon" type="image/png" sizes="512x512" href="icon-512.png?v=7">
  <link rel="apple-touch-icon" href="icon-192.png?v=7">
  <link rel="shortcut icon" href="icon-192.png?v=7">"""

        top_switch_button = """<a href="text.html" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-950/60 hover:bg-emerald-900/60 text-xs font-semibold text-emerald-400 border border-emerald-700/80 transition-colors">
          <span>📱 Text Terminal</span>
        </a>
        <a href="regimes.html" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-cyan-400 border border-zinc-700/80 transition-colors">
          <span>5 Regimes Guide &rarr;</span>
        </a>
        <a href="regime.json" target="_blank" class="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-zinc-400 hover:text-zinc-200 border border-zinc-800 transition-colors">
          <span>REST API</span>
        </a>"""

        mobile_nav_bar = ""

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
{pwa_meta_tags}
  <title>{page_title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #09090b;
      color: #f4f4f5;
    }}
    .mono {{
      font-family: 'JetBrains Mono', monospace;
    }}
    html {{
      scroll-behavior: smooth;
    }}
  </style>
</head>
<body class="min-h-screen bg-zinc-950 text-zinc-100 antialiased {body_padding}">

  <!-- Data-Age / Staleness Banner (filled in by script; always tells the user how old the verdict is) -->
  <div id="data-age-banner" role="status" aria-live="polite" class="px-4 py-2 text-center text-xs font-semibold border-b border-zinc-800 bg-zinc-900 text-zinc-300">
    Checking scan freshness...
  </div>

  <!-- Swappable content root: the script replaces this with the latest live scan when a newer one exists -->
  <div id="app-root" data-scan-ts="{data.get("timestamp", "")}">

  <!-- Top Navigation Bar -->
  <header class="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-50 px-4 sm:px-6 py-3.5">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl overflow-hidden border border-zinc-800 flex items-center justify-center shadow-inner flex-shrink-0 bg-zinc-950 p-0.5">
          <img src="./assets/app-logo.png?v=4" alt="BTC Magnet Monitor Logo" class="w-full h-full object-contain">
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-base tracking-tight text-white">BTC Magnet Monitor</span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-zinc-800/80 text-zinc-300 border border-zinc-700/60">5-Regime Radar</span>
          </div>
          <p class="text-xs text-zinc-400 hidden sm:block">Observable Positioning Mechanics &amp; Regime Intelligence</p>
        </div>
      </div>

      <div class="flex items-center gap-3 sm:gap-6">
        {top_switch_button}
        <div class="text-right">
          <div class="text-[11px] font-medium text-zinc-400">Bitcoin Price</div>
          <div class="text-base font-bold mono text-white">${price:,.2f}</div>
        </div>
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium {'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' if data_quality == 'LIVE' else 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}">
          <span class="w-2 h-2 rounded-full {'bg-emerald-400' if data_quality == 'LIVE' else 'bg-amber-400'} animate-pulse"></span>
          <span>{data_quality}</span>
        </div>
      </div>
    </div>
  </header>

  <!-- Sub-Header Info Bar -->
  <div class="border-b border-indigo-500/30 bg-zinc-900/40 px-4 sm:px-6 py-2 text-xs text-zinc-400">
    <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
      <div>Raw Feeds: <span class="text-zinc-300">{spot_source}</span> &bull; <span class="text-zinc-300">{futures_source}</span></div>
      <div>Last Scan: <span class="text-zinc-200 font-medium mono">{utc_time_str}</span> (<span class="text-emerald-300 mono">{sgt_time_str}</span>) &bull; Cadence: <span class="text-indigo-300 font-semibold">Every 30m (:00/:30 UTC)</span> &bull; Next: <span id="subhdr-next-update" class="text-amber-300 mono font-semibold">--:-- UTC</span></div>
    </div>
  </div>

  <main class="max-w-6xl mx-auto px-4 sm:px-6 pt-6 space-y-6">

    <!-- ============================================================ -->
    <!-- PANEL 1: REAL-TIME BTC SPOT PRICE & MARKET SESSION COCKPIT    -->
    <!-- ============================================================ -->
    <div id="panel-1" class="rounded-2xl border-2 border-emerald-500/60 bg-gradient-to-b from-zinc-950 via-zinc-900/90 to-zinc-950 p-5 sm:p-6 backdrop-blur-md shadow-[0_0_25px_rgba(16,185,129,0.12)] space-y-4">
      
      <!-- Top Section: Live Ticker & Drift -->
      <div class="p-4 sm:p-5 rounded-xl bg-zinc-950/90 border border-emerald-500/45 shadow-inner">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="space-y-1.5">
            <div class="flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
              <span class="text-xs font-bold tracking-wider uppercase text-emerald-400 mono">Panel 1 &bull; Real-Time BTC Spot Price (Live)</span>
            </div>
            <div class="flex items-baseline gap-3 flex-wrap">
              <div id="live-btc-price" class="text-3xl sm:text-5xl font-extrabold mono text-white tracking-tight">
                ${price:,.2f}
              </div>
              <div class="px-2.5 py-1 rounded-md text-xs font-mono font-bold {'bg-rose-500/20 text-rose-300 border border-rose-500/30' if price_change_24h < 0 else 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'}">
                {price_change_24h:+.2f}% (24h)
              </div>
            </div>
            <div class="text-xs text-zinc-400 mono pt-0.5">
              Drift vs Scan (${price:,.2f}): <span id="live-price-drift" class="text-zinc-200 font-medium">$0.00 (0.00%)</span>
            </div>
          </div>

          <div class="text-left sm:text-right space-y-1 border-t sm:border-t-0 border-zinc-800 pt-2 sm:pt-0">
            <div class="text-xs font-bold uppercase tracking-wider text-zinc-300 mono">Binance Spot Public Ticker</div>
            <div class="text-[11px] text-zinc-400 mono">Live REST 3s Price Feed</div>
            <div id="live-ticker-status" class="inline-flex items-center gap-1.5 text-[11px] px-2 py-0.5 rounded bg-zinc-900 border border-emerald-500/40 text-emerald-400 mono">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Live Exchange REST Feed
            </div>
          </div>
        </div>
      </div>

      <!-- Middle Section: Dual Clocks (UTC & SGT) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        <!-- UTC Clock -->
        <div class="p-4 rounded-xl bg-zinc-950/80 border border-sky-500/45 space-y-1">
          <div class="flex items-center gap-2 text-xs font-semibold text-sky-400 uppercase tracking-wider">
            <span>🌐</span>
            <span>UTC Time (Exchange Standard)</span>
          </div>
          <div id="clock-utc-time" class="text-2xl sm:text-3xl font-extrabold mono text-white tracking-tight">
            --:--:-- UTC
          </div>
          <div id="clock-utc-date" class="text-xs text-zinc-400 mono">
            {scan_date_str}
          </div>
        </div>

        <!-- SGT Clock (UTC+8) -->
        <div class="p-4 rounded-xl bg-zinc-950/80 border border-teal-500/45 space-y-1">
          <div class="flex items-center gap-2 text-xs font-semibold text-teal-400 uppercase tracking-wider">
            <span>🇸🇬</span>
            <span>SGT Time (UTC+8 Asia Anchor)</span>
          </div>
          <div id="clock-sgt-time" class="text-2xl sm:text-3xl font-extrabold mono text-emerald-300 tracking-tight">
            --:--:-- SGT
          </div>
          <div id="clock-sgt-date" class="text-xs text-zinc-400 mono">
            {scan_date_str}
          </div>
        </div>
      </div>

      <!-- Automated Update Cadence & Next Scheduled Update Card -->
      <div class="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/45 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="space-y-0.5">
          <div class="text-xs font-bold uppercase tracking-wider text-indigo-400 mono">Automated Telemetry Schedule</div>
          <div class="text-xs text-zinc-300">
            Updates <strong class="text-white">Every 30 Minutes</strong> (:00 &amp; :30 UTC) &bull; Last Scan: <span class="mono text-zinc-200">{utc_time_str} ({sgt_time_str})</span>
          </div>
        </div>
        <div class="text-left sm:text-right border-t sm:border-t-0 border-indigo-500/30 pt-2 sm:pt-0">
          <div class="text-[11px] text-indigo-300 uppercase font-bold tracking-wider mono">Next Scheduled Update</div>
          <div class="text-sm font-extrabold mono text-white">
            <span id="next-update-time">--:-- UTC (--:-- SGT)</span>
            <span id="next-update-countdown" class="ml-2 text-xs text-emerald-400">in --m --s</span>
          </div>
        </div>
      </div>

      <!-- Bottom Section: Active Market Session Zone -->
      <div class="p-4 sm:p-5 rounded-xl bg-zinc-950/90 border border-violet-500/45 space-y-2">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span class="text-xs font-bold uppercase tracking-wider text-violet-300 mono">Active Market Session Zone</span>
          </div>
          <span id="session-badge" class="px-2.5 py-0.5 rounded text-[11px] font-mono font-bold uppercase border border-purple-500/40 bg-purple-500/15 text-purple-300">
            OFF-HOURS
          </span>
        </div>
        <div class="flex items-baseline gap-2">
          <span id="session-name" class="text-lg sm:text-xl font-bold text-white">
            🌙 Pacific / Off-Hours Transition
          </span>
        </div>
        <div class="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-zinc-400 gap-1 pt-1 border-t border-zinc-800/60">
          <div id="session-hours" class="mono text-zinc-300">
            21:00 - 00:00 UTC (05:00 - 08:00 SGT)
          </div>
          <div id="session-desc" class="text-zinc-400">
            Off-Hours Liquidity &bull; Mean Reversion &amp; Overnight Reset
          </div>
        </div>
      </div>

    </div>

    <!-- ============================================================ -->
    <!-- PANEL 2: ON-EXCHANGE TELEMETRY (4 MICROSTRUCTURE FEEDS)      -->
    <!-- ============================================================ -->
    <div id="panel-2" class="rounded-2xl border-2 border-cyan-500/60 bg-gradient-to-b from-zinc-950 via-zinc-900/90 to-zinc-950 p-5 sm:p-6 backdrop-blur-md shadow-[0_0_25px_rgba(6,182,212,0.12)] space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-cyan-500/30 pb-3">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold uppercase tracking-widest text-cyan-400">Panel 2 &bull; On-Exchange Telemetry &amp; Modeled Pools</span>
            <span class="text-[11px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 mono">Raw Feeds (1-3) + Modeled Pools (4)</span>
          </div>
          <h3 class="text-lg sm:text-xl font-bold text-white mt-0.5">Real-Time Market Microstructure Feeds</h3>
        </div>
        <div class="text-xs text-zinc-400">
          Sources: <span class="text-zinc-200 mono">{spot_source} &bull; {futures_source}</span>
        </div>
      </div>

      <!-- 4 Categories Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5 text-xs">
        
        <!-- Category 1: Price & Structure -->
        <div class="p-4 rounded-xl bg-zinc-950/90 border border-cyan-500/45 space-y-2">
          <div class="text-[11px] font-bold uppercase tracking-wider text-cyan-400 border-b border-cyan-500/30 pb-1.5 flex items-center justify-between">
            <span>1. Price &amp; Structure</span>
            <span class="text-[10px] text-cyan-300 font-mono">Raw Spot</span>
          </div>
          <div class="space-y-1.5 text-zinc-300">
            <div class="flex justify-between"><span>Spot Price:</span> <span class="font-mono font-bold text-white">${price:,.2f}</span></div>
            <div class="flex justify-between"><span>Daily VWAP:</span> <span class="font-mono text-zinc-300">${daily_vwap:,.2f}</span></div>
            <div class="flex justify-between"><span>Weekly VWAP:</span> <span class="font-mono text-zinc-300">${weekly_vwap:,.2f}</span></div>
            <div class="flex justify-between"><span>20D EMA:</span> <span class="font-mono text-zinc-300">${ema_20d:,.2f}</span></div>
            <div class="flex justify-between"><span>50D EMA:</span> <span class="font-mono text-zinc-300">${ema_50d:,.2f}</span></div>
            <div class="flex justify-between"><span>200D SMA:</span> <span class="font-mono text-zinc-300">${ma_200d:,.2f}</span></div>
            <div class="flex justify-between"><span>4H Swing Range:</span> <span class="font-mono text-zinc-300">${swing_low:,.0f} - ${swing_high:,.0f}</span></div>
            <div class="flex justify-between"><span>3D Base Floor:</span> <span class="font-mono text-zinc-300">${base_floor:,.2f}</span></div>
          </div>
        </div>

        <!-- Category 2: Order Flow & CVD -->
        <div class="p-4 rounded-xl bg-zinc-950/90 border border-emerald-500/45 space-y-2">
          <div class="text-[11px] font-bold uppercase tracking-wider text-emerald-400 border-b border-emerald-500/30 pb-1.5 flex items-center justify-between">
            <span>2. Order Flow &amp; CVD</span>
            <span class="text-[10px] text-emerald-300 font-mono">Raw Taker</span>
          </div>
          <div class="space-y-1.5 text-zinc-300">
            <div class="flex justify-between"><span>Spot CVD Ratio:</span> <span class="font-mono font-bold text-emerald-400">{spot_cvd_ratio:.2f}</span></div>
            <div class="flex justify-between"><span>24h Spot Volume:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_vol_24h", 0.0):,.0f} BTC</span></div>
            <div class="flex justify-between"><span>Volume / 20D MA:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_vol_ratio", 1.0):.2f}x</span></div>
            <div class="flex justify-between"><span>7D Spot CVD Slope:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_cvd_slope_7d", 0.0):+.0f}</span></div>
            <div class="flex justify-between"><span>14D Spot CVD Slope:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_cvd_slope_14d", 0.0):+.0f}</span></div>
            <div class="flex justify-between"><span>Perp Flow Trend:</span> <span class="font-mono text-zinc-300 capitalize">{metrics.get("perp_cvd_trend", "Flat")}</span></div>
            <div class="flex justify-between"><span>Order Depth Ratio:</span> <span class="font-mono text-zinc-300">{metrics.get("bids_asks_depth_ratio", 1.0):.2f}</span></div>
          </div>
        </div>

        <!-- Category 3: Derivatives Crowding -->
        <div class="p-4 rounded-xl bg-zinc-950/90 border border-amber-500/45 space-y-2">
          <div class="text-[11px] font-bold uppercase tracking-wider text-amber-400 border-b border-amber-500/30 pb-1.5 flex items-center justify-between">
            <span>3. Derivatives Crowding</span>
            <span class="text-[10px] text-amber-300 font-mono">Venue OI</span>
          </div>
          <div class="space-y-1.5 text-zinc-300">
            <div class="flex justify-between" title="{oi_scope}"><span>Tracked Venue OI:</span> <span class="font-mono font-bold text-white">{current_oi:,.0f} BTC</span></div>
            <div class="flex justify-between"><span>OI 24h Change:</span> <span class="font-mono text-zinc-300">{oi_24h_str}</span></div>
            <div class="flex justify-between"><span>OI 1h / 4h:</span> <span class="font-mono text-zinc-300">{oi_1h_str} / {oi_4h_str}</span></div>
            <div class="flex justify-between"><span>Funding Rate (8h):</span> <span class="font-mono text-zinc-300">{funding_rate:+.4f}%</span></div>
            <div class="flex justify-between"><span>Futures Basis Ann.:</span> <span class="font-mono text-zinc-300">{basis:+.2f}%</span></div>
            <div class="flex justify-between"><span>Retail Long/Short:</span> <span class="font-mono text-zinc-300">{ls_pct_disp}</span></div>
            <div class="text-[10px] text-zinc-500 pt-1 border-t border-zinc-800/80 leading-tight">{oi_scope}</div>
          </div>
        </div>

        <!-- Category 4: Volatility & Magnets -->
        <div class="p-4 rounded-xl bg-zinc-950/90 border border-rose-500/45 space-y-2">
          <div class="text-[11px] font-bold uppercase tracking-wider text-rose-400 border-b border-rose-500/30 pb-1.5 flex items-center justify-between">
            <span>4. Volatility &amp; Magnets</span>
            <span class="text-[10px] text-rose-300 font-mono">Modeled Est.</span>
          </div>
          <div class="space-y-1.5 text-zinc-300">
            <div class="flex justify-between"><span>1H ATR:</span> <span class="font-mono text-zinc-300">${metrics.get("atr", 0.0):,.2f}</span></div>
            <div class="flex justify-between"><span>ATR Compression:</span> <span class="font-mono font-bold text-white">{metrics.get("atr_compression_pct", 0.0):.1f}%{atr_pct_disp}</span></div>
            <div class="flex justify-between"><span>4H Channel Width:</span> <span class="font-mono text-zinc-300">{(((swing_high - swing_low) / max(price, 1.0)) * 100):.2f}%</span></div>
            <div class="flex justify-between"><span>Upper Short Pool:</span> <span class="font-mono text-rose-400">${upper_c.get('price_level', 0.0):,.0f} (+{upper_c.get('distance_pct', 0.0):.2f}%)</span></div>
            <div class="flex justify-between"><span>Upper Est. Pool:</span> <span class="font-mono text-zinc-300">{self._format_pool_m(upper_c.get('estimated_vol_usd', 0.0)/1e6)}</span></div>
            <div class="flex justify-between"><span>Lower Long Pool:</span> <span class="font-mono text-emerald-400">${lower_c.get('price_level', 0.0):,.0f} (-{lower_c.get('distance_pct', 0.0):.2f}%)</span></div>
            <div class="flex justify-between"><span>Lower Est. Pool:</span> <span class="font-mono text-zinc-300">{self._format_pool_m(lower_c.get('estimated_vol_usd', 0.0)/1e6)}</span></div>
          </div>
        </div>

      </div>
    </div>

    <!-- ============================================================ -->
    <!-- PANEL 3: MACRO MARKET REGIME DIAGNOSIS                       -->
    <!-- ============================================================ -->
    <div id="panel-3" class="rounded-2xl border-2 {regime_border_color} bg-gradient-to-b from-zinc-900/95 via-zinc-900/80 to-zinc-950 p-6 sm:p-8 backdrop-blur-md shadow-2xl relative overflow-hidden space-y-6">
      
      <!-- Top Bar: Category, Rule Score & Subpage Link -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-amber-500/25">
        <div>
          <div class="flex items-center gap-2 mb-1 flex-wrap">
            <span class="text-xs font-bold uppercase tracking-wider text-cyan-400">Panel 3 &bull; Macro Market Regime Diagnosis</span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700/60 mono">{majority_score}</span>
          </div>
          <h2 class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
            What market environment is Bitcoin currently in?
          </h2>
          <p class="text-xs text-zinc-400 mt-0.5">
            Bitcoin is classified strictly into 1 of 5 deterministic regimes (or Transition / Mixed when conflicted).
          </p>
        </div>

        <a href="regimes.html" class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-zinc-800/80 hover:bg-zinc-700 text-xs font-medium text-cyan-300 border border-cyan-500/40 transition-all self-start sm:self-auto">
          <span>Learn About the 5 Regimes &amp; Math</span>
          <span>&rarr;</span>
        </a>
      </div>

      <!-- Main Regime Hero Banner -->
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-5 p-5 sm:p-6 rounded-2xl bg-zinc-950/90 border border-amber-500/35">
        <div class="flex items-start gap-4">
          <div class="text-4xl sm:text-5xl mt-1 select-none">
            {regime_icon}
          </div>
          <div class="space-y-1">
            <div class="flex items-center gap-2.5 flex-wrap">
              <span class="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full {regime_badge_bg}">
                Active Market Regime
              </span>
              <span class="text-xs text-zinc-400 mono">Diagnostic Engine Call</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-black text-white tracking-tight">
              {name}
            </h1>
            <p class="text-sm font-semibold text-zinc-300">
              {diagnosis}
            </p>
            <p class="text-xs text-zinc-400 leading-relaxed pt-0.5">
              {regime_tagline}
            </p>
          </div>
        </div>

        <div class="flex flex-col sm:flex-row md:flex-col gap-2 shrink-0 border-t md:border-t-0 md:border-l border-zinc-800/80 pt-3 md:pt-0 md:pl-6">
          <div class="text-xs text-zinc-400">Rule Match Confirmation:</div>
          <div class="text-sm font-bold {'text-amber-300' if regime_id == 'TRANSITION_MIXED' else 'text-emerald-400'} flex items-center gap-1.5">
            <span>{'⚠️' if regime_id == 'TRANSITION_MIXED' else '✓'}</span> {majority_score}
          </div>
          <div id="confidence-freshness-tag" class="text-[11px] text-zinc-400">Deterministic Rule Gate Status</div>
        </div>
      </div>

      <!-- Verified On-Exchange Evidence Checklist -->
      <div class="space-y-2.5">
        <div class="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center justify-between">
          <span>Verified On-Exchange Evidence ({majority_score})</span>
          <span class="text-[11px] text-zinc-400 font-normal">Rule Gate Check</span>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {evidence_cards_html}
        </div>
      </div>

      <!-- 5-Regime Radar Framework Matrix + Transition Overlay -->
      <div class="pt-4 border-t border-zinc-800/80 space-y-2">
        <div class="text-[11px] font-bold uppercase tracking-wider text-zinc-400">5-Regime Radar Framework Matrix</div>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 text-center text-xs">
          <a href="regimes.html#regime-1" class="p-2.5 rounded-xl border {'border-emerald-400 bg-emerald-500/15 text-emerald-300 font-bold shadow-sm' if regime_id == 'SPOT_LED_EXPANSION' else 'border-emerald-500/30 bg-zinc-950/60 text-zinc-400 hover:border-emerald-500/60'} transition-all">
            1. Spot Expansion
          </a>
          <a href="regimes.html#regime-2" class="p-2.5 rounded-xl border {'border-orange-400 bg-orange-500/15 text-orange-300 font-bold shadow-sm' if regime_id == 'LEVERAGED_FRAGILE_UPSIDE' else 'border-orange-500/30 bg-zinc-950/60 text-zinc-400 hover:border-orange-500/60'} transition-all">
            2. Leveraged Trap
          </a>
          <a href="regimes.html#regime-3" class="p-2.5 rounded-xl border {'border-cyan-400 bg-cyan-500/15 text-cyan-300 font-bold shadow-sm' if regime_id == 'RANGE_LIQUIDATION_MAGNET' else 'border-cyan-500/30 bg-zinc-950/60 text-zinc-400 hover:border-cyan-500/60'} transition-all">
            3. Range / Magnet
          </a>
          <a href="regimes.html#regime-4" class="p-2.5 rounded-xl border {'border-rose-400 bg-rose-500/15 text-rose-300 font-bold shadow-sm' if regime_id == 'CASCADE_FORCED_DELEVERAGING' else 'border-rose-500/30 bg-zinc-950/60 text-zinc-400 hover:border-rose-500/60'} transition-all">
            4. Cascade
          </a>
          <a href="regimes.html#regime-5" class="p-2.5 rounded-xl border {'border-rose-400 bg-rose-500/15 text-rose-300 font-bold shadow-sm' if regime_id == 'DISTRIBUTION_BEAR_CONTINUATION' else 'border-rose-500/30 bg-zinc-950/60 text-zinc-400 hover:border-rose-500/60'} transition-all">
            5. Distribution
          </a>
          <div class="p-2.5 rounded-xl border {'border-amber-400 bg-amber-500/15 text-amber-300 font-bold shadow-sm' if regime_id == 'TRANSITION_MIXED' else 'border-amber-500/30 bg-zinc-950/60 text-zinc-400'}">
            Transition / Mixed {'(ACTIVE)' if regime_id == 'TRANSITION_MIXED' else '(Fallback)'}
          </div>
        </div>
      </div>

    </div>

    <!-- ============================================================ -->
    <!-- BRIDGE: TWO INDEPENDENT VERDICT METHODS                      -->
    <!-- ============================================================ -->
    <div class="rounded-2xl border-2 border-violet-500/60 bg-gradient-to-r from-cyan-950/40 via-zinc-900/90 to-emerald-950/40 p-6 backdrop-blur-md shadow-[0_0_25px_rgba(139,92,246,0.12)] text-center space-y-3">
      <div class="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-violet-500/15 border border-violet-500/40 text-violet-300 text-xs font-extrabold uppercase tracking-wider">
        <span>⚖️ High-Conviction Decision Architecture</span>
      </div>
      <h3 class="text-xl sm:text-2xl font-black text-white tracking-tight">
        How to Get Your Trading Verdict: Two Independent Methods
      </h3>
      <p class="text-xs sm:text-sm text-zinc-300 max-w-2xl mx-auto leading-relaxed">
        Don't rely blindly on our verdict or any single algorithm. Choose between an unanchored blind metrics export for your own AI, or inspect our system's deterministic verdict and liquidation model below.
      </p>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl mx-auto pt-2 text-left">
        <a href="#method-1" class="p-4 rounded-xl bg-zinc-950/85 border border-sky-500/50 hover:border-sky-400 transition-all flex items-start gap-3">
          <span class="text-2xl">📋</span>
          <div>
            <div class="text-xs font-bold text-sky-400 uppercase tracking-wider">Method 1</div>
            <div class="text-sm font-extrabold text-white">Copy Data &amp; Prompt to AI</div>
            <p class="text-[11px] text-zinc-400 mt-0.5">Copy either Blind Telemetry (unanchored metrics-only vote) or Full Audit Prompt for ChatGPT, Claude, Grok, or Gemini.</p>
          </div>
        </a>

        <a href="#method-2" class="p-4 rounded-xl bg-zinc-950/85 border border-purple-500/50 hover:border-purple-400 transition-all flex items-start gap-3">
          <span class="text-2xl">🧠</span>
          <div>
            <div class="text-xs font-bold text-purple-400 uppercase tracking-wider">Method 2</div>
            <div class="text-sm font-extrabold text-white">Our System Verdict (Full-On View)</div>
            <p class="text-[11px] text-zinc-400 mt-0.5">Explore our plain-English verdict, 3 empirical drivers, LSCE state gate, 10x-100x modeled ladder, and 6-factor logic.</p>
          </div>
        </a>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- METHOD 1: VERDICT BY COPY DATA & PROMPT TO AI                -->
    <!-- ============================================================ -->
    <div id="method-1" class="rounded-2xl border-2 border-sky-500/60 bg-zinc-900/85 p-6 sm:p-8 backdrop-blur-md shadow-[0_0_25px_rgba(14,165,233,0.12)] space-y-5">
      
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-sky-500/25 pb-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-extrabold uppercase tracking-widest text-sky-400 flex items-center gap-1.5">
              <span>📋</span>
              <span>Method 1: Verdict by Copy Data &amp; Prompt to AI</span>
            </span>
          </div>
          <h2 class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
            Analyze Live Telemetry with Your Own AI
          </h2>
          <p class="text-xs sm:text-sm text-zinc-300 mt-1 max-w-2xl leading-relaxed">
            Use <strong>Blind Telemetry</strong> for an unanchored second opinion (no system verdict or sizing revealed), or <strong>Full Audit Prompt</strong> to stress-test our deterministic regime call.
          </p>
        </div>

        <!-- Dual One-Click Copy Buttons -->
        <div class="flex-shrink-0 flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          <button id="copy-blind-btn" onclick="copyBlindPrompt()" class="inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-black font-extrabold text-xs shadow-lg shadow-sky-500/25 transition-all cursor-pointer">
            <span id="copy-blind-icon" class="text-base">🧪</span>
            <span id="copy-blind-text">Copy Blind Telemetry (Unanchored)</span>
          </button>
          <button id="copy-prompt-btn" onclick="copyTelemetryPrompt()" class="inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs shadow-lg shadow-cyan-500/25 transition-all cursor-pointer">
            <span id="copy-btn-icon" class="text-base">📋</span>
            <span id="copy-btn-text">Copy Full Audit Prompt</span>
          </button>
        </div>
      </div>

      <!-- 3-Step Simple Instructions -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-sky-500/35 space-y-1">
          <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider">Step 1</span>
          <div class="font-bold text-white">Choose Blind or Full Copy</div>
          <p class="text-[11px] text-zinc-400">Blind exports raw exchange metrics and labeled modeled liquidity tiers without anchoring your AI to our verdict.</p>
        </div>

        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-cyan-500/35 space-y-1">
          <span class="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Step 2</span>
          <div class="font-bold text-white">Paste into Any Major LLM</div>
          <p class="text-[11px] text-zinc-400">Works seamlessly with Claude, ChatGPT, Grok, or Google Gemini.</p>
        </div>

        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-indigo-500/35 space-y-1">
          <span class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Step 3</span>
          <div class="font-bold text-white">Compare Independent Votes</div>
          <p class="text-[11px] text-zinc-400">Cross-check your AI's regime call and invalidation levels against Method 2 below.</p>
        </div>
      </div>

      <!-- Collapsible Blind Prompt Preview -->
      <details class="rounded-xl border border-sky-500/35 bg-zinc-950/70 p-4 text-xs text-zinc-400">
        <summary class="font-semibold text-sky-200 cursor-pointer hover:text-white flex items-center justify-between">
          <span>🧪 Preview Blind Metrics-Only Prompt — No Engine Verdict ({len(blind_prompt)} chars)</span>
          <span class="text-[11px] text-sky-400">Click to expand</span>
        </summary>
        <div class="mt-3 pt-3 border-t border-zinc-800 font-mono text-[11px] text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto bg-zinc-950 p-4 rounded-lg border border-sky-500/25">
{blind_prompt_escaped}
        </div>
      </details>

      <!-- Collapsible Full Audit Prompt Preview -->
      <details class="rounded-xl border border-cyan-500/35 bg-zinc-950/70 p-4 text-xs text-zinc-400">
        <summary class="font-semibold text-zinc-300 cursor-pointer hover:text-white flex items-center justify-between">
          <span>🔍 Preview Complete Telemetry &amp; Full Audit Prompt ({len(llm_prompt)} characters)</span>
          <span class="text-[11px] text-cyan-400">Click to expand</span>
        </summary>
        <div class="mt-3 pt-3 border-t border-zinc-800 font-mono text-[11px] text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto bg-zinc-950 p-4 rounded-lg border border-cyan-500/25">
{llm_prompt_escaped}
        </div>
      </details>

      <!-- Hidden Pre-Formatted Prompts for Copying -->
      <textarea id="blind-prompt-data" class="hidden" readonly>{blind_prompt_escaped}</textarea>
      <textarea id="llm-prompt-data" class="hidden" readonly>{llm_prompt_escaped}</textarea>
    </div>

    <!-- ============================================================ -->
    <!-- METHOD 2: OUR SYSTEM VERDICT • FULL-ON VIEW                  -->
    <!-- ============================================================ -->
    <div id="method-2" class="rounded-2xl border-2 border-purple-500/60 bg-zinc-900/85 p-6 sm:p-8 backdrop-blur-md shadow-[0_0_25px_rgba(168,85,247,0.12)] space-y-6">
      
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-500/25 pb-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-extrabold uppercase tracking-widest text-purple-400 flex items-center gap-1.5">
              <span>🧠</span>
              <span>Method 2: Our System Verdict (Full-On View)</span>
            </span>
          </div>
          <h2 class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
            Our System Verdict
          </h2>
          <p class="text-xs text-zinc-400 mt-0.5">
            Full-on view of our quantitative regime diagnosis, 3 empirical drivers, LSCE sweep status, 10x-100x modeled heatmap, and 6-factor decision hierarchy.
          </p>
        </div>
        <div class="px-3.5 py-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 text-amber-300 text-xs font-medium self-start sm:self-auto">
          <span class="text-zinc-400">Dominant Magnet:</span> <strong class="text-white ml-1">{dom_reason}</strong>
        </div>
      </div>

      <!-- Plain English Bottom Line Breakdown (For 95% Beginners) -->
      <div class="p-5 sm:p-6 rounded-2xl bg-zinc-950/90 border border-emerald-500/40 space-y-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-bold uppercase tracking-wider text-emerald-400">Bottom Line Verdict &bull; Plain English</span>
            <span class="text-xs text-zinc-500 font-medium">(No Jargon Required)</span>
          </div>
          <h3 class="text-lg sm:text-xl font-extrabold text-white tracking-tight">
            Why This Recommendation?
          </h3>
          <div class="mt-3 p-4 rounded-xl bg-zinc-900/60 border border-emerald-500/35 flex items-start gap-3">
            <span class="text-2xl">💡</span>
            <p class="text-sm sm:text-base text-zinc-200 font-medium leading-relaxed">
              {plain_verdict}
            </p>
          </div>
        </div>

        <!-- 3 Driving Market Factors & Sizing Breakdown -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-2">
          <div class="lg:col-span-2 space-y-2.5">
            <div class="text-xs font-bold uppercase tracking-wider text-zinc-400">The 3 Key Market Factors Driving This Call</div>
            <div class="space-y-2.5">
              {why_points_html}
            </div>
          </div>

          <div class="space-y-3">
            <div class="bg-zinc-900/60 p-4 rounded-xl border border-amber-500/40 space-y-1">
              <div class="text-xs font-bold uppercase tracking-wider text-amber-400">Why This Exact Sizing?</div>
              <p class="text-xs text-zinc-300 leading-relaxed font-normal">{why_sizing}</p>
              <div class="pt-1.5 text-[11px] font-mono text-zinc-400 border-t border-zinc-800/80">{risk.get('risk_advisory', '')}</div>
            </div>
            <div class="bg-zinc-900/60 p-4 rounded-xl border border-rose-500/40 space-y-1">
              <div class="text-xs font-bold uppercase tracking-wider text-rose-400">Where Is Your Safety Net?</div>
              <p class="text-xs text-zinc-300 leading-relaxed font-normal">{why_stop}</p>
              <p class="text-[11px] text-amber-300/90 leading-relaxed pt-1 border-t border-zinc-800/80 {'hidden' if not stop_note else ''}">{stop_note}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- LSCE Execution State Banner -->
      <div class="p-4 rounded-xl border {lsce_badge_class} flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
        <div class="flex items-center gap-3">
          <span class="text-2xl">{lsce_badge_icon}</span>
          <div>
            <div class="text-[10px] uppercase font-bold tracking-wider text-zinc-400">Liquidation Sweep Confirmation Engine (LSCE)</div>
            <div class="text-sm font-extrabold">{lsce_badge_title}</div>
          </div>
        </div>
        <div class="text-xs text-zinc-200 font-medium max-w-xl text-left sm:text-right bg-zinc-950/60 p-2.5 rounded-lg border border-zinc-700/70">
          {lsce_detail}
        </div>
      </div>

      <!-- Nearest Liquidity Pools Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Upper Short Pool -->
        <div class="bg-zinc-950/80 p-5 rounded-xl border border-rose-500/45 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-rose-400 uppercase tracking-wide">Upper Short Liquidity Pool</span>
            <span class="text-xs mono font-medium bg-zinc-800 text-zinc-200 px-2.5 py-0.5 rounded-full">
              +{upper_c.get('distance_pct', 0.0):.2f}% (+{upper_c.get('distance_atr', 0.0):.2f} ATR)
            </span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold mono text-white">
            ${upper_c.get('price_level', 0.0):,.2f}
          </div>
          <div class="text-xs text-zinc-400">
            Estimated Pool Size: <span class="font-bold text-zinc-200 mono">{self._format_pool_m(upper_c.get('estimated_vol_usd', 0.0)/1e6)}</span> <span class="text-[11px] text-zinc-500">(Modeled Estimate)</span>
          </div>
          <div class="w-full bg-zinc-900 h-2 rounded-full overflow-hidden">
            <div class="bg-rose-500 h-full rounded-full transition-all" style="width: min(100%, {max(15, upper_c.get('distance_pct', 1.0) * 15)}%);"></div>
          </div>
        </div>

        <!-- Lower Long Pool -->
        <div class="bg-zinc-950/80 p-5 rounded-xl border border-emerald-500/45 space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-emerald-400 uppercase tracking-wide">Lower Long Liquidity Pool</span>
            <span class="text-xs mono font-medium bg-zinc-800 text-zinc-200 px-2.5 py-0.5 rounded-full">
              -{lower_c.get('distance_pct', 0.0):.2f}% (-{lower_c.get('distance_atr', 0.0):.2f} ATR)
            </span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold mono text-white">
            ${lower_c.get('price_level', 0.0):,.2f}
          </div>
          <div class="text-xs text-zinc-400">
            Estimated Pool Size: <span class="font-bold text-zinc-200 mono">{self._format_pool_m(lower_c.get('estimated_vol_usd', 0.0)/1e6)}</span> <span class="text-[11px] text-zinc-500">(Modeled Estimate)</span>
          </div>
          <div class="w-full bg-zinc-900 h-2 rounded-full overflow-hidden">
            <div class="bg-emerald-500 h-full rounded-full transition-all" style="width: min(100%, {max(15, lower_c.get('distance_pct', 1.0) * 15)}%);"></div>
          </div>
        </div>
      </div>

      <!-- Visual Liquidation Heatmap & Leverage Depth Ladder (10x - 100x Bands) -->
      <div class="p-5 rounded-xl border border-indigo-500/45 bg-zinc-950/90 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-indigo-500/25 pb-3">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span>🔥</span>
              <span>Liquidation Heatmap &amp; Leverage Depth Map</span>
            </span>
            <span class="text-[11px] px-2 py-0.5 rounded bg-indigo-500/15 border border-indigo-500/35 text-indigo-300 font-mono">Modeled Estimate &bull; 10x - 100x Bands</span>
          </div>
          <div class="text-xs text-zinc-400 flex items-center gap-3">
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-rose-500"></span> Short Liq Pool</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-cyan-400"></span> Spot Price</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span> Long Liq Pool</span>
          </div>
        </div>

        <!-- Heatmap Depth Ladder Rows -->
        <div class="space-y-2 text-xs">
{upper_ladder_block}

          <!-- ZERO LINE: SPOT PRICE EQUILIBRIUM -->
          <div class="flex items-center justify-between p-3 rounded-xl bg-cyan-500/10 border-2 border-cyan-500/50 my-1">
            <div class="flex items-center gap-2.5">
              <span class="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping"></span>
              <span class="font-extrabold text-cyan-300 text-xs uppercase tracking-wider">Spot Price Zero-Axis</span>
            </div>
            <div class="font-mono font-extrabold text-white text-sm">
              ${price:,.2f}
            </div>
            <div class="text-xs text-cyan-400 font-mono hidden sm:block">
              Current Microstructure Anchor
            </div>
          </div>

{lower_ladder_block}
        </div>

        <!-- Dual Imbalance Display: Immediate Tier vs Total Ladder -->
        <div class="pt-3 border-t border-zinc-800/80 space-y-2">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div class="p-3 rounded-lg bg-zinc-900/60 border border-amber-500/40">
              <span class="text-[10px] uppercase font-bold text-amber-300 tracking-wider block">Immediate Nearest Tier Imbalance (100x vs 50-100x)</span>
              <div class="text-base font-extrabold text-amber-300 font-mono mt-0.5">{imm_disp} Skew <span class="text-[10px] text-zinc-400 font-normal">(Modeled)</span></div>
              <p class="text-[11px] text-zinc-400 mt-1">Single nearest bands: Lower Longs ({self._format_pool_m(lower_c.get('estimated_vol_usd', 0.0)/1e6)}) vs Upper Shorts ({self._format_pool_m(upper_c.get('estimated_vol_usd', 0.0)/1e6)}).{" Thin short denominator (<$5M) increases ratio sensitivity." if (upper_c.get('estimated_vol_usd', 0.0)/1e6) < 5.0 else ""}</p>
            </div>
            <div class="p-3 rounded-lg bg-zinc-900/60 border border-emerald-500/40">
              <span class="text-[10px] uppercase font-bold text-emerald-300 tracking-wider block">Total Leverage Ladder Imbalance (10x - 100x Spectrum)</span>
              <div class="text-base font-extrabold text-emerald-400 font-mono mt-0.5">{tot_ratio:.2f}x {'Downside' if tot_l_vol >= tot_u_vol else 'Upside'} Skew <span class="text-[10px] text-zinc-400 font-normal">(Modeled)</span></div>
              <p class="text-[11px] text-zinc-400 mt-1">Total modeled lower pools ({self._format_pool_m(tot_l_vol)}) vs total upper pools ({self._format_pool_m(tot_u_vol)}) scaled from {oi_scope}.</p>
            </div>
          </div>
          <div class="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-zinc-400 gap-2 pt-1">
            <div><strong class="text-zinc-200">How the Heatmap Works:</strong> Modeled clusters scale proportionally to tracked exchange OI &amp; positioning skew (see 5 Regimes Guide for math).</div>
            <div class="text-emerald-400 font-bold shrink-0">Dominant Gravitational Pull: {dom_magnet}</div>
          </div>
        </div>
      </div>

      <!-- Six-Factor Decision Logic Section -->
      <div class="border border-teal-500/45 rounded-xl p-5 bg-zinc-950/90 space-y-3.5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-teal-500/25 pb-3 gap-1">
          <span class="text-xs font-bold text-teal-300 uppercase tracking-wider">Magnet Decision Analysis (Six-Factor Evaluation)</span>
          <span class="text-xs text-zinc-400">Hierarchy: Pool Size &gt; Spot CVD &gt; Crowding &gt; Regime &gt; Distance &gt; ATR</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-zinc-300">
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-rose-500/35">
            <strong class="text-rose-300 block mb-1">1. Cluster Size / Magnitude:</strong>
            <span class="text-zinc-200 leading-relaxed">{f1}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-cyan-500/35">
            <strong class="text-cyan-300 block mb-1">2. Spot vs. Derivatives Leadership:</strong>
            <span class="text-zinc-200 leading-relaxed">{f2}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-amber-500/35">
            <strong class="text-amber-300 block mb-1">3. Crowding &amp; Market Fuel:</strong>
            <span class="text-zinc-200 leading-relaxed">{f3}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-indigo-500/35">
            <strong class="text-indigo-300 block mb-1">4. Higher-Timeframe Market Structure:</strong>
            <span class="text-zinc-200 leading-relaxed">{f4}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-emerald-500/35">
            <strong class="text-emerald-300 block mb-1">5. Distance Asymmetry:</strong>
            <span class="text-zinc-200 leading-relaxed">{f5}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-violet-500/35">
            <strong class="text-violet-300 block mb-1">6. Volatility Regime (ATR):</strong>
            <span class="text-zinc-200 leading-relaxed">{f6}</span>
          </div>
        </div>

        <div class="mt-3 pt-3 border-t border-zinc-800/80 flex items-start gap-2 text-xs">
          <span class="text-amber-400 font-bold uppercase tracking-wider">Decisive Conclusion:</span>
          <span class="text-white font-medium leading-relaxed">{dom_reason}</span>
        </div>
      </div>

    </div>

  </main>

  </div><!-- /#app-root -->

{mobile_nav_bar}

  <!-- Sticky Toast Notification for Copying -->
  <div id="copy-toast" class="fixed bottom-6 right-6 z-50 transform translate-y-4 opacity-0 pointer-events-none transition-all duration-300 bg-emerald-500 text-black font-extrabold px-5 py-3 rounded-xl shadow-2xl flex items-center gap-2 text-xs">
    <span>✓</span>
    <span id="copy-toast-text">Copied Live Telemetry &amp; AI Prompt to Clipboard!</span>
  </div>

  <!-- Standard Institutional Footer -->
  <footer class="border-t border-zinc-800/80 pt-8 mt-12 text-center text-xs text-zinc-400 space-y-2">
    <div class="flex items-center justify-center gap-3">
      <span class="text-white font-bold">BTC Magnet Monitor</span>
      <span>&bull;</span>
      <a href="text.html" class="text-emerald-400 hover:underline font-semibold">📱 Text Terminal</a>
      <span>&bull;</span>
      <a href="regimes.html" class="text-cyan-400 hover:underline">5 Regimes Guide</a>
      <span>&bull;</span>
      <a href="privacy.html" class="text-cyan-400 hover:underline">Privacy Policy</a>
    </div>
    <p>Scan ID: <span class="mono text-zinc-300">{scan_id}</span> &bull; Updates Every 30m (:00/:30 UTC) &bull; {spot_source} &bull; {futures_source}</p>
    <p class="text-[11px] text-zinc-400">Strictly for informational and risk research purposes. Not financial advice.</p>
  </footer>

  <script>
    const IS_NATIVE_APP = !!(window.Capacitor && typeof window.Capacitor.isNativePlatform === 'function' && window.Capacitor.isNativePlatform()) || location.protocol === 'file:';
    const LIVE_BASE = IS_NATIVE_APP ? 'https://aikeluargalee-tech.github.io/btc-magnet-monitor/' : './';
    const rootAtLoad = document.getElementById('app-root');
    let currentScanTs = Date.parse(rootAtLoad ? rootAtLoad.getAttribute('data-scan-ts') : '') || 0;
    let lastFetchOk = null;

    function copyElementText(elemId, btnId, iconId, textId, origLabel, origIcon, origBg, origHover, toastText) {{
      const promptEl = document.getElementById(elemId);
      if (!promptEl) return;
      const textToCopy = promptEl.value;

      function fallbackCopy() {{
        const ta = document.createElement('textarea');
        ta.value = textToCopy;
        ta.style.position = 'fixed';
        ta.style.left = '-999999px';
        ta.style.top = '-999999px';
        document.body.appendChild(ta);
        ta.focus();
        ta.select();
        try {{
          document.execCommand('copy');
          showSuccess();
        }} catch (err) {{
          alert('Could not copy automatically. Please open the preview or JSON feed.');
        }}
        document.body.removeChild(ta);
      }}

      function showSuccess() {{
        const btn = document.getElementById(btnId);
        const btnText = document.getElementById(textId);
        const btnIcon = document.getElementById(iconId);
        const toast = document.getElementById('copy-toast');
        const toastTextEl = document.getElementById('copy-toast-text');

        if (btnText) btnText.innerText = '✓ Copied to Clipboard!';
        if (btnIcon) btnIcon.innerText = '✅';
        if (btn) {{
          btn.classList.remove(origBg, origHover);
          btn.classList.add('bg-emerald-500');
        }}
        if (toastTextEl && toastText) toastTextEl.innerText = toastText;

        if (toast) {{
          toast.classList.remove('opacity-0', 'pointer-events-none', 'translate-y-4');
          toast.classList.add('opacity-100', 'translate-y-0');

          setTimeout(() => {{
            toast.classList.remove('opacity-100', 'translate-y-0');
            toast.classList.add('opacity-0', 'pointer-events-none', 'translate-y-4');
            if (btnText) btnText.innerText = origLabel;
            if (btnIcon) btnIcon.innerText = origIcon;
            if (btn) {{
              btn.classList.remove('bg-emerald-500');
              btn.classList.add(origBg, origHover);
            }}
          }}, 3500);
        }}
      }}

      if (navigator.clipboard && window.isSecureContext) {{
        navigator.clipboard.writeText(textToCopy).then(showSuccess, fallbackCopy);
      }} else {{
        fallbackCopy();
      }}
    }}

    function copyTelemetryPrompt() {{
      copyElementText(
        'llm-prompt-data',
        'copy-prompt-btn',
        'copy-btn-icon',
        'copy-btn-text',
        'Copy Full Audit Prompt',
        '📋',
        'bg-cyan-500',
        'hover:bg-cyan-400',
        'Copied Full Audit Prompt to Clipboard!'
      );
    }}

    function copyBlindPrompt() {{
      copyElementText(
        'blind-prompt-data',
        'copy-blind-btn',
        'copy-blind-icon',
        'copy-blind-text',
        'Copy Blind Telemetry (Unanchored)',
        '🧪',
        'bg-sky-500',
        'hover:bg-sky-400',
        'Copied Blind Telemetry (No Verdict) to Clipboard!'
      );
    }}

    // Live Clocks, Next Scheduled Update Countdown, and Market Session Tracker
    function updateClocksAndSession() {{
      const now = new Date();
      const utcMs = now.getTime();

      // UTC Clock
      const utcHours = String(now.getUTCHours()).padStart(2, '0');
      const utcMinutes = String(now.getUTCMinutes()).padStart(2, '0');
      const utcSeconds = String(now.getUTCSeconds()).padStart(2, '0');
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const utcDateStr = `${{now.getUTCDate()}} ${{months[now.getUTCMonth()]}} ${{now.getUTCFullYear()}}`;

      const utcEl = document.getElementById('clock-utc-time');
      const utcDateEl = document.getElementById('clock-utc-date');
      if (utcEl) utcEl.innerText = `${{utcHours}}:${{utcMinutes}}:${{utcSeconds}} UTC`;
      if (utcDateEl) utcDateEl.innerText = utcDateStr;

      // SGT Clock (UTC + 8 hours)
      const sgtOffset = 8 * 60;
      const sgtDate = new Date(utcMs + (sgtOffset + now.getTimezoneOffset()) * 60000);
      const sgtHours = String(sgtDate.getHours()).padStart(2, '0');
      const sgtMinutes = String(sgtDate.getMinutes()).padStart(2, '0');
      const sgtSeconds = String(sgtDate.getSeconds()).padStart(2, '0');
      const sgtDateStr = `${{sgtDate.getDate()}} ${{months[sgtDate.getMonth()]}} ${{sgtDate.getFullYear()}}`;

      const sgtEl = document.getElementById('clock-sgt-time');
      const sgtDateEl = document.getElementById('clock-sgt-date');
      if (sgtEl) sgtEl.innerText = `${{sgtHours}}:${{sgtMinutes}}:${{sgtSeconds}} SGT`;
      if (sgtDateEl) sgtDateEl.innerText = sgtDateStr;

      // Next scheduled :00 or :30 UTC update boundary + countdown
      const nextTarget = new Date(utcMs);
      nextTarget.setUTCSeconds(0, 0);
      if (now.getUTCMinutes() < 30) {{
        nextTarget.setUTCMinutes(30);
      }} else {{
        nextTarget.setUTCMinutes(0);
        nextTarget.setUTCHours(now.getUTCHours() + 1);
      }}
      const nUtcH = String(nextTarget.getUTCHours()).padStart(2, '0');
      const nUtcM = String(nextTarget.getUTCMinutes()).padStart(2, '0');
      const nextSgt = new Date(nextTarget.getTime() + (sgtOffset + nextTarget.getTimezoneOffset()) * 60000);
      const nSgtH = String(nextSgt.getHours()).padStart(2, '0');
      const nSgtM = String(nextSgt.getMinutes()).padStart(2, '0');
      const nextStr = `${{nUtcH}}:${{nUtcM}} UTC (${{nSgtH}}:${{nSgtM}} SGT)`;
      const remSec = Math.max(0, Math.floor((nextTarget.getTime() - utcMs) / 1000));
      const remM = String(Math.floor(remSec / 60)).padStart(2, '0');
      const remS = String(remSec % 60).padStart(2, '0');

      const subHdrNext = document.getElementById('subhdr-next-update');
      const p1Next = document.getElementById('next-update-time');
      const p1Cd = document.getElementById('next-update-countdown');
      if (subHdrNext) subHdrNext.innerText = nextStr;
      if (p1Next) p1Next.innerText = nextStr;
      if (p1Cd) {{
        const ageMin = currentScanTs > 0 ? Math.max(0, Math.floor((utcMs - currentScanTs) / 60000)) : 0;
        if (currentScanTs > 0 && ageMin > 35) {{
          p1Cd.className = 'ml-2 text-xs text-amber-300';
          p1Cd.innerText = `in ${{remM}}m ${{remS}}s (overdue)`;
        }} else {{
          p1Cd.className = 'ml-2 text-xs text-emerald-400';
          p1Cd.innerText = `in ${{remM}}m ${{remS}}s`;
        }}
      }}

      // Active Market Session Zone (based on UTC hour)
      const uH = now.getUTCHours();
      let sessionName = '🌙 Pacific / Off-Hours Transition';
      let sessionHours = '21:00 - 00:00 UTC (05:00 - 08:00 SGT)';
      let sessionDesc = 'Off-Hours Liquidity • Mean Reversion & Overnight Reset';
      let sessionBadge = 'OFF-HOURS';
      let sessionBadgeClass = 'border-purple-500/40 bg-purple-500/15 text-purple-300';

      if (uH >= 0 && uH < 8) {{
        sessionName = '🌏 Asian / Pacific Session';
        sessionHours = '00:00 - 08:00 UTC (08:00 - 16:00 SGT)';
        sessionDesc = 'Tokyo, Singapore & HK Open • Range Definition & Baseline Flow';
        sessionBadge = 'ASIAN ACTIVE';
        sessionBadgeClass = 'border-cyan-500/40 bg-cyan-500/15 text-cyan-300';
      }} else if (uH >= 8 && uH < 14) {{
        sessionName = '🏛️ European / London Session';
        sessionHours = '08:00 - 14:00 UTC (16:00 - 22:00 SGT)';
        sessionDesc = 'London Open & Frankfurt • Volatility Expansion & Sweep Fuel';
        sessionBadge = 'LONDON ACTIVE';
        sessionBadgeClass = 'border-amber-500/40 bg-amber-500/15 text-amber-300';
      }} else if (uH >= 14 && uH < 21) {{
        sessionName = '⚡ US / New York Cash Session';
        sessionHours = '14:00 - 21:00 UTC (22:00 - 05:00 SGT)';
        sessionDesc = 'Peak Wall Street ETF Inflows & Derivatives Liquidity Squeeze';
        sessionBadge = 'US CASH PEAK';
        sessionBadgeClass = 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300';
      }}

      const sNameEl = document.getElementById('session-name');
      const sHoursEl = document.getElementById('session-hours');
      const sDescEl = document.getElementById('session-desc');
      const sBadgeEl = document.getElementById('session-badge');

      if (sNameEl) sNameEl.innerText = sessionName;
      if (sHoursEl) sHoursEl.innerText = sessionHours;
      if (sDescEl) sDescEl.innerText = sessionDesc;
      if (sBadgeEl) {{
        sBadgeEl.innerText = sessionBadge;
        sBadgeEl.className = `px-2.5 py-0.5 rounded text-[11px] font-mono font-bold uppercase border ${{sessionBadgeClass}}`;
      }}
    }}

    setInterval(updateClocksAndSession, 1000);
    updateClocksAndSession();

    // Live BTC price ticker (Binance Public Market-Data REST first: non-geoblocked; falls back to api.binance.com)
    let scanPrice = {price};
    const PRICE_ENDPOINTS = [
      'https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT',
      'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
    ];
    let priceFailCount = 0;
    let priceTick = 0;
    async function updateLivePriceTicker() {{
      if (document.hidden) return;
      if (priceFailCount >= 3 && (priceTick++ % 10) !== 0) return;
      let livePrice = NaN;
      for (const url of PRICE_ENDPOINTS) {{
        try {{
          const r = await fetch(url);
          if (!r.ok) continue;
          const d = await r.json();
          const p = parseFloat(d && d.price);
          if (!isNaN(p) && p > 0) {{ livePrice = p; break; }}
        }} catch (e) {{}}
      }}
      const priceEl = document.getElementById('live-btc-price');
      const driftEl = document.getElementById('live-price-drift');
      const statusEl = document.getElementById('live-ticker-status');
      if (isNaN(livePrice)) {{
        priceFailCount++;
        if (priceFailCount >= 3) {{
          if (driftEl) {{
            driftEl.className = 'text-amber-400 font-medium';
            driftEl.textContent = 'live price feed unreachable (showing scan baseline)';
          }}
          if (statusEl) {{
            statusEl.className = 'inline-flex items-center gap-1.5 text-[11px] px-2 py-0.5 rounded bg-amber-950/50 border border-amber-500/50 text-amber-300 mono';
            statusEl.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span> ⚠ Ticker Unreachable — Scan Baseline';
          }}
        }}
        return;
      }}
      priceFailCount = 0;
      if (statusEl) {{
        statusEl.className = 'inline-flex items-center gap-1.5 text-[11px] px-2 py-0.5 rounded bg-zinc-900 border border-emerald-500/40 text-emerald-400 mono';
        statusEl.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span> Live Exchange REST Feed';
      }}
      if (priceEl) priceEl.innerText = '$' + livePrice.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
      if (driftEl && scanPrice > 0) {{
        const diff = livePrice - scanPrice;
        const diffPct = (diff / scanPrice) * 100;
        const up = diff >= 0;
        driftEl.className = (up ? 'text-emerald-400' : 'text-rose-400') + ' font-medium';
        driftEl.textContent = (up ? '+' : '-') + '$' + Math.abs(diff).toFixed(2) + ' (' + (up ? '+' : '') + diffPct.toFixed(2) + '%)';
      }}
    }}
    setInterval(updateLivePriceTicker, 3000);
    updateLivePriceTicker();

    function formatAge(mins) {{
      if (mins < 60) return mins + ' min';
      return Math.floor(mins / 60) + 'h ' + (mins % 60) + 'm';
    }}

    function renderAgeBanner() {{
      const el = document.getElementById('data-age-banner');
      const confTag = document.getElementById('confidence-freshness-tag');
      if (!el) return;
      const base = 'px-4 py-2 text-center text-xs font-semibold border-b ';
      if (currentScanTs <= 0) {{
        el.className = base + 'border-amber-500/40 bg-amber-500/10 text-amber-300';
        el.textContent = '⚠ Scan time unknown - verify the data before acting on it.';
        if (confTag) {{
          confTag.className = 'text-[11px] text-amber-300 font-semibold';
          confTag.textContent = '⚠ Timestamp unknown — verify freshness';
        }}
        return;
      }}
      const ageMin = Math.max(0, Math.floor((Date.now() - currentScanTs) / 60000));
      const age = formatAge(ageMin);
      if (ageMin > 180) {{
        el.className = base + 'border-rose-500/50 bg-rose-500/15 text-rose-300';
        el.textContent = '⛔ STALE DATA - this scan is ' + age + ' old' + (lastFetchOk === false ? ' and the live feed is unreachable' : '') + '. Do NOT act on this verdict until it refreshes.';
        if (confTag) {{
          confTag.className = 'text-[11px] text-rose-300 font-semibold';
          confTag.textContent = '⛔ Confidence Suspended: Scan ' + age + ' old';
        }}
      }} else if (lastFetchOk === false) {{
        el.className = base + 'border-amber-500/40 bg-amber-500/10 text-amber-300';
        el.textContent = '⚠ Cannot reach the live feed - showing the last known scan (' + age + ' old).';
        if (confTag) {{
          confTag.className = 'text-[11px] text-amber-300 font-semibold';
          confTag.textContent = '⚠ Offline / Last Known Scan (' + age + ' old)';
        }}
      }} else if (ageMin > 35) {{
        el.className = base + 'border-amber-500/40 bg-amber-500/10 text-amber-300';
        el.textContent = '⚠ Scan is ' + age + ' old (past 30m scheduled cadence) - awaiting next automated CI run.';
        if (confTag) {{
          confTag.className = 'text-[11px] text-amber-300 font-semibold';
          confTag.textContent = '⚠ Confidence Downgraded: Scan ' + age + ' old (>30m cadence)';
        }}
      }} else {{
        el.className = base + 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
        el.textContent = '● Scan data is ' + age + ' old - updates every 30m (:00/:30 UTC); checking feed every minute.';
        if (confTag) {{
          confTag.className = 'text-[11px] text-zinc-400';
          confTag.textContent = 'Deterministic Rule Gate Status (Fresh)';
        }}
      }}
    }}

    // Defence in depth: only our own markup is allowed in. Strip scripts, frames, unknown event handlers and javascript: links.
    function sanitizeLiveNode(root) {{
      root.querySelectorAll('script, iframe, object, embed, link, meta, base, form').forEach(function (n) {{ n.remove(); }});
      root.querySelectorAll('*').forEach(function (n) {{
        Array.from(n.attributes).forEach(function (a) {{
          const name = a.name.toLowerCase();
          const val = (a.value || '').trim().toLowerCase();
          const trimmedVal = (a.value || '').trim();
          if (name.indexOf('on') === 0 && !(name === 'onclick' && (trimmedVal === 'copyTelemetryPrompt()' || trimmedVal === 'copyBlindPrompt()'))) {{
            n.removeAttribute(a.name);
          }} else if ((name === 'href' || name === 'src' || name === 'xlink:href') && val.indexOf('javascript:') === 0) {{
            n.removeAttribute(a.name);
          }}
        }});
      }});
    }}

    async function refreshLiveScan() {{
      if (document.hidden) return;
      try {{
        const res = await fetch(LIVE_BASE + 'regime.json?t=' + Date.now(), {{ cache: 'no-store' }});
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        const liveTs = Date.parse(data && data.timestamp);
        if (isNaN(liveTs)) throw new Error('invalid scan timestamp');
        lastFetchOk = true;
        if (liveTs > currentScanTs) {{
          const hres = await fetch(LIVE_BASE + 'index.html?t=' + Date.now(), {{ cache: 'no-store' }});
          if (!hres.ok) throw new Error('HTTP ' + hres.status);
          const doc = new DOMParser().parseFromString(await hres.text(), 'text/html');
          const newRoot = doc.getElementById('app-root');
          const root = document.getElementById('app-root');
          const newTs = newRoot ? Date.parse(newRoot.getAttribute('data-scan-ts')) : NaN;
          if (root && newRoot && !isNaN(newTs) && newTs > currentScanTs) {{
            sanitizeLiveNode(newRoot);
            root.innerHTML = newRoot.innerHTML;
            root.setAttribute('data-scan-ts', newRoot.getAttribute('data-scan-ts'));
            currentScanTs = newTs;
            const livePx = Number(data.metrics && data.metrics.price);
            if (livePx > 0) scanPrice = livePx;
            updateClocksAndSession();
            updateLivePriceTicker();
          }}
        }}
      }} catch (e) {{
        lastFetchOk = false;
      }}
      renderAgeBanner();
    }}
    setInterval(refreshLiveScan, 60000);
    setInterval(renderAgeBanner, 30000);
    document.addEventListener('visibilitychange', function () {{
      if (!document.hidden) {{ refreshLiveScan(); updateLivePriceTicker(); }}
    }});
    renderAgeBanner();
    refreshLiveScan();

    // PWA Service Worker Registration & Stale Cache Purge
    if ('serviceWorker' in navigator) {{
      window.addEventListener('load', () => {{
        navigator.serviceWorker.register('./sw.js')
          .then((reg) => {{
            reg.update();
          }})
          .catch(() => {{}});
      }});
    }}
    // Actively purge legacy caches from previous versions
    if ('caches' in window) {{
      caches.keys().then((keys) => {{
        keys.forEach((key) => {{
          if (key !== 'btc-magnet-pwa-v7') {{
            caches.delete(key);
          }}
        }});
      }});
    }}
    // Native Capacitor Bridge & Google AdMob Initialization
    if (window.Capacitor && window.Capacitor.isPluginAvailable && window.Capacitor.isPluginAvailable('AdMob')) {{
      try {{
        const {{ AdMob }} = window.Capacitor.Plugins;
        AdMob.initialize({{
          requestTrackingAuthorization: true,
          initializeForTesting: true,
        }}).then(() => {{
          AdMob.showBanner({{
            adId: 'ca-app-pub-3940256099942544/6300978111',
            adSize: 'BANNER',
            position: 'BOTTOM_CENTER',
            margin: 0,
            isTesting: true
          }}).catch(() => {{}});
        }}).catch(() => {{}});
      }} catch (e) {{}}
    }}
  </script>

</body>
</html>"""
        return html

    def _render_privacy_page(self) -> str:
        """Renders the comprehensive Privacy Policy subpage required by Google Play & Google AdMob."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Privacy Policy — BTC Magnet Monitor</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #09090b;
      color: #f4f4f5;
    }
    .mono {
      font-family: 'JetBrains Mono', monospace;
    }
  </style>
</head>
<body class="min-h-screen bg-zinc-950 text-zinc-100 antialiased pb-20">

  <!-- Top Header -->
  <header class="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-50 px-4 sm:px-6 py-4">
    <div class="max-w-4xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <a href="index.html" class="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-xl hover:border-emerald-500/50 transition-colors">
          🧲
        </a>
        <div>
          <h1 class="font-extrabold text-base tracking-tight text-white">BTC Magnet Monitor</h1>
          <p class="text-xs text-zinc-400">Privacy Policy &amp; Data Transparency</p>
        </div>
      </div>
      <a href="index.html" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-emerald-400 border border-zinc-700/80 transition-colors">
        <span>&larr; Return to Dashboard</span>
      </a>
    </div>
  </header>

  <main class="max-w-4xl mx-auto px-4 sm:px-6 pt-10 space-y-8">

    <div class="space-y-3 border-b border-zinc-800 pb-6">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
        <span>🛡️ User Privacy &amp; Data Protection</span>
      </div>
      <h2 class="text-3xl font-black text-white tracking-tight">Privacy Policy</h2>
      <p class="text-sm text-zinc-400">
        Last Updated: November 11, 2026 &bull; Effective Date: November 11, 2026
      </p>
    </div>

    <!-- Section 1: Overview -->
    <section class="space-y-3">
      <h3 class="text-xl font-bold text-white flex items-center gap-2">
        <span class="text-emerald-400">1.</span> Overview
      </h3>
      <p class="text-sm text-zinc-300 leading-relaxed">
        BTC Magnet Monitor ("we", "our", or "the Application") is an open quantitative Bitcoin spot market analysis platform. We are committed to complete transparency, user privacy, and zero unnecessary data collection. This Privacy Policy explains our policies regarding the collection, use, and disclosure of information when you use our web application, PWA, or native mobile applications.
      </p>
    </section>

    <!-- Section 2: Zero Personal Data Collection -->
    <section class="p-6 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 space-y-3">
      <h3 class="text-xl font-bold text-white flex items-center gap-2">
        <span class="text-emerald-400">2.</span> Zero Personal Data Collection
      </h3>
      <p class="text-sm text-zinc-300 leading-relaxed">
        We firmly believe in privacy-by-design. You can use BTC Magnet Monitor completely anonymously:
      </p>
      <ul class="list-disc pl-5 text-sm text-zinc-300 space-y-1.5">
        <li><strong>No Account Required:</strong> We do not require you to create an account, register, or log in.</li>
        <li><strong>No Personal Identifiers:</strong> We do not collect, store, or transmit your name, email address, phone number, physical address, or IP addresses.</li>
        <li><strong>No Financial Account Linking:</strong> The Application never asks for, connects to, or accesses your bank accounts, crypto wallets, seed phrases, or private exchange API keys. The system cannot execute trades on your behalf.</li>
      </ul>
    </section>

    <!-- Section 3: Third-Party Advertising (Google AdMob) -->
    <section class="p-6 rounded-2xl bg-zinc-900/60 border border-zinc-800/80 space-y-3">
      <h3 class="text-xl font-bold text-white flex items-center gap-2">
        <span class="text-emerald-400">3.</span> Advertising &amp; Third-Party Services (Google AdMob)
      </h3>
      <p class="text-sm text-zinc-300 leading-relaxed">
        To support the ongoing operation, free access, and serverless scanning infrastructure of the Application, we may display mobile advertisements served by <strong>Google AdMob</strong> (Google LLC).
      </p>
      <div class="space-y-2 text-sm text-zinc-300 leading-relaxed">
        <p>Google AdMob may automatically collect and process certain non-personal device information in accordance with its privacy policies, including:</p>
        <ul class="list-disc pl-5 space-y-1 text-zinc-400">
          <li>Device advertising identifiers (e.g. Google Advertising ID / IDFA).</li>
          <li>General device characteristics (device model, operating system version, carrier).</li>
          <li>Coarse location data derived from general network IP addresses.</li>
        </ul>
        <p class="pt-2">
          <strong>Opt-Out &amp; Ad Personalization Controls:</strong> You can manage, reset, or opt out of personalized interest-based advertising at any time through your mobile device settings:
        </p>
        <ul class="list-disc pl-5 space-y-1 text-zinc-400">
          <li><strong>Android:</strong> Settings &rarr; Google &rarr; Ads &rarr; Reset Advertising ID or Delete Advertising ID.</li>
          <li><strong>iOS:</strong> Settings &rarr; Privacy &amp; Security &rarr; Tracking &rarr; Disable tracking permissions.</li>
        </ul>
        <p class="pt-2">
          For more information on how Google processes advertising data, please review Google's official privacy documentation: <a href="https://policies.google.com/privacy" target="_blank" class="text-cyan-400 hover:underline">Google Privacy Policy</a> and <a href="https://policies.google.com/technologies/ads" target="_blank" class="text-cyan-400 hover:underline">How Google Uses Information from Sites or Apps</a>.
        </p>
      </div>
    </section>

    <!-- Section 4: Public Market Telemetry -->
    <section class="space-y-3">
      <h3 class="text-xl font-bold text-white flex items-center gap-2">
        <span class="text-emerald-400">4.</span> Public Market Telemetry &amp; Exchange Feeds
      </h3>
      <p class="text-sm text-zinc-300 leading-relaxed">
        The market metrics displayed by BTC Magnet Monitor (spot prices, taker volume deltas, open interest, funding rates, and basis spreads) are retrieved from public, anonymized market data APIs provided by major digital asset exchanges (Binance Vision, Deribit). These feeds contain strictly aggregated market statistics and do not expose or process any personal trader information.
      </p>
      <div class="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800/80 space-y-2 text-sm text-zinc-300 leading-relaxed">
        <p><strong>Direct connections made from your device.</strong> We operate no servers that receive your data. However, to show live information, the Application makes network requests directly from your device to the following third parties. Like any internet request, these providers can see your device's IP address and basic request details, and handle them under their own privacy policies:</p>
        <ul class="list-disc pl-5 space-y-1 text-zinc-400">
          <li><strong>Binance</strong> (<span class="mono">data-api.binance.vision</span>, <span class="mono">api.binance.com</span>) &mdash; live BTC spot price, requested every few seconds while the Application is open.</li>
          <li><strong>GitHub Pages</strong> (<span class="mono">aikeluargalee-tech.github.io</span>) &mdash; the latest published market scan (<span class="mono">regime.json</span>) and dashboard page, checked about once a minute while the Application is open.</li>
          <li><strong>Google AdMob</strong> &mdash; advertisements in the mobile app (see section 3).</li>
          <li><strong>Web version only:</strong> the website (not the Android app) additionally loads the Tailwind CSS library (<span class="mono">cdn.tailwindcss.com</span>) and fonts from Google Fonts. The Android app bundles these files and does not contact those services.</li>
        </ul>
        <p>No account identifiers, clipboard contents, or personal information are included in these requests. The only data stored on your device is your display-theme preference (in local storage) and cached copies of the app's own pages.</p>
      </div>
    </section>

    <!-- Section 5: AI Audit Copy Functionality -->
    <section class="space-y-3">
      <h3 class="text-xl font-bold text-white flex items-center gap-2">
        <span class="text-emerald-400">5.</span> "Copy Data for AI" Client Functionality
      </h3>
      <p class="text-sm text-zinc-300 leading-relaxed">
        The Application includes a client-side button allowing users to copy the current market telemetry prompt to their device clipboard. This action is executed entirely locally on your device. The Application does not transmit your clipboard data to any external server. Any subsequent interaction with third-party LLMs (such as OpenAI ChatGPT, Anthropic Claude, xAI Grok, or Google Gemini) is initiated solely by the user within their own browser or account.
      </p>
    </section>

    <!-- Section 6: Children's Privacy -->
    <section class="space-y-3">
      <h3 class="text-xl font-bold text-white flex items-center gap-2">
        <span class="text-emerald-400">6.</span> Children's Privacy
      </h3>
      <p class="text-sm text-zinc-300 leading-relaxed">
        Our Application is not directed to individuals under the age of 13 (or under 16 in certain jurisdictions). We do not knowingly collect personal information from children.
      </p>
    </section>

    <!-- Section 7: Financial & Analytical Disclaimer -->
    <section class="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 space-y-3">
      <h3 class="text-xl font-bold text-rose-300 flex items-center gap-2">
        <span>⚠️</span> Financial &amp; Investment Disclaimer
      </h3>
      <p class="text-xs sm:text-sm text-rose-200/90 leading-relaxed">
        BTC Magnet Monitor is an analytical research and educational tool designed to visualize observable positioning mechanics and liquidity imbalances. <strong>None of the information, regime classifications, sizing factors, or stop-loss calculations provided in this Application constitutes financial, investment, trading, tax, or legal advice.</strong> Cryptocurrency trading carries significant financial risk. Users are exclusively responsible for their own capital decisions.
      </p>
    </section>

    <!-- Section 8: Changes & Contact -->
    <section class="space-y-3">
      <h3 class="text-xl font-bold text-white flex items-center gap-2">
        <span class="text-emerald-400">7.</span> Policy Updates &amp; Contact
      </h3>
      <p class="text-sm text-zinc-300 leading-relaxed">
        We may update this Privacy Policy from time to time. Any revisions will be reflected on this page with an updated "Last Updated" date. If you have any questions or feedback regarding this Privacy Policy, please open an issue on our public repository at:
      </p>
      <div class="pt-2">
        <a href="https://github.com/aikeluargalee-tech/btc-magnet-monitor" target="_blank" class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-xs font-bold text-cyan-400 border border-zinc-700/80 transition-all">
          <span>GitHub: aikeluargalee-tech/btc-magnet-monitor</span>
          <span>&rarr;</span>
        </a>
      </div>
    </section>

    <!-- Bottom Return Button -->
    <div class="text-center pt-8 border-t border-zinc-800">
      <a href="index.html" class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-sm font-bold text-white border border-zinc-700 shadow-xl transition-all">
        <span>&larr; Return to Live BTC Magnet Monitor</span>
      </a>
    </div>

  </main>

</body>
</html>"""





    def _render_regimes_subpage(self, data: Dict[str, Any]) -> str:
        """Renders the comprehensive educational reference subpage explaining all 5 regimes."""
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        current_regime_id = regime.get("regime_id", "RANGE_LIQUIDATION_MAGNET")
        current_name = regime.get("name", "Range / Liquidation Magnet")
        llm_prompt = self._build_llm_prompt(data)
        llm_prompt_escaped = llm_prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The 5 Market Regimes — BTC Magnet Monitor Reference Guide</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #09090b;
      color: #f4f4f5;
    }}
    .mono {{
      font-family: 'JetBrains Mono', monospace;
    }}
  </style>
</head>
<body class="min-h-screen bg-zinc-950 text-zinc-100 antialiased pb-20">

  <!-- Header -->
  <header class="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-50 px-4 sm:px-6 py-4">
    <div class="max-w-4xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl overflow-hidden border border-zinc-800 flex items-center justify-center shadow-inner flex-shrink-0 bg-zinc-950 p-0.5">
          <img src="./assets/app-logo.png?v=4" alt="BTC Magnet Monitor Logo" class="w-full h-full object-contain">
        </div>
        <div>
          <span class="font-extrabold text-base tracking-tight text-white">BTC Magnet Monitor</span>
          <span class="text-xs text-zinc-400 block">The 5-Regime Radar Reference Guide</span>
        </div>
      </div>
      <a href="index.html" class="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-white border border-zinc-700 transition-colors">
        <span>&larr; Back to Live Monitor</span>
      </a>
    </div>
  </header>

  <main class="max-w-4xl mx-auto px-4 sm:px-6 pt-8 space-y-10">

    <!-- Hero Title -->
    <div class="space-y-3">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
        System Architecture &bull; Observable Positioning Mechanics
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
        The Simplified 5-Regime Radar
      </h1>
      <p class="text-base sm:text-lg text-zinc-300 leading-relaxed">
        Why trading edge is strictly regime-dependent, how the majority-voting calculation engine works, and why liquidation magnets only apply inside Range regimes.
      </p>
    </div>

    <!-- Active State Banner with Copy Prompt -->
    <div class="p-5 rounded-2xl border-2 border-cyan-500/60 bg-cyan-500/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-[0_0_20px_rgba(6,182,212,0.12)]">
      <div>
        <div class="text-xs uppercase font-bold text-cyan-400 tracking-wider">Current Live Market State</div>
        <div class="text-xl font-bold text-white mt-0.5">{current_name}</div>
        <div class="text-xs text-zinc-400 mt-1">Diagnosed by empirical on-exchange order flow &bull; Updates every 30m (:00/:30 UTC).</div>
      </div>
      <div class="flex items-center gap-2.5">
        <button onclick="copySubpagePrompt()" class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all cursor-pointer">
          <span>📋</span>
          <span id="sub-copy-text">Copy Telemetry for LLM</span>
        </button>
        <a href="index.html" class="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white font-bold text-xs border border-zinc-700 transition-all">
          Live Monitor &rarr;
        </a>
      </div>
    </div>
    <textarea id="subpage-prompt-data" class="hidden" readonly>{llm_prompt_escaped}</textarea>

    <!-- Section 1: Philosophy -->
    <div class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-sky-500/45 space-y-4">
      <h2 class="text-2xl font-bold text-white flex items-center gap-2.5">
        <span>1. Core Philosophy: Regime First, Magnet Second</span>
      </h2>
      <div class="prose prose-invert text-sm text-zinc-300 space-y-3 leading-relaxed">
        <p>
          In quantitative crypto swing trading, <strong>strategy edge is regime-dependent</strong>. Applying a valid trading playbook in the wrong regime is the single most consistent way retail traders lose capital:
        </p>
        <ul class="space-y-2 list-disc list-inside text-zinc-300">
          <li><strong>The Trend Playbook</strong> (buying breakouts above VWAP) succeeds in <em>Spot-Led Expansion</em>, but gets chopped to pieces in a <em>Range</em>.</li>
          <li><strong>The Liquidation Magnet Playbook</strong> (buying at support to target trapped shorts above) has high mathematical edge in a <em>Range</em>, but has <strong>fatal negative expectancy inside an active Liquidation Cascade</strong>.</li>
        </ul>
        <p>
          Therefore, the monitor always diagnoses the <strong>Macro Regime first</strong>. Only if the market is diagnosed as a <em>Range / Liquidation Magnet</em> does the engine activate the 6-factor Liquidation Magnet target calculator.
        </p>
      </div>
    </div>

    <!-- Section 2: How the Majority Voting Works -->
    <div class="p-6 rounded-2xl bg-zinc-900/70 border-2 border-indigo-500/45 space-y-4">
      <h2 class="text-2xl font-bold text-white flex items-center gap-2.5">
        <span>2. How the Majority-Voting Engine Works</span>
      </h2>
      <div class="space-y-3 text-sm text-zinc-300 leading-relaxed">
        <p>
          Traditional trading algorithms fail because of <strong>fragile multi-AND rules</strong> (requiring 5 or 6 indicators to be simultaneously true). If one obscure metric misses by 0.1%, the system breaks or jumps erratically.
        </p>
        <p>
          The 5-Regime Radar uses a <strong>robust majority-vote model</strong>:
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-emerald-500/40">
            <strong class="text-emerald-400 block text-xs uppercase font-bold mb-1">Majority Rule (&ge;3 of 4)</strong>
            <p class="text-xs text-zinc-400">Each regime defines 4 observable facts. If 3 or 4 are confirmed on-exchange, the regime is verified.</p>
          </div>
          <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-amber-500/40">
            <strong class="text-amber-400 block text-xs uppercase font-bold mb-1">Default Fallback (Transition / Mixed)</strong>
            <p class="text-xs text-zinc-400">If no regime achieves 3/4 matches, or conflict gates fire, the system cleanly defaults to Cash (0.0x) until clarity returns.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 3: Deep Dive into the 5 Regimes -->
    <div class="space-y-6">
      <h2 class="text-2xl font-bold text-white">3. Complete Specification of the 5 Regimes</h2>

      <!-- Regime 1 -->
      <div id="regime-1" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-emerald-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            Regime 1 &bull; Spot-Led Expansion
          </span>
          <span class="text-xs font-mono text-zinc-400 font-bold">Action: Buy Spot (0.75x–1.0x)</span>
        </div>
        <h3 class="text-lg font-bold text-white">Genuine spot demand supporting upward trend</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          The healthiest market state in crypto. Real institutional cash is buying physical Bitcoin and withdrawing from exchanges. Price consistently holds above daily and weekly volume benchmarks (VWAP).
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-emerald-500/30">
          <div class="font-bold text-emerald-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price holding above Daily and Weekly VWAP or rising with structure.</div>
          <div class="text-zinc-300">2. Spot CVD ratio clearly positive (&ge;1.15) or 7-day slope upward.</div>
          <div class="text-zinc-300">3. Spot trading volume expanding (&ge;1.10x 20-day moving average).</div>
          <div class="text-zinc-300">4. Futures funding rates healthy (&le;0.012%) and Open Interest not surging parabolically.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-emerald-500/25">
            <strong class="text-emerald-300 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">60% breakout confirmation / 40% limit at Daily VWAP retest.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-rose-500/25">
            <strong class="text-rose-300 block text-[11px] uppercase">Safety Stop-Loss:</strong>
            <span class="text-zinc-200">Anchored under recent 4-hour swing low (-0.6%).</span>
          </div>
        </div>
      </div>

      <!-- Regime 2 -->
      <div id="regime-2" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-orange-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-orange-500/10 text-orange-400 border border-orange-500/30">
            Regime 2 &bull; Leveraged / Fragile Upside
          </span>
          <span class="text-xs font-mono text-zinc-400 font-bold">Action: Trim / Stand Aside (0.0x)</span>
        </div>
        <h3 class="text-lg font-bold text-white">Upside driven mainly by speculative futures debt</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          A dangerous bull trap. Price moves upward, but the rally is artificially propped up by retail futures leverage while spot buyers are passive or selling. High probability of a sharp long-squeeze.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-orange-500/30">
          <div class="font-bold text-orange-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price rising but Spot CVD is flat or declining (bearish divergence).</div>
          <div class="text-zinc-300">2. Perpetual futures CVD and/or Open Interest rising sharply (&gt;+4% in 24h).</div>
          <div class="text-zinc-300">3. Funding rates elevated (&gt;0.015% per 8h) or basis contango stretched.</div>
          <div class="text-zinc-300">4. Spot volume failing to confirm the move (below 20D average).</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-orange-500/25">
            <strong class="text-orange-300 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">Strictly zero new buying. Harvest 33% profit directly into perp pumps.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-rose-500/25">
            <strong class="text-rose-300 block text-[11px] uppercase">Safety Stop-Loss:</strong>
            <span class="text-zinc-200">Move protective stops tight to 4H swing low to lock in profits.</span>
          </div>
        </div>
      </div>

      <!-- Regime 3 -->
      <div id="regime-3" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-cyan-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
            Regime 3 &bull; Range / Liquidation Magnet (Core Operating Zone)
          </span>
          <span class="text-xs font-mono text-zinc-400 font-bold">Action: Trade the Magnet (0.50x–0.75x)</span>
        </div>
        <h3 class="text-lg font-bold text-white">Positioning imbalance &amp; liquidation pools dominate</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          The natural habitat for the Liquidation Magnet Monitor. Price is oscillating inside a horizontal channel. Trend-following fails here, but fading the range edges toward dense liquidation pools has a massive statistical edge.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-cyan-500/30">
          <div class="font-bold text-cyan-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price oscillating in a defined range (width &le;4.5%) with ATR compressed &gt;30%.</div>
          <div class="text-zinc-300">2. Spot CVD neutral or balanced (ratio between 0.90 and 1.15).</div>
          <div class="text-zinc-300">3. Funding and OI showing positioning crowding on one side (L/S ratio &ge;1.60).</div>
          <div class="text-zinc-300">4. Clear liquidation clusters active both above and below current price.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-cyan-500/25">
            <strong class="text-cyan-300 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">Trade toward dominant magnet: 50% on 1H range reclaim / 50% limit at support low.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-rose-500/25">
            <strong class="text-rose-300 block text-[11px] uppercase">Safety Stop-Loss:</strong>
            <span class="text-zinc-200">Anchored outside range floor (Lowest sweep wick - 0.5%, capped at 4.5% max distance).</span>
          </div>
        </div>
      </div>

      <!-- Regime 4 -->
      <div id="regime-4" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-rose-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-rose-500/10 text-rose-400 border border-rose-500/30">
            Regime 4 &bull; Cascade / Forced Deleveraging
          </span>
          <span class="text-xs font-mono text-zinc-400 font-bold">Action: Wait / 100% Cash (0.0x)</span>
        </div>
        <h3 class="text-lg font-bold text-white">Forced long unwind &amp; margin waterfall in progress</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          Emergency state. A domino chain of forced liquidations is collapsing the price. Bids disappear as exchange risk engines market-sell collateral. Never buy into an active waterfall.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-rose-500/30">
          <div class="font-bold text-rose-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Sharp vertical price plunge (&le;-3.0% in 1h or &le;-6.0% in 24h).</div>
          <div class="text-zinc-300">2. Open Interest crashing violently (&le;-3.5% in 1h or &le;-7.0% in 4h).</div>
          <div class="text-zinc-300">3. Funding rate plunged deeply negative (&le;-0.005%).</div>
          <div class="text-zinc-300">4. Severe basis discount / backwardation (&lt;1.0% annualized).</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-rose-500/25">
            <strong class="text-rose-300 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">100% Cash. Wait for Phase 3: 5m liquidations stop, OI flatlines, and 1H hammer forms.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-700/60">
            <strong class="text-zinc-300 block text-[11px] uppercase">Safety Stop-Loss:</strong>
            <span class="text-zinc-200">N/A (Holding cash reserve).</span>
          </div>
        </div>
      </div>

      <!-- Regime 5 -->
      <div id="regime-5" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-red-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-red-500/10 text-red-400 border border-red-500/30">
            Regime 5 &bull; Distribution / Bear Continuation
          </span>
          <span class="text-xs font-mono text-zinc-400 font-bold">Action: Defensive Cash (0.0x)</span>
        </div>
        <h3 class="text-lg font-bold text-white">Persistent seller control &amp; exit liquidity traps</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          Smart money is actively selling down inventory into retail dip-buyers. Every minor bounce occurs on light volume and is sold off immediately.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-red-500/30">
          <div class="font-bold text-red-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price trapped below Daily VWAP, 20D EMA, and 50D EMA.</div>
          <div class="text-zinc-300">2. Spot CVD persistently negative (7D/14D slope &lt;0).</div>
          <div class="text-zinc-300">3. Bounces occur on light spot volume (&lt;0.95x 20D MA).</div>
          <div class="text-zinc-300">4. Trapped longs paying positive funding with compressed futures basis.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-red-500/25">
            <strong class="text-red-300 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">Defensive 100% USDT cash. Treat bounces as exit liquidity.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-rose-500/25">
            <strong class="text-rose-300 block text-[11px] uppercase">Safety Invalidation:</strong>
            <span class="text-zinc-200">1D close &gt; 50D EMA backed by positive Spot CVD.</span>
          </div>
        </div>
      </div>

    </div>

    <!-- Section 4: Modeled Liquidation Pool & Tier Scaling Methodology -->
    <div id="methodology-pools" class="p-6 rounded-2xl bg-zinc-900/70 border-2 border-purple-500/50 space-y-4">
      <h2 class="text-2xl font-bold text-white">4. Modeled Liquidation Pool &amp; Tier Scaling Methodology</h2>
      <p class="text-xs sm:text-sm text-zinc-300 leading-relaxed">
        No public REST API exposes individual traders' private margin prices or cross-exchange liquidation ledgers in real time. All liquidity dollar sizes in this monitor are <strong>Modeled Estimates</strong> derived transparently from observable exchange inputs:
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div class="p-4 rounded-xl bg-zinc-950/80 border border-purple-500/35 space-y-1.5">
          <div class="font-bold text-purple-300 uppercase text-[11px]">OI Scope &amp; Venue Disclosure</div>
          <p class="text-zinc-300 leading-relaxed">Tracked Open Interest reflects the active perpetual venue subset reported in Panel 2 (for example OKX/Deribit perpetuals when US runner restrictions block Binance Futures), never claimed as total global BTC futures OI.</p>
        </div>
        <div class="p-4 rounded-xl bg-zinc-950/80 border border-indigo-500/35 space-y-1.5">
          <div class="font-bold text-indigo-300 uppercase text-[11px]">Leverage Projection Grid</div>
          <p class="text-zinc-300 leading-relaxed">Projects standard 100x (0.8%), 50x (1.8%), 25x (3.8%), and 10x (9.5%) offsets from the last 40 4H swing extremes into adaptive ATR bins (<span class="mono">max($100, ATR*0.25)</span>), scaled proportionally by <span class="mono">OI &times; Spot Price</span> and L/S crowding skew.</p>
        </div>
      </div>
    </div>

    <!-- Section 5: LSCE Deterministic State Machine -->
    <div id="methodology-lsce" class="p-6 rounded-2xl bg-zinc-900/70 border-2 border-teal-500/50 space-y-4">
      <h2 class="text-2xl font-bold text-white">5. LSCE Deterministic State Machine &amp; Reclaim Rules</h2>
      <p class="text-xs sm:text-sm text-zinc-300 leading-relaxed">
        The <strong>Liquidation Sweep Confirmation Engine (LSCE)</strong> uses live spot price against the nearest modeled lower liquidation shelf to prevent front-running active waterfalls:
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-zinc-700/60">
          <strong class="text-zinc-300 block uppercase text-[11px] mb-1">UNTESTED</strong>
          <p class="text-zinc-400">Spot remains more than +0.20% above the nearest lower shelf. Waiting for test or trend setup.</p>
        </div>
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-amber-500/40">
          <strong class="text-amber-300 block uppercase text-[11px] mb-1">SWEEP_IN_PROGRESS (&plusmn;0.20% Zone)</strong>
          <p class="text-zinc-300">Spot enters within &plusmn;0.20% of the modeled shelf without verified absorption. Hard entry lock until reclaim gates clear.</p>
        </div>
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-emerald-500/40">
          <strong class="text-emerald-300 block uppercase text-[11px] mb-1">SWEEP_AND_RECLAIM_CONFIRMED</strong>
          <p class="text-zinc-300">Requires spot &gt; shelf AND <strong>Spot CVD Ratio &ge; 1.05</strong> AND <strong>Orderbook Depth Ratio &ge; 0.50</strong>. Only authorizes buys when the Macro Regime allows risk-on positioning (blocked during Cascade / Distribution / Transition).</p>
        </div>
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-rose-500/40">
          <strong class="text-rose-300 block uppercase text-[11px] mb-1">SWEEP_FAILED_BREAKDOWN</strong>
          <p class="text-zinc-300">Spot breaks &gt;0.30% below the shelf without spot bid absorption or amid negative CVD (&lt; 0.90) / deep depth deficit. Hard 100% cash lock.</p>
        </div>
      </div>
    </div>

    <!-- Bottom Return Button -->
    <div class="text-center pt-8 border-t border-zinc-800">
      <a href="index.html" class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-sm font-bold text-white border border-zinc-700 shadow-xl transition-all">
        <span>&larr; Return to Live BTC Magnet Monitor</span>
      </a>
    </div>

  </main>

  <script>
    function copySubpagePrompt() {{
      const promptEl = document.getElementById('subpage-prompt-data');
      if (!promptEl) return;
      const textToCopy = promptEl.value;

      navigator.clipboard.writeText(textToCopy).then(() => {{
        const btnText = document.getElementById('sub-copy-text');
        if (btnText) {{
          btnText.innerText = '✓ Prompt Copied!';
          setTimeout(() => {{ btnText.innerText = 'Copy Telemetry for LLM'; }}, 3000);
        }}
      }});
    }}
    // Native Capacitor Bridge & Google AdMob Initialization
    if (window.Capacitor && window.Capacitor.isPluginAvailable && window.Capacitor.isPluginAvailable('AdMob')) {{
      try {{
        const {{ AdMob }} = window.Capacitor.Plugins;
        AdMob.initialize({{
          requestTrackingAuthorization: true,
          initializeForTesting: true,
        }}).then(() => {{
          AdMob.showBanner({{
            adId: 'ca-app-pub-3940256099942544/6300978111',
            adSize: 'BANNER',
            position: 'BOTTOM_CENTER',
            margin: 0,
            isTesting: true
          }}).catch(() => {{}});
        }}).catch(() => {{}});
      }} catch (e) {{}}
    }}
  </script>

</body>
</html>"""
        return html







    def _verify_text_telemetry(self, data: Dict[str, Any]) -> None:
        """Verification linter before rendering text.html:
          - Asserts immediate_imbalance_ratio matches lower_pool / upper_pool (within tolerance).
          - Confirms portfolio_risk_pct & effective_risk_budget_pct respect strict 1% risk budget.
          - Checks prose fields (`why_points`, `plain_english_verdict`, `lsce_detail`) against scan metrics
            to catch stale hardcoded numbers (`$74,963`, `-1.3%`, `0.19`, `Over 70%`).
        """
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})
        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_v = float(upper_c.get("estimated_vol_usd", 1.0))
        l_v = float(lower_c.get("estimated_vol_usd", 0.0))
        imm_ratio = float(regime.get("immediate_imbalance_ratio", 0.0))

        expected_ratio = l_v / max(u_v, 0.1)
        if imm_ratio > 0 and expected_ratio > 0:
            diff_direct = abs(imm_ratio - expected_ratio)
            diff_inverse = abs(imm_ratio - (1.0 / max(expected_ratio, 0.01)))
            assert diff_direct < 2.0 or diff_inverse < 2.0, (
                f"Linter assertion failed: immediate_skew_ratio ({imm_ratio}) does not match "
                f"lower_pool_size/upper_pool_size ({expected_ratio:.2f})"
            )

        portfolio_risk = float(risk.get("portfolio_risk_pct", 0.0))
        effective_risk = float(risk.get("effective_risk_budget_pct", portfolio_risk))
        assert portfolio_risk <= 1.05, f"Linter assertion failed: portfolio_risk_pct ({portfolio_risk}%) > 1.0%"
        assert effective_risk <= 1.05, f"Linter assertion failed: effective_risk_budget_pct ({effective_risk}%) > 1.0%"
        assert risk.get("risk_budget_ok", True) is True, "Linter assertion failed: risk_budget_ok is False"

        # Narrative vs Scan Consistency Check (T1)
        prose_blob = " ".join([
            str(regime.get("plain_english_verdict", "")),
            str(regime.get("lsce_detail", "")),
            " ".join(str(x) for x in regime.get("why_points", [])),
        ])
        d_vwap = float(metrics.get("daily_vwap", 0.0))
        basis = float(metrics.get("futures_basis_annualized", 0.0))
        depth = float(metrics.get("bids_asks_depth_ratio", 1.0))
        if d_vwap > 0 and abs(d_vwap - 74963.0) > 100.0:
            assert "74,963" not in prose_blob and "74963" not in prose_blob, (
                "Linter assertion failed: stale hardcoded VWAP $74,963 found in prose"
            )
        if abs(basis - (-1.3)) > 0.08:
            assert "-1.3%" not in prose_blob, (
                "Linter assertion failed: stale hardcoded basis -1.3% found in prose"
            )
        if abs(depth - 0.19) > 0.02:
            assert "0.19 ratio" not in prose_blob and "0.19 depth" not in prose_blob, (
                "Linter assertion failed: stale hardcoded depth 0.19 found in prose"
            )

    def _render_text_page(self, data: Dict[str, Any]) -> str:
        """Renders the Mobile Text/Data Terminal (text.html).
        Strictly starts with Panel 1 and preserves zero-framework vanilla HTML/CSS/JS:
          - 2-Line Monospace Header + Session/Cadence/Mandate Metadata Line
          - 44px Touch-Friendly Top View Switcher ([HUD], [JSON], [DELTA], [PROMPT])
          - Telemetry Stale >30M Warning Banner
          - Panel 1 • Real-Time BTC Spot Price (Live), Clocks, Next Update & Market Session
          - Panel 2 • On-Exchange Telemetry (Raw Feeds vs Modeled Scope)
          - Panel 3 • Macro Market Regime Diagnosis & 5-Regime + Transition Matrix
          - Method 1: Blind Telemetry Copy + Full Audit Prompt Copy
          - Method 2: Our System Verdict (Full-On View & Canonical Liquidation Ladder)
          - Institutional Footer & Platform Links
        """
        import json as _json
        import textwrap as _tw
        import datetime as _dt

        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})
        ts_iso = str(data.get("timestamp", ""))
        scan_id = self._compute_scan_id(data)
        raw_prompt = self._build_llm_prompt(data)
        blind_prompt = self._build_blind_llm_prompt(data)

        # Linter check before rendering
        self._verify_text_telemetry(data)

        # Telemetry age verification (>30 minutes check)
        is_stale_telemetry = False
        try:
            dt_scan = _dt.datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
            now_utc = _dt.datetime.now(_dt.timezone.utc)
            if (now_utc - dt_scan).total_seconds() > 1800:
                is_stale_telemetry = True
        except Exception:
            pass

        def wrap36(s: str) -> str:
            return "\n".join(_tw.wrap(str(s), width=35))

        utc_time_str, sgt_time_str, date_str = self._format_utc_sgt(ts_iso)
        regime_id = str(regime.get("regime_id", "RANGE_LIQUIDATION_MAGNET"))

        if regime_id == "SPOT_LED_EXPANSION":
            tagline_src = "Genuine spot demand supporting upward trend. Spot trend environment."
            regime_css_cls = "panel-box-emerald"
            regime_txt_cls = "c-green"
        elif regime_id == "LEVERAGED_FRAGILE_UPSIDE":
            tagline_src = "Upside driven by futures leverage rather than spot demand. Long-squeeze caution."
            regime_css_cls = "panel-box-orange"
            regime_txt_cls = "c-amber"
        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            tagline_src = "Forced margin liquidation cascade in progress. Strictly cash preservation."
            regime_css_cls = "panel-box-rose"
            regime_txt_cls = "c-rose"
        elif regime_id == "DISTRIBUTION_BEAR_CONTINUATION":
            tagline_src = "Structural seller control. Whales distributing into bounces. Hold cash."
            regime_css_cls = "panel-box-rose"
            regime_txt_cls = "c-rose"
        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            tagline_src = "Price bound within defined horizontal channel. Positioning imbalance and liquidation magnets dominate."
            regime_css_cls = "panel-box-cyan"
            regime_txt_cls = "c-cyan"
        else:
            tagline_src = "Market indicators conflicting or transitioning between regimes. Capital preservation in cash."
            regime_css_cls = "panel-box-amber"
            regime_txt_cls = "c-amber"

        price = float(metrics.get("price", 0.0))
        d_vwap = float(metrics.get("daily_vwap", 0.0))
        w_vwap = float(metrics.get("weekly_vwap", 0.0))
        e_20 = float(metrics.get("ema_20d", 0.0))
        e_50 = float(metrics.get("ema_50d", 0.0))
        m_200 = float(metrics.get("ma_200d", 0.0))
        sw_h = float(metrics.get("swing_high_4h", 0.0))
        sw_l = float(metrics.get("swing_low_4h", 0.0))
        floor = float(metrics.get("base_floor", 0.0))

        d_vwap_diff = ((price - d_vwap) / d_vwap * 100) if d_vwap > 0 else 0.0
        w_vwap_diff = ((price - w_vwap) / w_vwap * 100) if w_vwap > 0 else 0.0
        e_20_diff = ((price - e_20) / e_20 * 100) if e_20 > 0 else 0.0
        e_50_diff = ((price - e_50) / e_50 * 100) if e_50 > 0 else 0.0
        m_200_diff = ((price - m_200) / m_200 * 100) if m_200 > 0 else 0.0

        spot_vol = float(metrics.get("spot_vol_24h", 0.0))
        vol_ratio = float(metrics.get("spot_vol_ratio", 1.0))
        cvd_ratio = float(metrics.get("spot_cvd_ratio", 1.0))
        cvd_7d = float(metrics.get("spot_cvd_slope_7d", 0.0))
        cvd_14d = float(metrics.get("spot_cvd_slope_14d", 0.0))
        perp_trend = str(metrics.get("perp_cvd_trend", "neutral"))
        perp_slope = float(metrics.get("perp_cvd_slope_24h", 0.0))
        depth = float(metrics.get("bids_asks_depth_ratio", 1.0))

        oi = float(metrics.get("open_interest", 0.0))
        oi_1h = float(metrics.get("oi_change_1h_pct", 0.0))
        oi_4h = float(metrics.get("oi_change_4h_pct", 0.0))
        oi_24h = float(metrics.get("oi_change_24h_pct", 0.0))
        oi_3d = float(metrics.get("oi_change_3d_pct", 0.0))
        oi_hist_ok = bool(metrics.get("oi_history_available", True))
        funding = float(metrics.get("funding_rate", 0.0)) * 100
        funding_ann = float(metrics.get("funding_rate_annualized", 0.0))
        basis = float(metrics.get("futures_basis_annualized", 0.0))
        ls_ratio = float(metrics.get("long_short_account_ratio", 1.0))
        ls_avail = bool(metrics.get("ls_ratio_available", True))
        ls_pct_72h = metrics.get("ls_ratio_percentile_72h")
        atr_pct_72h = metrics.get("atr_percentile_72h")
        long_pct = (ls_ratio / (1.0 + ls_ratio) * 100) if (1.0 + ls_ratio) > 0 else 50.0
        spot_source = str(metrics.get("spot_data_source", "Binance Public Market-Data REST"))
        futures_source = str(metrics.get("futures_data_source", "Perp Public REST"))
        oi_scope = str(metrics.get("oi_scope", "Tracked venue perpetual subset"))

        atr = float(metrics.get("atr", 0.0))
        atr_comp = float(metrics.get("atr_compression_pct", 0.0))
        ch_width = ((sw_h - sw_l) / max(price, 1.0) * 100) if sw_h > 0 else 0.0
        chg_24h = float(metrics.get("price_change_24h_pct", 0.0))

        oi_24h_disp = f"{oi_24h:+.2f}%" if oi_hist_ok else "N/A (Fallback)"
        oi_1h_4h_disp = f"{oi_1h:+.2f}% / {oi_4h:+.2f}%" if oi_hist_ok else "N/A / N/A"
        oi_3d_disp = f"{oi_3d:+.2f}%" if oi_hist_ok else "N/A"
        ls_disp = (
            f"{ls_ratio:.2f} ({long_pct:.1f}% L"
            + (f", p{ls_pct_72h:.0f} 72h" if ls_pct_72h is not None else "")
            + ")"
        ) if ls_avail else "Unavailable (Fallback)"
        atr_comp_disp = f"{atr_comp:.1f}%" + (f" (p{atr_pct_72h:.0f} 72h)" if atr_pct_72h is not None else "")

        regime_name = str(regime.get("name", "Transition / Mixed"))
        diagnosis = wrap36(str(regime.get("diagnosis", "")))
        tagline = wrap36(tagline_src)
        action = wrap36(str(regime.get("action", "Wait / Hold 100% USDT (0.0x)")))
        rotation = str(regime.get("rotation", "Remain USDT"))
        stop_p = float(regime.get("stop_price", 0.0))
        stop_dist = float(regime.get("stop_distance_pct", 0.0))
        struct_low = float(regime.get("structural_invalidation_level", sw_l or 0.0))
        stop_rule = wrap36(str(regime.get("stop_rule", "")))
        stop_note = wrap36(str(regime.get("stop_placement_note", ""))) if regime.get("stop_placement_note") else ""
        entry_inst = wrap36(str(regime.get("entry_instruction", "")))
        rule_score = str(regime.get("majority_score", "0/4 observations confirmed"))
        dom_magnet = str(regime.get("dominant_magnet", "Neutral"))
        imm_ratio = float(regime.get("immediate_imbalance_ratio", 1.0))
        imm_disp = f"~{round(imm_ratio):.0f}x" if imm_ratio >= 10 else f"{imm_ratio:.1f}x"
        tot_ratio = float(regime.get("total_ladder_imbalance_ratio", 1.0))
        tot_lower = float(regime.get("total_ladder_lower_vol", 0.0))
        tot_upper = float(regime.get("total_ladder_upper_vol", 0.0))
        lsce_status = str(regime.get("lsce_status", "UNTESTED"))
        lsce_detail = wrap36(str(regime.get("lsce_detail", "")))

        matched_crit = regime.get("matched_criteria", [])
        criteria_lines = [f"✓ {wrap36(c)}" for c in matched_crit] if matched_crit else ["(No rule criteria matched)"]
        matched_crit_ascii = "\n".join(criteria_lines)

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_p = float(upper_c.get("price_level", 0.0))
        u_d = float(upper_c.get("distance_pct", 0.0))
        u_v = float(upper_c.get("estimated_vol_usd", 0.0)) / 1e6
        l_p = float(lower_c.get("price_level", 0.0))
        l_d = float(lower_c.get("distance_pct", 0.0))
        l_v = float(lower_c.get("estimated_vol_usd", 0.0)) / 1e6

        # Deliverable 2 + T3: Fixed-Column Liquidation Ladder using CANONICAL ladder
        ladder = self._get_canonical_ladder(data)
        lsce_up = lsce_status.upper()
        is_sweep = ("IN_PROGRESS" in lsce_up) or ("FAILED" in lsce_up)
        upper_lines = []
        lower_lines = []
        for row in ladder:
            tier_lbl = row["tier"]
            # Keep fixed <=11-char column width on mobile
            if "50-100x" in tier_lbl:
                tier_short = "50-100x S"
            elif "100x" in tier_lbl:
                tier_short = "100x Longs"
            else:
                tier_short = tier_lbl
            px_str = f"${row['price']:,.0f}"
            dist_str = f"{row['distance_pct']:+.2f}%"
            vol_str = self._format_pool_m(row["estimated_vol_m"])
            if row["side"] == "upper":
                upper_lines.append(f"{tier_short:<10} {px_str:>8} {dist_str:>7} {vol_str:>8}")
            else:
                if row.get("is_nearest"):
                    lower_lines.append(
                        f"{tier_short:<10} {px_str:>8} {dist_str:>7} <span class=\"c-rose\">{vol_str:>8}</span> [🔥]"
                    )
                    if is_sweep:
                        lower_lines.append(
                            '<span class="c-rose" style="font-weight: bold;">  └─► &lt;&lt;&lt; PIERCING / ACTIVE SWEEP &gt;&gt;&gt;</span>'
                        )
                else:
                    lower_lines.append(f"{tier_short:<10} {px_str:>8} {dist_str:>7} {vol_str:>8}")

        hdr_row = f"{'TIER':<10} {'PRICE':>8} {'DIST':>7} {'EST.POOL':>8}"
        row_spot = f"{'SPOT PRICE':<10} {f'${price:,.0f}':>8} (Zero-Axis Anchor)"
        ladder_table = "\n".join([
            hdr_row,
            "------------------------------------",
            *upper_lines,
            "------------------------------------",
            row_spot,
            "------------------------------------",
            *lower_lines,
            "------------------------------------",
            f"Total (Est): {self._format_pool_m(tot_lower)} Down vs {self._format_pool_m(tot_upper)} Up",
        ])

        plain_verdict = wrap36(str(regime.get("plain_english_verdict", "")))
        why_pts = regime.get("why_points", [])
        why_1 = wrap36("1. " + why_pts[0]) if len(why_pts) > 0 else ""
        why_2 = wrap36("2. " + why_pts[1]) if len(why_pts) > 1 else ""
        why_3 = wrap36("3. " + why_pts[2]) if len(why_pts) > 2 else ""
        why_sizing = wrap36(str(regime.get("why_sizing_reason", "")))
        why_stop = wrap36(str(regime.get("why_stop_reason", "")))
        risk_summary_txt = wrap36(str(risk.get("risk_advisory", "")))

        mf = regime.get("magnet_factors", {})
        f1_size = wrap36(str(mf.get("factor_1_size", "")))
        f2_lead = wrap36(str(mf.get("factor_2_spot_leadership", "")))
        f3_crowd = wrap36(str(mf.get("factor_3_crowding_fuel", "")))
        f4_struct = wrap36(str(mf.get("factor_4_regime_structure", "")))
        f5_asym = wrap36(str(mf.get("factor_5_asymmetry", "")))
        f6_atr = wrap36(str(mf.get("factor_6_atr_volatility", "")))
        dom_reason = wrap36(str(regime.get("dominant_magnet_reason", dom_magnet)))

        # Build 6-state matrix strip for Panel 3 (T7)
        matrix_defs = [
            ("SPOT_LED_EXPANSION", "1.Spot Exp", "#10b981"),
            ("LEVERAGED_FRAGILE_UPSIDE", "2.Lev Trap", "#f97316"),
            ("RANGE_LIQUIDATION_MAGNET", "3.Range/Mag", "#06b6d4"),
            ("CASCADE_FORCED_DELEVERAGING", "4.Cascade", "#f43f5e"),
            ("DISTRIBUTION_BEAR_CONTINUATION", "5.Distrib", "#ef4444"),
            ("TRANSITION_MIXED", "Transition", "#f59e0b"),
        ]
        matrix_chips = []
        for mid, mlabel, mcol in matrix_defs:
            active = mid == regime_id
            bg = f"background: {mcol}26; border: 1.5px solid {mcol}; color: #ffffff; font-weight: 900;" if active else f"background: #101218; border: 1px solid {mcol}55; color: #a1a1aa;"
            tag = " *" if active else ""
            matrix_chips.append(
                f'<div style="{bg} border-radius: 5px; padding: 5px 4px; font-size: 9px; text-align: center;">{mlabel}{tag}</div>'
            )
        regime_matrix_html = "\n".join(matrix_chips)

        lsce_card_cls = "sub-card-rose" if lsce_status == "SWEEP_FAILED_BREAKDOWN" else (
            "sub-card-amber" if "SWEEP_IN_PROGRESS" in lsce_status else (
                "sub-card-emerald" if "CONFIRMED" in lsce_status else "sub-card-sky"
            )
        )

        raw_json_str = _json.dumps(data, indent=2)

        tpl = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
  <title>BTC Magnet Monitor • Mobile Text Terminal</title>
  <meta name="theme-color" content="#09090b">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="BTC Magnet">
  <link rel="manifest" href="manifest.json?v=7">
  <link rel="icon" type="image/png" sizes="192x192" href="icon-192.png?v=7">
  <link rel="icon" type="image/png" sizes="512x512" href="icon-512.png?v=7">
  <link rel="apple-touch-icon" href="icon-192.png?v=7">
  <link rel="shortcut icon" href="icon-192.png?v=7">
  <style>
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    html {
      width: 100%;
      max-width: 100vw;
      overflow-x: hidden;
      background-color: #09090b;
    }
    body {
      width: 100%;
      max-width: 100vw;
      overflow-x: hidden;
      background-color: #09090b;
      color: #e4e4e7;
      font-family: Consolas, "Liberation Mono", Menlo, Monaco, "Courier New", monospace;
      font-size: 11px;
      line-height: 1.5;
      padding: 8px 8px 80px 8px;
      -webkit-font-smoothing: antialiased;
    }
    .terminal-wrapper {
      width: 100%;
      max-width: 390px;
      margin: 0 auto;
    }

    .app-brand-header {
      background: linear-gradient(180deg, #131622 0%, #09090b 100%);
      border: 1.5px solid rgba(56, 189, 248, 0.55);
      box-shadow: 0 0 14px rgba(56, 189, 248, 0.12);
      border-radius: 8px;
      padding: 10px 10px;
      margin-bottom: 10px;
      width: 100%;
    }
    .brand-top-row {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
    }
    .brand-logo-squircle {
      width: 44px;
      height: 44px;
      flex-shrink: 0;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid rgba(0, 230, 118, 0.4);
      background: radial-gradient(circle at center, #14171f 0%, #09090b 100%);
      box-shadow: 0 0 14px rgba(0, 230, 118, 0.25);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2px;
    }
    .brand-logo-img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: contain;
    }
    .brand-title-group {
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
      flex: 1;
    }
    .header-line-1 {
      font-size: 11.5px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: -0.3px;
      font-family: inherit;
      overflow-wrap: break-word;
    }
    .header-line-2 {
      font-size: 9.5px;
      font-weight: 600;
      color: #38bdf8;
      letter-spacing: -0.1px;
      font-family: inherit;
      overflow-wrap: break-word;
    }
    .header-meta-sep {
      margin-top: 8px;
      padding-top: 6px;
      border-top: 1px dashed rgba(56, 189, 248, 0.35);
      font-size: 9px;
      color: #a1a1aa;
      font-family: inherit;
      line-height: 1.45;
      overflow-wrap: break-word;
    }

    /* Touch Ergonomics Top View Switcher (Min 44px Hitboxes) */
    .view-switcher {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
      margin-bottom: 12px;
    }
    .view-btn {
      min-height: 44px;
      min-width: 44px;
      padding: 10px 4px;
      background: #14171f;
      border: 1.5px solid rgba(99, 102, 241, 0.45);
      border-radius: 6px;
      color: #a1a1aa;
      font-family: inherit;
      font-size: 11px;
      font-weight: 800;
      text-align: center;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
      touch-action: manipulation;
    }
    .view-btn.active {
      background: #0284c7;
      color: #ffffff;
      border-color: #38bdf8;
      box-shadow: 0 0 12px rgba(2, 132, 199, 0.4);
    }
    .view-btn:active { transform: scale(0.96); }

    .stale-banner {
      background: rgba(225, 29, 72, 0.15);
      border: 1.5px solid #e11d48;
      border-radius: 6px;
      padding: 8px 10px;
      font-size: 10px;
      font-weight: 800;
      color: #f43f5e;
      margin-bottom: 12px;
      line-height: 1.4;
      text-align: center;
    }

    /* Distinctive Panel Boxes */
    .panel-box {
      background: #0d0e12;
      border: 1.5px solid #27272a;
      border-radius: 8px;
      padding: 11px 10px 8px 10px;
      margin-bottom: 14px;
    }
    .panel-hdr {
      font-size: 11.5px;
      font-weight: 900;
      color: #38bdf8;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      margin-top: 0;
      margin-bottom: 9px;
      padding-bottom: 6px;
      border-bottom: 1.5px solid #27272a;
    }

    .panel-box-hero {
      background: linear-gradient(180deg, #0d1615 0%, #090a0d 100%);
      border-color: #10b981;
      box-shadow: 0 0 16px rgba(16, 185, 129, 0.15);
    }
    .panel-box-hero .panel-hdr { color: #34d399; border-bottom-color: rgba(16, 185, 129, 0.35); }

    .panel-box-cyan {
      background: linear-gradient(180deg, #0c171c 0%, #090a0d 100%);
      border-color: #06b6d4;
      box-shadow: 0 0 14px rgba(6, 182, 212, 0.13);
    }
    .panel-box-cyan .panel-hdr { color: #22d3ee; border-bottom-color: rgba(6, 182, 212, 0.35); }

    .panel-box-emerald {
      background: linear-gradient(180deg, #0d1713 0%, #090a0d 100%);
      border-color: #10b981;
      box-shadow: 0 0 14px rgba(16, 185, 129, 0.13);
    }
    .panel-box-emerald .panel-hdr { color: #34d399; border-bottom-color: rgba(16, 185, 129, 0.35); }

    .panel-box-amber {
      background: linear-gradient(180deg, #19130b 0%, #090a0d 100%);
      border-color: #f59e0b;
      box-shadow: 0 0 14px rgba(245, 158, 11, 0.14);
    }
    .panel-box-amber .panel-hdr { color: #fbbf24; border-bottom-color: rgba(245, 158, 11, 0.35); }

    .panel-box-orange {
      background: linear-gradient(180deg, #1b110b 0%, #090a0d 100%);
      border-color: #f97316;
      box-shadow: 0 0 14px rgba(249, 115, 22, 0.14);
    }
    .panel-box-orange .panel-hdr { color: #fb923c; border-bottom-color: rgba(249, 115, 22, 0.35); }

    .panel-box-rose {
      background: linear-gradient(180deg, #1b0d12 0%, #090a0d 100%);
      border-color: #f43f5e;
      box-shadow: 0 0 14px rgba(244, 63, 94, 0.14);
    }
    .panel-box-rose .panel-hdr { color: #fb7185; border-bottom-color: rgba(244, 63, 94, 0.35); }

    .panel-box-sky {
      background: linear-gradient(180deg, #0c141d 0%, #090a0d 100%);
      border-color: #0ea5e9;
      box-shadow: 0 0 14px rgba(14, 165, 233, 0.13);
    }
    .panel-box-sky .panel-hdr { color: #38bdf8; border-bottom-color: rgba(14, 165, 233, 0.35); }

    .panel-box-purple {
      background: linear-gradient(180deg, #150e1e 0%, #090a0d 100%);
      border-color: #a855f7;
      box-shadow: 0 0 14px rgba(168, 85, 247, 0.14);
    }
    .panel-box-purple .panel-hdr { color: #c084fc; border-bottom-color: rgba(168, 85, 247, 0.35); }

    .panel-box-gold {
      background: linear-gradient(180deg, #17150b 0%, #090a0d 100%);
      border-color: #eab308;
      box-shadow: 0 0 14px rgba(234, 179, 8, 0.13);
    }
    .panel-box-gold .panel-hdr { color: #fde047; border-bottom-color: rgba(234, 179, 8, 0.35); }

    /* Distinctive Sub-Cards inside Panels */
    .sub-card {
      background: #0a0b0f;
      border: 1px solid #27272a;
      border-radius: 6px;
      padding: 8px 8px 6px 8px;
      margin-bottom: 8px;
    }
    .sub-card-emerald { border-color: rgba(16, 185, 129, 0.48); }
    .sub-card-cyan    { border-color: rgba(6, 182, 212, 0.48); }
    .sub-card-sky     { border-color: rgba(56, 189, 248, 0.48); }
    .sub-card-indigo  { border-color: rgba(129, 140, 248, 0.50); }
    .sub-card-amber   { border-color: rgba(245, 158, 11, 0.50); }
    .sub-card-rose    { border-color: rgba(244, 63, 94, 0.50); }
    .sub-card-purple  { border-color: rgba(168, 85, 247, 0.50); }
    .sub-card-teal    { border-color: rgba(20, 184, 166, 0.48); }

    pre.ascii {
      font-family: inherit;
      font-size: 10.5px;
      line-height: 1.46;
      letter-spacing: -0.2px;
      white-space: pre-wrap !important;
      word-break: break-word !important;
      overflow-wrap: break-word !important;
      color: #d4d4d8;
      margin-bottom: 2px;
    }
    .c-gold   { color: #fde047; font-weight: bold; }
    .c-cyan   { color: #38bdf8; font-weight: bold; }
    .c-green  { color: #4ade80; font-weight: bold; }
    .c-rose   { color: #fb7185; font-weight: bold; }
    .c-amber  { color: #fbbf24; font-weight: bold; }
    .c-indigo { color: #a5b4fc; font-weight: bold; }
    .c-purple { color: #c084fc; font-weight: bold; }
    .c-muted  { color: #71717a; }

    .matrix-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 5px;
      margin-top: 6px;
    }

    .btn-copy {
      display: block;
      width: 100%;
      background: #0284c7;
      color: #ffffff;
      padding: 11px 10px;
      font-family: inherit;
      font-size: 11.5px;
      font-weight: 900;
      border: 1.5px solid #38bdf8;
      border-radius: 6px;
      cursor: pointer;
      text-align: center;
      margin: 8px 0;
      box-shadow: 0 4px 14px rgba(2, 132, 199, 0.3);
      min-height: 44px;
    }
    .btn-copy-blind {
      background: #0f766e;
      border-color: #2dd4bf;
      box-shadow: 0 4px 14px rgba(20, 184, 166, 0.25);
    }
    .btn-copy:active { opacity: 0.9; }
    .btn-copy.copied {
      background: #16a34a !important;
      border-color: #4ade80 !important;
      color: #ffffff !important;
    }

    .prompt-box {
      max-height: 240px;
      overflow-y: auto;
      overflow-x: hidden;
      background: #0b0c10;
      border: 1px solid rgba(56, 189, 248, 0.35);
      border-radius: 6px;
      padding: 8px;
      margin: 6px 0;
      font-size: 9.5px;
      color: #a1a1aa;
      white-space: pre-wrap !important;
      word-break: break-word !important;
      overflow-wrap: break-word !important;
    }

    footer {
      text-align: center;
      padding: 20px 4px 12px 4px;
      font-size: 10px;
      color: #71717a;
      line-height: 1.7;
      border-top: 1px dashed rgba(99, 102, 241, 0.45);
      margin-top: 20px;
    }
    footer a { color: #38bdf8; text-decoration: none; }

    #toast {
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: #16a34a;
      color: #ffffff;
      padding: 9px 18px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 800;
      box-shadow: 0 4px 20px rgba(0,0,0,0.85);
      z-index: 9999;
      opacity: 0;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
      white-space: nowrap;
    }
    #toast.show {
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }
  </style>
</head>
<body>

  <div class="terminal-wrapper">

    <!-- APP BRANDING HEADER -->
    <header class="app-brand-header">
      <div class="brand-top-row">
        <div class="brand-logo-squircle">
          <img src="./assets/app-logo.png?v=7" alt="BTC Magnet Monitor Logo" class="brand-logo-img">
        </div>
        <div class="brand-title-group">
          <div class="header-line-1">BTC MAGNET MONITOR :: 5-REGIME ENGINE</div>
          <div class="header-line-2">Microstructure Positioning &amp; Liquidation Telemetry</div>
        </div>
      </div>
      <div class="header-meta-sep">
        MANDATE: SPOT ONLY (0.0x) &bull; SESSION: <span class="c-green" id="hdr-session">ACTIVE</span><br>
        SCAN: <span class="c-cyan" id="hdr-scan-ts">__TIME_UTC__</span> &bull; EVERY 30M (:00/:30)<br>
        NEXT UPDATE: <span class="c-amber" id="hdr-next-upd">--:-- UTC</span> (<span class="c-green" id="hdr-countdown">in --m --s</span>)
      </div>
      <div style="display:none;" aria-hidden="true">5-Regime Radar Observable Positioning Mechanics</div>
    </header>

    <!-- TOP VIEW SWITCHER -->
    <nav class="view-switcher" role="tablist" aria-label="HUD Navigation Modes">
      <button class="view-btn active" id="btn-view-hud" onclick="switchView('hud')" role="tab" aria-selected="true">[HUD]</button>
      <button class="view-btn" id="btn-view-json" onclick="switchView('json')" role="tab" aria-selected="false">[JSON]</button>
      <button class="view-btn" id="btn-view-delta" onclick="switchView('delta')" role="tab" aria-selected="false">[DELTA]</button>
      <button class="view-btn" id="btn-view-prompt" onclick="switchView('prompt')" role="tab" aria-selected="false">[PROMPT]</button>
    </nav>

    <!-- STALE TELEMETRY BANNER (>30M) -->
    <div class="stale-banner" id="static-stale-banner" style="__STATIC_STALE_STYLE__">
      ⚠️ [WARNING: TELEMETRY STALE &gt;30M] &bull; Past 30m scheduled scan cadence. Live spot REST feed active below.
    </div>
    <div class="stale-banner" id="dyn-stale-banner" style="display: none;">
      ⚠️ [WARNING: TELEMETRY STALE &gt;30M] &bull; Past 30m scheduled scan cadence. Live spot REST feed active below.
    </div>

    <!-- RAW JSON VIEW CONTAINER -->
    <div id="json-view-container" style="display: none;" class="panel-box panel-box-gold">
      <div class="panel-hdr">Raw Telemetry JSON Feed (regime.json)</div>
      <button class="btn-copy" onclick="copyJsonFeed()" style="margin-top: 0; margin-bottom: 10px;">
        📋 COPY RAW JSON TELEMETRY
      </button>
      <pre class="prompt-box" id="raw-json-pre" style="max-height: 480px;">__RAW_JSON__</pre>
    </div>

    <!-- MAIN HUD VIEW CONTAINER -->
    <div id="hud-view-container">

      <!-- PANEL 1: REAL-TIME BTC SPOT PRICE (LIVE) -->
      <div id="panel-1" class="panel-box panel-box-hero">
        <div class="panel-hdr">Panel 1 &bull; Real-Time BTC Spot Price (Live)</div>

        <div class="sub-card sub-card-emerald">
          <pre class="ascii"><span class="c-gold" style="font-size: 19px; display: block; padding: 2px 0;" id="live-btc-price">$__PRICE__</span>
<span id="live-24h-change">__CHANGE_24H__% (24h)</span>
Drift vs Scan ($__PRICE__): <span id="live-price-drift">$0.00 (0.00%)</span>
Binance Spot Public Ticker
Live REST 5s Price Feed
<span class="c-green" id="live-ticker-status">● Live Exchange REST Feed</span></pre>
        </div>

        <div class="sub-card sub-card-sky">
          <pre class="ascii">🌐 UTC Time (Exchange Standard)
<span class="c-cyan" id="clock-utc-time">__TIME_UTC__</span> (<span id="clock-utc-date">__DATE_UTC__</span>)
🇸🇬 SGT Time (UTC+8 Asia Anchor)
<span class="c-gold" id="clock-sgt-time">__TIME_SGT__</span> (<span id="clock-sgt-date">__DATE_UTC__</span>)</pre>
        </div>

        <div class="sub-card sub-card-indigo">
          <pre class="ascii"><span class="c-indigo">Automated Telemetry Cadence:</span>
Updates: <span class="c-cyan">Every 30 Minutes</span> (:00 &amp; :30 UTC)
Last Scan: __TIME_UTC__ (__TIME_SGT__)
Next Update: <span class="c-amber" id="p1-next-upd">--:-- UTC (--:-- SGT)</span>
Countdown:   <span class="c-green" id="p1-countdown">in --m --s</span></pre>
        </div>

        <div class="sub-card sub-card-amber" style="margin-bottom: 2px;">
          <pre class="ascii">Active Market Session Zone:
<span class="c-green" id="session-name">ACTIVE</span>
<span id="session-desc">Market Session</span>
<span id="session-hours">00:00 - 24:00 UTC</span></pre>
        </div>
      </div>

      <!-- PANEL 2: ON-EXCHANGE TELEMETRY -->
      <div id="panel-2" class="panel-box panel-box-cyan">
        <div class="panel-hdr">Panel 2 &bull; On-Exchange Telemetry (Raw vs Modeled)</div>

        <div class="sub-card sub-card-cyan">
          <pre class="ascii"><span class="c-cyan">Raw Feed Provenance:</span>
Spot: __SPOT_SOURCE__
Perps: __FUTURES_SOURCE__
OI Scope: __OI_SCOPE__
<span class="c-amber">Modeled:</span> 10x-100x liquidity tiers below</pre>
        </div>

        <div class="sub-card sub-card-sky">
          <pre class="ascii"><span class="c-cyan">Feed 1 &bull; Trend &amp; Moving Averages:</span>
Spot Price:     $__PRICE__
Daily VWAP:     $__DAILY_VWAP__ (__DAILY_VWAP_DIFF__%)
Weekly VWAP:    $__WEEKLY_VWAP__ (__WEEKLY_VWAP_DIFF__%)
20D EMA:        $__EMA_20D__ (__EMA_20D_DIFF__%)
50D EMA:        $__EMA_50D__ (__EMA_50D_DIFF__%)
200D SMA:       $__MA_200D__ (__MA_200D_DIFF__%)
4H Swing L/H:   $__SWING_LOW__ / $__SWING_HIGH__
4H Range Width: __RANGE_WIDTH__%
Base Floor:     $__BASE_FLOOR__</pre>
        </div>

        <div class="sub-card sub-card-emerald">
          <pre class="ascii"><span class="c-green">Feed 2 &bull; Spot CVD &amp; Order Book:</span>
24h Spot Vol:   __SPOT_VOL__ BTC (__SPOT_VOL_RATIO__x)
Spot CVD Ratio: __SPOT_CVD_RATIO__
7D / 14D Slope: __SPOT_CVD_7D__ / __SPOT_CVD_14D__
Perp CVD Trend: __PERP_TREND__ (__PERP_SLOPE__)
Book Depth:     __DEPTH_RATIO__ (Bids/Asks)</pre>
        </div>

        <div class="sub-card sub-card-amber">
          <pre class="ascii"><span class="c-amber">Feed 3 &bull; Derivatives Positioning:</span>
Open Interest:  __OI__ BTC
OI 24h Delta:   __OI_24H__
OI 1h / 4h:     __OI_1H_4H__
OI 3D Delta:    __OI_3D__
Funding (8h/A): __FUNDING__% / __FUNDING_ANN__%
Futures Basis:  __BASIS__% (Ann.)
L/S Ratio:      __LS_RATIO_DISP__</pre>
        </div>

        <div class="sub-card sub-card-purple" style="margin-bottom: 2px;">
          <pre class="ascii"><span class="c-purple">Feed 4 &bull; Volatility &amp; Exhaustion:</span>
Daily ATR:      $__ATR__
ATR Compress:   __ATR_COMP_DISP__</pre>
        </div>
      </div>

      <!-- PANEL 3: MACRO MARKET REGIME DIAGNOSIS -->
      <div id="panel-3" class="panel-box __REGIME_CSS_CLS__">
        <div class="panel-hdr">Panel 3 &bull; Macro Market Regime Diagnosis</div>

        <div class="sub-card sub-card-amber">
          <pre class="ascii">Classified Market Regime:
<span class="__REGIME_TXT_CLS__" style="font-size: 12.5px;">__REGIME_NAME__</span>

Diagnosis:
__DIAGNOSIS__

Executive Summary:
__TAGLINE__

Rule Match Confirmation:
__RULE_SCORE__
<span id="p3-conf-fresh" class="c-muted">Freshness: Verified &le;35m Cadence</span></pre>
        </div>

        <div class="sub-card sub-card-teal">
          <pre class="ascii"><span class="c-green">Empirical Rule Gate Evidence:</span>
__MATCHED_CRITERIA_ASCII__</pre>
        </div>

        <div class="sub-card sub-card-indigo" style="margin-bottom: 2px;">
          <pre class="ascii"><span class="c-indigo">5-Regime + Transition Matrix:</span></pre>
          <div class="matrix-grid">
            __REGIME_MATRIX_HTML__
          </div>
        </div>
      </div>

      <!-- METHOD 1: VERDICT BY COPY DATA & PROMPT TO AI -->
      <div id="method-1" class="panel-box panel-box-sky">
        <div class="panel-hdr">Method 1 &bull; Copy Data &amp; Prompt to AI</div>

        <div class="sub-card sub-card-teal">
          <pre class="ascii"><span class="c-cyan">Zero-Black-Box Audit Modes:</span>
Choose <span class="c-green">Blind Telemetry</span> (metrics only, no
system verdict revealed) for an unbiased
LLM vote, or <span class="c-cyan">Full Audit Prompt</span> below.</pre>
          <button class="btn-copy btn-copy-blind" id="copy-blind-btn" onclick="copyBlindPrompt()">
            🧪 COPY BLIND TELEMETRY (NO VERDICT)
          </button>
        </div>

        <div class="sub-card sub-card-sky" style="margin-bottom: 2px;">
          <button class="btn-copy" id="copy-prompt-btn" onclick="copyTelemetryPrompt()">
            📋 COPY FULL AUDIT PROMPT FOR AI
          </button>

          <pre class="ascii">[Full Telemetry &amp; Audit Prompt (__PROMPT_LEN__ chars)]</pre>
          <pre class="prompt-box" id="prompt-box-pre">__RAW_PROMPT__</pre>
        </div>
      </div>

      <!-- METHOD 2: OUR SYSTEM VERDICT (FULL-ON VIEW) -->
      <div id="method-2" class="panel-box panel-box-purple">
        <div class="panel-hdr">Method 2 &bull; Our System Verdict (Full-On View)</div>

        <div class="sub-card sub-card-emerald">
          <pre class="ascii">Dominant Magnet:
<span class="c-rose">__DOM_REASON__</span>

Plain English Bottom Line:
💡 "__PLAIN_VERDICT__"

The 3 Key Empirical Drivers:
__WHY_1__
__WHY_2__
__WHY_3__</pre>
        </div>

        <div class="sub-card sub-card-amber">
          <pre class="ascii"><span class="c-amber">Why This Exact Sizing &amp; Risk:</span>
__WHY_SIZING__
__RISK_SUMMARY__</pre>
        </div>

        <div class="sub-card sub-card-rose">
          <pre class="ascii"><span class="c-rose">Where Is Your Safety Net?</span>
__WHY_STOP__
__STOP_NOTE__</pre>
        </div>

        <div class="sub-card __LSCE_CARD_CLS__">
          <pre class="ascii"><span class="c-amber">LSCE State Machine Gate:</span>
Status: <span class="c-rose">__LSCE_STATUS__</span>
Detail:
__LSCE_DETAIL__</pre>
        </div>

        <div class="sub-card sub-card-indigo">
          <pre class="ascii"><span class="c-indigo">Modeled Liquidity Pools (Estimate):</span>
Upper Short: $__UPPER_P__ (+__UPPER_D__%) &bull; $__UPPER_V__M (Est)
Lower Long:  $__LOWER_P__ (-__LOWER_D__%) &bull; <span class="c-rose">$__LOWER_V__M (Est)</span>

<span class="c-indigo">10x-100x Modeled Heatmap Ladder:</span>
__LADDER_TABLE__

Immediate Skew: <span class="c-amber">__IMM_RATIO__</span> (Modeled)
Total Ladder:   <span class="c-rose">__TOT_RATIO__x</span> (Modeled)
Dominant Pull:  <span class="c-rose">__DOMINANT_MAGNET__</span></pre>
        </div>

        <div class="sub-card sub-card-teal" style="margin-bottom: 2px;">
          <pre class="ascii"><span class="c-cyan">Six-Factor Magnet Analysis:</span>
1. Cluster Size:
__F1_SIZE__
2. Spot vs Perps:
__F2_LEADERSHIP__
3. Crowding Fuel:
__F3_CROWDING__
4. Structure:
__F4_STRUCTURE__
5. Distance:
__F5_ASYMMETRY__
6. Volatility:
__F6_ATR__
Decisive Call:
<span class="c-rose">__DOM_REASON__</span></pre>
        </div>
      </div>

    </div><!-- /#hud-view-container -->

    <footer>
      <div style="font-weight: 800; color: #f4f4f5; margin-bottom: 6px;">
        BTC Magnet Monitor &bull; 5-Regime Radar
      </div>
      <div>
        <a href="index.html">Web Dashboard</a> &bull;
        <a href="regimes.html">5 Regimes &amp; Math</a> &bull;
        <a href="privacy.html">Privacy Policy</a>
      </div>
      <div style="margin-top: 8px; color: #71717a; font-size: 9px;">
        Scan ID: <span class="c-cyan">__SCAN_ID__</span> &bull; Updates Every 30m (:00/:30 UTC)<br>
        __SPOT_SOURCE__ &bull; __FUTURES_SOURCE__<br>
        Strictly for informational and risk research purposes. Not financial advice.
      </div>
    </footer>

  </div>

  <!-- Toast Notification -->
  <div id="toast">✓ Copied to Clipboard!</div>

  <script>
    const SCAN_PRICE = __PRICE_RAW__;
    const SCAN_TS = '__SCAN_TS__';
    const PROMPT_TEXT = _RAW_PROMPT_JSON_;
    const BLIND_PROMPT_TEXT = _BLIND_PROMPT_JSON_;
    const RAW_JSON_PAYLOAD = _RAW_JSON_TEXT_;

    function switchView(mode) {
      document.querySelectorAll('.view-btn').forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      const activeBtn = document.getElementById('btn-view-' + mode);
      if (activeBtn) {
        activeBtn.classList.add('active');
        activeBtn.setAttribute('aria-selected', 'true');
      }

      const hudView = document.getElementById('hud-view-container');
      const jsonView = document.getElementById('json-view-container');

      if (mode === 'hud') {
        hudView.style.display = 'block';
        jsonView.style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else if (mode === 'json') {
        hudView.style.display = 'none';
        jsonView.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else if (mode === 'delta') {
        hudView.style.display = 'block';
        jsonView.style.display = 'none';
        const d = document.getElementById('method-2');
        if (d) d.scrollIntoView({ behavior: 'smooth' });
      } else if (mode === 'prompt') {
        hudView.style.display = 'block';
        jsonView.style.display = 'none';
        const p = document.getElementById('method-1');
        if (p) p.scrollIntoView({ behavior: 'smooth' });
      }
    }

    function copyTextPayload(txt, msg, btnId) {
      function markBtn() {
        const b = btnId ? document.getElementById(btnId) : null;
        if (b) {
          b.classList.add('copied');
          setTimeout(() => b.classList.remove('copied'), 2200);
        }
        showToast(msg);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(markBtn).catch(() => fallbackCopy(txt, markBtn));
      } else {
        fallbackCopy(txt, markBtn);
      }
    }

    function copyTelemetryPrompt() {
      copyTextPayload(PROMPT_TEXT, '✓ Copied Full Audit Prompt!', 'copy-prompt-btn');
    }
    function copyPrompt() { copyTelemetryPrompt(); }
    function copyBlindPrompt() {
      copyTextPayload(BLIND_PROMPT_TEXT, '✓ Copied Blind Telemetry (No Verdict)!', 'copy-blind-btn');
    }
    function copyJsonFeed() {
      copyTextPayload(RAW_JSON_PAYLOAD, '✓ Copied Raw JSON Telemetry!', null);
    }

    function fallbackCopy(text, onOk) {
      try {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        if (onOk) onOk(); else showToast('✓ Copied to Clipboard!');
      } catch (err) {}
    }

    function showToast(msg) {
      const toast = document.getElementById('toast');
      if (toast) {
        toast.innerText = msg;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2200);
      }
      if (navigator.vibrate) {
        try { navigator.vibrate(40); } catch(e) {}
      }
    }

    const scanMs = Date.parse(SCAN_TS);

    function updateClocks() {
      const now = new Date();
      const utcMs = now.getTime();
      const pad = n => String(n).padStart(2, '0');
      const uH = pad(now.getUTCHours()), uM = pad(now.getUTCMinutes()), uS = pad(now.getUTCSeconds());
      const utcEl = document.getElementById('clock-utc-time');
      if (utcEl) utcEl.innerText = `${uH}:${uM}:${uS} UTC`;

      const sgt = new Date(utcMs + 8 * 3600000);
      const sH = pad(sgt.getUTCHours()), sM = pad(sgt.getUTCMinutes()), sS = pad(sgt.getUTCSeconds());
      const sgtEl = document.getElementById('clock-sgt-time');
      if (sgtEl) sgtEl.innerText = `${sH}:${sM}:${sS} SGT`;

      const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
      const uDate = `${now.getUTCDate()} ${months[now.getUTCMonth()]} ${now.getUTCFullYear()}`;
      const sDate = `${sgt.getUTCDate()} ${months[sgt.getUTCMonth()]} ${sgt.getUTCFullYear()}`;
      const uDateEl = document.getElementById('clock-utc-date');
      if (uDateEl) uDateEl.innerText = uDate;
      const sDateEl = document.getElementById('clock-sgt-date');
      if (sDateEl) sDateEl.innerText = sDate;

      // Next scheduled :00 / :30 UTC scan window & countdown
      const nextTarget = new Date(utcMs);
      nextTarget.setUTCSeconds(0, 0);
      if (now.getUTCMinutes() < 30) {
        nextTarget.setUTCMinutes(30);
      } else {
        nextTarget.setUTCMinutes(0);
        nextTarget.setUTCHours(now.getUTCHours() + 1);
      }
      const nUH = pad(nextTarget.getUTCHours()), nUM = pad(nextTarget.getUTCMinutes());
      const nextSgt = new Date(nextTarget.getTime() + 8 * 3600000);
      const nSH = pad(nextSgt.getUTCHours()), nSM = pad(nextSgt.getUTCMinutes());
      const remSec = Math.max(0, Math.floor((nextTarget.getTime() - utcMs) / 1000));
      const remM = pad(Math.floor(remSec / 60)), remS = pad(remSec % 60);

      const hdrNext = document.getElementById('hdr-next-upd');
      if (hdrNext) hdrNext.innerText = `${nUH}:${nUM} UTC`;
      const p1Next = document.getElementById('p1-next-upd');
      if (p1Next) p1Next.innerText = `${nUH}:${nUM} UTC (${nSH}:${nSM} SGT)`;
      const overdue = !isNaN(scanMs) && ((utcMs - scanMs) > 35 * 60 * 1000);
      const cdText = overdue ? `in ${remM}m ${remS}s (overdue)` : `in ${remM}m ${remS}s`;
      ['hdr-countdown', 'p1-countdown'].forEach(id => {
        const el = document.getElementById(id);
        if (el) {
          el.innerText = cdText;
          el.className = overdue ? 'c-amber' : 'c-green';
        }
      });

      const h = now.getUTCHours();
      let sess = 'ASIA ACCUMULATION', desc = '🌏 Asian / Pacific Session', hours = '00:00 - 08:00 UTC (08:00 - 16:00 SGT)';
      if (h >= 8 && h < 14) {
        sess = 'LONDON ACTIVE';
        desc = '🏛️ European / London Session';
        hours = '08:00 - 14:00 UTC (16:00 - 22:00 SGT)';
      } else if (h >= 14 && h < 21) {
        sess = 'NEW YORK CORE';
        desc = '🇺🇸 US Core Session • Volume Peak & Directional Flows';
        hours = '14:00 - 21:00 UTC (22:00 - 05:00 SGT)';
      } else if (h >= 21) {
        sess = 'US CLOSE / ASIA PRE-OPEN';
        desc = '🌙 Off-Hours Transition • Mean Reversion & Overnight Reset';
        hours = '21:00 - 24:00 UTC (05:00 - 08:00 SGT)';
      }
      const sName = document.getElementById('session-name');
      if (sName) sName.innerText = sess;
      const sDesc = document.getElementById('session-desc');
      if (sDesc) sDesc.innerText = desc;
      const sHours = document.getElementById('session-hours');
      if (sHours) sHours.innerText = hours;
      const hdrSess = document.getElementById('hdr-session');
      if (hdrSess) hdrSess.innerText = sess;
    }
    setInterval(updateClocks, 1000);
    updateClocks();

    // Dynamic 30-minute Stale Telemetry & Confidence Downgrade Checker
    if (!isNaN(scanMs) && (Date.now() - scanMs) > 30 * 60 * 1000) {
      const dynBanner = document.getElementById('dyn-stale-banner');
      if (dynBanner) dynBanner.style.display = 'block';
      const confFresh = document.getElementById('p3-conf-fresh');
      if (confFresh) {
        const ageM = Math.floor((Date.now() - scanMs) / 60000);
        confFresh.className = 'c-amber';
        confFresh.innerText = `⚠ Confidence Downgraded: Scan ${ageM}m old (>30m)`;
      }
    }

    const PRICE_APIS = [
      'https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT',
      'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
    ];
    let tickerFails = 0;
    async function updateLivePrice() {
      if (document.hidden) return;
      let p = NaN;
      for (const url of PRICE_APIS) {
        try {
          const r = await fetch(url);
          if (!r.ok) continue;
          const d = await r.json();
          const val = parseFloat(d && d.price);
          if (!isNaN(val) && val > 0) { p = val; break; }
        } catch(e) {}
      }
      const dEl = document.getElementById('live-price-drift');
      const stEl = document.getElementById('live-ticker-status');
      if (isNaN(p) || p <= 0) {
        tickerFails++;
        if (tickerFails >= 3) {
          if (stEl) {
            stEl.className = 'c-amber';
            stEl.innerText = '⚠ Ticker Unreachable — Scan Baseline';
          }
          if (dEl) {
            dEl.innerText = 'feed unreachable';
            dEl.style.color = '#fbbf24';
          }
        }
        return;
      }
      tickerFails = 0;
      if (stEl) {
        stEl.className = 'c-green';
        stEl.innerText = '● Live Exchange REST Feed';
      }
      const pEl = document.getElementById('live-btc-price');
      if (pEl) pEl.innerText = '$' + p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

      if (dEl && SCAN_PRICE > 0) {
        const diff = p - SCAN_PRICE;
        const pct = (diff / SCAN_PRICE) * 100;
        const sign = diff >= 0 ? '+' : '-';
        const pctSign = diff >= 0 ? '+' : '';
        const driftText = `${sign}$${Math.abs(diff).toFixed(2)} (${pctSign}${pct.toFixed(2)}%)`;
        const color = diff >= 0 ? '#4ade80' : '#fb7185';
        dEl.innerText = driftText;
        dEl.style.color = color;
      }
    }
    setInterval(updateLivePrice, 5000);
    updateLivePrice();
  </script>
</body>
</html>"""

        html = tpl.replace("__PRICE__", f"{price:,.2f}")
        html = html.replace("__PRICE_RAW__", f"{price:.2f}")
        html = html.replace("__SCAN_TS__", ts_iso)
        html = html.replace("__SCAN_ID__", scan_id)
        html = html.replace("__CHANGE_24H__", f"{chg_24h:+.2f}")
        html = html.replace("__ROTATION__", rotation)
        html = html.replace("__PLAYBOOK__", action)
        html = html.replace("__REGIME_CSS_CLS__", regime_css_cls)
        html = html.replace("__REGIME_TXT_CLS__", regime_txt_cls)
        html = html.replace("__REGIME_MATRIX_HTML__", regime_matrix_html)
        html = html.replace("__LSCE_CARD_CLS__", lsce_card_cls)
        html = html.replace("__REGIME_NAME__", regime_name)
        html = html.replace("__DIAGNOSIS__", diagnosis)
        html = html.replace("__TAGLINE__", tagline)
        html = html.replace("__RULE_SCORE__", rule_score)
        html = html.replace("__MATCHED_CRITERIA_ASCII__", matched_crit_ascii)
        html = html.replace("__STOP_PRICE__", f"{stop_p:,.2f}")
        html = html.replace("__STOP_DIST__", f"{stop_dist:.2f}")
        html = html.replace("__STRUCT_LOW__", f"{struct_low:,.2f}")
        html = html.replace("__STOP_RULE__", stop_rule)
        html = html.replace("__STOP_NOTE__", stop_note)
        html = html.replace("__ENTRY_INST__", entry_inst)
        html = html.replace("__RISK_SUMMARY__", risk_summary_txt)

        html = html.replace("__DOMINANT_MAGNET__", dom_magnet)
        html = html.replace("__IMM_RATIO__", imm_disp)
        html = html.replace("__TOT_RATIO__", f"{tot_ratio:.2f}")
        html = html.replace("__LS_RATIO_DISP__", ls_disp)

        html = html.replace("__UPPER_P__", f"{u_p:,.0f}")
        html = html.replace("__UPPER_D__", f"{u_d:.2f}")
        html = html.replace("__UPPER_V__", f"{u_v:.1f}")
        html = html.replace("__LOWER_P__", f"{l_p:,.0f}")
        html = html.replace("__LOWER_D__", f"{l_d:.2f}")
        html = html.replace("__LOWER_V__", f"{l_v:.1f}")
        html = html.replace("__TOT_LOWER__", f"{tot_lower:.1f}")
        html = html.replace("__TOT_UPPER__", f"{tot_upper:.1f}")
        html = html.replace("__LSCE_STATUS__", lsce_status)
        html = html.replace("__LSCE_DETAIL__", lsce_detail)
        html = html.replace("__LADDER_TABLE__", ladder_table)

        html = html.replace("__SPOT_SOURCE__", spot_source)
        html = html.replace("__FUTURES_SOURCE__", futures_source)
        html = html.replace("__OI_SCOPE__", oi_scope)

        html = html.replace("__DAILY_VWAP__", f"{d_vwap:,.2f}")
        html = html.replace("__DAILY_VWAP_DIFF__", f"{d_vwap_diff:+.2f}")
        html = html.replace("__WEEKLY_VWAP__", f"{w_vwap:,.2f}")
        html = html.replace("__WEEKLY_VWAP_DIFF__", f"{w_vwap_diff:+.2f}")
        html = html.replace("__EMA_20D__", f"{e_20:,.2f}")
        html = html.replace("__EMA_20D_DIFF__", f"{e_20_diff:+.2f}")
        html = html.replace("__EMA_50D__", f"{e_50:,.2f}")
        html = html.replace("__EMA_50D_DIFF__", f"{e_50_diff:+.2f}")
        html = html.replace("__MA_200D__", f"{m_200:,.2f}")
        html = html.replace("__MA_200D_DIFF__", f"{m_200_diff:+.2f}")
        html = html.replace("__SWING_LOW__", f"{sw_l:,.0f}")
        html = html.replace("__SWING_HIGH__", f"{sw_h:,.0f}")
        html = html.replace("__RANGE_WIDTH__", f"{ch_width:.2f}")
        html = html.replace("__BASE_FLOOR__", f"{floor:,.2f}")

        html = html.replace("__SPOT_VOL__", f"{spot_vol:,.0f}")
        html = html.replace("__SPOT_VOL_RATIO__", f"{vol_ratio:.2f}")
        html = html.replace("__SPOT_CVD_RATIO__", f"{cvd_ratio:.2f}")
        html = html.replace("__SPOT_CVD_7D__", f"{cvd_7d:+.0f}")
        html = html.replace("__SPOT_CVD_14D__", f"{cvd_14d:+.0f}")
        html = html.replace("__PERP_TREND__", perp_trend)
        html = html.replace("__PERP_SLOPE__", f"{perp_slope:+.0f}")
        html = html.replace("__DEPTH_RATIO__", f"{depth:.2f}")

        html = html.replace("__OI__", f"{oi:,.1f}")
        html = html.replace("__OI_24H__", oi_24h_disp)
        html = html.replace("__OI_1H_4H__", oi_1h_4h_disp)
        html = html.replace("__OI_3D__", oi_3d_disp)
        html = html.replace("__FUNDING__", f"{funding:.4f}")
        html = html.replace("__FUNDING_ANN__", f"{funding_ann:+.2f}")
        html = html.replace("__BASIS__", f"{basis:+.2f}")

        html = html.replace("__ATR__", f"{atr:,.2f}")
        html = html.replace("__ATR_COMP_DISP__", atr_comp_disp)

        html = html.replace("__PROMPT_LEN__", f"{len(raw_prompt)}")
        html = html.replace("__RAW_PROMPT__", raw_prompt)
        html = html.replace("_RAW_PROMPT_JSON_", _json.dumps(raw_prompt))
        html = html.replace("_BLIND_PROMPT_JSON_", _json.dumps(blind_prompt))
        html = html.replace("__RAW_JSON__", raw_json_str)
        html = html.replace("_RAW_JSON_TEXT_", _json.dumps(raw_json_str))
        html = html.replace("__STATIC_STALE_STYLE__", "display: block;" if is_stale_telemetry else "display: none;")

        html = html.replace("__PLAIN_VERDICT__", plain_verdict)
        html = html.replace("__WHY_1__", why_1)
        html = html.replace("__WHY_2__", why_2)
        html = html.replace("__WHY_3__", why_3)
        html = html.replace("__WHY_SIZING__", why_sizing)
        html = html.replace("__WHY_STOP__", why_stop)

        html = html.replace("__F1_SIZE__", f1_size)
        html = html.replace("__F2_LEADERSHIP__", f2_lead)
        html = html.replace("__F3_CROWDING__", f3_crowd)
        html = html.replace("__F4_STRUCTURE__", f4_struct)
        html = html.replace("__F5_ASYMMETRY__", f5_asym)
        html = html.replace("__F6_ATR__", f6_atr)
        html = html.replace("__DOM_REASON__", dom_reason)

        html = html.replace("__TIME_UTC__", utc_time_str)
        html = html.replace("__TIME_SGT__", sgt_time_str)
        html = html.replace("__DATE_UTC__", date_str)

        return html
