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
        index.html, text.html, and exported AI prompts (percentage-distance only; zero ATR).
        """
        regime = data.get("regime", {}) or {}
        metrics = data.get("metrics", {}) or {}
        existing = regime.get("liquidation_ladder")
        if isinstance(existing, list) and len(existing) == 6:
            return [
                {**row, "distance_atr": None}
                for row in existing
            ]

        price = max(1.0, float(metrics.get("price", 0.0) or 1.0))
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

        def _make_row(tier: str, lev: str, side: str, lvl: float, vol_m: float, dist_ovr=None, is_near: bool = False):
            d_pct = ((lvl - price) / price) * 100.0
            if dist_ovr is not None:
                d_pct = float(dist_ovr) if side == "upper" else -float(dist_ovr)
            return {
                "tier": tier,
                "leverage": lev,
                "side": side,
                "price": round(lvl, 2),
                "distance_pct": round(d_pct, 2),
                "distance_atr": None,
                "estimated_vol_m": round(vol_m, 1),
                "modeled": True,
                "is_nearest": is_near,
            }

        return [
            _make_row("10x Shorts", "10x", "upper", sw_h * 1.025, u_10_v),
            _make_row("25x Shorts", "25x", "upper", sw_h * 1.012, u_25_v),
            _make_row("50-100x Shorts", "50-100x", "upper", u_p, u_v, upper_c.get("distance_pct"), True),
            _make_row("100x Longs", "100x", "lower", l_p, l_v, lower_c.get("distance_pct"), True),
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

    @staticmethod
    def _fmt_usd_or_na(val: Any, decimals: int = 2) -> str:
        """Formats positive USD prices or emits explicit DATA UNAVAILABLE."""
        try:
            num = float(val or 0.0)
        except (TypeError, ValueError):
            return "DATA UNAVAILABLE"
        if num <= 0.0:
            return "DATA UNAVAILABLE"
        return f"${num:,.{decimals}f}"

    def _build_telemetry_sections(self, data: Dict[str, Any], mark_dominant: bool = False) -> Dict[str, Any]:
        """Builds unified raw Sections 1-4 (closed 4H bars, zero MA/EMA/RSI/MACD/ATR)."""
        regime = data.get("regime", {}) or {}
        metrics = data.get("metrics", {}) or {}
        ts = data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
        scan_id = self._compute_scan_id(data)
        ladder = self._get_canonical_ladder(data)

        price = float(metrics.get("price", 0.0) or 0.0)
        daily_vwap = float(metrics.get("daily_vwap", 0.0) or 0.0)
        weekly_vwap = float(metrics.get("weekly_vwap", 0.0) or 0.0)
        swing_high = float(metrics.get("swing_high_4h", 0.0) or 0.0)
        swing_low = float(metrics.get("swing_low_4h", 0.0) or 0.0)
        base_floor = float(metrics.get("base_floor", 0.0) or 0.0)
        base_ceiling = float(metrics.get("base_ceiling", 0.0) or 0.0)
        cap_wick = float(metrics.get("capitulation_wick_low", 0.0) or 0.0)
        euph_wick = float(metrics.get("euphoria_wick_high", 0.0) or 0.0)
        closed_4h_cutoff = metrics.get("closed_4h_bar_close_time") or "Closed 4H bars (klines[:-1])"

        spot_vol = float(metrics.get("spot_vol_24h", 0.0) or 0.0)
        spot_vol_ratio = float(metrics.get("spot_vol_ratio", 1.0) or 1.0)
        spot_cvd_ratio = float(metrics.get("spot_cvd_ratio", 1.0) or 1.0)
        spot_cvd_7d = float(metrics.get("spot_cvd_slope_7d", 0.0) or 0.0)
        spot_cvd_14d = float(metrics.get("spot_cvd_slope_14d", 0.0) or 0.0)
        perp_trend = metrics.get("perp_cvd_trend") or "DATA UNAVAILABLE"
        bids_asks_depth = float(metrics.get("bids_asks_depth_ratio", 0.0) or 0.0)

        oi = float(metrics.get("open_interest", 0.0) or 0.0)
        oi_24h = float(metrics.get("oi_change_24h_pct", 0.0) or 0.0)
        oi_1h = float(metrics.get("oi_change_1h_pct", 0.0) or 0.0)
        oi_4h = float(metrics.get("oi_change_4h_pct", 0.0) or 0.0)
        oi_3d = float(metrics.get("oi_change_3d_pct", 0.0) or 0.0)
        oi_hist_ok = bool(metrics.get("oi_history_available", True))
        funding_rate = float(metrics.get("funding_rate", 0.0) or 0.0) * 100
        funding_ann = float(metrics.get("funding_rate_annualized", 0.0) or 0.0)
        basis = float(metrics.get("futures_basis_annualized", 0.0) or 0.0)
        ls_ratio = float(metrics.get("long_short_account_ratio", 1.0) or 1.0)
        ls_avail = bool(metrics.get("ls_ratio_available", True))
        long_pct = (ls_ratio / (1.0 + ls_ratio)) * 100 if (1.0 + ls_ratio) > 0 else 50.0
        ls_pct_72h = metrics.get("ls_ratio_percentile_72h")
        range_width = ((swing_high - swing_low) / max(price, 1.0)) * 100 if (swing_high > 0 and swing_low > 0) else 0.0
        spot_src = metrics.get("spot_data_source", "Binance Public Market-Data REST")
        fut_src = metrics.get("futures_data_source", "Perp Public REST")
        oi_scope = metrics.get("oi_scope", "Tracked venue perp subset (not total market OI)")

        oi_disp = f"{oi:,.1f} BTC (~${(oi * price) / 1e9:.2f}B notional in tracked contract(s))" if oi > 0 else "DATA UNAVAILABLE"
        oi_delta_line = (
            f"1H: {oi_1h:+.2f}% | 4H: {oi_4h:+.2f}% | 24H: {oi_24h:+.2f}% | 3D: {oi_3d:+.2f}%"
            if (oi_hist_ok and oi > 0) else "DATA UNAVAILABLE (Multi-hour OI history missing on fallback feed)"
        )
        ls_line = (
            f"{ls_ratio:.2f} ({long_pct:.1f}% long" + (f", p{ls_pct_72h:.0f} 72h)" if ls_pct_72h is not None else ")")
            if ls_avail else "DATA UNAVAILABLE (L/S account ratio unavailable on fallback feed)"
        )
        dvwap_str = (
            f"${daily_vwap:,.2f} [{((price - daily_vwap) / daily_vwap * 100):+.2f}% vs Spot]"
            if daily_vwap > 0 and price > 0 else "DATA UNAVAILABLE"
        )
        wvwap_str = (
            f"${weekly_vwap:,.2f} [{((price - weekly_vwap) / weekly_vwap * 100):+.2f}% vs Spot]"
            if weekly_vwap > 0 and price > 0 else "DATA UNAVAILABLE"
        )
        ch_4h_str = (
            f"${swing_low:,.0f} (Floor) to ${swing_high:,.0f} (Ceiling) [Width: {range_width:.2f}%]"
            if (swing_high > 0 and swing_low > 0) else "DATA UNAVAILABLE"
        )
        depth_str = f"{bids_asks_depth:.2f}" if bids_asks_depth > 0 else "DATA UNAVAILABLE"
        spot_vol_str = f"{spot_vol:,.0f} BTC ({spot_vol_ratio:.2f}x 20D baseline)" if spot_vol > 0 else "DATA UNAVAILABLE"

        upper_rows = [r for r in ladder if r["side"] == "upper"]
        lower_rows = [r for r in ladder if r["side"] == "lower"]
        upper_lines = "\n".join(
            f"  ▲ {r['tier']:<14} ${r['price']:,.0f} ({r['distance_pct']:+.2f}%) | {self._format_pool_m(r['estimated_vol_m'])} (Modeled Estimate)"
            for r in upper_rows
        )
        lower_lines = "\n".join(
            f"  ▼ {r['tier']:<14} ${r['price']:,.0f} ({r['distance_pct']:+.2f}%) | {self._format_pool_m(r['estimated_vol_m'])} (Modeled Estimate)"
            + (" [🔥 DOMINANT MAGNET CORE]" if (mark_dominant and r.get("is_nearest")) else "")
            for r in lower_rows
        )

        sections = f"""SECTION 1 • RAW PRICE BENCHMARKS & CLOSED 4H STRUCTURE
• Current BTC Spot Price: {self._fmt_usd_or_na(price)}
• Closed 4H Structural Cutoff: {closed_4h_cutoff} (Completed bars only — zero intrabar repainting)
• Daily VWAP (00:00 UTC): {dvwap_str}
• Weekly VWAP (Closed 4H, Monday): {wvwap_str}
• 4-Hour Closed Channel: {ch_4h_str}
• 3D Closed 4H Envelope: Floor {self._fmt_usd_or_na(base_floor)} | Ceiling {self._fmt_usd_or_na(base_ceiling)}
• 24H Closed 1H Wicks: Low {self._fmt_usd_or_na(cap_wick)} | High {self._fmt_usd_or_na(euph_wick)}

SECTION 2 • RAW ORDER FLOW & KLINE TAKER VOLUME DELTA
• 24h Spot Volume: {spot_vol_str}
• Spot CVD Ratio (24h kline taker buy/sell): {spot_cvd_ratio:.2f} | Slopes: 7D {spot_cvd_7d:+.0f} | 14D {spot_cvd_14d:+.0f}
• Perp Flow Trend: {perp_trend}
• Order Book Depth Ratio (±1.5% bids/asks): {depth_str}

SECTION 3 • RAW DERIVATIVES POSITIONING ({oi_scope})
• Tracked Venue Open Interest: {oi_disp}
• OI Velocity: {oi_delta_line}
• 8-Hour Funding Rate: {funding_rate:+.4f}% ({funding_ann:+.2f}% Ann.)
• Futures Basis (Ann.): {basis:+.2f}%
• Tracked L/S Account Ratio: {ls_line}

SECTION 4 • MODELED LIQUIDATION LADDER (CLOSED 4H SWINGS & PRICE-% BANDS)
[MODELED UPPER SHORT POOLS — LOOP B SQUEEZE/RESISTANCE TARGETS]:
{upper_lines}
● CURRENT BTC SPOT ANCHOR: {self._fmt_usd_or_na(price)}
[MODELED LOWER LONG POOLS — LOOP A WASHOUT/ACCUMULATION TARGETS]:
{lower_lines}"""

        return {
            "scan_id": scan_id,
            "ts": ts,
            "spot_src": spot_src,
            "fut_src": fut_src,
            "oi_scope": oi_scope,
            "price": price,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "closed_4h_cutoff": closed_4h_cutoff,
            "ladder": ladder,
            "sections": sections,
        }

    def _build_blind_llm_prompt(self, data: Dict[str, Any]) -> str:
        """Constructs an unanchored DIBSE telemetry prompt with zero engine verdict bias."""
        t = self._build_telemetry_sections(data, mark_dominant=False)
        return f"""================================================================================
DIBSE BLIND SPOT TELEMETRY AUDIT (UNANCHORED MODE)
Scan ID: {t['scan_id']} | Timestamp: {t['ts'][:19]} UTC | Cadence: Every 30m (:02 & :32 UTC)
Raw Spot Feed: {t['spot_src']}
Raw Futures Feed: {t['fut_src']}
Mandate: DUAL-INVENTORY BIDIRECTIONAL SWING ENGINE (DIBSE) — 10% USDT Sleeve + 10% BTC Sleeve (20% Active Sandbox | 80% Untouched Core Reserve). Spot-only. Zero leverage. Zero liquidation risk. Zero stop-losses.
Note: System engine verdict, LSCE gate pick, and Loop A/B call are withheld to prevent anchoring bias. Closed-bar telemetry + framework rules only (zero MA/EMA/RSI/MACD/ATR).
[ACTIVE INVENTORY WATERMARKS]: Baseline 10% USDT Sleeve + 10% BTC Sleeve ready (No active P_buy / P_sell cost-basis override set).
================================================================================

{t['sections']}

================================================================================
DIBSE + 5-REGIME RADAR REFERENCE DEFINITIONS (UNANCHORED RULEBOOK)
Evaluate using majority convergence (>=3 of 4 gates) on closed 4H bars (klines[:-1]):
- REGIME 1 (Spot-Led Expansion): Price > Daily & Weekly VWAP; Spot CVD >= 1.05 & 7D/14D slope > 0; Funding <= +0.012% & OI 24h <= +3.5%; Spot Vol >= 1.0x 20D baseline. (DIBSE: Loop A buy on VWAP pullbacks; hold 10% BTC sleeve — zero upside stop-buys.)
- REGIME 2 (Leveraged / Fragile Upside): 24h Price > +0.8% while Spot CVD < 1.12; OI 24h >= +4.0% or 3D >= +10.0% or Perp CVD surging; Funding >= +0.015% or Basis >= +12.0%; Spot Vol < 1.0x. (DIBSE: Loop B sell 10% BTC sleeve into squeeze euphoria.)
- REGIME 3 (Range / Liquidation Magnet): Closed 4H width <= 4.5% inside channel; Spot CVD 0.90-1.25; L/S >= 1.6 or funding skewed; upper & lower modeled pools active. (DIBSE Core Two-Way Habitat: Loop A on lower washout reclaim [CVD >= 1.05, Depth >= 0.50], Loop B on upper sweep rejection/ceiling, else Hold Both Sleeves.)
- REGIME 4 (Cascade / Forced Deleveraging): Sharp OI flush (-3% 4h / -6% 24h) + negative Spot/Perp CVD + negative funding/basis + 2.0x+ vol. (DIBSE: Hold Both Sleeves dry until stabilization.)
- REGIME 5 (Distribution / Bear Continuation): Price < Daily & Weekly VWAP, weak volume (<1.0x), negative Spot & Perp CVD slopes, bounces sold. (DIBSE: Loop B trim into relief rallies; Loop A accumulation paused.)
- TRANSITION / MIXED (Conflict Override): Triggered when <3 gates confirm OR conflicting signals align (Spot < Daily & Weekly VWAP + Basis < 0% + Depth < 0.35 without confirmed edge reclaim/rejection). (DIBSE: Hold Both Sleeves.)

INSTITUTIONAL RISK OFFICER & BLIND DIBSE ANALYST TASK:
Audit the telemetry critically and answer all 5 sections independently:
1. INDEPENDENT REGIME CLASSIFICATION: Identify the regime (1-5 or Transition/Mixed) using the definitions above and cite at least 3 specific raw metrics from Sections 1-3.
2. BIDIRECTIONAL SWING CALL (LOOP A vs LOOP B vs HOLD BOTH SLEEVES):
   - Loop A (USDT -> BTC -> USDT): Should the 10% USDT Sleeve accumulate spot BTC at a lower sweep washout/reclaim, or stay in USDT? Specify exact entry zone & profit exit target (P_exit > P_buy).
   - Loop B (BTC -> USDT -> BTC): Should the 10% BTC Sleeve sell spot BTC into USDT on an upper short-squeeze/distribution rally, or stay in BTC? Specify exact sell zone & lower rebuy target (P_rebuy < P_sell).
   - Or verdict HOLD BOTH SLEEVES if spot sits mid-range without asymmetric edge.
3. MODELED LIQUIDATION POOL & SKEW AUDIT: Critique Upper Short Pools vs Lower Long Pools in Section 4, flag any small-denominator skew inflation, and identify which pool acts as the stronger price magnet.
4. SELF-HEALING & WATERMARK COMPLIANCE (ZERO STOP-LOSSES / ZERO STOP-BUYS): Apply any active P_buy or P_sell watermark listed at the top. Specify exact spot patience rules if filled early (zero forced stop-losses, zero FOMO stop-buys above resistance).
5. CONTRARIAN RISK OFFICER CRITIQUE & DATA GAPS: What divergence (Spot vs Perps, Funding/Basis, thin Order Book Depth) or DATA UNAVAILABLE feed most threatens your primary thesis?""".strip()

    def _build_llm_prompt(self, data: Dict[str, Any]) -> str:
        """Internal full DIBSE telemetry snapshot (aligned to single closed-4H scan state)."""
        regime = data.get("regime", {}) or {}
        metrics = data.get("metrics", {}) or {}
        risk = data.get("risk", {}) or {}
        t = self._build_telemetry_sections(data, mark_dominant=True)
        ladder = t["ladder"]

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_v = float(upper_c.get("estimated_vol_usd", 0.0) or 0.0) / 1e6
        l_v = float(lower_c.get("estimated_vol_usd", 0.0) or 0.0) / 1e6

        imm_ratio = regime.get("immediate_imbalance_ratio", round(l_v / max(u_v, 0.1), 1))
        tot_u_vol = regime.get("total_ladder_upper_vol", sum(r["estimated_vol_m"] for r in ladder if r["side"] == "upper"))
        tot_l_vol = regime.get("total_ladder_lower_vol", sum(r["estimated_vol_m"] for r in ladder if r["side"] == "lower"))
        tot_ratio = regime.get("total_ladder_imbalance_ratio", round(tot_l_vol / max(tot_u_vol, 0.1), 2))
        imm_disp = f"~{round(imm_ratio):.0f}x" if imm_ratio >= 10 else f"{imm_ratio:.1f}x"

        lsce_status = regime.get("lsce_status", "UNTESTED")
        lsce_side = regime.get("lsce_side", "NONE")
        lsce_detail = regime.get("lsce_detail", "Monitoring both upper short-squeeze & lower washout liquidation bands.")
        dibse_signal = regime.get("dibse_signal", "HOLD BOTH SLEEVES")
        sleeve_alloc = regime.get("sleeve_allocation", "10% USDT + 10% BTC (80% Core Untouched)")
        loop_a_zone = regime.get("loop_a_zone", "Monitor closed 4H support sweep")
        loop_b_zone = regime.get("loop_b_zone", "Monitor closed 4H resistance squeeze")
        failure_protocol = regime.get("failure_protocol", "Zero stop-losses; hold spot inventory asymmetrically.")

        regime_name = regime.get("name", "Unknown")
        majority = regime.get("majority_score", "")
        diagnosis = regime.get("diagnosis", "")
        dom_magnet = regime.get("dominant_magnet", "")
        dom_reason = regime.get("dominant_magnet_reason", "")
        rotation = regime.get("rotation", "Hold Both Sleeves")
        action = regime.get("action", "")
        sizing = regime.get("sizing_factor", 0.0)
        sandbox_ok = bool(risk.get("risk_budget_ok", True))
        risk_banner = f"DIBSE 20% ACTIVE SANDBOX ({sleeve_alloc}) | Zero Borrowed Leverage | Zero Stop-Losses" if sandbox_ok else "SANDBOX CAP GUARD"

        prompt = f"""================================================================================
DIBSE FULL SYSTEM AUDIT SNAPSHOT
System: BTC Magnet Monitor | Scan ID: {t['scan_id']} | Cadence: Every 30m (:02 & :32 UTC)
Raw Spot Feed: {t['spot_src']}
Raw Futures Feed: {t['fut_src']}
Mandate: DUAL-INVENTORY BIDIRECTIONAL SWING ENGINE (10% USDT Sleeve + 10% BTC Sleeve | Zero Stops)
Timestamp: {t['ts'][:19]} UTC | Status: {data.get('data_status', 'LIVE')}
================================================================================

[DIBSE ENGINE CALL & BIDIRECTIONAL SLEEVE DIRECTIVE]:
• Engine Regime Diagnosis: {regime_name} ({majority})
• DIBSE Signal: {dibse_signal} ({rotation} | Sleeve Sizing: {sizing}x)
• Loop A Zone (USDT -> BTC -> USDT): {loop_a_zone}
• Loop B Zone (BTC -> USDT -> BTC): {loop_b_zone}
• Playbook Execution Protocol: {action}
• Microstructure Diagnosis: {diagnosis}
• Bidirectional LSCE Status: {lsce_status} (Side: {lsce_side}) — {lsce_detail}
• Self-Healing Protocol: {failure_protocol}
• Dominant Liquidation Magnet Target: {dom_magnet} ({dom_reason})
• Sandbox Budget Status: {risk_banner}

{t['sections']}

• Dual Imbalance Summary (Modeled Estimate — small denominator sensitivity when Upper ~${u_v:.1f}M):
  ├ Immediate Tier Imbalance: Lower 100x pool is {imm_disp} vs Upper 50-100x pool ({self._format_pool_m(l_v)} vs {self._format_pool_m(u_v)}).
  └ Total Leverage Ladder Imbalance (10x-100x Modeled Bands): Total Lower ({self._format_pool_m(tot_l_vol)}) vs Total Upper ({self._format_pool_m(tot_u_vol)}) = {tot_ratio:.2f}x skew.
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
        rotation = regime.get("rotation", "Hold Both Sleeves")
        dibse_signal = regime.get("dibse_signal", "HOLD BOTH SLEEVES")
        dibse_headline = regime.get("dibse_action_headline", rotation)
        loop_a_zone = regime.get("loop_a_zone", "Monitor closed 4H support sweep")
        loop_b_zone = regime.get("loop_b_zone", "Monitor closed 4H resistance squeeze")
        sleeve_alloc = regime.get("sleeve_allocation", "10% USDT + 10% BTC (80% Core Untouched)")
        failure_protocol = regime.get("failure_protocol", "Zero stop-losses; hold spot inventory asymmetrically.")
        sizing = regime.get("sizing_factor", 0.0)
        action = regime.get("action", "")
        stop_rule = regime.get("stop_rule", "ZERO STOP-LOSSES (DIBSE Asymmetric Self-Healing Inventory)")
        stop_price = regime.get("stop_price", 0.0)
        stop_dist = regime.get("stop_distance_pct", 0.0)
        entry_inst = regime.get("entry_instruction", "")
        dom_magnet = regime.get("dominant_magnet", "Neutral")
        dom_reason = regime.get("dominant_magnet_reason", dom_magnet)
        notes = regime.get("notes", "")
        data_quality = regime.get("data_quality", "LIVE")

        plain_verdict = regime.get("plain_english_verdict", "Analyzing current market conditions...")
        why_points = regime.get("why_points", [])
        why_sizing = regime.get("why_sizing_reason", f"DIBSE Active Sandbox: {sleeve_alloc}.")
        why_stop = regime.get("why_stop_reason", failure_protocol)

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}

        # Dual Imbalance & Bidirectional LSCE
        imm_ratio = regime.get("immediate_imbalance_ratio", 1.0)
        tot_l_vol = regime.get("total_ladder_lower_vol", 0.0)
        tot_u_vol = regime.get("total_ladder_upper_vol", 0.0)
        tot_ratio = regime.get("total_ladder_imbalance_ratio", 1.0)
        lsce_status = regime.get("lsce_status", "UNTESTED")
        lsce_side = regime.get("lsce_side", "NONE")
        lsce_detail = regime.get("lsce_detail", "")

        if lsce_status == "SWEEP_AND_RECLAIM_CONFIRMED":
            if sizing > 0 and "USDT -> BTC" in rotation:
                lsce_badge_class = "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
                lsce_badge_icon = "✅"
                lsce_badge_title = f"LOWER SWEEP &amp; RECLAIM CONFIRMED (LOOP A: 10% USDT &rarr; BTC {sizing:.2f}x)"
            else:
                lsce_badge_class = "border-amber-500/40 bg-amber-500/15 text-amber-300"
                lsce_badge_icon = "🛡️"
                lsce_badge_title = "LOWER SWEEP OBSERVED — LOOP A PAUSED BY MACRO REGIME"
        elif lsce_status == "UPPER_SWEEP_REJECTION_CONFIRMED":
            if sizing > 0 and "BTC -> USDT" in rotation:
                lsce_badge_class = "border-sky-500/45 bg-sky-500/15 text-sky-300"
                lsce_badge_icon = "🔄"
                lsce_badge_title = f"UPPER SQUEEZE REJECTION CONFIRMED (LOOP B: 10% BTC &rarr; USDT {sizing:.2f}x)"
            else:
                lsce_badge_class = "border-amber-500/40 bg-amber-500/15 text-amber-300"
                lsce_badge_icon = "🛡️"
                lsce_badge_title = "UPPER WICK REJECTION OBSERVED — HOLDING BTC SLEEVE"
        elif lsce_status == "SWEEP_IN_PROGRESS":
            lsce_badge_class = "border-amber-500/40 bg-amber-500/15 text-amber-300 animate-pulse"
            lsce_badge_icon = "⚠️"
            lsce_badge_title = "LOWER SWEEP IN PROGRESS (WAIT FOR CLOSED 4H RECLAIM)"
        elif lsce_status == "UPPER_SWEEP_IN_PROGRESS":
            lsce_badge_class = "border-amber-500/40 bg-amber-500/15 text-amber-300 animate-pulse"
            lsce_badge_icon = "⚡"
            lsce_badge_title = "UPPER SHORT SQUEEZE IN PROGRESS (WAIT FOR CLOSED 4H REJECTION)"
        elif lsce_status == "SWEEP_FAILED_BREAKDOWN":
            lsce_badge_class = "border-rose-500/40 bg-rose-500/15 text-rose-300"
            lsce_badge_icon = "🚨"
            lsce_badge_title = "LOWER FLOOR BROKEN — LOOP A PAUSED (HOLD SLEEVES)"
        else:
            lsce_badge_class = "border-zinc-700 bg-zinc-800/80 text-zinc-300"
            lsce_badge_icon = "⏸️"
            lsce_badge_title = "UNTESTED (MONITORING LOOP A &amp; LOOP B BANDS)"

        magnet_factors = regime.get("magnet_factors", {})
        f1 = magnet_factors.get("factor_1_size", "Evaluating cluster size disparity...")
        f2 = magnet_factors.get("factor_2_spot_leadership", "Evaluating spot vs derivatives CVD...")
        f3 = magnet_factors.get("factor_3_crowding_fuel", "Evaluating funding and positioning crowding...")
        f4 = magnet_factors.get("factor_4_regime_structure", "Evaluating closed 4H regime structure...")
        f5 = magnet_factors.get("factor_5_asymmetry", "Evaluating cluster distance asymmetry...")
        f6 = magnet_factors.get("factor_6_range_compression", magnet_factors.get("factor_6_atr_volatility", "Evaluating closed 4H range compression..."))

        # Specific styling tokens for the Standout Regime Panel
        if regime_id == "SPOT_LED_EXPANSION":
            regime_border_color = "border-emerald-500/50 shadow-emerald-500/10"
            regime_badge_bg = "bg-emerald-500/15 text-emerald-300 border-emerald-500/30"
            regime_icon = "🚀"
            regime_tagline = "Genuine spot buyers in control. Loop A accumulation on dips; hold BTC sleeve for upside continuation."
        elif regime_id == "LEVERAGED_FRAGILE_UPSIDE":
            regime_border_color = "border-orange-500/50 shadow-orange-500/10"
            regime_badge_bg = "bg-orange-500/15 text-orange-300 border-orange-500/30"
            regime_icon = "⚠️"
            regime_tagline = "Advance built on borrowed futures leverage. Prime Loop B setup to harvest BTC into USDT above shorts."
        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            regime_border_color = "border-rose-500/60 shadow-rose-500/15"
            regime_badge_bg = "bg-rose-500/15 text-rose-300 border-rose-500/30"
            regime_icon = "⚡"
            regime_tagline = "Forced margin liquidation cascade in progress. Keep 10% USDT dry until closed 4H washout stabilizes."
        elif regime_id == "DISTRIBUTION_BEAR_CONTINUATION":
            regime_border_color = "border-rose-500/50 shadow-rose-500/10"
            regime_badge_bg = "bg-rose-500/15 text-rose-300 border-rose-500/30"
            regime_icon = "📉"
            regime_tagline = "Structural seller control. Loop B distribution sells BTC sleeve into weak bounces; Loop A waits for deep washout."
        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            regime_border_color = "border-cyan-500/50 shadow-cyan-500/10"
            regime_badge_bg = "bg-cyan-500/15 text-cyan-300 border-cyan-500/30"
            regime_icon = "🧲"
            regime_tagline = "Price bound in closed 4H channel. DIBSE alternates Loop A at floor washouts and Loop B at ceiling squeezes."
        else:
            regime_border_color = "border-amber-500/60 shadow-[0_0_25px_rgba(245,158,11,0.12)]"
            regime_badge_bg = "bg-amber-500/15 text-amber-300 border-amber-500/30"
            regime_icon = "⚖️"
            regime_tagline = "Market indicators mixed across closed 4H range. Hold both sleeves (10% USDT + 10% BTC) at equilibrium."

        # Action banner color styling
        if "USDT -> BTC" in rotation:
            action_bg = "bg-emerald-500/10 border-emerald-500/35 text-emerald-300"
            action_pill = "LOOP A: 10% USDT → BTC"
        elif "BTC -> USDT" in rotation:
            action_bg = "bg-sky-500/10 border-sky-500/35 text-sky-300"
            action_pill = "LOOP B: 10% BTC → USDT"
        else:
            action_bg = "bg-amber-500/10 border-amber-500/35 text-amber-300"
            action_pill = "HOLD BOTH SLEEVES (10% + 10%)"

        ev_border = "border-amber-500/35" if regime_id == "TRANSITION_MIXED" else "border-emerald-500/35"
        evidence_cards_html = "".join([
            f"""<div class='flex items-start gap-2.5 p-3 rounded-xl bg-zinc-950/75 border {ev_border}'>
                 <span class='text-emerald-400 font-bold mt-0.5 text-xs'>✓</span>
                 <span class='text-xs text-zinc-200 leading-relaxed'>{item}</span>
               </div>"""
            for item in regime.get("matched_criteria", [])
        ])

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

        price = float(metrics.get("price", 0.0) or 0.0)
        price_change_24h = float(metrics.get("price_change_24h_pct", 0.0) or 0.0)
        daily_vwap = float(metrics.get("daily_vwap", 0.0) or 0.0)
        weekly_vwap = float(metrics.get("weekly_vwap", 0.0) or 0.0)
        swing_high = float(metrics.get("swing_high_4h", 0.0) or 0.0)
        swing_low = float(metrics.get("swing_low_4h", 0.0) or 0.0)
        base_floor = float(metrics.get("base_floor", 0.0) or 0.0)
        base_ceiling = float(metrics.get("base_ceiling", 0.0) or 0.0)
        cap_wick = float(metrics.get("capitulation_wick_low", 0.0) or 0.0)
        euph_wick = float(metrics.get("euphoria_wick_high", 0.0) or 0.0)
        raw_cutoff = str(metrics.get("closed_4h_bar_close_time") or "")
        closed_4h_cutoff = (raw_cutoff[:16].replace("T", " ") + " UTC") if ("T" in raw_cutoff and len(raw_cutoff) >= 16) else (raw_cutoff or "Closed 4H bars")
        funding_rate = float(metrics.get("funding_rate", 0.0) or 0.0) * 100
        spot_cvd_ratio = float(metrics.get("spot_cvd_ratio", 1.0) or 1.0)
        oi_change_24h = float(metrics.get("oi_change_24h_pct", 0.0) or 0.0)
        oi_change_1h = float(metrics.get("oi_change_1h_pct", 0.0) or 0.0)
        oi_change_4h = float(metrics.get("oi_change_4h_pct", 0.0) or 0.0)
        oi_hist_ok = bool(metrics.get("oi_history_available", True))
        basis = float(metrics.get("futures_basis_annualized", 0.0) or 0.0)
        ls_ratio = float(metrics.get("long_short_account_ratio", 1.0) or 1.0)
        ls_avail = bool(metrics.get("ls_ratio_available", True))
        ls_pct_72h = metrics.get("ls_ratio_percentile_72h")
        current_oi = float(metrics.get("open_interest", 0.0) or 0.0)
        depth_ratio = float(metrics.get("bids_asks_depth_ratio", 0.0) or 0.0)
        spot_vol_24h = float(metrics.get("spot_vol_24h", 0.0) or 0.0)
        spot_source = metrics.get("spot_data_source", "Binance Public Market-Data REST (data-api.binance.vision/api/v3)")
        futures_source = metrics.get("futures_data_source", "Perp Public REST")
        oi_scope = metrics.get("oi_scope", "Tracked venue perpetual subset (not total market OI)")

        oi_val_str = f"{current_oi:,.0f} BTC" if current_oi > 0 else "DATA UNAVAILABLE"
        oi_24h_str = f"{oi_change_24h:+.2f}%" if (oi_hist_ok and current_oi > 0) else "DATA UNAVAILABLE"
        oi_1h_4h_str = f"{oi_change_1h:+.2f}% / {oi_change_4h:+.2f}%" if (oi_hist_ok and current_oi > 0) else "DATA UNAVAILABLE"
        ls_pct_disp = f"{ls_ratio:.2f}" + (f" (p{ls_pct_72h:.0f} 72h)" if ls_pct_72h is not None else "") if ls_avail else "DATA UNAVAILABLE"
        depth_disp = f"{depth_ratio:.2f}" if depth_ratio > 0 else "DATA UNAVAILABLE"
        wick_span_pct = ((euph_wick - cap_wick) / max(price, 1.0)) * 100.0 if (euph_wick > 0 and cap_wick > 0 and price > 0) else None
        wick_span_disp = f"{wick_span_pct:.2f}%" if wick_span_pct is not None else "DATA UNAVAILABLE"
        ch_width_pct = ((swing_high - swing_low) / max(price, 1.0)) * 100.0 if (swing_high > 0 and swing_low > 0 and price > 0) else None
        ch_width_disp = f"{ch_width_pct:.2f}%" if ch_width_pct is not None else "DATA UNAVAILABLE"
        env_3d_disp = f"${base_floor:,.0f} - ${base_ceiling:,.0f}" if (base_floor > 0 and base_ceiling > 0) else (f"${base_floor:,.0f} floor" if base_floor > 0 else "DATA UNAVAILABLE")
        wicks_24h_disp = f"${cap_wick:,.0f} / ${euph_wick:,.0f}" if (cap_wick > 0 and euph_wick > 0) else (f"${cap_wick:,.0f} low" if cap_wick > 0 else "DATA UNAVAILABLE")

        upper_ladders_html = []
        lower_ladders_html = []
        upper_active = "UPPER_SWEEP" in lsce_status
        lower_active = ("SWEEP" in lsce_status) and not upper_active
        for row in ladder:
            vol_disp = self._format_pool_m(row["estimated_vol_m"])
            if row["side"] == "upper":
                if row.get("is_nearest"):
                    w_bar = min(100, max(15, row["estimated_vol_m"] / 20.0 * 100.0))
                    sq_tag = " <span class='text-[10px] text-amber-300 font-bold'>&laquo; SQUEEZE WATCH</span>" if upper_active else ""
                    upper_ladders_html.append(f"""          <!-- Upper Tier: {row['tier']} Nearest Active Pool -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-rose-500/10 {'border-2 border-rose-400/70 shadow-lg shadow-rose-500/15' if upper_active else 'border border-rose-500/45'}">
            <div class="flex items-center gap-2.5 w-48">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">{row['tier']}</span>
              <span class="font-mono font-bold text-rose-300">${row['price']:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-rose-700 to-rose-400 h-full rounded-full {'animate-pulse' if upper_active else ''}" style="width: {w_bar:.0f}%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-rose-300 text-xs w-48">
              {row['distance_pct']:+.2f}% &bull; {vol_disp}{sq_tag}
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
            <div class="text-right font-mono text-zinc-400 text-xs w-48">
              {row['distance_pct']:+.2f}% &bull; {vol_disp} <span class="text-[10px] text-zinc-500">(Est.)</span>
            </div>
          </div>""")
            else:
                if row.get("is_nearest"):
                    sweep_tag = " <span class='text-[10px] text-amber-300 font-bold'>&laquo; TESTING</span>" if lower_active else ""
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
            <div class="text-right font-mono text-emerald-300 font-bold text-xs w-48">
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
            <div class="text-right font-mono text-zinc-400 text-xs w-48">
              {row['distance_pct']:+.2f}% &bull; {vol_disp} <span class="text-[10px] text-zinc-500">(Est.)</span>
            </div>
          </div>""")
        upper_ladder_block = "\n".join(upper_ladders_html)
        lower_ladder_block = "\n".join(lower_ladders_html)

        imm_disp = f"~{round(imm_ratio):.0f}x" if imm_ratio >= 10 else f"{imm_ratio:.1f}x"

        # Build blind telemetry prompt (Method 1 uses single Upgraded Blind Telemetry workflow)
        blind_prompt = self._build_blind_llm_prompt(data)
        blind_prompt_escaped = blind_prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Unified PWA meta and styling tags
        page_title = "BTC Magnet Monitor — 5-Regime Radar &amp; DIBSE Spot Engine"
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
      overflow-x: clip;
    }}
    body {{
      overflow-x: clip;
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
    <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl overflow-hidden border border-zinc-800 flex items-center justify-center shadow-inner flex-shrink-0 bg-zinc-950 p-0.5">
          <img src="./assets/app-logo.png?v=4" alt="BTC Magnet Monitor Logo" class="w-full h-full object-contain">
        </div>
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <span class="font-extrabold text-base tracking-tight text-white">BTC Magnet Monitor</span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-zinc-800/80 text-zinc-300 border border-zinc-700/60">5-Regime Radar</span>
          </div>
          <p class="text-xs text-zinc-400 hidden sm:block">Observable Positioning Mechanics &amp; Regime Intelligence</p>
        </div>
      </div>

      <div class="flex flex-wrap items-center gap-2 sm:gap-6">
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
      <div>Last Scan: <span class="text-zinc-200 font-medium mono">{utc_time_str}</span> (<span class="text-emerald-300 mono">{sgt_time_str}</span>) &bull; Cadence: <span class="text-indigo-300 font-semibold">Every 30m (:02/:32 UTC)</span> &bull; Next: <span id="subhdr-next-update" class="text-amber-300 mono font-semibold">--:-- UTC</span></div>
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
            Updates <strong class="text-white">Every 30 Minutes</strong> (:02 &amp; :32 UTC target; CI best-effort) &bull; Last Scan: <span class="mono text-zinc-200">{utc_time_str} ({sgt_time_str})</span>
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
    <!-- PANEL 2: ON-EXCHANGE TELEMETRY (CLOSED 4H & MODELED POOLS)   -->
    <!-- ============================================================ -->
    <div id="panel-2" class="rounded-2xl border-2 border-cyan-500/60 bg-gradient-to-b from-zinc-950 via-zinc-900/90 to-zinc-950 p-5 sm:p-6 backdrop-blur-md shadow-[0_0_25px_rgba(6,182,212,0.12)] space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-cyan-500/30 pb-3">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs font-bold uppercase tracking-widest text-cyan-400">Panel 2 &bull; On-Exchange Telemetry &amp; Modeled Pools</span>
            <span class="text-[11px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 mono">Closed 4H Bars (1-3) + Modeled Pools (4)</span>
          </div>
          <h3 class="text-lg sm:text-xl font-bold text-white mt-0.5">Real-Time Market Microstructure Feeds</h3>
        </div>
        <div class="text-xs text-zinc-400">
          Sources: <span class="text-zinc-200 mono">{spot_source} &bull; {futures_source}</span>
        </div>
      </div>

      <!-- 4 Categories Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5 text-xs">
        
        <!-- Category 1: Price & Closed 4H Structure -->
        <div class="p-4 rounded-xl bg-zinc-950/90 border border-cyan-500/45 space-y-2">
          <div class="text-[11px] font-bold uppercase tracking-wider text-cyan-400 border-b border-cyan-500/30 pb-1.5 flex items-center justify-between">
            <span>1. Closed 4H Structure</span>
            <span class="text-[10px] text-cyan-300 font-mono">Zero Repaint</span>
          </div>
          <div class="space-y-1.5 text-zinc-300">
            <div class="flex justify-between"><span>Spot Price:</span> <span class="font-mono font-bold text-white">${price:,.2f}</span></div>
            <div class="flex justify-between"><span>Daily VWAP:</span> <span class="font-mono text-zinc-300">{self._fmt_usd_or_na(daily_vwap)}</span></div>
            <div class="flex justify-between"><span>Weekly VWAP (4H):</span> <span class="font-mono text-zinc-300">{self._fmt_usd_or_na(weekly_vwap)}</span></div>
            <div class="flex justify-between"><span>Closed 4H Channel:</span> <span class="font-mono text-zinc-300">${swing_low:,.0f} - ${swing_high:,.0f}</span></div>
            <div class="flex justify-between"><span>3D 4H Envelope:</span> <span class="font-mono text-zinc-300">{env_3d_disp}</span></div>
            <div class="flex justify-between"><span>24H Closed Wicks:</span> <span class="font-mono text-zinc-300">{wicks_24h_disp}</span></div>
            <div class="flex justify-between"><span>4H Bar Cutoff:</span> <span class="font-mono text-[11px] text-cyan-300">{closed_4h_cutoff}</span></div>
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
            <div class="flex justify-between"><span>24h Spot Volume:</span> <span class="font-mono text-zinc-300">{f"{spot_vol_24h:,.0f} BTC" if spot_vol_24h > 0 else "DATA UNAVAILABLE"}</span></div>
            <div class="flex justify-between"><span>Volume / 20D Base:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_vol_ratio", 1.0):.2f}x</span></div>
            <div class="flex justify-between"><span>7D Spot CVD Slope:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_cvd_slope_7d", 0.0):+.0f}</span></div>
            <div class="flex justify-between"><span>14D Spot CVD Slope:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_cvd_slope_14d", 0.0):+.0f}</span></div>
            <div class="flex justify-between"><span>Perp Flow Trend:</span> <span class="font-mono text-zinc-300 capitalize">{metrics.get("perp_cvd_trend", "DATA UNAVAILABLE")}</span></div>
            <div class="flex justify-between"><span>Order Depth Ratio:</span> <span class="font-mono text-zinc-300">{depth_disp}</span></div>
          </div>
        </div>

        <!-- Category 3: Derivatives Crowding -->
        <div class="p-4 rounded-xl bg-zinc-950/90 border border-amber-500/45 space-y-2">
          <div class="text-[11px] font-bold uppercase tracking-wider text-amber-400 border-b border-amber-500/30 pb-1.5 flex items-center justify-between">
            <span>3. Derivatives Crowding</span>
            <span class="text-[10px] text-amber-300 font-mono">Venue OI</span>
          </div>
          <div class="space-y-1.5 text-zinc-300">
            <div class="flex justify-between" title="{oi_scope}"><span>Tracked Venue OI:</span> <span class="font-mono font-bold text-white">{oi_val_str}</span></div>
            <div class="flex justify-between"><span>OI 24h Change:</span> <span class="font-mono text-zinc-300">{oi_24h_str}</span></div>
            <div class="flex justify-between"><span>OI 1h / 4h:</span> <span class="font-mono text-zinc-300">{oi_1h_4h_str}</span></div>
            <div class="flex justify-between"><span>Funding Rate (8h):</span> <span class="font-mono text-zinc-300">{funding_rate:+.4f}%</span></div>
            <div class="flex justify-between"><span>Futures Basis Ann.:</span> <span class="font-mono text-zinc-300">{basis:+.2f}%</span></div>
            <div class="flex justify-between"><span>Retail Long/Short:</span> <span class="font-mono text-zinc-300">{ls_pct_disp}</span></div>
            <div class="text-[10px] text-zinc-500 pt-1 border-t border-zinc-800/80 leading-tight">{oi_scope}</div>
          </div>
        </div>

        <!-- Category 4: Range Compression & Magnets -->
        <div class="p-4 rounded-xl bg-zinc-950/90 border border-rose-500/45 space-y-2">
          <div class="text-[11px] font-bold uppercase tracking-wider text-rose-400 border-b border-rose-500/30 pb-1.5 flex items-center justify-between">
            <span>4. Range &amp; Magnets</span>
            <span class="text-[10px] text-rose-300 font-mono">Modeled Est.</span>
          </div>
          <div class="space-y-1.5 text-zinc-300">
            <div class="flex justify-between"><span>4H Channel Width:</span> <span class="font-mono font-bold text-white">{ch_width_disp}</span></div>
            <div class="flex justify-between"><span>24h Closed Wick Span:</span> <span class="font-mono text-zinc-300">{wick_span_disp}</span></div>
            <div class="flex justify-between"><span>Book Depth (±1.5%):</span> <span class="font-mono text-zinc-300">{depth_disp}</span></div>
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
    <div id="verdict-guide" class="rounded-2xl border-2 border-violet-500/60 bg-gradient-to-r from-cyan-950/40 via-zinc-900/90 to-emerald-950/40 p-6 backdrop-blur-md shadow-[0_0_25px_rgba(139,92,246,0.12)] text-center space-y-3">
      <div class="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-violet-500/15 border border-violet-500/40 text-violet-300 text-xs font-extrabold uppercase tracking-wider">
        <span>⚖️ Bridge &bull; How to Get Your DIBSE Spot Verdict</span>
      </div>
      <h3 class="text-xl sm:text-2xl font-black text-white tracking-tight">
        Choose Method 1 (Your Own AI) or Method 2 (Our Bidirectional Engine)
      </h3>
      <p class="text-xs sm:text-sm text-zinc-300 max-w-2xl mx-auto leading-relaxed">
        Panels 1–3 give you closed-bar market facts with zero advice. To decide whether to rotate <strong>Loop A (10% USDT &rarr; BTC)</strong>, <strong>Loop B (10% BTC &rarr; USDT)</strong>, or <strong>Hold Both Sleeves</strong>, use either method below—or pair both for an unanchored second opinion.
      </p>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-3xl mx-auto pt-2 text-left">
        <a href="#method-1" class="p-4 rounded-xl bg-zinc-950/85 border border-sky-500/50 hover:border-sky-400 transition-all flex items-start gap-3">
          <span class="text-2xl">🧪</span>
          <div>
            <div class="text-xs font-bold text-sky-400 uppercase tracking-wider">Method 1 &bull; Use Your Own AI</div>
            <div class="text-sm font-extrabold text-white">Copy Blind Telemetry &rarr; ChatGPT / Claude / Gemini</div>
            <p class="text-[11px] text-zinc-300 mt-1 leading-relaxed">1. Scroll to Method 1, optionally fill your <strong>P_buy / P_sell</strong> watermarks, and tap <strong class="text-sky-300">Copy Blind Telemetry for AI</strong>.<br>2. Paste into your own AI for an unanchored Loop A / Loop B verdict.</p>
          </div>
        </a>

        <a href="#method-2" class="p-4 rounded-xl bg-zinc-950/85 border border-purple-500/50 hover:border-purple-400 transition-all flex items-start gap-3">
          <span class="text-2xl">🧠</span>
          <div>
            <div class="text-xs font-bold text-purple-400 uppercase tracking-wider">Method 2 &bull; Built-In DIBSE Engine</div>
            <div class="text-sm font-extrabold text-white">Read Our Bidirectional System Verdict</div>
            <p class="text-[11px] text-zinc-300 mt-1 leading-relaxed">1. Scroll to Method 2 for our Loop A &amp; Loop B zones, symmetric LSCE sweep gate, and 10% + 10% sleeve call.<br>2. Review the zero-stop-loss self-healing rules and 10x–100x modeled liquidity map.</p>
          </div>
        </a>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- METHOD 1: VERDICT BY BLIND TELEMETRY COPY TO AI              -->
    <!-- ============================================================ -->
    <div id="method-1" class="rounded-2xl border-2 border-sky-500/60 bg-zinc-900/85 p-6 sm:p-8 backdrop-blur-md shadow-[0_0_25px_rgba(14,165,233,0.12)] space-y-5">
      
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-sky-500/25 pb-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-extrabold uppercase tracking-widest text-sky-400 flex items-center gap-1.5">
              <span>🧪</span>
              <span>Method 1: Upgraded Blind Telemetry (Zero System Bias)</span>
            </span>
          </div>
          <h2 class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
            Analyze Live DIBSE Telemetry with Your Own AI
          </h2>
          <p class="text-xs sm:text-sm text-zinc-300 mt-1 max-w-2xl leading-relaxed">
            One clean export containing closed-4H market facts, modeled liquidation bands, and your optional inventory watermarks—with <strong>zero system verdict revealed</strong> so your AI stays 100% objective.
          </p>
        </div>

        <!-- Single Clean One-Click Copy Button -->
        <div class="flex-shrink-0 flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          <button id="copy-blind-btn" onclick="copyBlindPrompt()" class="inline-flex items-center justify-center gap-2 px-6 py-4 rounded-xl bg-sky-500 hover:bg-sky-400 text-black font-extrabold text-xs sm:text-sm shadow-lg shadow-sky-500/25 transition-all cursor-pointer">
            <span id="copy-blind-icon" class="text-base">🧪</span>
            <span id="copy-blind-text">Copy Blind Telemetry for AI</span>
          </button>
        </div>
      </div>

      <!-- Optional Local-Only Inventory Watermarks (Collapsed for 1-Button Simplicity) -->
      <details id="wb-details" class="rounded-xl bg-zinc-950/90 border border-sky-500/35 px-4 py-3">
        <summary class="flex flex-col sm:flex-row sm:items-center justify-between gap-1 cursor-pointer select-none">
          <span class="text-xs font-bold uppercase tracking-wider text-sky-300">▸ Optional: Add P_buy / P_sell Inventory Watermarks (Local Only)</span>
          <span id="wb-status" class="text-[11px] font-mono text-zinc-400">Baseline: 10% USDT + 10% BTC sleeves ready</span>
        </summary>
        <div class="grid grid-cols-1 sm:grid-cols-12 gap-3 items-end pt-3 mt-3 border-t border-zinc-800/80">
          <div class="sm:col-span-5">
            <label for="wb-buy" class="block text-[10px] font-bold uppercase tracking-wider text-emerald-300 mb-1">Loop A Spot BTC Cost ($P_buy)</label>
            <input id="wb-buy" type="number" step="0.01" min="0" inputmode="decimal" placeholder="e.g. 71200 (if holding Loop A BTC)" class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-xs font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-emerald-400">
          </div>
          <div class="sm:col-span-5">
            <label for="wb-sell" class="block text-[10px] font-bold uppercase tracking-wider text-sky-300 mb-1">Loop B BTC Sale Price ($P_sell)</label>
            <input id="wb-sell" type="number" step="0.01" min="0" inputmode="decimal" placeholder="e.g. 75800 (if waiting to rebuy BTC)" class="w-full px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-700 text-xs font-mono text-white placeholder-zinc-500 focus:outline-none focus:border-sky-400">
          </div>
          <div class="sm:col-span-2">
            <button id="wb-clear" type="button" class="w-full px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 text-[11px] font-bold text-zinc-200 cursor-pointer">Clear</button>
          </div>
        </div>
      </details>

      <!-- 3-Step Simple Instructions -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-sky-500/35 space-y-1">
          <span class="text-[10px] font-bold text-sky-400 uppercase tracking-wider">Step 1</span>
          <div class="font-bold text-white">Copy Upgraded Blind Telemetry</div>
          <p class="text-[11px] text-zinc-400">Exports closed-4H structure, CVD, OI, and modeled pools + your watermarks—without leaking Method 2's verdict.</p>
        </div>

        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-cyan-500/35 space-y-1">
          <span class="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Step 2</span>
          <div class="font-bold text-white">Paste into Any Major LLM</div>
          <p class="text-[11px] text-zinc-400">Works directly in Claude, ChatGPT, Grok, Qwen, or Gemini with DIBSE dual-sleeve context built in.</p>
        </div>

        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-indigo-500/35 space-y-1">
          <span class="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Step 3</span>
          <div class="font-bold text-white">Cross-Check Loop A &amp; Loop B</div>
          <p class="text-[11px] text-zinc-400">Compare your AI's independent Loop A (buy washout) &amp; Loop B (sell squeeze) levels against Method 2 below.</p>
        </div>
      </div>

      <!-- Collapsible Blind Prompt Preview -->
      <details class="rounded-xl border border-sky-500/35 bg-zinc-950/70 p-4 text-xs text-zinc-400">
        <summary class="font-semibold text-sky-200 cursor-pointer hover:text-white flex items-center justify-between">
          <span>🧪 Preview Upgraded Blind Telemetry Prompt (<span id="blind-char-count">{len(blind_prompt)}</span> chars)</span>
          <span class="text-[11px] text-sky-400">Click to expand</span>
        </summary>
        <div id="blind-preview-pre" style="overflow-wrap: anywhere;" class="mt-3 pt-3 border-t border-zinc-800 font-mono text-[11px] text-zinc-300 whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto overflow-x-auto max-w-full bg-zinc-950 p-4 rounded-lg border border-sky-500/25">
{blind_prompt_escaped}
        </div>
      </details>

      <!-- Hidden Pre-Formatted Prompts for Copying & Live Watermark Merge -->
      <textarea id="blind-prompt-base" class="hidden" readonly>{blind_prompt_escaped}</textarea>
      <textarea id="blind-prompt-data" class="hidden" readonly>{blind_prompt_escaped}</textarea>
    </div>

    <!-- ============================================================ -->
    <!-- METHOD 2: OUR SYSTEM VERDICT • DIBSE BIDIRECTIONAL ENGINE    -->
    <!-- ============================================================ -->
    <div id="method-2" class="rounded-2xl border-2 border-purple-500/60 bg-zinc-900/85 p-6 sm:p-8 backdrop-blur-md shadow-[0_0_25px_rgba(168,85,247,0.12)] space-y-6">
      
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-purple-500/25 pb-4">
        <div>
          <div class="flex items-center gap-2 mb-1 flex-wrap">
            <span class="text-xs font-extrabold uppercase tracking-widest text-purple-400 flex items-center gap-1.5">
              <span>🧠</span>
              <span>Method 2: Our Bidirectional DIBSE System Verdict</span>
            </span>
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold border {action_bg}">{action_pill}</span>
          </div>
          <h2 class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
            Our System Verdict
          </h2>
          <p class="text-xs text-zinc-400 mt-0.5">
            Closed-4H deterministic regime call, Loop A &amp; Loop B swing zones, symmetric LSCE sweep/squeeze gate, 10x–100x modeled heatmap, and zero-stop self-healing inventory rules.
          </p>
        </div>
        <div class="px-3.5 py-1.5 rounded-full border border-amber-500/40 bg-amber-500/10 text-amber-300 text-xs font-medium self-start sm:self-auto">
          <span class="text-zinc-400">Dominant Magnet:</span> <strong class="text-white ml-1">{dom_reason}</strong>
        </div>
      </div>

      <!-- Reminder Banner: Method 2 is Deterministic Second Opinion; Always Compare with Method 1 AI -->
      <div id="method2-ai-reminder" class="p-3.5 sm:p-4 rounded-xl bg-sky-500/10 border border-sky-400/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
        <div class="text-xs text-sky-100 leading-relaxed">
          <strong class="text-sky-300 uppercase tracking-wider">Always Compare with Method 1 AI:</strong>
          Method 2 is a fixed deterministic rule baseline. For deeper reasoning and more accurate DIBSE entries/exits, always copy <strong>Method 1 (Blind Telemetry)</strong> into your own AI and compare both verdicts.
        </div>
        <a href="#method-1" class="flex-shrink-0 inline-flex items-center justify-center px-3.5 py-2 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 border border-sky-400/60 text-[11px] font-bold text-sky-200 transition-all">
          &uarr; Compare via Method 1
        </a>
      </div>

      <!-- Plain English Bottom Line Breakdown + DIBSE Bidirectional Playbook -->
      <div class="p-5 sm:p-6 rounded-2xl bg-zinc-950/90 border border-emerald-500/40 space-y-4">
        <div>
          <div class="flex items-center gap-2 mb-1 flex-wrap">
            <span class="text-xs font-bold uppercase tracking-wider text-emerald-400">Bottom Line Verdict &bull; DIBSE Spot Engine</span>
            <span class="text-xs text-zinc-500 font-medium">({sleeve_alloc})</span>
          </div>
          <h3 class="text-lg sm:text-xl font-extrabold text-white tracking-tight">
            Why This Bidirectional Call?
          </h3>
          <div class="mt-3 p-4 rounded-xl bg-zinc-900/60 border border-emerald-500/35 flex items-start gap-3">
            <span class="text-2xl">💡</span>
            <p class="text-sm sm:text-base text-zinc-200 font-medium leading-relaxed">
              {plain_verdict}
            </p>
          </div>
        </div>

        <!-- Loop A / Loop B Playbook Zones -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div class="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/40 space-y-1">
            <div class="text-[11px] font-bold uppercase tracking-wider text-emerald-400">Loop A (10% USDT &rarr; BTC &rarr; USDT)</div>
            <div class="font-mono text-zinc-200 leading-relaxed">{loop_a_zone}</div>
          </div>
          <div class="p-3.5 rounded-xl bg-sky-950/20 border border-sky-500/40 space-y-1">
            <div class="text-[11px] font-bold uppercase tracking-wider text-sky-400">Loop B (10% BTC &rarr; USDT &rarr; BTC)</div>
            <div class="font-mono text-zinc-200 leading-relaxed">{loop_b_zone}</div>
          </div>
        </div>

        <!-- 3 Driving Market Factors & DIBSE Self-Healing Rules -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 pt-2">
          <div class="lg:col-span-2 space-y-2.5">
            <div class="text-xs font-bold uppercase tracking-wider text-zinc-400">The 3 Key Market Factors Driving This Call</div>
            <div class="space-y-2.5">
              {why_points_html}
            </div>
          </div>

          <div class="space-y-3">
            <div class="bg-zinc-900/60 p-4 rounded-xl border border-amber-500/40 space-y-1">
              <div class="text-xs font-bold uppercase tracking-wider text-amber-400">Dual-Sleeve Sandbox Allocation</div>
              <p class="text-xs text-zinc-300 leading-relaxed font-normal">{why_sizing}</p>
              <div class="pt-1.5 text-[11px] font-mono text-zinc-400 border-t border-zinc-800/80">{risk.get('risk_advisory', '')}</div>
            </div>
            <div class="bg-zinc-900/60 p-4 rounded-xl border border-indigo-500/40 space-y-1">
              <div class="text-xs font-bold uppercase tracking-wider text-indigo-300">Asymmetric Self-Healing Protocol</div>
              <p class="text-xs text-zinc-300 leading-relaxed font-normal">{why_stop}</p>
              <p class="text-[11px] text-emerald-300/90 leading-relaxed pt-1 border-t border-zinc-800/80">{stop_rule}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- LSCE Execution State Banner -->
      <div class="p-4 rounded-xl border {lsce_badge_class} flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
        <div class="flex items-center gap-3">
          <span class="text-2xl">{lsce_badge_icon}</span>
          <div>
            <div class="text-[10px] uppercase font-bold tracking-wider text-zinc-400">Bidirectional Liquidation Sweep Engine (LSCE &bull; Closed 4H)</div>
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
            <span class="text-xs font-bold text-rose-400 uppercase tracking-wide">Upper Short Pool (Loop B Target)</span>
            <span class="text-xs mono font-medium bg-zinc-800 text-zinc-200 px-2.5 py-0.5 rounded-full">
              +{upper_c.get('distance_pct', 0.0):.2f}%
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
            <span class="text-xs font-bold text-emerald-400 uppercase tracking-wide">Lower Long Pool (Loop A Target)</span>
            <span class="text-xs mono font-medium bg-zinc-800 text-zinc-200 px-2.5 py-0.5 rounded-full">
              -{lower_c.get('distance_pct', 0.0):.2f}%
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
            <div><strong class="text-zinc-200">How the Heatmap Works:</strong> Modeled clusters scale proportionally to tracked exchange OI &amp; closed-4H swing levels (see 5 Regimes Guide for math).</div>
            <div class="text-emerald-400 font-bold shrink-0">Dominant Gravitational Pull: {dom_magnet}</div>
          </div>
        </div>
      </div>

      <!-- Six-Factor Decision Logic Section -->
      <div class="border border-teal-500/45 rounded-xl p-5 bg-zinc-950/90 space-y-3.5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-teal-500/25 pb-3 gap-1">
          <span class="text-xs font-bold text-teal-300 uppercase tracking-wider">Magnet Decision Analysis (Six-Factor Evaluation)</span>
          <span class="text-xs text-zinc-400">Hierarchy: Pool Size &gt; Spot CVD &gt; Crowding &gt; Regime &gt; Distance &gt; 4H Width</span>
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
            <strong class="text-indigo-300 block mb-1">4. Closed-4H Market Structure:</strong>
            <span class="text-zinc-200 leading-relaxed">{f4}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-emerald-500/35">
            <strong class="text-emerald-300 block mb-1">5. Distance Asymmetry:</strong>
            <span class="text-zinc-200 leading-relaxed">{f5}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-violet-500/35">
            <strong class="text-violet-300 block mb-1">6. Closed 4H Range Compression:</strong>
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
    <p>Scan ID: <span class="mono text-zinc-300">{scan_id}</span> &bull; Updates Every 30m (:02/:32 UTC) &bull; {spot_source} &bull; {futures_source}</p>
    <p class="text-[11px] text-zinc-400">Strictly for informational and risk research purposes. Not financial advice.</p>
  </footer>

  <script>
    const IS_NATIVE_APP = !!(window.Capacitor && typeof window.Capacitor.isNativePlatform === 'function' && window.Capacitor.isNativePlatform()) || location.protocol === 'file:';
    const LIVE_BASE = IS_NATIVE_APP ? 'https://aikeluargalee-tech.github.io/btc-magnet-monitor/' : './';
    const rootAtLoad = document.getElementById('app-root');
    let currentScanTs = Date.parse(rootAtLoad ? rootAtLoad.getAttribute('data-scan-ts') : '') || 0;
    let lastFetchOk = null;

    const WB_KEY_BUY = 'dibse_wb_buy';
    const WB_KEY_SELL = 'dibse_wb_sell';

    function lsGetSafe(k) {{
      try {{ return (window.localStorage && localStorage.getItem(k)) || ''; }} catch (e) {{ return ''; }}
    }}
    function lsSetSafe(k, v) {{
      try {{
        if (!window.localStorage) return;
        if (v) localStorage.setItem(k, v);
        else localStorage.removeItem(k);
      }} catch (e) {{}}
    }}

    function formatWatermarkSummary(pBuy, pSell) {{
      const parts = [];
      const bNum = parseFloat(pBuy);
      const sNum = parseFloat(pSell);
      if (!isNaN(bNum) && bNum > 0) {{
        const fmtB = '$' + bNum.toLocaleString('en-US', {{ maximumFractionDigits: 2 }});
        parts.push('Loop A Holding Spot BTC from P_buy=' + fmtB + ' (Need P_exit > ' + fmtB + '; Zero Stop-Loss)');
      }}
      if (!isNaN(sNum) && sNum > 0) {{
        const fmtS = '$' + sNum.toLocaleString('en-US', {{ maximumFractionDigits: 2 }});
        parts.push('Loop B Holding Spot USDT from BTC sold at P_sell=' + fmtS + ' (Seek Rebuy P_rebuy < ' + fmtS + ')');
      }}
      return parts.length ? parts.join(' | ') : '';
    }}

    function syncWatermarksToDom(loadFromStorage) {{
      const buyEl = document.getElementById('wb-buy');
      const sellEl = document.getElementById('wb-sell');
      if (loadFromStorage) {{
        if (buyEl) buyEl.value = lsGetSafe(WB_KEY_BUY);
        if (sellEl) sellEl.value = lsGetSafe(WB_KEY_SELL);
      }}
      const pBuy = buyEl ? buyEl.value.trim() : lsGetSafe(WB_KEY_BUY);
      const pSell = sellEl ? sellEl.value.trim() : lsGetSafe(WB_KEY_SELL);
      const customLine = formatWatermarkSummary(pBuy, pSell);

      const baseEl = document.getElementById('blind-prompt-base');
      const dataEl = document.getElementById('blind-prompt-data');
      const prevEl = document.getElementById('blind-preview-pre');
      const cntEl = document.getElementById('blind-char-count');
      const statusEl = document.getElementById('wb-status');

      if (baseEl && dataEl) {{
        const baseText = baseEl.value || '';
        const merged = customLine
          ? baseText.replace(/^\\[ACTIVE INVENTORY WATERMARKS\\]:.*$/m, '[ACTIVE INVENTORY WATERMARKS]: ' + customLine)
          : baseText;
        dataEl.value = merged;
        if (prevEl) prevEl.textContent = merged;
        if (cntEl) cntEl.textContent = String(merged.length);
      }}
      if (statusEl) {{
        statusEl.textContent = customLine
          ? 'Active watermark: ' + customLine
          : 'Baseline: 10% USDT + 10% BTC sleeves ready (local only)';
      }}
    }}

    document.addEventListener('input', function (e) {{
      const t = e.target;
      if (!t || (t.id !== 'wb-buy' && t.id !== 'wb-sell')) return;
      if (t.id === 'wb-buy') lsSetSafe(WB_KEY_BUY, t.value.trim());
      if (t.id === 'wb-sell') lsSetSafe(WB_KEY_SELL, t.value.trim());
      syncWatermarksToDom(false);
    }});

    document.addEventListener('click', function (e) {{
      const btn = e.target && e.target.closest ? e.target.closest('#wb-clear') : null;
      if (!btn) return;
      lsSetSafe(WB_KEY_BUY, '');
      lsSetSafe(WB_KEY_SELL, '');
      const buyEl = document.getElementById('wb-buy');
      const sellEl = document.getElementById('wb-sell');
      if (buyEl) buyEl.value = '';
      if (sellEl) sellEl.value = '';
      syncWatermarksToDom(false);
    }});

    function copyElementText(elemId, btnId, iconId, textId, origLabel, origIcon, origBg, origHover, toastText) {{
      syncWatermarksToDom(false);
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

    function copyBlindPrompt() {{
      copyElementText(
        'blind-prompt-data',
        'copy-blind-btn',
        'copy-blind-icon',
        'copy-blind-text',
        'Copy Blind Telemetry for AI',
        '🧪',
        'bg-sky-500',
        'hover:bg-sky-400',
        'Copied Upgraded Blind Telemetry to Clipboard!'
      );
    }}
    syncWatermarksToDom(true);

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

      // Next scheduled :02 or :32 UTC update boundary + countdown
      const nextTarget = new Date(utcMs);
      nextTarget.setUTCSeconds(0, 0);
      if (now.getUTCMinutes() < 2) {{
        nextTarget.setUTCMinutes(2);
      }} else if (now.getUTCMinutes() < 32) {{
        nextTarget.setUTCMinutes(32);
      }} else {{
        nextTarget.setUTCMinutes(2);
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
        if (currentScanTs > 0 && ageMin > 40) {{
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
      }} else if (ageMin > 40) {{
        el.className = base + 'border-amber-500/40 bg-amber-500/10 text-amber-300';
        el.textContent = '⚠ Scan is ' + age + ' old (past 30m target + CI backup grace) - awaiting next automated CI run.';
        if (confTag) {{
          confTag.className = 'text-[11px] text-amber-300 font-semibold';
          confTag.textContent = '⚠ Confidence Downgraded: Scan ' + age + ' old (>40m)';
        }}
      }} else {{
        el.className = base + 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
        el.textContent = '● Scan data is ' + age + ' old - updates every 30m (:02/:32 UTC); checking feed every minute.';
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
          if (name.indexOf('on') === 0 && !(name === 'onclick' && trimmedVal === 'copyBlindPrompt()')) {{
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
            syncWatermarksToDom(true);
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
    <div class="max-w-4xl mx-auto flex flex-wrap items-center justify-between gap-3">
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
        """Renders the educational reference subpage explaining the 5 regimes & DIBSE math."""
        regime = data.get("regime", {})
        current_name = regime.get("name", "Range / Liquidation Magnet")
        blind_prompt = self._build_blind_llm_prompt(data)
        blind_prompt_escaped = blind_prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>The 5 Market Regimes &amp; DIBSE Math — BTC Magnet Monitor Reference Guide</title>
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
    <div class="max-w-4xl mx-auto flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl overflow-hidden border border-zinc-800 flex items-center justify-center shadow-inner flex-shrink-0 bg-zinc-950 p-0.5">
          <img src="./assets/app-logo.png?v=4" alt="BTC Magnet Monitor Logo" class="w-full h-full object-contain">
        </div>
        <div>
          <span class="font-extrabold text-base tracking-tight text-white">BTC Magnet Monitor</span>
          <span class="text-xs text-zinc-400 block">5-Regime Radar &amp; DIBSE Reference Guide</span>
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
        DIBSE Architecture &bull; Observable Positioning Mechanics
      </div>
      <h1 class="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
        5-Regime Radar &amp; DIBSE Spot Protocol
      </h1>
      <p class="text-base sm:text-lg text-zinc-300 leading-relaxed">
        How the Dual-Inventory Bidirectional Swing Engine pairs a <strong>10% USDT Sleeve</strong> and a <strong>10% BTC Sleeve</strong> (80% Core untouched, zero leverage, zero stop-losses) with closed-4H microstructure regimes.
      </p>
    </div>

    <!-- Active State Banner with Copy Prompt -->
    <div class="p-5 rounded-2xl border-2 border-cyan-500/60 bg-cyan-500/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-[0_0_20px_rgba(6,182,212,0.12)]">
      <div>
        <div class="text-xs uppercase font-bold text-cyan-400 tracking-wider">Current Live Market State</div>
        <div class="text-xl font-bold text-white mt-0.5">{current_name}</div>
        <div class="text-xs text-zinc-400 mt-1">Evaluated on completed 4H bars (klines[:-1]) &bull; Updates every 30m (:02/:32 UTC).</div>
      </div>
      <div class="flex items-center gap-2.5">
        <button onclick="copySubpagePrompt()" class="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500 hover:bg-sky-400 text-black font-bold text-xs shadow-lg shadow-sky-500/20 transition-all cursor-pointer">
          <span>🧪</span>
          <span id="sub-copy-text">Copy Blind Telemetry for AI</span>
        </button>
        <a href="index.html" class="inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-white font-bold text-xs border border-zinc-700 transition-all">
          Live Monitor &rarr;
        </a>
      </div>
    </div>
    <textarea id="subpage-prompt-data" class="hidden" readonly>{blind_prompt_escaped}</textarea>

    <!-- Section 1: DIBSE Philosophy -->
    <div class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-sky-500/45 space-y-4">
      <h2 class="text-2xl font-bold text-white flex items-center gap-2.5">
        <span>1. Core Philosophy: Bidirectional Spot Swings (Zero Forced Stops)</span>
      </h2>
      <div class="prose prose-invert text-sm text-zinc-300 space-y-3 leading-relaxed">
        <p>
          Rather than making leveraged all-in directional bets with forced stop-losses, <strong>DIBSE</strong> keeps <strong>10% in USDT</strong> and <strong>10% in Spot BTC</strong> (while 80% sits untouched in core reserve) to harvest two-way volatility:
        </p>
        <ul class="space-y-2 list-disc list-inside text-zinc-300">
          <li><strong>Swing Loop A (USDT &rarr; BTC &rarr; USDT):</strong> Deploys the 10% USDT Sleeve into discounted Spot BTC on lower-band washout sweeps &amp; reclaims, then harvests back into USDT above cost basis (<em>P_exit &gt; P_buy</em>).</li>
          <li><strong>Swing Loop B (BTC &rarr; USDT &rarr; BTC):</strong> Rotates the 10% BTC Sleeve into USDT during upper short-squeeze distribution rallies, then repurchases more BTC after retracement (<em>P_rebuy &lt; P_sell</em>).</li>
          <li><strong>Asymmetric Self-Healing Inventory:</strong> Zero borrowed leverage and zero stop-losses. Early entries remain productive spot inventory (Spot BTC held for recovery &gt; P_buy, or Spot USDT held until retrace &lt; P_sell). Zero lagged oscillators (no MA/EMA/RSI/MACD/ATR).</li>
        </ul>
      </div>
    </div>

    <!-- Section 2: How the Majority Voting Works -->
    <div class="p-6 rounded-2xl bg-zinc-900/70 border-2 border-indigo-500/45 space-y-4">
      <h2 class="text-2xl font-bold text-white flex items-center gap-2.5">
        <span>2. How the Closed-4H Majority-Voting Engine Works</span>
      </h2>
      <div class="space-y-3 text-sm text-zinc-300 leading-relaxed">
        <p>
          All structural range boundaries, Weekly VWAP, and modeled liquidation tiers are computed strictly from <strong>closed (completed) 4H bars (<span class="mono">klines[:-1]</span>)</strong> so open-candle wicks never cause intrabar repainting.
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-emerald-500/40">
            <strong class="text-emerald-400 block text-xs uppercase font-bold mb-1">Majority Rule (&ge;3 of 4)</strong>
            <p class="text-xs text-zinc-400">Each regime defines 4 observable orderflow/positioning facts. If 3 or 4 clear simultaneously, the regime activates.</p>
          </div>
          <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-amber-500/40">
            <strong class="text-amber-400 block text-xs uppercase font-bold mb-1">Hold Both Sleeves Fallback</strong>
            <p class="text-xs text-zinc-400">If signals conflict mid-range or feeds drop out (<span class="mono">DATA UNAVAILABLE</span>), both 10% USDT and 10% BTC sleeves hold intact.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 3: Deep Dive into the 5 Regimes -->
    <div class="space-y-6">
      <h2 class="text-2xl font-bold text-white">3. Complete Specification of the 5 DIBSE Regimes</h2>

      <!-- Regime 1 -->
      <div id="regime-1" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-emerald-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            Regime 1 &bull; Spot-Led Expansion
          </span>
          <span class="text-xs font-mono text-emerald-300 font-bold">Loop A: Accumulate Dips | Hold BTC Sleeve</span>
        </div>
        <h3 class="text-lg font-bold text-white">Genuine spot demand supporting upward structure</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          Real institutional bids absorb supply above Daily &amp; Weekly VWAP without excessive perp leverage. Loop A deploys on VWAP pullbacks; Loop B holds the 10% BTC sleeve for expansion instead of selling prematurely.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-emerald-500/30">
          <div class="font-bold text-emerald-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price holding above Daily VWAP and closed-4H Weekly VWAP.</div>
          <div class="text-zinc-300">2. Spot CVD ratio clearly positive (&ge;1.15) or 7-day slope upward.</div>
          <div class="text-zinc-300">3. Spot trading volume expanding (&ge;1.10x 20-day baseline).</div>
          <div class="text-zinc-300">4. Funding rates contained (&le;0.012%) and OI not overheating parabolically.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-emerald-500/25">
            <strong class="text-emerald-300 block text-[11px] uppercase">DIBSE Sleeve Protocol:</strong>
            <span class="text-zinc-200">Deploy Loop A (10% USDT &rarr; BTC) at Daily/Weekly VWAP pullbacks; keep BTC sleeve riding trend.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-indigo-500/25">
            <strong class="text-indigo-300 block text-[11px] uppercase">Self-Healing Rule:</strong>
            <span class="text-zinc-200">Zero stop-losses. Any early BTC fill remains productive spot inventory (wait for P_exit &gt; P_buy).</span>
          </div>
        </div>
      </div>

      <!-- Regime 2 -->
      <div id="regime-2" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-orange-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-orange-500/10 text-orange-400 border border-orange-500/30">
            Regime 2 &bull; Leveraged / Fragile Upside
          </span>
          <span class="text-xs font-mono text-sky-300 font-bold">Loop B: Rotate 10% BTC &rarr; USDT (Harvest Squeeze)</span>
        </div>
        <h3 class="text-lg font-bold text-white">Upside driven by stretched perp leverage while Spot CVD lags</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          Price pushes higher on surging OI and elevated funding while spot taker buyers step back. Ideal environment for <strong>Swing Loop B (BTC &rarr; USDT)</strong> to harvest the 10% BTC sleeve into retail euphoria—with strictly zero chase buying.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-orange-500/30">
          <div class="font-bold text-orange-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price rising but Spot CVD is flat or negative (bearish spot divergence).</div>
          <div class="text-zinc-300">2. Perp CVD and/or Open Interest rising sharply (&gt;+4% in 24h).</div>
          <div class="text-zinc-300">3. Funding rates elevated (&gt;0.015% per 8h) or basis contango stretched.</div>
          <div class="text-zinc-300">4. Spot volume lagging (&lt;1.0x baseline) inside upper squeeze band.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-sky-500/25">
            <strong class="text-sky-300 block text-[11px] uppercase">DIBSE Sleeve Protocol:</strong>
            <span class="text-zinc-200">Zero upside stop-buys. Rotate 10% BTC &rarr; USDT near upper short pool; rebuy on retrace &lt; P_sell.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-indigo-500/25">
            <strong class="text-indigo-300 block text-[11px] uppercase">Self-Healing Rule:</strong>
            <span class="text-zinc-200">Zero forced rebuy stops. If price rallies further after sale, keep Spot USDT until pullback &lt; P_sell.</span>
          </div>
        </div>
      </div>

      <!-- Regime 3 -->
      <div id="regime-3" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-cyan-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
            Regime 3 &bull; Range / Liquidation Magnet (Two-Way Core)
          </span>
          <span class="text-xs font-mono text-cyan-300 font-bold">Loop A at Floor Sweep &harr; Loop B at Ceiling Squeeze</span>
        </div>
        <h3 class="text-lg font-bold text-white">Closed-4H horizontal channel where extremes trigger two-way swings</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          Price oscillates inside a defined closed-4H channel bounded by upper short pools and lower long pools. DIBSE waits patiently in mid-range, buying swept lower floors (<strong>Loop A</strong>) and trimming swept upper ceilings (<strong>Loop B</strong>).
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-cyan-500/30">
          <div class="font-bold text-cyan-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price oscillating inside closed-4H channel (width &le;4.5%).</div>
          <div class="text-zinc-300">2. Spot CVD balanced in neutral zone (0.90 to 1.15).</div>
          <div class="text-zinc-300">3. L/S account ratio or funding skewed across liquidation bands.</div>
          <div class="text-zinc-300">4. Distinct upper short and lower long liquidation clusters flanking spot.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-cyan-500/25">
            <strong class="text-cyan-300 block text-[11px] uppercase">DIBSE Sleeve Protocol:</strong>
            <span class="text-zinc-200">Wait mid-range; execute Loop A on lower LSCE reclaim or Loop B on upper LSCE rejection.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-indigo-500/25">
            <strong class="text-indigo-300 block text-[11px] uppercase">Self-Healing Rule:</strong>
            <span class="text-zinc-200">Zero forced stop-losses outside channel; inventory holds spot symmetrically across cycle flips.</span>
          </div>
        </div>
      </div>

      <!-- Regime 4 -->
      <div id="regime-4" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-rose-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-rose-500/10 text-rose-400 border border-rose-500/30">
            Regime 4 &bull; Cascade / Forced Deleveraging
          </span>
          <span class="text-xs font-mono text-amber-300 font-bold">Hold Both Sleeves (Do Not Catch Falling Knife)</span>
        </div>
        <h3 class="text-lg font-bold text-white">Forced long unwind &amp; OI liquidation waterfall in progress</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          Domino margin liquidations drive vertical drops as OI collapses. DIBSE keeps the 10% USDT sleeve strictly on standby until forced unwinding completes and a closed-4H washout stabilizes.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-rose-500/30">
          <div class="font-bold text-rose-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Sharp vertical price plunge (&le;-3.0% in 1h or &le;-6.0% in 24h).</div>
          <div class="text-zinc-300">2. Open Interest crashing violently (&le;-3.5% in 1h or &le;-7.0% in 4h).</div>
          <div class="text-zinc-300">3. Funding rate plunged deeply negative (&le;-0.005%).</div>
          <div class="text-zinc-300">4. Severe futures basis discount / backwardation (&lt;1.0% annualized).</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-rose-500/25">
            <strong class="text-rose-300 block text-[11px] uppercase">DIBSE Sleeve Protocol:</strong>
            <span class="text-zinc-200">Hold 10% USDT dry until closed 4H bar stabilizes above washout low &amp; OI flatlines.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-indigo-500/25">
            <strong class="text-indigo-300 block text-[11px] uppercase">Self-Healing Rule:</strong>
            <span class="text-zinc-200">Zero panic stop-sells on your 10% BTC sleeve during forced margin cascades.</span>
          </div>
        </div>
      </div>

      <!-- Regime 5 -->
      <div id="regime-5" class="p-6 rounded-2xl bg-zinc-900/60 border-2 border-red-500/50 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-red-500/10 text-red-400 border border-red-500/30">
            Regime 5 &bull; Distribution / Bear Continuation
          </span>
          <span class="text-xs font-mono text-sky-300 font-bold">Loop B: Rotate 10% BTC &rarr; USDT on Weak Bounces</span>
        </div>
        <h3 class="text-lg font-bold text-white">Persistent seller control below Daily &amp; Weekly VWAP</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          Larger participants distribute into weak low-volume bounces below VWAP. Loop B converts the 10% BTC sleeve into Spot USDT to repurchase lower; Loop A pauses until deep structural support reclaims.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-red-500/30">
          <div class="font-bold text-red-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price trapped below Daily VWAP and closed-4H Weekly VWAP.</div>
          <div class="text-zinc-300">2. Spot CVD persistently negative (7D/14D slope &lt;0).</div>
          <div class="text-zinc-300">3. Rallies occur on fading spot volume (&lt;0.95x baseline).</div>
          <div class="text-zinc-300">4. Long-heavy accounts trapped above resistance with soft basis.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-sky-500/25">
            <strong class="text-sky-300 block text-[11px] uppercase">DIBSE Sleeve Protocol:</strong>
            <span class="text-zinc-200">Loop B sells 10% BTC &rarr; USDT into VWAP resistance rejections; rebuy lower below P_sell.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-indigo-500/25">
            <strong class="text-indigo-300 block text-[11px] uppercase">Macro Shift Trigger:</strong>
            <span class="text-zinc-200">Closed 4H reclaim above Weekly VWAP backed by Spot CVD &ge; 1.05.</span>
          </div>
        </div>
      </div>

    </div>

    <!-- Section 4: Modeled Liquidation Pool & Tier Scaling Methodology -->
    <div id="methodology-pools" class="p-6 rounded-2xl bg-zinc-900/70 border-2 border-purple-500/50 space-y-4">
      <h2 class="text-2xl font-bold text-white">4. Modeled Liquidation Pool &amp; Closed-4H Scaling Methodology</h2>
      <p class="text-xs sm:text-sm text-zinc-300 leading-relaxed">
        No public REST API exposes individual traders' private margin prices or cross-exchange liquidation ledgers in real time. All liquidity dollar sizes in this monitor are <strong>Modeled Estimates</strong> derived transparently from observable exchange inputs:
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div class="p-4 rounded-xl bg-zinc-950/80 border border-purple-500/35 space-y-1.5">
          <div class="font-bold text-purple-300 uppercase text-[11px]">OI Scope &amp; Venue Disclosure</div>
          <p class="text-zinc-300 leading-relaxed">Tracked Open Interest reflects the active perpetual venue subset reported in Panel 2 (e.g. OKX/Deribit perpetuals when US runner restrictions block Binance Futures), never claimed as total global BTC futures OI.</p>
        </div>
        <div class="p-4 rounded-xl bg-zinc-950/80 border border-indigo-500/35 space-y-1.5">
          <div class="font-bold text-indigo-300 uppercase text-[11px]">Closed-4H Leverage Projection Grid</div>
          <p class="text-zinc-300 leading-relaxed">Projects 100x (0.8%), 50x (1.8%), 25x (3.8%), and 10x (9.5%) tiers strictly from completed closed 4H swing extremes (<span class="mono">klines[:-1]</span>) into price-proportional bins (<span class="mono">max($100, round(price*0.0015,-1))</span>), scaled by <span class="mono">OI &times; Spot Price</span> and L/S skew (zero ATR).</p>
        </div>
      </div>
    </div>

    <!-- Section 5: Bidirectional LSCE State Machine -->
    <div id="methodology-lsce" class="p-6 rounded-2xl bg-zinc-900/70 border-2 border-teal-500/50 space-y-4">
      <h2 class="text-2xl font-bold text-white">5. Bidirectional LSCE State Machine &amp; Gate Rules</h2>
      <p class="text-xs sm:text-sm text-zinc-300 leading-relaxed">
        The <strong>Bidirectional Liquidation Sweep Confirmation Engine (LSCE)</strong> evaluates live spot against both the nearest lower long shelf (<strong>Loop A</strong>) and nearest upper short shelf (<strong>Loop B</strong>):
      </p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-zinc-700/60">
          <strong class="text-zinc-300 block uppercase text-[11px] mb-1">UNTESTED</strong>
          <p class="text-zinc-400">Spot sits cleanly between lower and upper modeled shelves (&gt;0.20% inside channel). Holding both 10% USDT and 10% BTC sleeves.</p>
        </div>
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-amber-500/40">
          <strong class="text-amber-300 block uppercase text-[11px] mb-1">SWEEP_IN_PROGRESS / UPPER_SWEEP_IN_PROGRESS</strong>
          <p class="text-zinc-300">Spot tests within &plusmn;0.20% of a shelf without confirmed absorption or rejection yet. Holding until closed confirmation clears.</p>
        </div>
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-emerald-500/40">
          <strong class="text-emerald-300 block uppercase text-[11px] mb-1">SWEEP_AND_RECLAIM_CONFIRMED (Loop A)</strong>
          <p class="text-zinc-300">Spot reclaims lower shelf with <strong>Spot CVD &ge; 1.05</strong> &amp; <strong>Depth &ge; 0.50</strong>. Rotates 10% USDT &rarr; Spot BTC (target P_exit &gt; P_buy; zero stop-loss).</p>
        </div>
        <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-sky-500/40">
          <strong class="text-sky-300 block uppercase text-[11px] mb-1">UPPER_SWEEP_REJECTION_CONFIRMED (Loop B)</strong>
          <p class="text-zinc-300">Upper short-squeeze wick stalls with exhausted Spot CVD (&le;1.02) or overhead ask wall (Depth &lt; 0.90). Rotates 10% BTC &rarr; USDT (rebuy &lt; P_sell).</p>
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
          btnText.innerText = '✓ Blind Telemetry Copied!';
          setTimeout(() => {{ btnText.innerText = 'Copy Blind Telemetry for AI'; }}, 3000);
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
        """DIBSE verification linter before rendering text.html:
          - Asserts immediate_imbalance_ratio matches lower_pool / upper_pool (within tolerance).
          - Enforces zero stop-loss portfolio risk under DIBSE (20% active sandbox = 10% USDT + 10% BTC).
          - Checks prose fields against scan metrics to catch stale hardcoded numbers.
          - Verifies blind prompt contains zero banned lagged oscillators (20D EMA/50D EMA/200D SMA/1H ATR).
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
        assert portfolio_risk <= 0.01, f"Linter assertion failed: DIBSE prohibits stop-loss risk ({portfolio_risk}% != 0)"
        assert effective_risk <= 0.01, f"Linter assertion failed: effective_risk_budget_pct ({effective_risk}% != 0)"
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

        # Ensure zero legacy lagged oscillators leak into blind prompt
        blind_txt = self._build_blind_llm_prompt(data)
        for banned_osc in ("20D EMA", "50D EMA", "200D SMA", "1H ATR", "ATR Compression"):
            assert banned_osc not in blind_txt, f"Linter assertion failed: banned oscillator {banned_osc!r} in blind prompt"

    def _render_text_page(self, data: Dict[str, Any]) -> str:
        """Renders the Mobile Text/Data Terminal (text.html).
        Strictly starts with Panel 1 and preserves zero-framework vanilla HTML/CSS/JS:
          - 2-Line Monospace Header + Session/Cadence/Mandate Metadata Line
          - Telemetry Stale >40M Warning Banner
          - Panel 1 • Real-Time BTC Spot Price (Live), Clocks, Next Update & Market Session
          - Panel 2 • On-Exchange Telemetry (Raw Closed-4H Feeds vs Modeled Scope)
          - Panel 3 • Macro Market Regime Diagnosis & 5-Regime + Transition Matrix
          - Bridge  • How to Get Your DIBSE Trading Verdict (Method 1 vs Method 2)
          - Method 1: ONE Clean Copy Button (DIBSE Blind Telemetry) + Local Watermarks
          - Method 2: Our System Verdict (DIBSE Bidirectional Playbook & Liquidation Ladder)
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
        blind_prompt = self._build_blind_llm_prompt(data)

        # Linter check before rendering
        self._verify_text_telemetry(data)

        # Telemetry age verification (>40m grace buffer allowing staggered CI backup slots)
        is_stale_telemetry = False
        try:
            dt_scan = _dt.datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
            now_utc = _dt.datetime.now(_dt.timezone.utc)
            if (now_utc - dt_scan).total_seconds() > 2400:
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
        d_vwap = float(metrics.get("daily_vwap", 0.0) or 0.0)
        w_vwap = float(metrics.get("weekly_vwap", 0.0) or 0.0)
        sw_h = float(metrics.get("swing_high_4h", 0.0) or 0.0)
        sw_l = float(metrics.get("swing_low_4h", 0.0) or 0.0)
        floor = float(metrics.get("base_floor", 0.0) or 0.0)
        ceil_lvl = float(metrics.get("base_ceiling", 0.0) or sw_h or 0.0)
        cap_wick = float(metrics.get("capitulation_wick_low", 0.0) or 0.0)
        euph_wick = float(metrics.get("euphoria_wick_high", 0.0) or 0.0)
        raw_cutoff_t = str(metrics.get("closed_4h_bar_close_time", "") or "")
        closed_4h_cutoff = (raw_cutoff_t[:16].replace("T", " ") + " UTC") if ("T" in raw_cutoff_t and len(raw_cutoff_t) >= 16) else (raw_cutoff_t or "Closed-4H Cutoff")

        d_vwap_diff = ((price - d_vwap) / d_vwap * 100) if d_vwap > 0 else 0.0
        w_vwap_diff = ((price - w_vwap) / w_vwap * 100) if w_vwap > 0 else 0.0

        spot_vol = float(metrics.get("spot_vol_24h", 0.0) or 0.0)
        vol_ratio = float(metrics.get("spot_vol_ratio", 1.0) or 1.0)
        cvd_ratio = float(metrics.get("spot_cvd_ratio", 1.0) or 1.0)
        cvd_7d = float(metrics.get("spot_cvd_slope_7d", 0.0) or 0.0)
        cvd_14d = float(metrics.get("spot_cvd_slope_14d", 0.0) or 0.0)
        perp_trend = str(metrics.get("perp_cvd_trend", "neutral") or "neutral")
        perp_slope = float(metrics.get("perp_cvd_slope_24h", 0.0) or 0.0)
        depth = float(metrics.get("bids_asks_depth_ratio", 1.0) or 1.0)

        oi = float(metrics.get("open_interest", 0.0) or 0.0)
        oi_1h = float(metrics.get("oi_change_1h_pct", 0.0) or 0.0)
        oi_4h = float(metrics.get("oi_change_4h_pct", 0.0) or 0.0)
        oi_24h = float(metrics.get("oi_change_24h_pct", 0.0) or 0.0)
        oi_3d = float(metrics.get("oi_change_3d_pct", 0.0) or 0.0)
        oi_hist_ok = bool(metrics.get("oi_history_available", True))
        funding = float(metrics.get("funding_rate", 0.0) or 0.0) * 100
        funding_ann = float(metrics.get("funding_rate_annualized", 0.0) or 0.0)
        basis = float(metrics.get("futures_basis_annualized", 0.0) or 0.0)
        ls_ratio = float(metrics.get("long_short_account_ratio", 1.0) or 1.0)
        ls_avail = bool(metrics.get("ls_ratio_available", True))
        ls_pct_72h = metrics.get("ls_ratio_percentile_72h")
        long_pct = (ls_ratio / (1.0 + ls_ratio) * 100) if (1.0 + ls_ratio) > 0 else 50.0
        spot_source = str(metrics.get("spot_data_source", "Binance Public Market-Data REST"))
        futures_source = str(metrics.get("futures_data_source", "Perp Public REST"))
        oi_scope = str(metrics.get("oi_scope", "Tracked venue perpetual subset"))

        ch_width = ((sw_h - sw_l) / max(price, 1.0) * 100) if (sw_h > 0 and sw_l > 0 and price > 0) else 0.0
        chg_24h = float(metrics.get("price_change_24h_pct", 0.0) or 0.0)
        wick_span_pct = ((euph_wick - cap_wick) / cap_wick * 100) if (euph_wick > 0 and cap_wick > 0) else 0.0

        d_vwap_disp = f"${d_vwap:,.2f} ({d_vwap_diff:+.2f}%)" if d_vwap > 0 else "DATA UNAVAILABLE"
        w_vwap_disp = f"${w_vwap:,.2f} ({w_vwap_diff:+.2f}%)" if w_vwap > 0 else "DATA UNAVAILABLE"
        sw_lh_disp = f"${sw_l:,.0f} / ${sw_h:,.0f}" if (sw_l > 0 and sw_h > 0) else "DATA UNAVAILABLE"
        ceil_floor_disp = f"${floor:,.0f} / ${ceil_lvl:,.0f}" if (floor > 0 or ceil_lvl > 0) else "DATA UNAVAILABLE"
        wicks_disp = f"${cap_wick:,.0f} / ${euph_wick:,.0f}" if (cap_wick > 0 and euph_wick > 0) else "DATA UNAVAILABLE"
        wick_span_disp = f"{wick_span_pct:.2f}%" if wick_span_pct > 0 else "DATA UNAVAILABLE"
        spot_vol_disp = f"{spot_vol:,.0f} BTC ({vol_ratio:.2f}x)" if spot_vol > 0 else "DATA UNAVAILABLE"
        cvd_disp = f"{cvd_ratio:.2f}" if spot_vol > 0 else "DATA UNAVAILABLE"
        oi_disp = f"{oi:,.1f} BTC" if oi > 0 else "DATA UNAVAILABLE"
        oi_24h_disp = f"{oi_24h:+.2f}%" if (oi > 0 and oi_hist_ok) else "DATA UNAVAILABLE"
        oi_1h_4h_disp = f"{oi_1h:+.2f}% / {oi_4h:+.2f}%" if (oi > 0 and oi_hist_ok) else "DATA UNAVAILABLE"
        oi_3d_disp = f"{oi_3d:+.2f}%" if (oi > 0 and oi_hist_ok) else "DATA UNAVAILABLE"
        ls_disp = (
            f"{ls_ratio:.2f} ({long_pct:.1f}% L"
            + (f", p{ls_pct_72h:.0f} 72h" if ls_pct_72h is not None else "")
            + ")"
        ) if ls_avail else "DATA UNAVAILABLE"

        regime_name = str(regime.get("name", "Transition / Mixed"))
        diagnosis = wrap36(str(regime.get("diagnosis", "")))
        tagline = wrap36(tagline_src)
        dibse_signal = str(regime.get("dibse_signal", "HOLD BOTH SLEEVES"))
        dibse_headline = wrap36(str(regime.get("dibse_action_headline", str(regime.get("action", "HOLD BOTH SLEEVES")))))
        rotation = str(regime.get("rotation", dibse_signal))
        loop_a_zone = wrap36(str(regime.get("loop_a_zone", "WAIT FOR SUPPORT SWEEP")))
        loop_b_zone = wrap36(str(regime.get("loop_b_zone", "WAIT FOR SQUEEZE EXHAUSTION")))
        sleeve_alloc = str(regime.get("sleeve_allocation", "10% USDT + 10% BTC (80% Core)"))
        failure_protocol = wrap36(str(regime.get("failure_protocol", "Zero stop-losses. Asymmetric self-healing spot hold.")))
        entry_inst = wrap36(str(regime.get("entry_instruction", "")))
        rule_score = str(regime.get("majority_score", "0/4 observations confirmed"))
        dom_magnet = str(regime.get("dominant_magnet", "Neutral"))
        imm_ratio = float(regime.get("immediate_imbalance_ratio", 1.0) or 1.0)
        imm_disp = f"~{round(imm_ratio):.0f}x" if imm_ratio >= 10 else f"{imm_ratio:.1f}x"
        tot_ratio = float(regime.get("total_ladder_imbalance_ratio", 1.0) or 1.0)
        tot_lower = float(regime.get("total_ladder_lower_vol", 0.0) or 0.0)
        tot_upper = float(regime.get("total_ladder_upper_vol", 0.0) or 0.0)
        lsce_status = str(regime.get("lsce_status", "UNTESTED"))
        lsce_side = str(regime.get("lsce_side", "NONE"))
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
        is_lower_sweep = (lsce_side.upper() == "LOWER" and ("IN_PROGRESS" in lsce_up or "FAILED" in lsce_up)) or (lsce_up in ("SWEEP_IN_PROGRESS", "SWEEP_FAILED_BREAKDOWN"))
        is_upper_sweep = ("UPPER_SWEEP" in lsce_up) or (lsce_side.upper() == "UPPER" and ("IN_PROGRESS" in lsce_up or "REJECTION" in lsce_up))
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
                if is_upper_sweep and "50-100x" in tier_lbl:
                    upper_lines.append(
                        f"{tier_short:<10} {px_str:>8} {dist_str:>7} <span class=\"c-amber\">{vol_str:>8}</span> [⚡]"
                    )
                    upper_lines.append(
                        '<span class="c-amber" style="font-weight: bold;">  └─► &lt;&lt;&lt; UPPER SQUEEZE WATCH &gt;&gt;&gt;</span>'
                    )
                else:
                    upper_lines.append(f"{tier_short:<10} {px_str:>8} {dist_str:>7} {vol_str:>8}")
            else:
                if row.get("is_nearest"):
                    lower_lines.append(
                        f"{tier_short:<10} {px_str:>8} {dist_str:>7} <span class=\"c-rose\">{vol_str:>8}</span> [🔥]"
                    )
                    if is_lower_sweep:
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
        why_stop = wrap36(str(regime.get("why_stop_reason", failure_protocol)))
        risk_summary_txt = wrap36(str(risk.get("risk_advisory", "")))

        mf = regime.get("magnet_factors", {})
        f1_size = wrap36(str(mf.get("factor_1_size", "")))
        f2_lead = wrap36(str(mf.get("factor_2_spot_leadership", "")))
        f3_crowd = wrap36(str(mf.get("factor_3_crowding_fuel", "")))
        f4_struct = wrap36(str(mf.get("factor_4_regime_structure", "")))
        f5_asym = wrap36(str(mf.get("factor_5_asymmetry", "")))
        f6_comp = wrap36(str(mf.get("factor_6_range_compression", mf.get("factor_6_atr_volatility", ""))))
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
      overflow-x: hidden;
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
      width: 100%;
      max-width: 100%;
      min-width: 0;
      overflow-x: hidden;
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

    .panel-box-violet {
      background: linear-gradient(180deg, #121024 0%, #090a0d 100%);
      border-color: #8b5cf6;
      box-shadow: 0 0 14px rgba(139, 92, 246, 0.16);
    }
    .panel-box-violet .panel-hdr { color: #a78bfa; border-bottom-color: rgba(139, 92, 246, 0.35); }

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
      width: 100%;
      max-width: 100%;
      min-width: 0;
      overflow-x: hidden;
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
      overflow-wrap: anywhere !important;
      max-width: 100%;
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
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 5px;
      margin-top: 6px;
      width: 100%;
    }
    .matrix-grid > div {
      min-width: 0;
      overflow-wrap: break-word;
    }

    .btn-copy {
      width: 100%;
      padding: 12px 12px;
      min-height: 44px;
      background: #0f766e;
      color: #ffffff;
      border: 1px solid #2dd4bf;
      border-radius: 6px;
      font-family: inherit;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.4px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      margin: 6px 0 8px 0;
      box-shadow: 0 4px 14px rgba(20, 184, 166, 0.25);
    }
    .btn-copy:active { opacity: 0.9; }
    .btn-copy.copied {
      background: #16a34a !important;
      border-color: #4ade80 !important;
      color: #ffffff !important;
    }

    .wb-box {
      background: #0b0e14;
      border: 1px dashed rgba(45, 212, 191, 0.45);
      border-radius: 6px;
      padding: 7px 8px;
      margin: 6px 0 8px 0;
      width: 100%;
      max-width: 100%;
      overflow: hidden;
    }
    .wb-summary {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      font-size: 9.5px;
      font-weight: 800;
      color: #38bdf8;
      cursor: pointer;
      user-select: none;
      list-style: none;
    }
    .wb-summary::-webkit-details-marker { display: none; }
    .wb-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      margin-top: 6px;
      width: 100%;
    }
    .wb-grid > div {
      min-width: 0;
    }
    .wb-lbl {
      display: block;
      font-size: 9px;
      font-weight: 800;
      color: #99f6e4;
      margin-bottom: 3px;
      text-transform: uppercase;
    }
    .wb-input {
      width: 100%;
      min-width: 0;
      max-width: 100%;
      box-sizing: border-box;
      padding: 7px 6px;
      min-height: 36px;
      border-radius: 5px;
      border: 1px solid rgba(113, 113, 122, 0.6);
      background: #11131a;
      color: #f4f4f5;
      font-family: inherit;
      font-size: 11px;
    }
    .wb-input:focus {
      outline: none;
      border-color: #2dd4bf;
    }
    .wb-foot {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-top: 6px;
      font-size: 9.5px;
      color: #94a3b8;
    }
    .wb-clear {
      padding: 4px 8px;
      min-height: 28px;
      border-radius: 4px;
      border: 1px solid rgba(113, 113, 122, 0.55);
      background: #18181b;
      color: #e4e4e7;
      font-family: inherit;
      font-size: 9.5px;
      font-weight: 700;
      cursor: pointer;
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
      max-width: 100%;
      white-space: pre-wrap !important;
      word-break: break-word !important;
      overflow-wrap: anywhere !important;
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
          <div class="header-line-1">BTC MAGNET MONITOR :: DIBSE ENGINE</div>
          <div class="header-line-2">Dual-Inventory Bidirectional Spot Terminal</div>
        </div>
      </div>
      <div class="header-meta-sep">
        MANDATE: DIBSE (10% USDT + 10% BTC | ZERO STOPS)<br>
        SESSION: <span class="c-green" id="hdr-session">ACTIVE</span> &bull; CADENCE: EVERY 30M (:02/:32)<br>
        SCAN: <span class="c-cyan" id="hdr-scan-ts">__TIME_UTC__</span> &bull; NEXT: <span class="c-amber" id="hdr-next-upd">--:-- UTC</span> (<span class="c-green" id="hdr-countdown">in --m --s</span>)
      </div>
      <div style="display:none;" aria-hidden="true">5-Regime Radar Observable Positioning Mechanics</div>
    </header>

    <!-- STALE TELEMETRY BANNER (>30M TARGET) -->
    <div class="stale-banner" id="static-stale-banner" style="__STATIC_STALE_STYLE__">
      ⚠️ [WARNING: TELEMETRY STALE &gt;30M] &bull; Past 30m target + CI grace. Live spot REST feed active below.
      <div style="margin-top: 6px;">
        <button type="button" onclick="refreshLiveScan(true)" style="background:#1c1917;border:1px solid #f59e0b;color:#fde68a;font-family:inherit;font-size:10px;font-weight:700;padding:4px 10px;border-radius:4px;cursor:pointer;">↻ CHECK NOW</button>
      </div>
    </div>
    <div class="stale-banner" id="dyn-stale-banner" style="display: none;">
      ⚠️ [WARNING: TELEMETRY STALE &gt;30M] &bull; Past 30m target + CI grace. Live spot REST feed active below.
      <div style="margin-top: 6px;">
        <button type="button" onclick="refreshLiveScan(true)" style="background:#1c1917;border:1px solid #f59e0b;color:#fde68a;font-family:inherit;font-size:10px;font-weight:700;padding:4px 10px;border-radius:4px;cursor:pointer;">↻ CHECK NOW</button>
      </div>
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
Updates: <span class="c-cyan">Every 30 Minutes</span> (:02 &amp; :32 UTC target; CI best-effort)
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
          <pre class="ascii"><span class="c-cyan">Feed 1 &bull; Closed-4H Structure &amp; VWAP:</span>
Spot Price:     $__PRICE__
Daily VWAP:     __D_VWAP_DISP__
Weekly VWAP:    __W_VWAP_DISP__
4H Swing L/H:   __SW_LH_DISP__
4H Range Width: __RANGE_WIDTH__%
Floor / Ceil:   __CEIL_FLOOR_DISP__
Closed Cutoff:  __CLOSED_4H_CUTOFF__</pre>
        </div>

        <div class="sub-card sub-card-emerald">
          <pre class="ascii"><span class="c-green">Feed 2 &bull; Spot CVD &amp; Order Book:</span>
24h Spot Vol:   __SPOT_VOL_DISP__
Spot CVD Ratio: __SPOT_CVD_DISP__
7D / 14D Slope: __SPOT_CVD_7D__ / __SPOT_CVD_14D__
Perp CVD Trend: __PERP_TREND__ (__PERP_SLOPE__)
Book Depth:     __DEPTH_RATIO__ (Bids/Asks)</pre>
        </div>

        <div class="sub-card sub-card-amber">
          <pre class="ascii"><span class="c-amber">Feed 3 &bull; Derivatives Positioning:</span>
Open Interest:  __OI_DISP__
OI 24h Delta:   __OI_24H__
OI 1h / 4h:     __OI_1H_4H__
OI 3D Delta:    __OI_3D__
Funding (8h/A): __FUNDING__% / __FUNDING_ANN__%
Futures Basis:  __BASIS__% (Ann.)
L/S Ratio:      __LS_RATIO_DISP__</pre>
        </div>

        <div class="sub-card sub-card-purple" style="margin-bottom: 2px;">
          <pre class="ascii"><span class="c-purple">Feed 4 &bull; Channel Swings &amp; Wicks:</span>
24h Wicks L/H:  __WICKS_24H__
Wick Span (24h):__WICK_SPAN__
Book Liquidity: __DEPTH_RATIO__ (Bids/Asks)
Indicators:     Zero MA/EMA/RSI/ATR</pre>
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
<span id="p3-conf-fresh" class="c-muted">Freshness: Verified &le;40m Window</span></pre>
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

      <!-- BRIDGE: HOW TO GET YOUR VERDICT (METHOD 1 VS METHOD 2) -->
      <div id="verdict-guide" class="panel-box panel-box-violet">
        <div class="panel-hdr">Bridge &bull; How to Get Your Trading Verdict</div>

        <div class="sub-card sub-card-indigo">
          <pre class="ascii"><span class="c-indigo">Panels 1-3 = Observable Facts Only.</span>
Compare Method 1 (Blind AI Prompt) against
Method 2 (Built-In DIBSE Engine) below:</pre>
        </div>

        <div class="sub-card sub-card-sky">
          <pre class="ascii"><span class="c-cyan">Method 1 &bull; Independent AI (Zero Bias)</span>
1. Optional: enter Loop A Buy / Loop B Sale
   watermarks (saved locally on device).
2. Tap the single <span class="c-green">COPY BLIND TELEMETRY</span> button
   and paste into ChatGPT, Claude, or Gemini.</pre>
          <a href="#method-1" style="display:inline-block;margin-top:4px;font-size:10.5px;font-weight:800;color:#38bdf8;text-decoration:none;">&darr; Go to Method 1</a>
        </div>

        <div class="sub-card sub-card-purple" style="margin-bottom: 2px;">
          <pre class="ascii"><span class="c-purple">Method 2 &bull; Built-In DIBSE Verdict</span>
1. View Loop A (USDT&rarr;BTC) &amp; Loop B (BTC&rarr;USDT)
   trigger zones, LSCE side, &amp; self-healing rule.
2. Zero leverage. Zero forced stop-losses.
Tip: Highest conviction when Method 1
(Blind AI) and Method 2 align.</pre>
          <a href="#method-2" style="display:inline-block;margin-top:4px;font-size:10.5px;font-weight:800;color:#c084fc;text-decoration:none;">&darr; Jump to Method 2</a>
        </div>
      </div>

      <!-- METHOD 1: ONE CLEAN COPY BUTTON (UPGRADED BLIND TELEMETRY) -->
      <div id="method-1" class="panel-box panel-box-sky">
        <div class="panel-hdr">Method 1 &bull; Copy Blind Telemetry to AI</div>

        <div class="sub-card sub-card-teal" style="margin-bottom: 2px;">
          <pre class="ascii"><span class="c-cyan">Unbiased Blind Telemetry + 5-Regime Audit:</span>
Closed-4H facts, 5-Regime rules, &amp; Risk
Officer checklist. Zero verdict leaked.</pre>

          <button class="btn-copy" id="copy-blind-btn" onclick="copyBlindPrompt()">
            🧪 COPY TELEMETRY FOR AI
          </button>

          <details class="wb-box" id="wb-details">
            <summary class="wb-summary">
              <span>▸ Optional: P_buy / P_sell (Local)</span>
              <span id="wb-status" style="color:#94a3b8;font-weight:600;">None</span>
            </summary>
            <div class="wb-grid">
              <div>
                <label class="wb-lbl" for="wb-buy">Loop A Cost ($P_buy)</label>
                <input class="wb-input" id="wb-buy" type="number" step="0.01" min="0" inputmode="decimal" placeholder="e.g. 71200">
              </div>
              <div>
                <label class="wb-lbl" for="wb-sell">Loop B Sale ($P_sell)</label>
                <input class="wb-input" id="wb-sell" type="number" step="0.01" min="0" inputmode="decimal" placeholder="e.g. 76500">
              </div>
            </div>
            <div class="wb-foot">
              <span>Saved only in browser localStorage</span>
              <button type="button" class="wb-clear" id="wb-clear">Clear</button>
            </div>
          </details>

          <pre class="ascii">[Blind Telemetry Prompt (<span id="blind-char-count">__BLIND_LEN__</span> chars)]</pre>
          <pre class="prompt-box" id="prompt-box-pre">__BLIND_PROMPT_HTML__</pre>
        </div>
      </div>

      <!-- METHOD 2: OUR SYSTEM VERDICT (FULL-ON VIEW) -->
      <div id="method-2" class="panel-box panel-box-purple">
        <div class="panel-hdr">Method 2 &bull; Built-In DIBSE Verdict</div>

        <div id="method2-ai-reminder" class="sub-card sub-card-sky">
          <pre class="ascii"><span class="c-cyan">Always Use Method 1 AI &amp; Compare:</span>
Method 2 is a fixed rule baseline only.
Copy <span class="c-green">Method 1</span> into your AI for deeper
context &amp; higher-accuracy DIBSE calls.</pre>
          <a href="#method-1" style="display:inline-block;margin-top:4px;font-size:10px;font-weight:800;color:#38bdf8;text-decoration:none;">&uarr; Go to Method 1 (Copy to AI)</a>
        </div>

        <div class="sub-card sub-card-emerald">
          <pre class="ascii">DIBSE Signal: <span class="c-cyan" style="font-weight:800;">__DIBSE_SIGNAL__</span>
Action Headline:
<span class="c-gold">__DIBSE_HEADLINE__</span>

Dominant Magnet:
<span class="c-rose">__DOM_REASON__</span>

Plain English Bottom Line:
💡 "__PLAIN_VERDICT__"

The 3 Key Empirical Drivers:
__WHY_1__
__WHY_2__
__WHY_3__</pre>
        </div>

        <div class="sub-card sub-card-amber">
          <pre class="ascii"><span class="c-amber">Dual-Sleeve Bidirectional Playbook:</span>
Allocation: <span class="c-green">__SLEEVE_ALLOC__</span>

Loop A (USDT &rarr; BTC &bull; Buy Support):
__LOOP_A_ZONE__

Loop B (BTC &rarr; USDT &bull; Sell Resistance):
__LOOP_B_ZONE__

Sizing Note:
__WHY_SIZING__
__RISK_SUMMARY__</pre>
        </div>

        <div class="sub-card sub-card-rose">
          <pre class="ascii"><span class="c-rose">Asymmetric Self-Healing Protocol:</span>
__FAILURE_PROTOCOL__</pre>
        </div>

        <div class="sub-card __LSCE_CARD_CLS__">
          <pre class="ascii"><span class="c-amber">LSCE Bidirectional State Machine:</span>
Side:   __LSCE_SIDE__
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
6. 4H Width Comp:
__F6_COMP__
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
        Scan ID: <span class="c-cyan">__SCAN_ID__</span> &bull; Updates Every 30m (:02/:32 UTC)<br>
        __SPOT_SOURCE__ &bull; __FUTURES_SOURCE__<br>
        Strictly for informational and risk research purposes. Not financial advice.
      </div>
    </footer>

  </div>

  <!-- Toast Notification -->
  <div id="toast">✓ Copied to Clipboard!</div>

  <script id="text-live-payload" type="application/json">_TEXT_LIVE_PAYLOAD_JSON_</script>

  <script>
    let SCAN_PRICE = __PRICE_RAW__;
    let SCAN_TS = '__SCAN_TS__';
    let BLIND_PROMPT_BASE = _BLIND_PROMPT_JSON_;
    let BLIND_PROMPT_TEXT = BLIND_PROMPT_BASE;

    const WB_KEY_BUY = 'dibse_wb_buy';
    const WB_KEY_SELL = 'dibse_wb_sell';

    function lsGetSafe(k) {
      try { return (window.localStorage && localStorage.getItem(k)) || ''; } catch (e) { return ''; }
    }
    function lsSetSafe(k, v) {
      try {
        if (!window.localStorage) return;
        if (v) localStorage.setItem(k, v);
        else localStorage.removeItem(k);
      } catch (e) {}
    }

    function buildWatermarksLine(buyRaw, sellRaw) {
      const b = parseFloat(buyRaw);
      const s = parseFloat(sellRaw);
      const parts = [];
      if (!isNaN(b) && b > 0) parts.push('Loop A BTC Entry Watermark P_buy = $' + b.toLocaleString('en-US', {maximumFractionDigits: 2}) + ' (sell target P_exit > P_buy; otherwise self-heal hold)');
      if (!isNaN(s) && s > 0) parts.push('Loop B BTC Sale Watermark P_sell = $' + s.toLocaleString('en-US', {maximumFractionDigits: 2}) + ' (rebuy target P_rebuy < P_sell; otherwise hold USDT)');
      return parts.join(' | ');
    }

    function syncWatermarksToDom(loadFromStorage) {
      const buyEl = document.getElementById('wb-buy');
      const sellEl = document.getElementById('wb-sell');
      const preEl = document.getElementById('prompt-box-pre');
      const cntEl = document.getElementById('blind-char-count');
      const stEl = document.getElementById('wb-status');
      if (loadFromStorage) {
        if (buyEl) buyEl.value = lsGetSafe(WB_KEY_BUY);
        if (sellEl) sellEl.value = lsGetSafe(WB_KEY_SELL);
      }
      const buyVal = buyEl ? buyEl.value.trim() : lsGetSafe(WB_KEY_BUY);
      const sellVal = sellEl ? sellEl.value.trim() : lsGetSafe(WB_KEY_SELL);
      const customLine = buildWatermarksLine(buyVal, sellVal);
      BLIND_PROMPT_TEXT = customLine
        ? BLIND_PROMPT_BASE.replace(/^\[ACTIVE INVENTORY WATERMARKS\]:.*$/m, '[ACTIVE INVENTORY WATERMARKS]: ' + customLine)
        : BLIND_PROMPT_BASE;
      if (preEl) preEl.textContent = BLIND_PROMPT_TEXT;
      if (cntEl) cntEl.textContent = String(BLIND_PROMPT_TEXT.length);
      if (stEl) {
        const flags = [];
        if (buyVal && !isNaN(parseFloat(buyVal)) && parseFloat(buyVal) > 0) flags.push('P_buy=$' + parseFloat(buyVal).toLocaleString('en-US'));
        if (sellVal && !isNaN(parseFloat(sellVal)) && parseFloat(sellVal) > 0) flags.push('P_sell=$' + parseFloat(sellVal).toLocaleString('en-US'));
        stEl.textContent = flags.length ? flags.join(' • ') : 'None';
        stEl.style.color = flags.length ? '#34d399' : '#94a3b8';
      }
    }

    document.addEventListener('input', function (e) {
      const t = e.target;
      if (!t || (t.id !== 'wb-buy' && t.id !== 'wb-sell')) return;
      if (t.id === 'wb-buy') lsSetSafe(WB_KEY_BUY, t.value.trim());
      if (t.id === 'wb-sell') lsSetSafe(WB_KEY_SELL, t.value.trim());
      syncWatermarksToDom(false);
    });
    document.addEventListener('click', function (e) {
      const btn = e.target && e.target.closest ? e.target.closest('#wb-clear') : null;
      if (!btn) return;
      lsSetSafe(WB_KEY_BUY, '');
      lsSetSafe(WB_KEY_SELL, '');
      const buyEl = document.getElementById('wb-buy');
      const sellEl = document.getElementById('wb-sell');
      if (buyEl) buyEl.value = '';
      if (sellEl) sellEl.value = '';
      syncWatermarksToDom(false);
      showToast('✓ Local watermarks cleared');
    });

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

    function copyBlindPrompt() {
      syncWatermarksToDom(false);
      copyTextPayload(BLIND_PROMPT_TEXT, '✓ Copied DIBSE Blind Telemetry!', 'copy-blind-btn');
    }
    syncWatermarksToDom(true);

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

    let scanMs = Date.parse(SCAN_TS);

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

      // Next scheduled :02 / :32 UTC scan window & countdown
      const nextTarget = new Date(utcMs);
      nextTarget.setUTCSeconds(0, 0);
      if (now.getUTCMinutes() < 2) {
        nextTarget.setUTCMinutes(2);
      } else if (now.getUTCMinutes() < 32) {
        nextTarget.setUTCMinutes(32);
      } else {
        nextTarget.setUTCMinutes(2);
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
      const overdue = !isNaN(scanMs) && ((utcMs - scanMs) > 40 * 60 * 1000);
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

    // Dynamic Stale Telemetry (>40m grace allowing staggered CI backup slots) & Live Scan Auto-Refresh
    function renderTextStaleState() {
      const staticBanner = document.getElementById('static-stale-banner');
      const dynBanner = document.getElementById('dyn-stale-banner');
      const confFresh = document.getElementById('p3-conf-fresh');
      const ageMs = !isNaN(scanMs) ? (Date.now() - scanMs) : NaN;
      const isStale = !isNaN(ageMs) && ageMs > 40 * 60 * 1000;
      if (staticBanner) {
        staticBanner.style.display = isStale ? 'block' : 'none';
      }
      if (dynBanner) {
        dynBanner.style.display = isStale && (!staticBanner || staticBanner.style.display === 'none') ? 'block' : 'none';
      }
      if (confFresh) {
        if (isStale) {
          const ageM = Math.max(0, Math.floor(ageMs / 60000));
          confFresh.className = 'c-amber';
          confFresh.innerText = `⚠ Confidence Downgraded: Scan ${ageM}m old (>40m)`;
        } else {
          confFresh.className = 'c-muted';
          confFresh.innerText = 'Freshness: Verified ≤40m Window';
        }
      }
    }
    renderTextStaleState();
    setInterval(renderTextStaleState, 30000);

    function sanitizeTextNode(root) {
      root.querySelectorAll('script, iframe, object, embed, link, meta, base, form').forEach(function (n) { n.remove(); });
      const allowedClicks = new Set([
        "copyBlindPrompt()",
        "refreshLiveScan(true)"
      ]);
      root.querySelectorAll('*').forEach(function (n) {
        Array.from(n.attributes).forEach(function (a) {
          const name = a.name.toLowerCase();
          const val = (a.value || '').trim().toLowerCase();
          const rawVal = (a.value || '').trim();
          if (name.indexOf('on') === 0 && !(name === 'onclick' && allowedClicks.has(rawVal))) {
            n.removeAttribute(a.name);
          } else if ((name === 'href' || name === 'src' || name === 'xlink:href') && val.indexOf('javascript:') === 0) {
            n.removeAttribute(a.name);
          }
        });
      });
    }

    async function refreshLiveScan(manual) {
      if (document.hidden && !manual) return;
      let updated = false;
      try {
        const res = await fetch('./regime.json?t=' + Date.now(), { cache: 'no-store' });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        const liveTs = Date.parse(data && data.timestamp);
        if (!isNaN(liveTs) && liveTs > scanMs) {
          const hres = await fetch('./text.html?t=' + Date.now(), { cache: 'no-store' });
          if (hres.ok) {
            const doc = new DOMParser().parseFromString(await hres.text(), 'text/html');
            const payloadNode = doc.getElementById('text-live-payload');
            const newWrapper = doc.querySelector('.terminal-wrapper');
            const curWrapper = document.querySelector('.terminal-wrapper');
            if (payloadNode && newWrapper && curWrapper) {
              const payload = JSON.parse(payloadNode.textContent || '{}');
              const parsedNewTs = Date.parse(payload.scan_ts || '');
              if (!isNaN(parsedNewTs) && parsedNewTs > scanMs) {
                sanitizeTextNode(newWrapper);
                curWrapper.innerHTML = newWrapper.innerHTML;
                SCAN_TS = payload.scan_ts;
                scanMs = parsedNewTs;
                const livePx = Number(payload.scan_price);
                if (livePx > 0) SCAN_PRICE = livePx;
                if (typeof payload.blind_prompt_text === 'string') {
                  BLIND_PROMPT_BASE = payload.blind_prompt_text;
                  syncWatermarksToDom(true);
                }
                updateClocks();
                updateLivePrice();
                updated = true;
                showToast('✓ Live Scan Telemetry Updated');
              }
            }
          }
        }
        if (manual && !updated) {
          showToast('Checked — awaiting next CI scan');
        }
      } catch (e) {
        if (manual) showToast('⚠ Check failed — offline or rate limited');
      }
      renderTextStaleState();
    }
    setInterval(function () { refreshLiveScan(false); }, 60000);
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) { refreshLiveScan(false); updateLivePrice(); }
    });
    refreshLiveScan(false);

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
        html = html.replace("__REGIME_CSS_CLS__", regime_css_cls)
        html = html.replace("__REGIME_TXT_CLS__", regime_txt_cls)
        html = html.replace("__REGIME_MATRIX_HTML__", regime_matrix_html)
        html = html.replace("__LSCE_CARD_CLS__", lsce_card_cls)
        html = html.replace("__REGIME_NAME__", regime_name)
        html = html.replace("__DIAGNOSIS__", diagnosis)
        html = html.replace("__TAGLINE__", tagline)
        html = html.replace("__RULE_SCORE__", rule_score)
        html = html.replace("__MATCHED_CRITERIA_ASCII__", matched_crit_ascii)
        html = html.replace("__DIBSE_SIGNAL__", dibse_signal)
        html = html.replace("__DIBSE_HEADLINE__", dibse_headline)
        html = html.replace("__SLEEVE_ALLOC__", sleeve_alloc)
        html = html.replace("__LOOP_A_ZONE__", loop_a_zone)
        html = html.replace("__LOOP_B_ZONE__", loop_b_zone)
        html = html.replace("__FAILURE_PROTOCOL__", failure_protocol)
        html = html.replace("__LSCE_SIDE__", lsce_side)
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

        html = html.replace("__D_VWAP_DISP__", d_vwap_disp)
        html = html.replace("__W_VWAP_DISP__", w_vwap_disp)
        html = html.replace("__SW_LH_DISP__", sw_lh_disp)
        html = html.replace("__RANGE_WIDTH__", f"{ch_width:.2f}")
        html = html.replace("__CEIL_FLOOR_DISP__", ceil_floor_disp)
        html = html.replace("__CLOSED_4H_CUTOFF__", closed_4h_cutoff[:22])
        html = html.replace("__WICKS_24H__", wicks_disp)
        html = html.replace("__WICK_SPAN__", wick_span_disp)

        html = html.replace("__SPOT_VOL_DISP__", spot_vol_disp)
        html = html.replace("__SPOT_CVD_DISP__", cvd_disp)
        html = html.replace("__SPOT_CVD_7D__", f"{cvd_7d:+.0f}")
        html = html.replace("__SPOT_CVD_14D__", f"{cvd_14d:+.0f}")
        html = html.replace("__PERP_TREND__", perp_trend)
        html = html.replace("__PERP_SLOPE__", f"{perp_slope:+.0f}")
        html = html.replace("__DEPTH_RATIO__", f"{depth:.2f}")

        html = html.replace("__OI_DISP__", oi_disp)
        html = html.replace("__OI_24H__", oi_24h_disp)
        html = html.replace("__OI_1H_4H__", oi_1h_4h_disp)
        html = html.replace("__OI_3D__", oi_3d_disp)
        html = html.replace("__FUNDING__", f"{funding:.4f}")
        html = html.replace("__FUNDING_ANN__", f"{funding_ann:+.2f}")
        html = html.replace("__BASIS__", f"{basis:+.2f}")

        live_payload_json = _json.dumps({
            "scan_ts": ts_iso,
            "scan_price": round(float(price), 2),
            "blind_prompt_text": blind_prompt,
        }).replace("</", "<\\/")

        blind_prompt_html = (
            blind_prompt.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        html = html.replace("__BLIND_LEN__", f"{len(blind_prompt)}")
        html = html.replace("__BLIND_PROMPT_HTML__", blind_prompt_html)
        html = html.replace("_TEXT_LIVE_PAYLOAD_JSON_", live_payload_json)
        html = html.replace("_BLIND_PROMPT_JSON_", _json.dumps(blind_prompt).replace("</", "<\\/"))
        html = html.replace("__STATIC_STALE_STYLE__", "display: block;" if is_stale_telemetry else "display: none;")

        html = html.replace("__PLAIN_VERDICT__", plain_verdict)
        html = html.replace("__WHY_1__", why_1)
        html = html.replace("__WHY_2__", why_2)
        html = html.replace("__WHY_3__", why_3)
        html = html.replace("__WHY_SIZING__", why_sizing)

        html = html.replace("__F1_SIZE__", f1_size)
        html = html.replace("__F2_LEADERSHIP__", f2_lead)
        html = html.replace("__F3_CROWDING__", f3_crowd)
        html = html.replace("__F4_STRUCTURE__", f4_struct)
        html = html.replace("__F5_ASYMMETRY__", f5_asym)
        html = html.replace("__F6_COMP__", f6_comp)
        html = html.replace("__DOM_REASON__", dom_reason)

        html = html.replace("__TIME_UTC__", utc_time_str)
        html = html.replace("__TIME_SGT__", sgt_time_str)
        html = html.replace("__DATE_UTC__", date_str)

        return html
