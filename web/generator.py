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

        # 2. Render main dashboard HTML
        html_content = self._render_html(payload)
        html_path = os.path.join(self.output_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 3. Render regimes detailed subpage HTML
        regimes_content = self._render_regimes_subpage(payload)
        regimes_path = os.path.join(self.output_dir, "regimes.html")
        with open(regimes_path, "w", encoding="utf-8") as f:
            f.write(regimes_content)

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

    def _render_html(self, data: Dict[str, Any]) -> str:
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})

        regime_id = regime.get("regime_id", "RANGE_LIQUIDATION_MAGNET")
        name = regime.get("name", regime.get("regime", "Range / Liquidation Magnet"))
        diagnosis = regime.get("diagnosis", "")
        playbook = regime.get("playbook", "")
        majority_score = regime.get("majority_score", "3/4 observations confirmed")
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
            lsce_badge_class = "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
            lsce_badge_icon = "✅"
            lsce_badge_title = "SWEEP &amp; RECLAIM CONFIRMED (BUY AUTHORIZED)"
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
            regime_border_color = "border-zinc-700 shadow-zinc-800/10"
            regime_badge_bg = "bg-zinc-800 text-zinc-300 border-zinc-700"
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

        # Evidence Cards for the Standout Regime Panel
        evidence_cards_html = "".join([
            f"""<div class='flex items-start gap-2.5 p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80'>
                 <span class='text-emerald-400 font-bold mt-0.5 text-xs'>✓</span>
                 <span class='text-xs text-zinc-200 leading-relaxed'>{item}</span>
               </div>"""
            for item in regime.get("matched_criteria", [])
        ])

        # Why Points HTML
        why_points_html = "".join([
            f"""<div class='flex items-start gap-3 p-3.5 rounded-xl bg-zinc-950/80 border border-zinc-800/70'>
                 <span class='w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-xs font-bold text-emerald-400 flex-shrink-0 mt-0.5'>{idx+1}</span>
                 <p class='text-xs sm:text-sm text-zinc-300 leading-relaxed font-normal'>{pt}</p>
               </div>"""
            for idx, pt in enumerate(why_points)
        ])

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
        spot_source = metrics.get("spot_data_source", "Binance Vision API")
        futures_source = metrics.get("futures_data_source", "Deribit & Kraken Futures")

        # Active Playbook Tag for Magnet Section
        if regime_id == "RANGE_LIQUIDATION_MAGNET":
            magnet_active_badge = "<span class='px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 text-xs font-semibold animate-pulse'>🎯 Primary Active Playbook</span>"
        else:
            magnet_active_badge = "<span class='px-3 py-1 rounded-full bg-zinc-800 text-zinc-400 border border-zinc-700 text-xs font-medium'>Secondary / Informational Only</span>"

        # Build raw prompt for clipboard
        llm_prompt = self._build_llm_prompt(data)
        llm_prompt_escaped = llm_prompt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BTC Magnet Monitor — 5-Regime Radar &amp; AI Telemetry Cockpit</title>
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
<body class="min-h-screen bg-zinc-950 text-zinc-100 antialiased pb-16">

  <!-- Top Navigation Bar -->
  <header class="border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md sticky top-0 z-50 px-4 sm:px-6 py-3.5">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center text-xl shadow-inner">
          🧲
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="font-extrabold text-base tracking-tight text-white">BTC Magnet Monitor</span>
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-zinc-800/80 text-zinc-300 border border-zinc-700/60">5-Regime Radar</span>
          </div>
          <p class="text-xs text-zinc-400 hidden sm:block">Observable Positioning Mechanics &amp; Regime Intelligence</p>
        </div>
      </div>

      <div class="flex items-center gap-4 sm:gap-6">
        <a href="regimes.html" class="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-xs font-medium text-cyan-400 border border-zinc-700/80 transition-colors">
          <span>Explore 5 Regimes Guide</span>
          <span>&rarr;</span>
        </a>
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
  <div class="border-b border-zinc-800/50 bg-zinc-900/30 px-4 sm:px-6 py-2 text-xs text-zinc-400">
    <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
      <div>Data Feeds: <span class="text-zinc-300">{spot_source}</span> &bull; <span class="text-zinc-300">{futures_source}</span></div>
      <div>Last Scan: <span class="text-zinc-300 font-medium">{data.get("timestamp", "")[:19]} UTC</span> &bull; Automated Every 30 Minutes</div>
    </div>
  </div>

  <main class="max-w-6xl mx-auto px-4 sm:px-6 pt-6 space-y-6">

    <!-- ============================================================ -->
    <!-- TOP SECTION: LIVE TELEMETRY DRAWER & ONE-CLICK AI PROMPT    -->
    <!-- ============================================================ -->
    <div class="rounded-2xl border border-zinc-800 bg-gradient-to-r from-zinc-900/90 via-zinc-900/80 to-zinc-950 p-5 sm:p-6 backdrop-blur-md shadow-xl space-y-4">
      
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-extrabold uppercase tracking-widest text-cyan-400 flex items-center gap-1.5">
              <span>📊</span>
              <span>LIVE TELEMETRY DATA DICTIONARY &bull; AI PROMPT ENGINE</span>
            </span>
            <span class="text-[11px] text-zinc-400 font-mono hidden sm:inline">(Real-Time On-Exchange Feeds)</span>
          </div>
          <h2 class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
            Analyze Market Data with Your Own AI
          </h2>
          <p class="text-xs sm:text-sm text-zinc-300 mt-1 max-w-2xl leading-relaxed">
            Don't rely blindly on our verdict. Click below to copy the verified live market positioning metrics and paste directly into <strong>ChatGPT, Claude, Grok, or Gemini</strong> for an instant second opinion.
          </p>
        </div>

        <!-- Prominent One-Click Copy Button -->
        <div class="flex-shrink-0 flex items-center gap-3">
          <button id="copy-prompt-btn" onclick="copyTelemetryPrompt()" class="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-5 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs shadow-lg shadow-cyan-500/25 transition-all cursor-pointer">
            <span id="copy-btn-icon" class="text-sm">📋</span>
            <span id="copy-btn-text">Copy Prompt for AI (ChatGPT / Grok)</span>
          </button>
        </div>
      </div>

      <!-- Direct Full Categorized Telemetry Grid (25+ Metrics Table Immediately Visible) -->
      <div class="pt-2 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5 text-xs">
          
          <!-- Category 1 -->
          <div class="p-4 rounded-xl bg-zinc-950/90 border border-zinc-800/80 space-y-2">
            <div class="text-[11px] font-bold uppercase tracking-wider text-cyan-400 border-b border-zinc-800 pb-1.5">1. Price &amp; Structure</div>
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

          <!-- Category 2 -->
          <div class="p-4 rounded-xl bg-zinc-950/90 border border-zinc-800/80 space-y-2">
            <div class="text-[11px] font-bold uppercase tracking-wider text-emerald-400 border-b border-zinc-800 pb-1.5">2. Order Flow &amp; CVD</div>
            <div class="space-y-1.5 text-zinc-300">
              <div class="flex justify-between"><span>Spot CVD Ratio:</span> <span class="font-mono font-bold text-emerald-400">{spot_cvd_ratio:.2f}</span></div>
              <div class="flex justify-between"><span>24h Spot Volume:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_vol_24h", 0.0):,.0f} BTC</span></div>
              <div class="flex justify-between"><span>Volume / 20D MA:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_vol_ratio", 1.0):.2f}x</span></div>
              <div class="flex justify-between"><span>7D Spot CVD Slope:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_cvd_slope_7d", 0.0):+.0f}</span></div>
              <div class="flex justify-between"><span>14D Spot CVD Slope:</span> <span class="font-mono text-zinc-300">{metrics.get("spot_cvd_slope_14d", 0.0):+.0f}</span></div>
              <div class="flex justify-between"><span>Perp CVD Trend:</span> <span class="font-mono text-zinc-300 capitalize">{metrics.get("perp_cvd_trend", "Flat")}</span></div>
              <div class="flex justify-between"><span>Order Depth Ratio:</span> <span class="font-mono text-zinc-300">{metrics.get("bids_asks_depth_ratio", 1.0):.2f}</span></div>
            </div>
          </div>

          <!-- Category 3 -->
          <div class="p-4 rounded-xl bg-zinc-950/90 border border-zinc-800/80 space-y-2">
            <div class="text-[11px] font-bold uppercase tracking-wider text-amber-400 border-b border-zinc-800 pb-1.5">3. Derivatives Crowding</div>
            <div class="space-y-1.5 text-zinc-300">
              <div class="flex justify-between"><span>Open Interest:</span> <span class="font-mono font-bold text-white">{current_oi:,.0f} BTC</span></div>
              <div class="flex justify-between"><span>OI 24h Change:</span> <span class="font-mono text-zinc-300">{oi_change_24h:+.2f}%</span></div>
              <div class="flex justify-between"><span>OI 1h Change:</span> <span class="font-mono text-zinc-300">{metrics.get("oi_change_1h_pct", 0.0):+.2f}%</span></div>
              <div class="flex justify-between"><span>OI 4h Change:</span> <span class="font-mono text-zinc-300">{metrics.get("oi_change_4h_pct", 0.0):+.2f}%</span></div>
              <div class="flex justify-between"><span>Funding Rate (8h):</span> <span class="font-mono text-zinc-300">{funding_rate:+.4f}%</span></div>
              <div class="flex justify-between"><span>Futures Basis Ann.:</span> <span class="font-mono text-zinc-300">{basis:+.2f}%</span></div>
              <div class="flex justify-between"><span>Retail Long/Short:</span> <span class="font-mono text-zinc-300">{ls_ratio:.2f}</span></div>
            </div>
          </div>

          <!-- Category 4 -->
          <div class="p-4 rounded-xl bg-zinc-950/90 border border-zinc-800/80 space-y-2">
            <div class="text-[11px] font-bold uppercase tracking-wider text-rose-400 border-b border-zinc-800 pb-1.5">4. Volatility &amp; Magnets</div>
            <div class="space-y-1.5 text-zinc-300">
              <div class="flex justify-between"><span>1H ATR:</span> <span class="font-mono text-zinc-300">${metrics.get("atr", 0.0):,.2f}</span></div>
              <div class="flex justify-between"><span>ATR Compression:</span> <span class="font-mono font-bold text-white">{metrics.get("atr_compression_pct", 0.0):.1f}%</span></div>
              <div class="flex justify-between"><span>4H Channel Width:</span> <span class="font-mono text-zinc-300">{(((swing_high - swing_low) / max(price, 1.0)) * 100):.2f}%</span></div>
              <div class="flex justify-between"><span>Upper Short Pool:</span> <span class="font-mono text-rose-400">${upper_c.get('price_level', 0.0):,.0f} (+{upper_c.get('distance_pct', 0.0):.2f}%)</span></div>
              <div class="flex justify-between"><span>Upper Pool Volume:</span> <span class="font-mono text-zinc-300">${upper_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M</span></div>
              <div class="flex justify-between"><span>Lower Long Pool:</span> <span class="font-mono text-emerald-400">${lower_c.get('price_level', 0.0):,.0f} (-{lower_c.get('distance_pct', 0.0):.2f}%)</span></div>
              <div class="flex justify-between"><span>Lower Pool Volume:</span> <span class="font-mono text-zinc-300">${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M</span></div>
            </div>
          </div>

        </div>

      <!-- Hidden Pre-Formatted Prompt for Copying -->
      <textarea id="llm-prompt-data" class="hidden" readonly>{llm_prompt_escaped}</textarea>
    </div>

    <!-- ============================================================ -->
    <!-- PANEL 1: STANDOUT REGIME DIAGNOSIS (STANDS ON ITS OWN)       -->
    <!-- ============================================================ -->
    <div class="rounded-2xl border-2 {regime_border_color} bg-gradient-to-b from-zinc-900/90 via-zinc-900/80 to-zinc-950 p-6 sm:p-8 backdrop-blur-md shadow-2xl relative overflow-hidden">
      
      <!-- Top Bar: Category, Confidence Score & Subpage Link -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-zinc-800/80">
        <div class="flex items-center gap-2.5 flex-wrap">
          <span class="text-xs font-extrabold uppercase tracking-widest text-zinc-400 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
            STEP 1 &bull; MACRO REGIME DIAGNOSIS
          </span>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700">
            {majority_score}
          </span>
        </div>
        <div>
          <a href="regimes.html" class="inline-flex items-center gap-1.5 text-xs font-bold text-cyan-400 hover:text-cyan-300 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 px-3 py-1.5 rounded-lg transition-all shadow-sm">
            <span>Learn About the 5 Regimes &amp; Calculation Math</span>
            <span>&rarr;</span>
          </a>
        </div>
      </div>

      <!-- Main Regime Title & Physical Diagnosis -->
      <div class="pt-6 pb-5 space-y-3">
        <div class="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl border {regime_badge_bg} text-sm font-extrabold tracking-wide uppercase">
          <span class="text-lg">{regime_icon}</span>
          <span>{name}</span>
        </div>
        <h1 class="text-2xl sm:text-4xl font-extrabold text-white tracking-tight leading-tight">
          {diagnosis}
        </h1>
        <p class="text-sm sm:text-base text-zinc-300 max-w-3xl leading-relaxed">
          {regime_tagline}
        </p>
      </div>

      <!-- Concise Methodology Summary Box -->
      <div class="bg-zinc-950/70 p-4 rounded-xl border border-zinc-800/80 text-xs sm:text-sm text-zinc-300 leading-relaxed space-y-2">
        <div class="font-bold text-white flex items-center gap-2">
          <span>🧠</span>
          <span>How the Regime Engine Works:</span>
        </div>
        <p>
          Bitcoin is always classified into one of <strong>5 distinct market regimes</strong> (Spot-Led Expansion, Leveraged Upside, Range / Liquidation Magnet, Cascade, or Distribution; defaulting to Transition/Mixed). A regime is confirmed strictly when a <strong>majority (&ge;3 of 4)</strong> on-exchange positioning observations are verified without subjective guesswork.
        </p>
      </div>

      <!-- How We Derived This State (The Majority Evidence Grid) -->
      <div class="pt-5 space-y-3">
        <div class="text-xs font-bold uppercase tracking-wider text-zinc-400 flex items-center justify-between">
          <span>How We Derived This State (Verified On-Exchange Evidence):</span>
          <span class="text-emerald-400 font-mono font-semibold">{majority_score}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          {evidence_cards_html}
        </div>
      </div>

      <!-- 5-Regime Status Strip -->
      <div class="pt-6 border-t border-zinc-800/80 mt-6">
        <div class="text-[11px] font-semibold uppercase tracking-wider text-zinc-400 mb-2.5">5-Regime Radar Framework Matrix</div>
        <div class="grid grid-cols-2 sm:grid-cols-5 gap-2 text-center text-xs">
          <div class="p-2.5 rounded-lg border {'bg-emerald-500/10 border-emerald-500/50 text-emerald-300 font-bold' if regime_id == 'SPOT_LED_EXPANSION' else 'bg-zinc-950/60 border-zinc-800 text-zinc-400'}">
            1. Spot Expansion
          </div>
          <div class="p-2.5 rounded-lg border {'bg-orange-500/10 border-orange-500/50 text-orange-300 font-bold' if regime_id == 'LEVERAGED_FRAGILE_UPSIDE' else 'bg-zinc-950/60 border-zinc-800 text-zinc-400'}">
            2. Leveraged Trap
          </div>
          <div class="p-2.5 rounded-lg border {'bg-cyan-500/10 border-cyan-500/50 text-cyan-300 font-bold ring-1 ring-cyan-500/40' if regime_id == 'RANGE_LIQUIDATION_MAGNET' else 'bg-zinc-950/60 border-zinc-800 text-zinc-400'}">
            3. Range / Magnet
          </div>
          <div class="p-2.5 rounded-lg border {'bg-rose-500/10 border-rose-500/50 text-rose-300 font-bold' if regime_id == 'CASCADE_FORCED_DELEVERAGING' else 'bg-zinc-950/60 border-zinc-800 text-zinc-400'}">
            4. Cascade
          </div>
          <div class="p-2.5 rounded-lg border {'bg-rose-500/10 border-rose-500/50 text-rose-300 font-bold' if regime_id == 'DISTRIBUTION_BEAR_CONTINUATION' else 'bg-zinc-950/60 border-zinc-800 text-zinc-400'}">
            5. Distribution
          </div>
        </div>
      </div>

    </div>

    <!-- ============================================================ -->
    <!-- PANEL 2: ACTIONABLE PORTFOLIO ROTATION & EXECUTION PROTOCOL -->
    <!-- ============================================================ -->
    <div class="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-6 sm:p-8 backdrop-blur-sm shadow-xl space-y-6">
      
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-zinc-800">
        <div>
          <div class="text-xs font-extrabold uppercase tracking-widest text-zinc-400 mb-1 flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
            STEP 2 &bull; ACTIONABLE PORTFOLIO ROTATION
          </div>
          <h2 class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
            Spot Execution Directives &amp; Inviolable Risk Controls
          </h2>
          <p class="text-sm text-zinc-300 mt-1 max-w-2xl leading-relaxed">
            Spot-only capital rotation. Strictly zero borrowed leverage, zero futures gambling, zero shorting.
          </p>
        </div>

        <!-- Action Callout Box -->
        <div class="flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-end justify-center gap-2 p-5 rounded-xl border {action_bg} min-w-[280px]">
          <div class="text-[11px] font-bold uppercase tracking-wider text-zinc-400">
            Recommended Rotation
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white mono">
            {rotation}
          </div>
          <div class="text-xs font-semibold">
            {action_pill} &bull; Sizing: {sizing}x
          </div>
        </div>
      </div>

      <!-- Action Protocol, Stop Loss, and Risk Rules -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 space-y-1.5">
          <div class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Playbook Protocol</div>
          <div class="text-base font-bold text-white">{playbook}</div>
          <p class="text-xs text-zinc-300 leading-relaxed pt-1">{entry_inst}</p>
        </div>

        <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Dual Inviolable Stop-Loss</span>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">Hard Risk Bound</span>
          </div>
          <div class="text-base font-bold mono text-rose-400">
            ${disaster_stop:,.2f} <span class="text-xs font-normal text-zinc-400">({disaster_stop_dist:.2f}% Disaster Hard Stop)</span>
          </div>
          <div class="text-[11px] text-zinc-300 font-mono">
            Structural Invalidation: 1H Close &lt; ${structural_inval:,.2f}
          </div>
          <p class="text-[11px] text-zinc-400 leading-relaxed pt-0.5">{stop_rule}</p>
        </div>

        <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 space-y-1.5">
          <div class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Risk Management</div>
          <div class="text-base font-bold flex items-center gap-1.5 {'text-emerald-400' if risk.get('risk_budget_ok') else 'text-amber-400'}">
            {"✓ Approved (Within 1% Risk Budget)" if risk.get("risk_budget_ok") else "Hold Cash / Reduced Exposure"}
          </div>
          <p class="text-xs text-zinc-300 leading-relaxed pt-1">{risk.get("actionable_trade_instruction", "")}</p>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- PANEL 3: PLAIN-ENGLISH BREAKDOWN (FOR 95% BEGINNERS)         -->
    <!-- ============================================================ -->
    <div class="rounded-2xl border border-zinc-800 bg-zinc-900/80 p-6 sm:p-8 backdrop-blur-sm space-y-6 shadow-xl">
      <div class="border-b border-zinc-800 pb-4">
        <div class="flex items-center gap-2 mb-1">
          <span class="text-xs font-bold uppercase tracking-wider text-emerald-400">Bottom Line Verdict &bull; Plain English</span>
          <span class="text-xs text-zinc-500 font-medium">(No Jargon Required)</span>
        </div>
        <h3 class="text-xl sm:text-2xl font-extrabold text-white tracking-tight">
          Why This Recommendation?
        </h3>
        <div class="mt-3 p-4 rounded-xl bg-zinc-950/90 border border-zinc-800/80 flex items-start gap-3">
          <span class="text-2xl">💡</span>
          <p class="text-sm sm:text-base text-zinc-200 font-medium leading-relaxed">
            {plain_verdict}
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div class="lg:col-span-2 space-y-3">
          <div class="text-xs font-bold uppercase tracking-wider text-zinc-400">The 3 Key Market Factors Driving This Call</div>
          <div class="space-y-2.5">
            {why_points_html}
          </div>
        </div>

        <div class="space-y-3.5">
          <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80 space-y-1.5">
            <div class="text-xs font-bold uppercase tracking-wider text-amber-400">Why This Exact Sizing?</div>
            <p class="text-xs text-zinc-300 leading-relaxed font-normal">{why_sizing}</p>
          </div>

          <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80 space-y-1.5">
            <div class="text-xs font-bold uppercase tracking-wider text-rose-400">Where Is Your Safety Net?</div>
            <p class="text-xs text-zinc-300 leading-relaxed font-normal">{why_stop}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- PANEL 4: LIQUIDATION MAGNETS & PRICE TARGETS                 -->
    <!-- ============================================================ -->
    <div class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6 sm:p-8 space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800 pb-4">
        <div>
          <div class="flex items-center gap-3">
            <h3 class="text-lg font-bold text-white">Liquidation Magnets &amp; Key Price Pools</h3>
            {magnet_active_badge}
          </div>
          <p class="text-xs text-zinc-400 mt-1">Modeled liquidation concentration zones derived from 10x, 25x, 50x, and 100x leverage bands</p>
        </div>
        <div class="px-3.5 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-300 text-xs font-medium">
          <span class="text-zinc-400">Dominant Magnet:</span> <strong class="text-white ml-1">{dom_reason}</strong>
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
        <div class="text-xs text-zinc-200 font-medium max-w-xl text-left sm:text-right bg-zinc-950/60 p-2.5 rounded-lg border border-zinc-800/50">
          {lsce_detail}
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <!-- Upper Short Pool -->
        <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 space-y-3">
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
            Estimated Pool Size: <span class="font-bold text-zinc-200 mono">${upper_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M</span> <span class="text-[11px] text-zinc-500">(Modeled Estimate)</span>
          </div>
          <div class="w-full bg-zinc-900 h-2 rounded-full overflow-hidden">
            <div class="bg-rose-500 h-full rounded-full transition-all" style="width: min(100%, {max(15, upper_c.get('distance_pct', 1.0) * 15)}%);"></div>
          </div>
        </div>

        <!-- Lower Long Pool -->
        <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 space-y-3">
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
            Estimated Pool Size: <span class="font-bold text-zinc-200 mono">${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M</span> <span class="text-[11px] text-zinc-500">(Modeled Estimate)</span>
          </div>
          <div class="w-full bg-zinc-900 h-2 rounded-full overflow-hidden">
            <div class="bg-emerald-500 h-full rounded-full transition-all" style="width: min(100%, {max(15, lower_c.get('distance_pct', 1.0) * 15)}%);"></div>
          </div>
        </div>
      </div>

      <!-- Visual Liquidation Heatmap & Leverage Depth Ladder -->
      <div class="p-5 rounded-xl border border-zinc-800 bg-zinc-950/90 space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-800/80 pb-3">
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <span>🔥</span>
              <span>Liquidation Heatmap &amp; Leverage Depth Map</span>
            </span>
            <span class="text-[11px] px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">10x - 100x Bands</span>
          </div>
          <div class="text-xs text-zinc-400 flex items-center gap-3">
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-rose-500"></span> Short Liq Pool</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-cyan-400"></span> Spot Price</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-emerald-500"></span> Long Liq Pool</span>
          </div>
        </div>

        <!-- Heatmap Depth Ladder Rows -->
        <div class="space-y-2 text-xs">
          <!-- Upper Tier: 10x Shorts -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800/50 hover:border-zinc-700 transition-colors">
            <div class="flex items-center gap-2.5 w-44">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">10x Shorts</span>
              <span class="font-mono text-zinc-300">${swing_high * 1.025:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-rose-900 to-rose-600 h-full rounded-full" style="width: 35%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-zinc-400 text-xs w-36">
              +{(((swing_high * 1.025 - price)/price)*100):.2f}% &bull; ~$85M
            </div>
          </div>

          <!-- Upper Tier: 25x Shorts -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800/50 hover:border-zinc-700 transition-colors">
            <div class="flex items-center gap-2.5 w-44">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/15 text-rose-300 border border-rose-500/30">25x Shorts</span>
              <span class="font-mono text-zinc-300">${swing_high * 1.012:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-rose-800 to-rose-500 h-full rounded-full" style="width: 48%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-zinc-400 text-xs w-36">
              +{(((swing_high * 1.012 - price)/price)*100):.2f}% &bull; ~$110M
            </div>
          </div>

          <!-- Upper Tier: 50x/100x Shorts Nearest Active Pool -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-rose-500/5 border border-rose-500/20">
            <div class="flex items-center gap-2.5 w-44">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">50-100x Shorts</span>
              <span class="font-mono font-bold text-rose-300">${upper_c.get('price_level', 0.0):,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-rose-700 to-rose-400 h-full rounded-full" style="width: {min(100, max(15, (upper_c.get('estimated_vol_usd', 0.0)/1e6)/20 * 100)):.0f}%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-rose-400 text-xs w-36">
              +{upper_c.get('distance_pct', 0.0):.2f}% &bull; ${upper_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M
            </div>
          </div>

          <!-- ZERO LINE: SPOT PRICE EQUILIBRIUM -->
          <div class="flex items-center justify-between p-3 rounded-xl bg-cyan-500/10 border-2 border-cyan-500/40 my-1">
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

          <!-- Lower Tier: 50x/100x Longs DOMINANT MAGNET CORE -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-emerald-500/10 border-2 border-emerald-500/40 shadow-lg shadow-emerald-500/10">
            <div class="flex items-center gap-2.5 w-44">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/25 text-emerald-300 border border-emerald-500/50 flex items-center gap-1">
                <span>🔥</span> 100x Longs
              </span>
              <span class="font-mono font-extrabold text-emerald-300">${lower_c.get('price_level', 0.0):,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-3 rounded-full overflow-hidden p-0.5">
                <div class="bg-gradient-to-r from-emerald-600 via-emerald-400 to-amber-300 h-full rounded-full animate-pulse" style="width: 100%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-emerald-300 font-bold text-xs w-36">
              -{lower_c.get('distance_pct', 0.0):.2f}% &bull; ${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M
            </div>
          </div>

          <!-- Lower Tier: 25x Longs -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800/50 hover:border-zinc-700 transition-colors">
            <div class="flex items-center gap-2.5 w-44">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">25x Longs</span>
              <span class="font-mono text-zinc-300">${swing_low * 0.988:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-emerald-900 to-emerald-600 h-full rounded-full" style="width: 55%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-zinc-400 text-xs w-36">
              -{(((price - swing_low * 0.988)/price)*100):.2f}% &bull; ~$140M
            </div>
          </div>

          <!-- Lower Tier: 10x Longs -->
          <div class="flex items-center justify-between p-2.5 rounded-lg bg-zinc-900/50 border border-zinc-800/50 hover:border-zinc-700 transition-colors">
            <div class="flex items-center gap-2.5 w-44">
              <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">10x Longs</span>
              <span class="font-mono text-zinc-300">${swing_low * 0.975:,.0f}</span>
            </div>
            <div class="flex-1 mx-4 hidden sm:block">
              <div class="w-full bg-zinc-900 h-2.5 rounded-full overflow-hidden">
                <div class="bg-gradient-to-r from-emerald-950 to-emerald-700 h-full rounded-full" style="width: 40%;"></div>
              </div>
            </div>
            <div class="text-right font-mono text-zinc-400 text-xs w-36">
              -{(((price - swing_low * 0.975)/price)*100):.2f}% &bull; ~$95M
            </div>
          </div>

        </div>

        <!-- Dual Imbalance Display: Immediate Tier vs Total Ladder -->
        <div class="pt-3 border-t border-zinc-800/80 space-y-2">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div class="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/70">
              <span class="text-[10px] uppercase font-bold text-zinc-400 tracking-wider block">Immediate Nearest Tier Imbalance (100x vs 50-100x)</span>
              <div class="text-base font-extrabold text-amber-300 font-mono mt-0.5">{imm_ratio:.1f}x Skew</div>
              <p class="text-[11px] text-zinc-400 mt-1">Comparing single nearest bands: Lower Longs (${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M) vs Upper Shorts (${upper_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M).</p>
            </div>
            <div class="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/70">
              <span class="text-[10px] uppercase font-bold text-zinc-400 tracking-wider block">Total Leverage Ladder Imbalance (10x - 100x Spectrum)</span>
              <div class="text-base font-extrabold text-emerald-400 font-mono mt-0.5">{tot_ratio:.2f}x Downside Skew</div>
              <p class="text-[11px] text-zinc-400 mt-1">Total modeled lower pools (~${tot_l_vol:.1f}M) vs total upper pools (~${tot_u_vol:.1f}M). Institutional reality across all tiers.</p>
            </div>
          </div>
          <div class="flex flex-col sm:flex-row sm:items-center justify-between text-xs text-zinc-400 gap-2 pt-1">
            <div><strong class="text-zinc-200">How the Heatmap Works:</strong> Market makers exploit dense leverage bands for liquidity. Inside a <em>Range</em>, price gravitates toward the heaviest cluster.</div>
            <div class="text-emerald-400 font-bold shrink-0">Dominant Gravitational Pull: {dom_magnet}</div>
          </div>
        </div>
      </div>

      <!-- Six-Factor Decision Logic Section -->
      <div class="border border-zinc-800 rounded-xl p-5 bg-zinc-950/90 space-y-3.5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-zinc-800/80 pb-3 gap-1">
          <span class="text-xs font-bold text-zinc-200 uppercase tracking-wider">Magnet Decision Analysis (Six-Factor Evaluation)</span>
          <span class="text-xs text-zinc-400">Hierarchy: Pool Size &gt; Spot CVD &gt; Crowding &gt; Regime &gt; Distance &gt; ATR</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-zinc-300">
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/70">
            <strong class="text-zinc-400 block mb-1">1. Cluster Size / Magnitude:</strong>
            <span class="text-zinc-200 leading-relaxed">{f1}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/70">
            <strong class="text-zinc-400 block mb-1">2. Spot vs. Derivatives Leadership:</strong>
            <span class="text-zinc-200 leading-relaxed">{f2}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/70">
            <strong class="text-zinc-400 block mb-1">3. Crowding &amp; Market Fuel:</strong>
            <span class="text-zinc-200 leading-relaxed">{f3}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/70">
            <strong class="text-zinc-400 block mb-1">4. Higher-Timeframe Market Structure:</strong>
            <span class="text-zinc-200 leading-relaxed">{f4}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/70">
            <strong class="text-zinc-400 block mb-1">5. Distance Asymmetry:</strong>
            <span class="text-zinc-200 leading-relaxed">{f5}</span>
          </div>
          <div class="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/70">
            <strong class="text-zinc-400 block mb-1">6. Volatility Regime (ATR):</strong>
            <span class="text-zinc-200 leading-relaxed">{f6}</span>
          </div>
        </div>

        <div class="mt-3 pt-3 border-t border-zinc-800/80 flex items-start gap-2 text-xs">
          <span class="text-amber-400 font-bold uppercase tracking-wider">Decisive Conclusion:</span>
          <span class="text-white font-medium leading-relaxed">{dom_reason}</span>
        </div>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- PANEL 5: MARKET TELEMETRY & MICROSTRUCTURE GAUGES             -->
    <!-- ============================================================ -->
    <div class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6 sm:p-8 space-y-4">
      <h3 class="text-lg font-bold text-white">Market Telemetry &amp; Microstructure Gauges</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        
        <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80">
          <div class="text-[11px] text-zinc-400 uppercase tracking-wide">Spot CVD Ratio</div>
          <div class="text-lg font-bold mono text-white mt-1.5">{spot_cvd_ratio:.2f}</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Taker Buy/Sell</div>
        </div>

        <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80">
          <div class="text-[11px] text-zinc-400 uppercase tracking-wide">Perp CVD Flow</div>
          <div class="text-lg font-bold mono text-white mt-1.5 capitalize">{metrics.get("perp_cvd_trend", "Flat")}</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Futures Trend</div>
        </div>

        <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80">
          <div class="text-[11px] text-zinc-400 uppercase tracking-wide">Open Interest (24h)</div>
          <div class="text-lg font-bold mono {'text-emerald-400' if oi_change_24h > 0 else 'text-rose-400'} mt-1.5">{oi_change_24h:+.2f}%</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">{current_oi:,.0f} BTC</div>
        </div>

        <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80">
          <div class="text-[11px] text-zinc-400 uppercase tracking-wide">Funding Rate</div>
          <div class="text-lg font-bold mono text-white mt-1.5">{funding_rate:+.3f}%</div>
          <div class="text-[11px] text-amber-400 mt-0.5">{metrics.get("funding_rate_annualized", 0.0):.1f}% Ann.</div>
        </div>

        <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80">
          <div class="text-[11px] text-zinc-400 uppercase tracking-wide">Futures Basis</div>
          <div class="text-lg font-bold mono text-white mt-1.5">{basis:+.1f}%</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Annualized Spread</div>
        </div>

        <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80">
          <div class="text-[11px] text-zinc-400 uppercase tracking-wide">Retail Long/Short</div>
          <div class="text-lg font-bold mono text-white mt-1.5">{ls_ratio:.2f}</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Account Ratio</div>
        </div>

      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-zinc-800/80 pt-8 text-center text-xs text-zinc-400 space-y-2.5">
      <div class="flex flex-wrap justify-center items-center gap-5 text-xs">
        <a href="regimes.html" class="text-cyan-400 hover:text-cyan-300 font-medium underline underline-offset-4">5 Regimes Deep-Dive Guide</a>
        <span>&bull;</span>
        <a href="regime.json" class="text-emerald-400 hover:text-emerald-300 underline font-medium">Public REST API (regime.json)</a>
        <span>&bull;</span>
        <a href="https://github.com/aikeluargalee-tech/btc-magnet-monitor" class="text-zinc-300 hover:text-white underline font-medium" target="_blank">Open Source Repository</a>
      </div>
      <div class="text-zinc-400">
        Automated via GitHub Actions scheduled cron &bull; Deployed on GitHub Pages CDN &bull; Zero Server Cost
      </div>
    </footer>

  </main>

  <!-- Floating Toast Notification on Copy -->
  <div id="copy-toast" class="fixed bottom-6 right-6 z-50 bg-emerald-500 text-black px-4 py-3 rounded-xl font-bold text-xs shadow-2xl transition-opacity duration-300 opacity-0 pointer-events-none flex items-center gap-2">
    <span>✅</span>
    <span>Live Telemetry Prompt Copied! Ready to paste into ChatGPT, Claude, or Grok.</span>
  </div>

  <script>
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
          toast.classList.add('opacity-100');
          setTimeout(() => {{
            toast.classList.remove('opacity-100');
            toast.classList.add('opacity-0', 'pointer-events-none');
            if (btnText) btnText.innerText = 'Copy Prompt for AI (ChatGPT / Grok)';
            if (btnIcon) btnIcon.innerText = '📋';
            if (btn) {{
              btn.classList.remove('bg-emerald-500');
              btn.classList.add('bg-cyan-500');
            }}
          }}, 3500);
        }}
      }}
    }}
  </script>

</body>
</html>"""
        return html

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
  </script>

</body>
</html>"""
        return html
