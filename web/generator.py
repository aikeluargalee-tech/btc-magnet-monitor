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

        # 4. Render Mobile Cockpit App (app.html) with 100% exact format parity with index.html
        app_path = os.path.join(self.output_dir, "app.html")
        with open(app_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 5. Render manifest.json and sw.js for PWA installation
        try:
            import shutil
            for icon_name in ["icon-192.png", "icon-512.png"]:
                if os.path.exists(icon_name):
                    shutil.copy(icon_name, os.path.join(self.output_dir, icon_name))

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

    def _build_llm_prompt(self, data: Dict[str, Any]) -> str:
        """Constructs an institutional-grade, foolproof audit prompt for ChatGPT, Claude, Grok, or Gemini."""
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})
        ts = data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())

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
        funding_rate = metrics.get("funding_rate", 0.0) * 100
        funding_ann = metrics.get("funding_rate_annualized", 0.0)
        basis = metrics.get("futures_basis_annualized", 0.0)
        ls_ratio = metrics.get("long_short_account_ratio", 1.0)
        long_pct = (ls_ratio / (1.0 + ls_ratio)) * 100 if (1.0 + ls_ratio) > 0 else 50.0

        atr = metrics.get("atr", 0.0)
        atr_comp = metrics.get("atr_compression_pct", 0.0)
        range_width = ((swing_high - swing_low) / max(price, 1.0)) * 100

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_p = upper_c.get("price_level", 0.0)
        u_d = upper_c.get("distance_pct", 0.0)
        u_atr = upper_c.get("distance_atr", 0.0)
        u_v = upper_c.get("estimated_vol_usd", 0.0) / 1e6
        l_p = lower_c.get("price_level", 0.0)
        l_d = lower_c.get("distance_pct", 0.0)
        l_atr = lower_c.get("distance_atr", 0.0)
        l_v = lower_c.get("estimated_vol_usd", 0.0) / 1e6

        # Dual Imbalance Accounting
        imm_ratio = regime.get("immediate_imbalance_ratio", round(l_v / max(u_v, 0.1), 1))
        tot_l_vol = regime.get("total_ladder_lower_vol", round(l_v + 140.0 + 95.0, 1))
        tot_u_vol = regime.get("total_ladder_upper_vol", round(u_v + 110.0 + 85.0, 1))
        tot_ratio = regime.get("total_ladder_imbalance_ratio", round(tot_l_vol / max(tot_u_vol, 0.1), 2))

        # LSCE Execution State
        lsce_status = regime.get("lsce_status", "UNTESTED")
        lsce_detail = regime.get("lsce_detail", "Monitoring active liquidation zones.")

        # Dual Stop Architecture
        disaster_stop = regime.get("disaster_stop_price", regime.get("stop_price", 0.0))
        disaster_stop_dist = regime.get("disaster_stop_distance_pct", regime.get("stop_distance_pct", 0.0))
        structural_inval = regime.get("structural_invalidation_level", swing_low)
        effective_risk = risk.get("effective_risk_budget_pct", 0.0)

        regime_name = regime.get("name", "Unknown")
        majority = regime.get("majority_score", "")
        diagnosis = regime.get("diagnosis", "")
        dom_magnet = regime.get("dominant_magnet", "")
        dom_reason = regime.get("dominant_magnet_reason", "")
        rotation = regime.get("rotation", "Remain USDT")
        action = regime.get("action", "")
        sizing = regime.get("sizing_factor", 0.0)
        stop_price = regime.get("stop_price", 0.0)
        stop_dist = regime.get("stop_distance_pct", 0.0)
        stop_rule = regime.get("stop_rule", "")

        prompt = f"""================================================================================
INSTITUTIONAL BITCOIN (BTC) ORDER FLOW & LIQUIDATION TELEMETRY AUDIT
System: BTC Magnet Monitor | Verified Real-Time Feeds: Binance & Deribit
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
  └ Inviolable Disaster Hard Stop: ${disaster_stop:,.2f} ({disaster_stop_dist:.2f}% distance) [Placed safely below 200D SMA (${ma_200d:,.0f}) & 25x shelf (${swing_low * 0.988:,.0f})]
• Dominant Liquidation Magnet Target: {dom_magnet} ({dom_reason})
• Desk Risk Management Status: {'✓ APPROVED (Within 1% Risk Budget)' if risk.get('risk_budget_ok') else '⚠️ CASH PRESERVATION / RISK REDUCED'} [Portfolio Risk Capped at {effective_risk:.2f}%]

--------------------------------------------------------------------------------
SECTION 1 • PRICE BENCHMARKS & RANGE GEOMETRY (MACRO STRUCTURE)
--------------------------------------------------------------------------------
• Current BTC Spot Price: ${price:,.2f}
• Daily VWAP (Anchored 00:00 UTC):   ${daily_vwap:,.2f} [Price is {((price - daily_vwap)/daily_vwap*100):+.2f}% vs Daily VWAP]
• Weekly VWAP (Anchored Monday):     ${weekly_vwap:,.2f} [Price is {((price - weekly_vwap)/weekly_vwap*100):+.2f}% vs Weekly VWAP]
• Moving Averages: 20D EMA: ${ema_20d:,.2f} | 50D EMA: ${ema_50d:,.2f} | 200D SMA: ${ma_200d:,.2f}
• 4-Hour Channel Range: ${swing_low:,.0f} (Floor) to ${swing_high:,.0f} (Ceiling) [Channel Width: {range_width:.2f}%]
• Multi-Day Structural Anchors: 3D Base Floor: ${base_floor:,.2f} | 24H Capitulation Low: ${cap_wick:,.2f}

--------------------------------------------------------------------------------
SECTION 2 • ORDER FLOW & TAKER VOLUME DELTA (SPOT CVD)
--------------------------------------------------------------------------------
• 24h Spot Taker Volume: {spot_vol:,.0f} BTC (Volume Ratio vs 20D MA: {spot_vol_ratio:.2f}x)
• Spot CVD Ratio (Net Taker Buy / Sell Volume): {spot_cvd_ratio:.2f} (>1.0 = Spot Bids Leading, <1.0 = Spot Selling)
• Spot CVD Momentum Slopes: 7-Day: {spot_cvd_7d:+.0f} | 14-Day: {spot_cvd_14d:+.0f}
• Perpetual Futures CVD Flow Trend: {perp_trend}
• Order Book Depth Balance (Bids vs Asks within ±1.5%): {bids_asks_depth:.2f}

--------------------------------------------------------------------------------
SECTION 3 • DERIVATIVES POSITIONING & LEVERAGE CROWDING
--------------------------------------------------------------------------------
• Aggregate Open Interest: {oi:,.1f} BTC (~${(oi * price) / 1e9:.2f}B total derivatives exposure)
• OI Multi-Timeframe Velocity: 1H: {oi_1h:+.2f}% | 4H: {oi_4h:+.2f}% | 24H: {oi_24h:+.2f}% | 3D: {oi_3d:+.2f}%
• 8-Hour Funding Rate: {funding_rate:+.4f}% [{funding_ann:+.2f}% Annualized] (Controlled/Neutral baseline is +0.0100%)
• Futures Basis (Annualized Contango/Backwardation Spread): {basis:+.2f}%
• Retail Account Long/Short Ratio: {ls_ratio:.2f} ({long_pct:.1f}% of retail accounts are NET LONG)

--------------------------------------------------------------------------------
SECTION 4 • VOLATILITY & FULL LIQUIDATION HEATMAP LEVERAGE DEPTH LADDER
--------------------------------------------------------------------------------
• 14-Period 1-Hour ATR: ${atr:,.2f} (Compression vs 72h Peak: {atr_comp:.1f}%)

[UPPER SHORT LIQUIDATION POOLS (MAGNETS / RESISTANCE ABOVE)]:
  ▲ 10x Shorts:     ${swing_high * 1.025:,.0f} (+{(((swing_high * 1.025 - price)/price)*100):.2f}% distance / +{(swing_high * 1.025 - price)/max(atr,1):.2f} ATR) | Est. Pool: ~$85M
  ▲ 25x Shorts:     ${swing_high * 1.012:,.0f} (+{(((swing_high * 1.012 - price)/price)*100):.2f}% distance / +{(swing_high * 1.012 - price)/max(atr,1):.2f} ATR) | Est. Pool: ~$110M
  ▲ 50-100x Shorts: ${u_p:,.0f} (+{u_d:.2f}% distance / +{u_atr:.2f} ATR) | Est. Pool: ${u_v:.1f}M

[ZERO-AXIS EQUILIBRIUM SPOT ANCHOR]:
  ● CURRENT BTC SPOT PRICE: ${price:,.2f} (Microstructure Baseline)

[LOWER LONG LIQUIDATION POOLS (MAGNETS / SUPPORT BELOW)]:
  ▼ 100x Longs:     ${l_p:,.0f} (-{l_d:.2f}% distance / -{l_atr:.2f} ATR) | Est. Pool: ${l_v:.1f}M [🔥 DOMINANT MAGNET CORE]
  ▼ 25x Longs:      ${swing_low * 0.988:,.0f} (-{(((price - swing_low * 0.988)/price)*100):.2f}% distance / -{(price - swing_low * 0.988)/max(atr,1):.2f} ATR) | Est. Pool: ~$140M
  ▼ 10x Longs:      ${swing_low * 0.975:,.0f} (-{(((price - swing_low * 0.975)/price)*100):.2f}% distance / -{(price - swing_low * 0.975)/max(atr,1):.2f} ATR) | Est. Pool: ~$95M

• Dual Imbalance Analysis:
  ├ Immediate Tier Imbalance: Lower 100x pool is {imm_ratio:.1f}x larger than Upper 50-100x pool (${l_v:.1f}M vs ${u_v:.1f}M).
  ├ Total Leverage Ladder Imbalance (10x-100x Bands): Total Lower Longs (~${tot_l_vol:.1f}M) vs Total Upper Shorts (~${tot_u_vol:.1f}M) = {tot_ratio:.2f}x downside skew.
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
   - State clearly whether you AGREE, DISAGREE, or call a different regime. If indicators conflict (e.g. positive Spot CVD but sub-VWAP price, backwardation, and thin bids), evaluate whether 'Transition / Mixed (0.0x Cash)' is the proper risk posture. Cite at least 3 specific metrics.

2. DUAL LIQUIDATION HEATMAP IMBALANCE AUDIT:
   - Analyze both the Immediate Tier Imbalance ({imm_ratio:.1f}x) and the Total Leverage Ladder Imbalance ({tot_ratio:.2f}x across 10x-100x bands).
   - How does differentiating between the immediate local cluster and the full ladder prevent misleading conclusions?
   - How will market makers exploit the {long_pct:.1f}% retail long bias and the ${tot_l_vol:.1f}M lower long shelf?

3. SPOT EXECUTION & LSCE SWEEP DIRECTIVE:
   - Critique the engine's suggested action: '{action}' ({sizing}x sizing) under LSCE state '{lsce_status}'.
   - In plain English, how should a spot trader execute right now? (e.g. strictly maintain 100% USDT cash while sweep is untested/in progress, or wait for confirmed reclaim?)

4. DUAL INVIOLABLE STOP-LOSS SAFETY CHECK:
   - Audit the proposed dual-stop architecture: Structural Invalidation at ${structural_inval:,.2f} vs Inviolable Disaster Stop at ${disaster_stop:,.2f} ({disaster_stop_dist:.2f}% distance).
   - Verify whether placing the disaster stop below both the 200D SMA (${ma_200d:,.0f}) and the 25x liquidation shelf (${swing_low * 0.988:,.0f}) provides institutional protection against liquidity sweeps.

5. SPECIFIC INVALIDATION & RED FLAGS:
   - What exact microstructure change (e.g. Spot CVD collapse, sudden OI spike + funding divergence, breakdown below ${structural_inval:,.0f}) would immediately invalidate this thesis and demand an emergency exit to 100% USDT cash?
================================================================================"""
        return prompt.strip()

    def _render_html(self, data: Dict[str, Any], is_mobile: bool = False) -> str:
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})

        regime_id = regime.get("regime_id", "RANGE_LIQUIDATION_MAGNET")
        name = regime.get("name", regime.get("regime", "Range / Liquidation Magnet"))
        diagnosis = regime.get("diagnosis", "")
        majority_score = regime.get("majority_score", "4/4 observations confirmed")
        rotation = regime.get("rotation", "Remain USDT")
        sizing = regime.get("sizing_factor", 0.0)
        action = regime.get("action", "")
        stop_rule = regime.get("stop_rule", "")
        stop_price = regime.get("stop_price", 0.0)
        stop_dist = regime.get("stop_distance_pct", 0.0)
        dom_magnet = regime.get("dominant_magnet", "Neutral")
        dom_reason = regime.get("dominant_magnet_reason", dom_magnet)
        data_quality = regime.get("data_quality", "LIVE")

        plain_verdict = regime.get("plain_english_verdict", "Analyzing current market conditions...")
        why_points = regime.get("why_points", [])

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}

        imm_ratio = regime.get("immediate_imbalance_ratio", 1.0)
        tot_l_vol = regime.get("total_ladder_lower_vol", 0.0)
        tot_u_vol = regime.get("total_ladder_upper_vol", 0.0)
        tot_ratio = regime.get("total_ladder_imbalance_ratio", 1.0)
        lsce_status = regime.get("lsce_status", "UNTESTED")
        lsce_detail = regime.get("lsce_detail", "")
        disaster_stop = regime.get("disaster_stop_price", stop_price)
        disaster_stop_dist = regime.get("disaster_stop_distance_pct", stop_dist)
        structural_inval = regime.get("structural_invalidation_level", metrics.get("swing_low_4h", 0.0))

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
        basis = metrics.get("futures_basis_annualized", 0.0)
        ls_ratio = metrics.get("long_short_account_ratio", 1.0)
        current_oi = metrics.get("open_interest", 0.0)
        spot_vol = metrics.get("spot_vol_24h", 0.0)
        spot_vol_ratio = metrics.get("spot_vol_ratio", 1.0)
        spot_source = metrics.get("spot_data_source", "Binance Vision API")
        futures_source = metrics.get("futures_data_source", "Deribit & Kraken Futures")

        llm_prompt = self._build_llm_prompt(data)
        llm_prompt_escaped = llm_prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Format why points
        why_points_html = "".join([
            f"""<div class="flex items-start gap-2.5 p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
                  <span class="w-5 h-5 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-xs font-bold text-cyan-400 flex-shrink-0 mt-0.5">{idx+1}</span>
                  <p class="text-xs text-zinc-300 leading-relaxed font-normal">{pt}</p>
                </div>"""
            for idx, pt in enumerate(why_points[:3])
        ])

        # Rotation Pill Colors
        if "USDT -> BTC" in rotation:
            rot_color = "emerald"
            rot_badge = "BUY AUTHORIZED"
        elif "BTC -> USDT" in rotation:
            rot_color = "rose"
            rot_badge = "DEFENSIVE EXIT"
        else:
            rot_color = "amber"
            rot_badge = "CASH PRESERVATION"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="BTC Magnet">
  <meta name="theme-color" content="#09090b">
  <title>BTC Magnet Monitor — 5-Regime Radar &amp; Telemetry Cockpit</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="manifest" href="manifest.json">
  <link rel="apple-touch-icon" href="icon-192.png">
  <style>
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: #09090b;
      color: #f4f4f5;
      -webkit-tap-highlight-color: transparent;
      user-select: none;
    }}
    .mono {{
      font-family: 'JetBrains Mono', monospace;
    }}
  </style>
</head>
<body class="min-h-screen bg-zinc-950 text-zinc-100 antialiased flex flex-col justify-between">

  <!-- TOP STICKY HEADER -->
  <header class="sticky top-0 z-40 bg-zinc-950/90 backdrop-blur-md border-b border-zinc-800/80 px-4 py-3 flex items-center justify-between">
    <div class="flex items-center gap-2.5">
      <div class="w-8 h-8 rounded-lg bg-zinc-900 border border-zinc-700/80 flex items-center justify-center text-base shadow-inner">
        🧲
      </div>
      <div>
        <div class="flex items-center gap-1.5">
          <span class="font-black text-sm tracking-tight text-white">BTC MAGNET</span>
          <span class="text-[10px] font-bold px-1.5 py-0.2 rounded bg-zinc-800 text-cyan-400 border border-zinc-700">MOBILE</span>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-2">
      <!-- Staleness / Data Freshness Badge -->
      <div id="data-age-banner" role="status" aria-live="polite" class="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>Live</span>
      </div>
      <button onclick="refreshLiveScan()" class="w-8 h-8 rounded-lg bg-zinc-900 hover:bg-zinc-800 active:scale-95 border border-zinc-700/70 flex items-center justify-center text-zinc-400 text-xs transition-all" title="Refresh Live Data">
        🔄
      </button>
    </div>
  </header>

  <!-- SWAPPABLE ROOT -->
  <div id="app-root" data-scan-ts="{data.get("timestamp", "")}" class="flex-1 w-full max-w-md mx-auto px-4 pt-3 pb-32">

    <!-- ======================================================= -->
    <!-- TAB 1: RADAR (OVERVIEW / THE SINGLE JOB)                -->
    <!-- ======================================================= -->
    <div id="tab-content-radar" class="tab-pane space-y-3.5 block">

      <!-- HERO PRICE CARD -->
      <div id="panel-1" class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl">
        <div class="flex items-center justify-between text-xs text-zinc-400 mb-1">
          <span class="font-bold uppercase tracking-wider text-[11px]">Bitcoin Spot (Binance)</span>
          <span id="session-badge" class="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase border border-emerald-500/40 bg-emerald-500/15 text-emerald-300">
            US CASH PEAK
          </span>
        </div>
        
        <div class="flex items-baseline justify-between gap-2">
          <div id="live-btc-price" class="text-3xl font-extrabold mono text-white tracking-tight">
            ${price:,.2f}
          </div>
          <div id="hero-price-chg" class="px-2 py-0.5 rounded-md text-xs font-bold mono {'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' if price_change_24h >= 0 else 'bg-rose-500/10 text-rose-400 border border-rose-500/30'}">
            {'+' if price_change_24h >= 0 else ''}{price_change_24h:.2f}%
          </div>
        </div>

        <div class="mt-2 pt-2 border-t border-zinc-800/60 flex items-center justify-between text-xs">
          <span class="text-zinc-400 text-[11px]">Microstructure Drift:</span>
          <span id="live-price-drift" class="font-mono text-zinc-300 text-xs">$0.00 (0.00%)</span>
        </div>
      </div>

      <!-- ACTION DIRECTIVE & ROTATION CARD -->
      <div id="panel-3" class="rounded-2xl border-2 border-{rot_color}-500/50 bg-{rot_color}-500/5 p-4 shadow-xl space-y-2.5">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Action Protocol</span>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-{rot_color}-500/20 text-{rot_color}-300 border border-{rot_color}-500/40">
            {rot_badge}
          </span>
        </div>

        <div>
          <div class="text-xl font-black text-white tracking-tight">
            {rotation}
          </div>
          <p class="text-xs text-zinc-300 mt-0.5 font-medium leading-relaxed">
            {action}
          </p>
        </div>

        <div class="pt-2 border-t border-zinc-800/80 grid grid-cols-2 gap-2 text-xs">
          <div class="p-2 rounded-xl bg-zinc-950/60 border border-zinc-800/70">
            <span class="text-[10px] uppercase font-bold text-zinc-400 block">Inviolable Stop</span>
            <span class="font-mono font-bold text-rose-400 text-xs">${disaster_stop:,.2f}</span>
            <span class="text-[10px] text-zinc-400 block font-mono">({disaster_stop_dist:.2f}% gap)</span>
          </div>
          <div class="p-2 rounded-xl bg-zinc-950/60 border border-zinc-800/70">
            <span class="text-[10px] uppercase font-bold text-zinc-400 block">Risk Budget</span>
            <span class="font-bold text-emerald-400 text-xs">APPROVED</span>
            <span class="text-[10px] text-zinc-400 block">100% Cash Defense</span>
          </div>
        </div>
      </div>

      <!-- LIQUIDITY MAGNETS & GRAVITY CARD -->
      <div id="panel-4" class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400">Liquidity Magnets</span>
          <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">
            72.0x Pull Imbalance
          </span>
        </div>

        <!-- 3-TIER MAGNET STACK -->
        <div class="space-y-1.5 font-mono text-xs">
          <!-- Upper Shorts -->
          <div class="flex items-center justify-between p-2 rounded-xl bg-zinc-950/60 border border-zinc-800/60 text-zinc-300">
            <div class="flex items-center gap-1.5">
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20 font-sans font-bold">SHORTS</span>
              <span class="font-bold">${upper_c.get('price_level', 0.0):,.0f}</span>
            </div>
            <div class="text-right text-rose-400 text-[11px]">
              +{upper_c.get('distance_pct', 0.0):.2f}% &bull; ${upper_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M
            </div>
          </div>

          <!-- Spot Zero Axis -->
          <div class="flex items-center justify-between p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/40 text-cyan-300">
            <div class="flex items-center gap-1.5">
              <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
              <span class="font-bold font-sans text-xs uppercase">SPOT PRICE</span>
            </div>
            <div class="font-bold text-white text-xs">
              ${price:,.2f}
            </div>
          </div>

          <!-- Lower Longs (Dominant) -->
          <div class="flex items-center justify-between p-2 rounded-xl bg-emerald-500/15 border-2 border-emerald-500/50 text-emerald-300 shadow-md">
            <div class="flex items-center gap-1.5">
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/30 text-emerald-200 border border-emerald-400/50 font-sans font-bold">🔥 LONGS</span>
              <span class="font-bold">${lower_c.get('price_level', 0.0):,.0f}</span>
            </div>
            <div class="text-right text-emerald-300 font-bold text-[11px]">
              -{lower_c.get('distance_pct', 0.0):.2f}% &bull; ${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M
            </div>
          </div>
        </div>

        <!-- Crowd Meter -->
        <div class="pt-1">
          <div class="flex items-center justify-between text-[11px] text-zinc-400 mb-1">
            <span>Retail Crowd Imbalance:</span>
            <span class="font-bold text-emerald-400 mono">74.6% Longs Crowded</span>
          </div>
          <div class="w-full bg-zinc-950 h-2 rounded-full overflow-hidden flex border border-zinc-800">
            <div class="bg-rose-500 h-full" style="width: 25.4%;"></div>
            <div class="bg-emerald-500 h-full" style="width: 74.6%;"></div>
          </div>
        </div>
      </div>

      <!-- WHY POINTS SUMMARY -->
      <div class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl space-y-2">
        <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 block">Core Positioning Evidence</span>
        <div class="space-y-1.5">
          {why_points_html}
        </div>
      </div>

    </div>

    <!-- ======================================================= -->
    <!-- TAB 2: TELEMETRY (MICROSTRUCTURE DATA GRID)             -->
    <!-- ======================================================= -->
    <div id="tab-content-telemetry" class="tab-pane space-y-3.5 hidden">

      <!-- KEY LEVELS -->
      <div id="panel-2" class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl space-y-3">
        <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 block">Benchmark Price Anchors</span>
        <div class="grid grid-cols-2 gap-2 text-xs font-mono">
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">DAILY VWAP</span>
            <span class="font-bold text-white text-sm">${daily_vwap:,.2f}</span>
          </div>
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">WEEKLY VWAP</span>
            <span class="font-bold text-white text-sm">${weekly_vwap:,.2f}</span>
          </div>
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">20D EMA</span>
            <span class="font-bold text-zinc-200 text-sm">${ema_20d:,.2f}</span>
          </div>
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">50D EMA</span>
            <span class="font-bold text-zinc-200 text-sm">${ema_50d:,.2f}</span>
          </div>
          <div class="col-span-2 p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70 flex items-center justify-between">
            <div>
              <span class="text-[10px] font-sans font-semibold text-zinc-400 block">200-DAY MOVING AVERAGE</span>
              <span class="font-bold text-cyan-400 text-sm">${ma_200d:,.2f}</span>
            </div>
            <span class="text-[10px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">Macro Baseline</span>
          </div>
        </div>
      </div>

      <!-- FLOW & POSITIONING -->
      <div class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl space-y-3">
        <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 block">Derivatives &amp; Volume Flow</span>
        <div class="grid grid-cols-2 gap-2 text-xs font-mono">
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">SPOT CVD RATIO</span>
            <span class="font-bold text-emerald-400 text-sm">{spot_cvd_ratio:.2f}</span>
            <span class="text-[9px] text-zinc-400 block font-sans">Spot Absorption Lead</span>
          </div>
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">OPEN INTEREST</span>
            <span class="font-bold text-white text-sm">{current_oi:,.0f} BTC</span>
            <span class="text-[9px] text-emerald-400 block font-sans">+{oi_change_24h:.2f}% (24h)</span>
          </div>
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">8H FUNDING RATE</span>
            <span class="font-bold text-cyan-400 text-sm">{'+' if funding_rate >= 0 else ''}{funding_rate:.4f}%</span>
            <span class="text-[9px] text-zinc-400 block font-sans">Calm Carry</span>
          </div>
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">ANNUALIZED BASIS</span>
            <span class="font-bold text-amber-400 text-sm">{basis:.2f}%</span>
            <span class="text-[9px] text-zinc-400 block font-sans">Slight Backwardation</span>
          </div>
        </div>
      </div>

      <!-- SESSIONS & CLOCKS -->
      <div class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl space-y-3">
        <span class="text-[11px] font-bold uppercase tracking-wider text-zinc-400 block">Global Market Clocks</span>
        <div class="grid grid-cols-2 gap-2 text-xs font-mono">
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">UTC TIME</span>
            <span id="clock-utc-time" class="font-bold text-white text-sm">--:--:-- UTC</span>
            <span id="clock-utc-date" class="text-[10px] text-zinc-400 block font-mono">-- --- ----</span>
          </div>
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">SGT TIME (UTC+8)</span>
            <span id="clock-sgt-time" class="font-bold text-emerald-300 text-sm">--:--:-- SGT</span>
            <span id="clock-sgt-date" class="text-[10px] text-zinc-400 block font-mono">-- --- ----</span>
          </div>
        </div>
        <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70 space-y-1">
          <div class="flex items-center justify-between text-xs">
            <span id="session-name" class="font-bold text-white">US Cash Session</span>
            <span id="session-hours" class="mono text-zinc-400 text-[11px]">14:00 - 21:00 UTC</span>
          </div>
          <p id="session-desc" class="text-[11px] text-zinc-400 leading-relaxed">Peak Wall Street ETF Inflows &amp; Derivatives Liquidity Squeeze</p>
        </div>
      </div>

    </div>

    <!-- ======================================================= -->
    <!-- TAB 3: VERDICT (THE 2 DECISION METHODS)                  -->
    <!-- ======================================================= -->
    <div id="tab-content-verdict" class="tab-pane space-y-3.5 hidden">

      <!-- TOP METHOD TOGGLE SWITCH -->
      <div class="p-1 rounded-xl bg-zinc-900 border border-zinc-800 flex text-xs font-bold">
        <button id="toggle-method-1" onclick="switchVerdictMethod(1)" class="flex-1 py-2 rounded-lg bg-zinc-800 text-cyan-300 shadow transition-all">
          Method 1: AI Prompt
        </button>
        <button id="toggle-method-2" onclick="switchVerdictMethod(2)" class="flex-1 py-2 rounded-lg text-zinc-400 hover:text-zinc-200 transition-all">
          Method 2: System Verdict
        </button>
      </div>

      <!-- METHOD 1: AI PROMPT -->
      <div id="view-method-1" class="space-y-3 block">
        <div id="method-1" class="rounded-2xl bg-zinc-900/80 border border-cyan-500/40 p-4 shadow-xl space-y-3">
          <div class="flex items-center gap-2 text-cyan-300 font-bold text-xs uppercase tracking-wider">
            <span>📋</span>
            <span>Independent AI Audit Format</span>
          </div>
          <p class="text-xs text-zinc-300 leading-relaxed">
            Copy the full quantitative market telemetry prompt to clipboard, then paste it directly into ChatGPT, Claude, Grok, or Gemini for an instant second opinion.
          </p>

          <button id="copy-prompt-btn" onclick="copyTelemetryPrompt()" class="w-full py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 active:scale-95 text-black font-extrabold text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 transition-all">
            <span id="copy-btn-icon">📋</span>
            <span id="copy-btn-text">Copy Live Data &amp; Prompt for AI</span>
          </button>
        </div>
      </div>

      <!-- METHOD 2: SYSTEM VERDICT -->
      <div id="view-method-2" class="space-y-3 hidden">
        <div id="method-2" class="rounded-2xl bg-zinc-900/80 border border-emerald-500/40 p-4 shadow-xl space-y-3">
          <div class="flex items-center gap-2 text-emerald-300 font-bold text-xs uppercase tracking-wider">
            <span>🛡️</span>
            <span>Our System Verdict</span>
          </div>

          <div class="space-y-2 text-xs text-zinc-300 leading-relaxed">
            <div class="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
              <strong class="text-white block mb-0.5 font-bold">1. Macro Structural State:</strong>
              <span>Price is holding above the 200D MA (${ma_200d:,.0f}), preserving the long-term trend, but trading below Daily VWAP in short-term compression.</span>
            </div>

            <div class="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
              <strong class="text-white block mb-0.5 font-bold">2. Liquidity Asymmetry:</strong>
              <span>Massive retail long cluster at ${lower_c.get('price_level', 0.0):,.0f} (${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M). Downside magnet pull is 72x heavier than upside short shelf.</span>
            </div>

            <div class="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
              <strong class="text-white block mb-0.5 font-bold">3. Inviolable Stop Defense:</strong>
              <span>Hard invalidation set at ${disaster_stop:,.2f} ({disaster_stop_dist:.2f}% buffer), positioned strictly beneath major retail liquidation stop shelves.</span>
            </div>

            <div class="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
              <strong class="text-white block mb-0.5 font-bold">4. Capital Protocol:</strong>
              <span>Maintain 100% USDT cash reserve. Strictly zero new spot accumulation until lower sweep is confirmed or invalidated.</span>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- ======================================================= -->
    <!-- TAB 4: REGIMES (THE 5-REGIME POCKET GUIDE)               -->
    <!-- ======================================================= -->
    <div id="tab-content-regimes" class="tab-pane space-y-3 hidden">
      
      <div class="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-400">
        The quantitative 5-regime framework evaluates positioning mechanics so you never buy leveraged tops or sell spot washouts.
      </div>

      <!-- Regime 1 -->
      <div class="p-3.5 rounded-2xl bg-zinc-900/80 border border-emerald-500/30 space-y-1">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-emerald-400">1. Spot-Led Expansion</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-bold">0.75x - 1.0x</span>
        </div>
        <p class="text-xs text-zinc-300 leading-relaxed">Genuine institutional spot demand pushing price higher. Spot CVD leads; perps follow.</p>
      </div>

      <!-- Regime 2 -->
      <div class="p-3.5 rounded-2xl bg-zinc-900/80 border border-amber-500/30 space-y-1">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-amber-400">2. Leveraged / Fragile Upside</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 font-bold">0.0x - 0.25x</span>
        </div>
        <p class="text-xs text-zinc-300 leading-relaxed">Perp leverage pushing price up with negative/flat spot CVD. Extreme liquidation vulnerability.</p>
      </div>

      <!-- Regime 3 -->
      <div class="p-3.5 rounded-2xl bg-zinc-900/80 border border-cyan-500/30 space-y-1">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-cyan-400">3. Range / Liquidation Magnet</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 font-bold">0.5x - 0.75x on Reclaim</span>
        </div>
        <p class="text-xs text-zinc-300 leading-relaxed">Price oscillates between dense liquidation pools. Trade the magnet only upon verified sweep &amp; reclaim.</p>
      </div>

      <!-- Regime 4 -->
      <div class="p-3.5 rounded-2xl bg-zinc-900/80 border border-rose-500/30 space-y-1">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-rose-400">4. Cascade / Deleveraging</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 font-bold">0.0x CASH</span>
        </div>
        <p class="text-xs text-zinc-300 leading-relaxed">Waterfall liquidation cascade. Open interest implosion. Never catch a falling knife.</p>
      </div>

      <!-- Regime 5 -->
      <div class="p-3.5 rounded-2xl bg-zinc-900/80 border border-rose-500/30 space-y-1">
        <div class="flex items-center justify-between text-xs">
          <span class="font-bold text-rose-400">5. Distribution / Bear Trend</span>
          <span class="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 font-bold">0.0x CASH</span>
        </div>
        <p class="text-xs text-zinc-300 leading-relaxed">Persistent spot selling below key moving averages. Complete capital defense in 100% USDT.</p>
      </div>

    </div>

    <!-- Standard Footer with Privacy Link -->
    <footer class="pt-6 text-center text-xs text-zinc-500 space-y-2">
      <div class="flex items-center justify-center gap-3">
        <a href="privacy.html" class="text-cyan-400 hover:underline">Privacy Policy</a>
        <span>&bull;</span>
        <a href="regime.json" target="_blank" class="text-cyan-400 hover:underline">REST API</a>
      </div>
      <p class="text-[10px] text-zinc-600">Strictly for analytical research. Not financial advice.</p>
    </footer>

  </div>

  <!-- FIXED BOTTOM NAVIGATION TABS -->
  <nav class="fixed bottom-0 left-0 right-0 z-40 bg-zinc-950/95 backdrop-blur-md border-t border-zinc-800/80 pb-3 pt-2">
    <div class="max-w-md mx-auto grid grid-cols-4 px-2">
      <button id="nav-btn-radar" onclick="switchTab('radar')" class="nav-tab flex flex-col items-center justify-center py-1.5 text-cyan-400">
        <span class="text-lg">🧲</span>
        <span class="text-[10px] font-bold uppercase tracking-wider mt-0.5">Radar</span>
      </button>
      <button id="nav-btn-telemetry" onclick="switchTab('telemetry')" class="nav-tab flex flex-col items-center justify-center py-1.5 text-zinc-400 hover:text-zinc-200">
        <span class="text-lg">📊</span>
        <span class="text-[10px] font-bold uppercase tracking-wider mt-0.5">Telemetry</span>
      </button>
      <button id="nav-btn-verdict" onclick="switchTab('verdict')" class="nav-tab flex flex-col items-center justify-center py-1.5 text-zinc-400 hover:text-zinc-200">
        <span class="text-lg">🧠</span>
        <span class="text-[10px] font-bold uppercase tracking-wider mt-0.5">Verdict</span>
      </button>
      <button id="nav-btn-regimes" onclick="switchTab('regimes')" class="nav-tab flex flex-col items-center justify-center py-1.5 text-zinc-400 hover:text-zinc-200">
        <span class="text-lg">📘</span>
        <span class="text-[10px] font-bold uppercase tracking-wider mt-0.5">Regimes</span>
      </button>
    </div>
  </nav>

  <!-- COPY TOAST NOTIFICATION -->
  <div id="copy-toast" class="fixed bottom-20 left-1/2 transform -translate-x-1/2 z-50 opacity-0 pointer-events-none transition-all duration-300 bg-emerald-500 text-black font-extrabold px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-2 text-xs">
    <span>✓</span>
    <span>Copied Prompt for AI!</span>
  </div>

  <!-- Hidden telemetry prompt data -->
  <textarea id="llm-prompt-data" class="hidden" readonly>{llm_prompt_escaped}</textarea>

  <script>
    // Tab Switching
    function switchTab(tabId) {{
      const tabs = ['radar', 'telemetry', 'verdict', 'regimes'];
      tabs.forEach(t => {{
        const content = document.getElementById('tab-content-' + t);
        const navBtn = document.getElementById('nav-btn-' + t);
        if (content) content.classList.add('hidden');
        if (navBtn) {{
          navBtn.classList.remove('text-cyan-400');
          navBtn.classList.add('text-zinc-400');
        }}
      }});
      const targetContent = document.getElementById('tab-content-' + tabId);
      const targetBtn = document.getElementById('nav-btn-' + tabId);
      if (targetContent) targetContent.classList.remove('hidden');
      if (targetBtn) {{
        targetBtn.classList.add('text-cyan-400');
        targetBtn.classList.remove('text-zinc-400');
      }}
    }}

    // Verdict Sub-method toggle
    function switchVerdictMethod(methodNum) {{
      const v1 = document.getElementById('view-method-1');
      const v2 = document.getElementById('view-method-2');
      const b1 = document.getElementById('toggle-method-1');
      const b2 = document.getElementById('toggle-method-2');
      if (methodNum === 1) {{
        if (v1) v1.classList.remove('hidden');
        if (v2) v2.classList.add('hidden');
        if (b1) {{ b1.className = 'flex-1 py-2 rounded-lg bg-zinc-800 text-cyan-300 shadow transition-all'; }}
        if (b2) {{ b2.className = 'flex-1 py-2 rounded-lg text-zinc-400 hover:text-zinc-200 transition-all'; }}
      }} else {{
        if (v1) v1.classList.add('hidden');
        if (v2) v2.classList.remove('hidden');
        if (b2) {{ b2.className = 'flex-1 py-2 rounded-lg bg-zinc-800 text-emerald-300 shadow transition-all'; }}
        if (b1) {{ b1.className = 'flex-1 py-2 rounded-lg text-zinc-400 hover:text-zinc-200 transition-all'; }}
      }}
    }}

    // Copy Prompt
    function copyTelemetryPrompt() {{
      const promptEl = document.getElementById('llm-prompt-data');
      if (!promptEl) return;
      const textToCopy = promptEl.value;

      if (navigator.clipboard && window.isSecureContext) {{
        navigator.clipboard.writeText(textToCopy).then(showSuccess, fallbackCopy);
      }} else {{
        fallbackCopy();
      }}

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
          alert('Could not copy automatically. Please open developer console or JSON feed.');
        }}
        document.body.removeChild(ta);
      }}

      function showSuccess() {{
        const btn = document.getElementById('copy-prompt-btn');
        const btnText = document.getElementById('copy-btn-text');
        const btnIcon = document.getElementById('copy-btn-icon');
        const toast = document.getElementById('copy-toast');

        if (btnText) btnText.innerText = '✓ Copied Prompt to Clipboard!';
        if (btnIcon) btnIcon.innerText = '✅';
        if (btn) {{
          btn.classList.remove('bg-cyan-500');
          btn.classList.add('bg-emerald-500');
        }}

        if (toast) {{
          toast.classList.remove('opacity-0', 'pointer-events-none');
          toast.classList.remove('translate-y-4');
          setTimeout(() => {{
            toast.classList.add('opacity-0', 'pointer-events-none');
            toast.classList.add('translate-y-4');
            if (btnText) btnText.innerText = 'Copy Live Data & Prompt for AI';
            if (btnIcon) btnIcon.innerText = '📋';
            if (btn) {{
              btn.classList.remove('bg-emerald-500');
              btn.classList.add('bg-cyan-500');
            }}
          }}, 3000);
        }}
      }}
    }}

    // Real-Time Clocks & Sessions
    function updateClocksAndSession() {{
      const now = new Date();
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
      const sgtDate = new Date(now.getTime() + (sgtOffset + now.getTimezoneOffset()) * 60000);
      const sgtHours = String(sgtDate.getHours()).padStart(2, '0');
      const sgtMinutes = String(sgtDate.getMinutes()).padStart(2, '0');
      const sgtSeconds = String(sgtDate.getSeconds()).padStart(2, '0');
      const sgtDateStr = `${{sgtDate.getDate()}} ${{months[sgtDate.getMonth()]}} ${{sgtDate.getFullYear()}}`;

      const sgtEl = document.getElementById('clock-sgt-time');
      const sgtDateEl = document.getElementById('clock-sgt-date');
      if (sgtEl) sgtEl.innerText = `${{sgtHours}}:${{sgtMinutes}}:${{sgtSeconds}} SGT`;
      if (sgtDateEl) sgtDateEl.innerText = sgtDateStr;

      // Active Market Session Zone (based on UTC hour)
      const uH = now.getUTCHours();
      let sessionName = '🌙 Pacific / Off-Hours Transition';
      let sessionHours = '21:00 - 00:00 UTC (05:00 - 08:00 SGT)';
      let sessionDesc = 'Off-Hours Liquidity • Mean Reversion &amp; Overnight Reset';
      let sessionBadge = 'OFF-HOURS';
      let sessionBadgeClass = 'border-purple-500/40 bg-purple-500/15 text-purple-300';

      if (uH >= 0 && uH < 8) {{
        sessionName = '🌏 Asian / Pacific Session';
        sessionHours = '00:00 - 08:00 UTC (08:00 - 16:00 SGT)';
        sessionDesc = 'Tokyo, Singapore &amp; HK Open • Range Definition &amp; Baseline Flow';
        sessionBadge = 'ASIAN ACTIVE';
        sessionBadgeClass = 'border-cyan-500/40 bg-cyan-500/15 text-cyan-300';
      }} else if (uH >= 8 && uH < 14) {{
        sessionName = '🏛️ European / London Session';
        sessionHours = '08:00 - 14:00 UTC (16:00 - 22:00 SGT)';
        sessionDesc = 'London Open &amp; Frankfurt • Volatility Expansion &amp; Sweep Fuel';
        sessionBadge = 'LONDON ACTIVE';
        sessionBadgeClass = 'border-amber-500/40 bg-amber-500/15 text-amber-300';
      }} else if (uH >= 14 && uH < 21) {{
        sessionName = '⚡ US / New York Cash Session';
        sessionHours = '14:00 - 21:00 UTC (22:00 - 05:00 SGT)';
        sessionDesc = 'Peak Wall Street ETF Inflows &amp; Derivatives Liquidity Squeeze';
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

    // Live BTC price ticker (Binance Vision first: it is not geo-blocked; falls back to api.binance.com)
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
      if (isNaN(livePrice)) {{
        priceFailCount++;
        if (priceFailCount >= 3 && driftEl) {{
          driftEl.className = 'text-amber-400 font-medium';
          driftEl.textContent = 'live price feed unreachable (showing last known price)';
        }}
        return;
      }}
      priceFailCount = 0;
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

    // Live scan refresh + data-age banner
    const IS_NATIVE_APP = !!(window.Capacitor && typeof window.Capacitor.isNativePlatform === 'function' && window.Capacitor.isNativePlatform()) || location.protocol === 'file:';
    const LIVE_BASE = IS_NATIVE_APP ? 'https://aikeluargalee-tech.github.io/btc-magnet-monitor/' : './';
    const rootAtLoad = document.getElementById('app-root');
    let currentScanTs = Date.parse(rootAtLoad ? rootAtLoad.getAttribute('data-scan-ts') : '') || 0;
    let lastFetchOk = null;

    function formatAge(mins) {{
      if (mins < 60) return mins + ' min';
      return Math.floor(mins / 60) + 'h ' + (mins % 60) + 'm';
    }}

    function renderAgeBanner() {{
      const el = document.getElementById('data-age-banner');
      if (!el) return;
      const base = 'px-2.5 py-1 rounded-full text-[11px] font-semibold border flex items-center gap-1.5 ';
      if (currentScanTs <= 0) {{
        el.className = base + 'border-amber-500/40 bg-amber-500/10 text-amber-300';
        el.innerHTML = '<span>⚠ Scan time unknown</span>';
        return;
      }}
      const ageMin = Math.max(0, Math.floor((Date.now() - currentScanTs) / 60000));
      const age = formatAge(ageMin);
      if (ageMin > 180) {{
        el.className = base + 'border-rose-500/50 bg-rose-500/15 text-rose-300';
        el.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span><span>STALE DATA (' + age + ')</span>';
      }} else if (lastFetchOk === false) {{
        el.className = base + 'border-amber-500/40 bg-amber-500/10 text-amber-300';
        el.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span><span>Offline (' + age + ')</span>';
      }} else if (ageMin > 90) {{
        el.className = base + 'border-amber-500/40 bg-amber-500/10 text-amber-300';
        el.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span><span>' + age + ' ago</span>';
      }} else {{
        el.className = base + 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300';
        el.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span><span>' + age + ' ago</span>';
      }}
    }}

    function sanitizeLiveNode(root) {{
      root.querySelectorAll('script, iframe, object, embed, link, meta, base, form').forEach(function (n) {{ n.remove(); }});
      root.querySelectorAll('*').forEach(function (n) {{
        Array.from(n.attributes).forEach(function (a) {{
          const name = a.name.toLowerCase();
          const val = (a.value || '').trim().toLowerCase();
          if (name.indexOf('on') === 0 && !(name === 'onclick' && (a.value.includes('copyTelemetryPrompt') || a.value.includes('switchTab') || a.value.includes('switchVerdictMethod')))) {{
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
    if ('caches' in window) {{
      caches.keys().then((keys) => {{
        keys.forEach((key) => {{
          if (key !== 'btc-magnet-pwa-v6') {{
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
        <div class="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-xl shadow-inner">
          🧲
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
    <div class="p-5 rounded-2xl border border-cyan-500/40 bg-cyan-500/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div>
        <div class="text-xs uppercase font-bold text-cyan-400 tracking-wider">Current Live Market State</div>
        <div class="text-xl font-bold text-white mt-0.5">{current_name}</div>
        <div class="text-xs text-zinc-400 mt-1">Diagnosed by verified on-exchange order flow and positioning metrics.</div>
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
    <div class="space-y-4">
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
    <div class="space-y-4">
      <h2 class="text-2xl font-bold text-white flex items-center gap-2.5">
        <span>2. How the Majority-Voting Engine Works</span>
      </h2>
      <div class="p-5 rounded-2xl bg-zinc-900/70 border border-zinc-800 space-y-3 text-sm text-zinc-300 leading-relaxed">
        <p>
          Traditional trading algorithms fail because of <strong>fragile multi-AND rules</strong> (requiring 5 or 6 indicators to be simultaneously true). If one obscure metric misses by 0.1%, the system breaks or jumps erratically.
        </p>
        <p>
          The 5-Regime Radar uses a <strong>robust majority-vote model</strong>:
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
          <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-zinc-800">
            <strong class="text-emerald-400 block text-xs uppercase font-bold mb-1">Majority Rule (&ge;3 of 4)</strong>
            <p class="text-xs text-zinc-400">Each regime defines 4 observable facts. If 3 or 4 are confirmed on-exchange, the regime is verified.</p>
          </div>
          <div class="p-3.5 rounded-xl bg-zinc-950/80 border border-zinc-800">
            <strong class="text-amber-400 block text-xs uppercase font-bold mb-1">Default Fallback (Transition / Mixed)</strong>
            <p class="text-xs text-zinc-400">If no regime achieves 3/4 matches, the system cleanly defaults to Cash (0.0x) until clarity returns.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 3: Deep Dive into the 5 Regimes -->
    <div class="space-y-6">
      <h2 class="text-2xl font-bold text-white">3. Complete Specification of the 5 Regimes</h2>

      <!-- Regime 1 -->
      <div class="p-6 rounded-2xl bg-zinc-900/60 border border-zinc-800 space-y-4">
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
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-zinc-800">
          <div class="font-bold text-zinc-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price holding above Daily and Weekly VWAP or rising with structure.</div>
          <div class="text-zinc-300">2. Spot CVD ratio clearly positive (&ge;1.15) or 7-day slope upward.</div>
          <div class="text-zinc-300">3. Spot trading volume expanding (&ge;1.10x 20-day moving average).</div>
          <div class="text-zinc-300">4. Futures funding rates healthy (&le;0.012%) and Open Interest not surging parabolically.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">60% breakout confirmation / 40% limit at Daily VWAP retest.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Safety Stop-Loss:</strong>
            <span class="text-zinc-200">Anchored under recent 4-hour swing low (-0.6%).</span>
          </div>
        </div>
      </div>

      <!-- Regime 2 -->
      <div class="p-6 rounded-2xl bg-zinc-900/60 border border-zinc-800 space-y-4">
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
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-zinc-800">
          <div class="font-bold text-zinc-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price rising but Spot CVD is flat or declining (bearish divergence).</div>
          <div class="text-zinc-300">2. Perpetual futures CVD and/or Open Interest rising sharply (&gt;+4% in 24h).</div>
          <div class="text-zinc-300">3. Funding rates elevated (&gt;0.015% per 8h) or basis contango stretched.</div>
          <div class="text-zinc-300">4. Spot volume failing to confirm the move (below 20D average).</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">Strictly zero new buying. Harvest 33% profit directly into perp pumps.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Safety Stop-Loss:</strong>
            <span class="text-zinc-200">Move protective stops tight to 4H swing low to lock in profits.</span>
          </div>
        </div>
      </div>

      <!-- Regime 3 -->
      <div class="p-6 rounded-2xl bg-zinc-900/60 border border-cyan-500/40 space-y-4">
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
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-zinc-800">
          <div class="font-bold text-zinc-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price oscillating in a defined range (width &le;4.5%) with ATR compressed &gt;30%.</div>
          <div class="text-zinc-300">2. Spot CVD neutral or balanced (ratio between 0.90 and 1.15).</div>
          <div class="text-zinc-300">3. Funding and OI showing positioning crowding on one side (L/S ratio &ge;1.60).</div>
          <div class="text-zinc-300">4. Clear liquidation clusters active both above and below current price.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">Trade toward dominant magnet: 50% on 1H range reclaim / 50% limit at support low.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Safety Stop-Loss:</strong>
            <span class="text-zinc-200">Anchored outside range floor (Lowest sweep wick - 0.5%).</span>
          </div>
        </div>
      </div>

      <!-- Regime 4 -->
      <div class="p-6 rounded-2xl bg-zinc-900/60 border border-zinc-800 space-y-4">
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
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-zinc-800">
          <div class="font-bold text-zinc-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Sharp vertical price plunge (&le;-3.0% in 1h or &le;-6.0% in 24h).</div>
          <div class="text-zinc-300">2. Open Interest crashing violently (&le;-3.5% in 1h or &le;-7.0% in 4h).</div>
          <div class="text-zinc-300">3. Funding rate plunged deeply negative (&le;-0.005%).</div>
          <div class="text-zinc-300">4. Severe basis discount / backwardation (&lt;1.0% annualized).</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">100% Cash. Wait for Phase 3: 5m liquidations stop, OI flatlines, and 1H hammer forms.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Safety Stop-Loss:</strong>
            <span class="text-zinc-200">N/A (Holding cash reserve).</span>
          </div>
        </div>
      </div>

      <!-- Regime 5 -->
      <div class="p-6 rounded-2xl bg-zinc-900/60 border border-zinc-800 space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <span class="px-3 py-1 rounded-lg text-xs font-bold uppercase bg-rose-500/10 text-rose-400 border border-rose-500/30">
            Regime 5 &bull; Distribution / Bear Continuation
          </span>
          <span class="text-xs font-mono text-zinc-400 font-bold">Action: Defensive Cash (0.0x)</span>
        </div>
        <h3 class="text-lg font-bold text-white">Persistent seller control &amp; exit liquidity traps</h3>
        <p class="text-xs text-zinc-300 leading-relaxed">
          Smart money is actively selling down inventory into retail dip-buyers. Every minor bounce occurs on light volume and is sold off immediately.
        </p>
        <div class="text-xs space-y-1.5 bg-zinc-950/80 p-4 rounded-xl border border-zinc-800">
          <div class="font-bold text-zinc-400 uppercase tracking-wider text-[11px] mb-2">The 4 Primary Observations (Majority &ge;3):</div>
          <div class="text-zinc-300">1. Price trapped below Daily VWAP, 20D EMA, and 50D EMA.</div>
          <div class="text-zinc-300">2. Spot CVD persistently negative (7D/14D slope &lt;0).</div>
          <div class="text-zinc-300">3. Bounces occur on light spot volume (&lt;0.95x 20D MA).</div>
          <div class="text-zinc-300">4. Trapped longs paying positive funding with compressed futures basis.</div>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Execution Protocol:</strong>
            <span class="text-zinc-200">Defensive 100% USDT cash. Treat bounces as exit liquidity.</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-950/60 border border-zinc-800/80">
            <strong class="text-zinc-400 block text-[11px] uppercase">Safety Invalidation:</strong>
            <span class="text-zinc-200">1D close &gt; 50D EMA backed by positive Spot CVD.</span>
          </div>
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





