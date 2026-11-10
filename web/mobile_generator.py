import datetime
import json
from typing import Dict, Any, Tuple

class MobileWebGenerator:
    """Generates the Mobile Cockpit Progressive Web Application (PWA) HTML,
    Web App Manifest, and Service Worker for BTC Magnet Monitor V2.
    """

    def render_manifest(self) -> str:
        manifest = {
            "name": "BTC Magnet Monitor V2",
            "short_name": "BTC Magnet",
            "description": "Observable 5-Regime Radar & Liquidation Telemetry Cockpit",
            "start_url": "./app.html",
            "display": "standalone",
            "background_color": "#060908",
            "theme_color": "#00ff66",
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "./icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "./icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }
        return json.dumps(manifest, indent=2)

    def render_service_worker(self) -> str:
        return """const CACHE_NAME = 'btc-magnet-mobile-v2';
const STATIC_ASSETS = [
  './app.html',
  './manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('regime.json')) {
    e.respondWith(
      fetch(e.request).catch(() => caches.match(e.request))
    );
  } else {
    e.respondWith(
      caches.match(e.request).then((res) => res || fetch(e.request))
    );
  }
});
"""

    def render_mobile_app(self, data: Dict[str, Any], raw_llm_prompt: str = "") -> str:
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})
        ts_iso = data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())

        spot_price = metrics.get("price", 74530.01)
        p_chg_24h = metrics.get("price_change_24h_pct", 0.71)
        daily_vwap = metrics.get("daily_vwap", spot_price * 1.004)
        weekly_vwap = metrics.get("weekly_vwap", spot_price * 1.002)
        ema_20d = metrics.get("ema_20d", spot_price * 1.025)
        ema_50d = metrics.get("ema_50d", spot_price * 1.042)
        ma_200d = metrics.get("ma_200d", 73195.0)
        swing_high = metrics.get("swing_high_4h", 75568.0)
        swing_low = metrics.get("swing_low_4h", 73750.0)
        base_floor = metrics.get("base_floor", 73510.0)

        vwap_dist_pct = ((spot_price - daily_vwap) / daily_vwap) * 100.0

        spot_vol = metrics.get("spot_vol_24h", 14851.0)
        spot_vol_ratio = metrics.get("spot_vol_ratio", 1.02)
        spot_cvd_ratio = metrics.get("spot_cvd_ratio", 1.28)
        spot_cvd_7d = metrics.get("spot_cvd_slope_7d", 1743.0)
        spot_cvd_14d = metrics.get("spot_cvd_slope_14d", 4829.0)
        perp_trend = metrics.get("perp_cvd_trend", "declining")
        bids_asks_depth = metrics.get("bids_asks_depth_ratio", 1.77)

        oi = metrics.get("open_interest", 9349.0)
        oi_24h = metrics.get("oi_change_24h_pct", -0.17)
        oi_1h = metrics.get("oi_change_1h_pct", -0.02)
        oi_4h = metrics.get("oi_change_4h_pct", -0.05)
        funding_rate = metrics.get("funding_rate", 0.000058) * 100.0
        funding_rate_ann = metrics.get("funding_rate_annualized", funding_rate * 3 * 365)
        basis = metrics.get("futures_basis_annualized", -1.22)
        ls_ratio = metrics.get("long_short_account_ratio", 1.85)

        atr = metrics.get("atr", 472.49)
        atr_comp = metrics.get("atr_compression_pct", 74.0)
        range_width = ((swing_high - swing_low) / max(spot_price, 1.0)) * 100

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_p = upper_c.get("price_level", 74880.0)
        u_d = upper_c.get("distance_pct", 0.07)
        u_atr = upper_c.get("distance_atr", 0.11)
        u_vol = upper_c.get("estimated_vol_usd", 4_200_000.0) / 1e6

        l_p = lower_c.get("price_level", 74760.0)
        l_d = lower_c.get("distance_pct", 0.09)
        l_atr = lower_c.get("distance_atr", 0.14)
        l_vol = lower_c.get("estimated_vol_usd", 102_800_000.0) / 1e6

        regime_id = regime.get("regime_id", "RANGE_LIQUIDATION_MAGNET")
        regime_name = regime.get("name", "Range / Liquidation Magnet")
        diagnosis = regime.get("diagnosis", "Positioning imbalance and forced liquidations dominate")
        score_str = regime.get("majority_score", "3/4 observations confirmed")
        rotation = regime.get("rotation", "Remain USDT")
        sizing = regime.get("sizing_factor", 0.0)
        action = regime.get("action", "Stand Aside (0.0x)")
        playbook = regime.get("action", "Defensive Cash (0.0x)")
        entry_inst = regime.get("entry_instruction", "Strict Cash (100% USDT). Treat bounces as exit liquidity. Only reverse on structure + Spot CVD reclaim.")

        stop_price = regime.get("stop_price", spot_price * 0.98)
        stop_dist = regime.get("stop_distance_pct", 2.0)
        disaster_stop = regime.get("disaster_stop_price", 72354.94)
        disaster_dist = regime.get("disaster_stop_distance_pct", 3.30)
        structural_inval = regime.get("structural_invalidation_level", 73750.00)
        stop_rule = regime.get("stop_rule", "Structural: 1H close < 4H swing low | Inviolable: Below 200D SMA & 25x shelf -0.7%")

        risk_budget_ok = risk.get("risk_budget_ok", True)
        actionable_trade_instruction = risk.get(
            "actionable_trade_instruction",
            "Maintain 100% USDT cash reserve. Strictly zero new buying."
        )

        plain_verdict = regime.get(
            "plain_english_verdict",
            "Bitcoin is in structural distribution. Bounces are being sold by institutions as exit liquidity."
        )
        why_points = regime.get("why_points", [
            "Sub-VWAP Trend: Price remains pinned beneath Daily and Weekly VWAP benchmarks with 20D/50D EMA overhead resistance.",
            "Depressed Volume Participation: Spot volume is running below the 20D moving average; bounces lack aggressive institutional taker buy volume.",
            "Defensive Capital Preservation: Preserving USDT cash in 100% reserve until authenticated Spot CVD and market structure reclaim occur."
        ])
        why_sizing = regime.get(
            "why_sizing_reason",
            f"Why {sizing*100:.0f}% Sizing? Sizing is strictly tied to post-sweep absorption proof. If sweep is in progress or untested, we hold 100% cash."
        )
        why_stop = regime.get(
            "why_stop_reason",
            f"Safety Net: Inviolable Disaster Stop at ${disaster_stop:,.2f} ({disaster_dist:.2f}% away), positioned safely below the 200D SMA and 25x liquidation shelf."
        )

        imm_ratio = regime.get("immediate_imbalance_ratio", 16.5)
        tot_ratio = regime.get("total_ladder_imbalance_ratio", 1.53)
        tot_l_vol = regime.get("total_ladder_lower_vol", 304.1)
        tot_u_vol = regime.get("total_ladder_upper_vol", 199.2)
        dom_magnet = regime.get("dominant_magnet", "Lower Long Sweep Magnet")
        dom_reason = regime.get("dominant_magnet_reason", f"LOWER (Immediate {imm_ratio:.1f}x / Ladder {tot_ratio:.2f}x; longs {ls_ratio/(1+ls_ratio)*100:.1f}% crowded)")

        # P0 Master Authorization Reconciliation:
        # A local sweep reclaim MUST NEVER display "BUY AUTHORIZED" if master allocation is 0.0x / Cash
        lsce_status = regime.get("lsce_status", "UNTESTED")
        if lsce_status == "SWEEP_AND_RECLAIM_CONFIRMED":
            if sizing > 0 and "USDT -> BTC" in rotation:
                lsce_badge_icon = "✅"
                lsce_badge_title = f"SWEEP & RECLAIM CONFIRMED (BUY AUTHORIZED {sizing:.2f}x)"
                lsce_badge_color = "var(--primary)"
                lsce_badge_bg = "rgba(0, 255, 102, 0.1)"
                lsce_badge_border = "rgba(0, 255, 102, 0.35)"
                lsce_detail = regime.get("lsce_detail", f"Lower liquidation shelf (${l_p:,.0f}) swept and reclaimed with positive spot absorption. Authorized {sizing:.2f}x entry.")
            else:
                lsce_badge_icon = "🛡️"
                lsce_badge_title = "LOCAL SWEEP OBSERVED — BUY BLOCKED BY MACRO REGIME"
                lsce_badge_color = "var(--warning)"
                lsce_badge_bg = "rgba(255, 184, 0, 0.1)"
                lsce_badge_border = "rgba(255, 184, 0, 0.35)"
                lsce_detail = f"Lower liquidation shelf (${l_p:,.0f}) swept, but new spot buying is strictly BLOCKED by macro regime ({regime_name}). Maintain 100% USDT Cash."
        elif lsce_status == "SWEEP_IN_PROGRESS":
            lsce_badge_icon = "⚠️"
            lsce_badge_title = "SWEEP IN PROGRESS (DO NOT BUY FALLING KNIFE)"
            lsce_badge_color = "var(--warning)"
            lsce_badge_bg = "rgba(255, 184, 0, 0.1)"
            lsce_badge_border = "rgba(255, 184, 0, 0.35)"
            lsce_detail = regime.get("lsce_detail", f"Price is actively piercing the ${l_p:,.0f} liquidation shelf. Do NOT buy active liquidations. Wait for absorption.")
        elif lsce_status == "SWEEP_FAILED_BREAKDOWN":
            lsce_badge_icon = "🌊"
            lsce_badge_title = "SWEEP FAILED / CASCADE RISK (100% CASH)"
            lsce_badge_color = "var(--danger)"
            lsce_badge_bg = "rgba(255, 51, 68, 0.1)"
            lsce_badge_border = "rgba(255, 51, 68, 0.35)"
            lsce_detail = regime.get("lsce_detail", f"Liquidation shelf at ${l_p:,.0f} failed to hold. Bids collapsed. Potential cascade in progress. Hold 100% USDT cash.")
        else:
            lsce_badge_icon = "⏸️"
            lsce_badge_title = "UNTESTED (MONITORING / CASH)"
            lsce_badge_color = "var(--text-muted)"
            lsce_badge_bg = "rgba(255, 255, 255, 0.05)"
            lsce_badge_border = "var(--border)"
            lsce_detail = regime.get("lsce_detail", "No active lower liquidation pool. Standing aside.")

        # Master Verdict Styling
        is_buy_authorized = (sizing > 0 and "USDT -> BTC" in rotation)
        if is_buy_authorized:
            verdict_hero_title = "ROTATE USDT → BTC"
            verdict_hero_icon = "🟢"
            verdict_hero_sub = f"{sizing:.2f}x Allocation • Buy Spot (Accumulate)"
            verdict_border_style = "border: 2px solid var(--primary); box-shadow: 0 0 24px rgba(0, 255, 102, 0.18);"
            verdict_badge_style = "background: rgba(0, 255, 102, 0.15); color: var(--primary); border: 1px solid rgba(0, 255, 102, 0.4);"
        elif "BTC -> USDT" in rotation:
            verdict_hero_title = "TRIM SPOT / ROTATE TO USDT"
            verdict_hero_icon = "🔴"
            verdict_hero_sub = "Harvest to Cash • Capital Preservation"
            verdict_border_style = "border: 2px solid var(--danger); box-shadow: 0 0 24px rgba(255, 51, 68, 0.18);"
            verdict_badge_style = "background: rgba(255, 51, 68, 0.15); color: var(--danger); border: 1px solid rgba(255, 51, 68, 0.4);"
        else:
            verdict_hero_title = "REMAIN 100% USDT CASH"
            verdict_hero_icon = "🛡️"
            verdict_hero_sub = "0.00x Allocation • Defensive Cash (Zero Buys)"
            verdict_border_style = "border: 2px solid var(--warning); box-shadow: 0 0 24px rgba(255, 184, 0, 0.18);"
            verdict_badge_style = "background: rgba(255, 184, 0, 0.15); color: var(--warning); border: 1px solid rgba(255, 184, 0, 0.4);"

        # Regime Tagline & Icon
        if regime_id == "SPOT_LED_EXPANSION":
            regime_icon = "🚀"
            regime_tagline = "Genuine spot buyers in control. Favorable environment for trend-following spot longs."
        elif regime_id == "LEVERAGED_FRAGILE_UPSIDE":
            regime_icon = "⚠️"
            regime_tagline = "Advance built on dangerous borrowed futures leverage. High probability of long squeeze."
        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            regime_icon = "🌊"
            regime_tagline = "Forced margin liquidation cascade in progress. Strictly avoid buying until selling ceases."
        elif regime_id == "DISTRIBUTION_BEAR_CONTINUATION":
            regime_icon = "📉"
            regime_tagline = "Structural seller control. Whales distributing into retail bounces. Cash preservation priority."
        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            regime_icon = "🧲"
            regime_tagline = "Price bound within defined horizontal channel. Positioning imbalance and liquidation magnets dominate."
        else:
            regime_icon = "⚖️"
            regime_tagline = "Market indicators conflicting or transitioning between regimes. Capital preservation in cash."

        matched_criteria = regime.get("matched_criteria", [
            f"Price below Daily VWAP, 20D EMA, and 50D EMA",
            f"Spot volume depressed ({spot_vol_ratio:.2f}x 20D MA)",
            f"Trapped longs paying funding ({funding_rate/100:.3f}%) / compressed basis ({basis:.1f}%)"
        ])

        magnet_factors = regime.get("magnet_factors", {})
        f1 = magnet_factors.get("factor_1_size", f"Immediate Tier: LOWER is {imm_ratio:.1f}x larger (${l_vol:.1f}M vs ${u_vol:.1f}M) | Total Ladder: LOWER is {tot_ratio:.2f}x (${tot_l_vol:.1f}M vs ${tot_u_vol:.1f}M)")
        f2 = magnet_factors.get("factor_2_spot_leadership", f"Spot CVD ratio {spot_cvd_ratio:.2f} vs Perp CVD {perp_trend}")
        f3 = magnet_factors.get("factor_3_crowding_fuel", f"Funding {funding_rate/100:.3f}%, Retail L/S {ls_ratio:.2f} ({(ls_ratio/(1+ls_ratio))*100:.1f}% long)")
        f4 = magnet_factors.get("factor_4_regime_structure", "Range compression with downside fragility")
        f5 = magnet_factors.get("factor_5_asymmetry", f"LOWER is {l_d:.2f}% away vs UPPER {u_d:.2f}% away")
        f6 = magnet_factors.get("factor_6_atr_volatility", f"ATR compressed {atr_comp:.1f}%")

        # Visual Heatmap Ladder Bar Widths (proportional to volume)
        max_vol_ref = max(tot_l_vol, 150.0)
        w_10x_short = min(100, max(14, int((85.0 / max_vol_ref) * 100)))
        w_25x_short = min(100, max(14, int((110.0 / max_vol_ref) * 100)))
        w_50_short = min(100, max(14, int((u_vol / max_vol_ref) * 100)))
        w_100_long = min(100, max(18, int((l_vol / max_vol_ref) * 100)))
        w_25x_long = min(100, max(14, int((140.0 / max_vol_ref) * 100)))
        w_10x_long = min(100, max(14, int((95.0 / max_vol_ref) * 100)))

        # Ladder Prices
        p_10x_short = swing_high * 1.025
        d_10x_short = ((p_10x_short - spot_price) / spot_price) * 100
        p_25x_short = swing_high * 1.012
        d_25x_short = ((p_25x_short - spot_price) / spot_price) * 100

        p_25x_long = swing_low * 0.988
        d_25x_long = ((spot_price - p_25x_long) / spot_price) * 100
        p_10x_long = swing_low * 0.975
        d_10x_long = ((spot_price - p_10x_long) / spot_price) * 100

        # Pre-computed HTML blocks
        evidence_items_html = "".join([
            f'<div class="evidence-item"><span class="evidence-check">✓</span><span>{item}</span></div>'
            for item in matched_criteria
        ])

        why_points_html = "".join([
            f'<div class="why-factor-row"><div class="why-num">{idx+1}</div><div style="color: var(--text-main); font-size: 11.5px; line-height: 1.45;">{pt}</div></div>'
            for idx, pt in enumerate(why_points)
        ])

        escaped_prompt = json.dumps(raw_llm_prompt)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>BTC Magnet Monitor V2 | Spot Decision Cockpit & AI Telemetry</title>
  
  <meta name="theme-color" content="#030804">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="BTC Magnet">
  <link rel="manifest" href="./manifest.json">

  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
      -webkit-tap-highlight-color: transparent;
    }}

    :root {{
      --bg-main: #060908;
      --bg-card: #0a110d;
      --bg-card-sub: #0f1c14;
      --border: #1a2f22;
      --primary: #00ff66;
      --primary-dim: rgba(0, 255, 102, 0.12);
      --warning: #ffb800;
      --warning-dim: rgba(255, 184, 0, 0.12);
      --danger: #ff3344;
      --danger-dim: rgba(255, 51, 68, 0.12);
      --info: #00e5ff;
      --info-dim: rgba(0, 229, 255, 0.12);
      --text-main: #f0fdf4;
      --text-muted: #8b9d92;
      --font-mono: 'JetBrains Mono', monospace, -apple-system;
      --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}

    /* RETRO IBM THEME OVERRIDES */
    body.theme-ibm {{
      --bg-main: #0a0802;
      --bg-card: #141005;
      --bg-card-sub: #1e1808;
      --border: #3b2e10;
      --primary: #ffb000;
      --primary-dim: rgba(255, 176, 0, 0.15);
      --text-main: #fff8e7;
      --text-muted: #a69268;
    }}

    
    /* BINANCE DARK THEME OVERRIDES (FROM META AI SPEC) */
    body.theme-binance {{
      --bg-main: #0B0E11;
      --bg-card: #12161C;
      --bg-card-sub: #171B20;
      --border: #2B3139;
      --primary: #0ECB81;
      --primary-dim: rgba(14, 203, 129, 0.15);
      --warning: #F0B90B;
      --warning-dim: rgba(240, 185, 11, 0.15);
      --danger: #F6465D;
      --danger-dim: rgba(246, 70, 93, 0.15);
      --info: #00C4E8;
      --info-dim: rgba(0, 196, 232, 0.15);
      --text-main: #EAECEF;
      --text-muted: #848E9C;
    }}

    /* SLATE PRO THEME OVERRIDES */
    body.theme-slate {{
      --bg-main: #090d16;
      --bg-card: #0f172a;
      --bg-card-sub: #1e293b;
      --border: #334155;
      --primary: #38bdf8;
      --primary-dim: rgba(56, 189, 248, 0.15);
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
    }}

    body {{
      background: var(--bg-main);
      color: var(--text-main);
      font-family: var(--font-sans);
      font-size: 13px;
      line-height: 1.45;
      padding-bottom: 96px;
      overflow-x: hidden;
    }}

    .app-container {{
      max-width: 480px;
      margin: 0 auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    /* STICKY TOP TICKER BAR */
    .top-ticker-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
    }}

    .brand-group {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .brand-icon {{
      width: 26px;
      height: 26px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--primary-dim);
      border: 1px solid var(--primary);
      border-radius: 7px;
      font-size: 14px;
    }}

    .brand-title {{
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.5px;
      color: #ffffff;
    }}

    .theme-toggle-btn {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      color: var(--text-muted);
      font-size: 10px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 6px;
      font-family: var(--font-mono);
      cursor: pointer;
    }}

    /* ======================================================== */
    /* LEVEL 1: EXECUTIVE DECISION HERO (ABOVE THE FOLD)        */
    /* ======================================================== */
    
    /* EXPERIENCE MODE TOGGLE (BEGINNER VS DESK) */
    .mode-toggle-wrap {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-bottom: 2px;
    }}

    .mode-toggle-bar {{
      display: flex;
      align-items: center;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 3px;
      gap: 4px;
    }}

    .mode-btn {{
      flex: 1;
      height: 32px;
      border: 0;
      border-radius: 999px;
      background: transparent;
      color: var(--text-muted);
      font-weight: 700;
      font-size: 11.5px;
      cursor: pointer;
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
    }}

    .mode-btn.active {{
      background: var(--warning);
      color: #111111;
      font-weight: 800;
      box-shadow: 0 2px 8px rgba(240, 185, 11, 0.25);
    }}

    .mode-caption {{
      font-size: 10px;
      color: var(--text-muted);
      text-align: center;
    }}

    /* INTERACTIVE RISK CALCULATOR */
    .calc-card {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      margin-top: 8px;
    }}

    .calc-top-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .calc-top-label {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 10.5px;
      font-weight: 800;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .calc-money-input {{
      display: flex;
      align-items: center;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 2px 8px;
    }}

    .calc-money-input span {{
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-muted);
      font-weight: 700;
    }}

    .calc-money-input input {{
      width: 82px;
      background: transparent;
      border: 0;
      outline: 0;
      color: #ffffff;
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 700;
      text-align: right;
      padding: 3px 0;
    }}

    .calc-slider {{
      width: 100%;
      accent-color: var(--warning);
      margin: 10px 0 8px;
      cursor: pointer;
    }}

    .calc-breakdown-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      padding-top: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.06);
    }}

    .calc-metric-lbl {{
      font-size: 9.5px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }}

    .calc-metric-val {{
      font-family: var(--font-mono);
      font-weight: 900;
      font-size: 14px;
      margin: 1px 0;
    }}

    .calc-metric-sub {{
      font-size: 9.5px;
      color: var(--text-muted);
      line-height: 1.3;
    }}

    /* ACCORDION CATEGORIES */
    .dict-cat-header {{
      cursor: pointer;
      user-select: none;
    }}

    .cat-chevron {{
      font-size: 10px;
      color: var(--text-muted);
      transition: transform 0.2s ease;
    }}

    .dict-cat-card.collapsed .dict-rows {{
      display: none;
    }}

    .dict-cat-card.collapsed .cat-chevron {{
      transform: rotate(-90deg);
    }}

    .executive-decision-card {{
      background: var(--bg-card);
      border-radius: 14px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .decision-top-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
    }}

    .decision-badge {{
      font-size: 10px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      padding: 3px 8px;
      border-radius: 6px;
    }}

    .live-feed-pill {{
      font-size: 10px;
      font-family: var(--font-mono);
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .decision-main-row {{
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .decision-callout-title {{
      font-size: 22px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: -0.3px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .decision-callout-sub {{
      font-size: 12px;
      font-weight: 700;
      color: var(--text-muted);
    }}

    .quick-price-band {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
      font-family: var(--font-mono);
    }}

    .price-band-val {{
      font-size: 16px;
      font-weight: 900;
      color: #ffffff;
    }}

    .price-band-lbl {{
      font-size: 10px;
      color: var(--text-muted);
      text-transform: uppercase;
    }}

    .executive-narrative-box {{
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 12px;
      line-height: 1.45;
      color: var(--text-main);
    }}

    .safety-net-callout {{
      background: rgba(255, 51, 68, 0.08);
      border-left: 3px solid var(--danger);
      border-radius: 0 8px 8px 0;
      padding: 8px 12px;
      font-size: 11.5px;
      line-height: 1.4;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    /* ======================================================== */
    /* LEVEL 2: PLAIN-ENGLISH DECISION & RISK SAFEGUARDS        */
    /* ======================================================== */
    .card-panel {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .panel-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 6px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
    }}

    .panel-title {{
      font-size: 13px;
      font-weight: 900;
      color: #ffffff;
      display: flex;
      align-items: center;
      gap: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .why-factor-row {{
      display: flex;
      gap: 8px;
      align-items: flex-start;
      margin-top: 6px;
    }}

    .why-num {{
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: var(--primary-dim);
      border: 1px solid var(--primary);
      color: var(--primary);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 800;
      flex-shrink: 0;
      margin-top: 1px;
    }}

    .risk-breakdown-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }}

    .risk-spec-box {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 11px;
    }}

    /* ======================================================== */
    /* LEVEL 3: VERIFIED LIVE TELEMETRY & AI PROMPT ENGINE      */
    /* ======================================================== */
    .dict-categories-stack {{
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .dict-cat-card {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
    }}

    .dict-cat-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11.5px;
      font-weight: 800;
      margin-bottom: 8px;
      padding-bottom: 4px;
      border-bottom: 1px solid var(--border);
    }}

    .cat-title-1 {{ color: var(--info); }}
    .cat-title-2 {{ color: var(--primary); }}
    .cat-title-3 {{ color: var(--warning); }}
    .cat-title-4 {{ color: var(--danger); }}

    .dict-rows {{
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-family: var(--font-mono);
      font-size: 11px;
    }}

    .dict-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 2px 0;
    }}

    .dict-lbl {{ color: var(--text-muted); }}
    .dict-val {{ color: var(--text-main); font-weight: 600; }}
    .dict-val.accent {{ color: var(--primary); font-weight: 800; }}
    .dict-val.warn {{ color: var(--warning); font-weight: 800; }}
    .dict-val.danger {{ color: var(--danger); font-weight: 800; }}

    .btn-copy-prompt {{
      width: 100%;
      background: var(--primary);
      color: #030804;
      border: none;
      border-radius: 10px;
      padding: 14px 16px;
      font-size: 13.5px;
      font-weight: 900;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      letter-spacing: 0.3px;
      box-shadow: 0 4px 14px rgba(0, 255, 102, 0.4);
      transition: transform 0.1s ease, background 0.2s ease;
      margin-top: 10px;
    }}

    .btn-copy-prompt:active {{
      transform: scale(0.97);
    }}

    /* ======================================================== */
    /* LEVEL 4: INSTITUTIONAL REFERENCE SUITE (ADVANCED)        */
    /* ======================================================== */
    .section-separator {{
      display: flex;
      align-items: center;
      text-align: center;
      margin: 12px 0 4px 0;
      color: var(--text-muted);
      font-size: 10px;
      font-weight: 800;
      letter-spacing: 1px;
      text-transform: uppercase;
    }}

    .section-separator::before,
    .section-separator::after {{
      content: '';
      flex: 1;
      border-bottom: 1px dashed var(--border);
    }}

    .section-separator span {{
      padding: 0 10px;
      color: var(--info);
    }}

    /* PROPORTIONAL VISUAL HEATMAP BARS */
    .heatmap-visual-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .visual-ladder-stack {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-family: var(--font-mono);
      font-size: 11px;
    }}

    .v-ladder-item {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .v-ladder-item.short {{
      border-color: rgba(255, 51, 68, 0.25);
    }}

    .v-ladder-item.long {{
      border-color: rgba(0, 255, 102, 0.25);
    }}

    .v-ladder-item.dominant {{
      border: 2px solid var(--primary);
      background: rgba(0, 255, 102, 0.08);
      box-shadow: 0 0 14px rgba(0, 255, 102, 0.18);
    }}

    .v-ladder-item.spot-zero {{
      border: 2px solid var(--info);
      background: rgba(0, 229, 255, 0.12);
      padding: 10px;
    }}

    .v-row-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .bar-track {{
      width: 100%;
      height: 8px;
      background: rgba(0, 0, 0, 0.4);
      border-radius: 4px;
      overflow: hidden;
    }}

    .bar-fill-short {{
      height: 100%;
      background: linear-gradient(90deg, #991b1b, #ef4444);
      border-radius: 4px;
    }}

    .bar-fill-long {{
      height: 100%;
      background: linear-gradient(90deg, #065f46, #10b981);
      border-radius: 4px;
    }}

    .bar-fill-dominant {{
      height: 100%;
      background: linear-gradient(90deg, #059669, #34d399, #fde047);
      border-radius: 4px;
      box-shadow: 0 0 8px rgba(0, 255, 102, 0.6);
    }}

    /* SKEW CHIPS */
    .skew-chips-row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}

    .skew-chip {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      font-size: 10.5px;
    }}

    /* 6 FACTORS & GAUGES */
    .factors-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 6px;
    }}

    .factor-item {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 7px;
      padding: 8px 10px;
      font-size: 11px;
      line-height: 1.35;
    }}

    .gauges-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }}

    .gauge-card {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 9px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .gauge-lbl {{
      font-size: 9px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 700;
    }}

    .gauge-val {{
      font-size: 14.5px;
      font-weight: 800;
      font-family: var(--font-mono);
      color: #ffffff;
    }}

    .gauge-sub {{
      font-size: 9px;
      color: var(--text-muted);
    }}

    /* 5-REGIME MATRIX */
    .matrix-grid {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 6px;
      font-size: 10.5px;
      text-align: center;
      font-weight: 700;
    }}

    @media (min-width: 420px) {{
      .matrix-grid {{
        grid-template-columns: repeat(3, 1fr);
      }}
    }}

    .matrix-item {{
      padding: 7px 8px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--bg-card-sub);
      color: var(--text-muted);
    }}

    .matrix-item.active {{
      border-color: var(--info);
      background: rgba(0, 229, 255, 0.12);
      color: #ffffff;
      box-shadow: 0 0 10px rgba(0, 229, 255, 0.25);
    }}

    /* STICKY BOTTOM QUICK-AUDIT BAR */
    .sticky-audit-bar {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(6, 9, 8, 0.94);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-top: 1px solid var(--border);
      padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px));
      z-index: 50;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      box-shadow: 0 -8px 24px rgba(0, 0, 0, 0.6);
    }}

    .sticky-ticker {{
      display: flex;
      flex-direction: column;
      font-family: var(--font-mono);
    }}

    .sticky-px {{
      font-size: 13px;
      font-weight: 800;
      color: #ffffff;
    }}

    .sticky-state {{
      font-size: 9.5px;
      color: var(--text-muted);
      text-transform: uppercase;
    }}

    .sticky-btn {{
      background: var(--primary);
      color: #030804;
      border: none;
      border-radius: 8px;
      padding: 9px 14px;
      font-size: 12px;
      font-weight: 900;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      white-space: nowrap;
    }}

    /* TOAST */
    .toast-overlay {{
      position: fixed;
      bottom: 64px;
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: var(--primary);
      color: #030804;
      font-weight: 800;
      font-size: 12px;
      padding: 10px 18px;
      border-radius: 30px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.8);
      display: flex;
      align-items: center;
      gap: 8px;
      z-index: 9999;
      opacity: 0;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      pointer-events: none;
      white-space: nowrap;
    }}

    .toast-overlay.active {{
      transform: translateX(-50%) translateY(0);
      opacity: 1;
    }}
  </style>
</head>
<body class="theme-nvg">

  <div class="app-container">

    <!-- TOP TICKER BAR -->
    <header class="top-ticker-bar">
      <div class="brand-group">
        <div class="brand-icon">🧲</div>
        <div>
          <div class="brand-title">BTC Magnet Monitor</div>
          <div style="font-size: 9.5px; color: var(--text-muted); font-family: var(--font-mono);">SPOT-ONLY • ZERO LEVERAGE</div>
        </div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 9.5px; color: var(--primary); font-family: var(--font-mono); font-weight: 700;">● LIVE FEED</span>
        <button class="theme-toggle-btn" id="theme-btn" onclick="cycleTheme()">NVG</button>
      </div>
    </header>

    <!-- ======================================================== -->
    <!-- LEVEL 1: EXECUTIVE DECISION HERO (FIRST 3 SECONDS)       -->
    <!-- ======================================================== -->
    
    <!-- EXPERIENCE MODE TOGGLE (BEGINNER VS DESK) -->
    <div class="mode-toggle-wrap">
      <div class="mode-toggle-bar" role="group" aria-label="Experience Mode">
        <button id="btn-mode-beginner" class="mode-btn active" onclick="setExperienceMode('beginner')">
          <span>🌱</span>
          <span>Beginner</span>
        </button>
        <button id="btn-mode-desk" class="mode-btn" onclick="setExperienceMode('desk')">
          <span>💼</span>
          <span>Desk (Pro)</span>
        </button>
      </div>
      <div class="mode-caption" id="mode-caption-text">
        Beginner mode: Executive decision &amp; plain rationale first. Switch to Desk for full data expansion.
      </div>
    </div>


    <section class="executive-decision-card" style="{verdict_border_style}">
      
      <div class="decision-top-meta">
        <span class="decision-badge" style="{verdict_badge_style}">
          CURRENT SYSTEM DIRECTIVE
        </span>
        <div class="live-feed-pill">
          <span>Binance &amp; Deribit</span>
          <span>•</span>
          <span id="data-age-tag">Updated live</span>
        </div>
      </div>

      <div class="decision-main-row">
        <div class="decision-callout-title">
          <span>{verdict_hero_icon}</span>
          <span id="hero-action-title">{verdict_hero_title}</span>
        </div>
        <div class="decision-callout-sub" id="hero-action-sub">
          {verdict_hero_sub}
        </div>
      </div>

      <!-- Quick Spot Price & VWAP Benchmark Band -->
      <div class="quick-price-band">
        <div>
          <div class="price-band-lbl">Spot Benchmark</div>
          <div class="price-band-val" id="d-spot-px">${spot_price:,.2f}</div>
          <div style="font-size: 9.5px; color: {'var(--primary)' if p_chg_24h >= 0 else 'var(--danger)'};">
            {p_chg_24h:+.2f}% (24h)
          </div>
        </div>
        <div>
          <div class="price-band-lbl">vs Daily VWAP</div>
          <div class="price-band-val" id="d-vwap-delta" style="color: {'var(--primary)' if vwap_dist_pct >= 0 else 'var(--danger)'};">
            {vwap_dist_pct:+.2f}%
          </div>
          <div style="font-size: 9.5px; color: var(--text-muted);">
            VWAP: ${daily_vwap:,.0f}
          </div>
        </div>
      </div>

      <!-- Active Market Regime Pill -->
      <div style="background: var(--bg-card-sub); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px; display: flex; justify-content: space-between; align-items: center;">
        <div style="display: flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 800; color: #ffffff;">
          <span>{regime_icon}</span>
          <span id="regime-name">{regime_name}</span>
        </div>
        <span style="font-size: 10px; font-family: var(--font-mono); color: var(--text-muted);">{score_str}</span>
      </div>

      <!-- 1-Sentence Executive Verdict -->
      <div class="executive-narrative-box" id="regime-diag">
        {diagnosis}. {plain_verdict}
      </div>

      <!-- Safety Net Callout -->
      <div class="safety-net-callout">
        <strong style="color: var(--danger); font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.5px;">
          🛡️ Inviolable Risk Safeguard
        </strong>
        <div style="color: var(--text-main);">
          {"Zero exposure required. Maintain 100% USDT cash patience." if sizing == 0 else f"Disaster Hard Stop at ${disaster_stop:,.2f} (-{disaster_dist:.2f}%), placed below 200D SMA."}
        </div>
      </div>

    </section>

    <!-- ======================================================== -->
    <!-- LEVEL 2: PLAIN-ENGLISH DECISION & RISK PROTECTION        -->
    <!-- ======================================================== -->
    <section class="card-panel">
      <div class="panel-header">
        <div class="panel-title">
          <span>💡</span>
          <span>Plain-English Decision Rationale</span>
        </div>
        <span style="font-size: 10px; color: var(--text-muted);">(No Jargon Required)</span>
      </div>

      <div>
        <div style="font-size: 10.5px; font-weight: 800; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px;">
          The 3 Key Market Factors Driving This Call
        </div>
        {why_points_html}
      </div>

      <!-- Dedicated Risk Protection Box -->
      <div class="risk-breakdown-grid" style="margin-top: 4px;">
        <div class="risk-spec-box" style="border-left: 3px solid var(--primary);">
          <div style="font-size: 9.5px; font-weight: 800; color: var(--text-muted); text-transform: uppercase;">
            Portfolio Risk Limit
          </div>
          <div style="font-size: 14px; font-weight: 900; color: var(--primary); font-family: var(--font-mono); margin: 2px 0;">
            1.00% Maximum Portfolio Risk Cap
          </div>
          <div style="font-size: 10.5px; color: var(--text-main);">
            {"If in USDT Cash: Do nothing. Zero risk. Your job is to wait." if sizing == 0 else f"Authorized Cash Deploy: {int(sizing*100*0.4)}% of available USDT (strictly capped at 0.99% portfolio loss)."}
          </div>
        </div>

        <div class="risk-spec-box" style="border-left: 3px solid var(--danger);">
          <div style="font-size: 9.5px; font-weight: 800; color: var(--text-muted); text-transform: uppercase;">
            Dual Inviolable Boundaries
          </div>
          <div style="font-size: 11px; font-family: var(--font-mono); color: var(--warning); margin-top: 3px;">
            • Thesis Wrong If: 1H Candle Close &lt; ${structural_inval:,.2f}
          </div>
          <div style="font-size: 11px; font-family: var(--font-mono); color: var(--danger); margin-top: 2px;">
            • Emergency Hard Stop: ${disaster_stop:,.2f} (-{disaster_dist:.2f}%)
          </div>
          <div style="font-size: 10px; color: var(--text-muted); margin-top: 4px;">
            Placed safely below both the 200D SMA (${ma_200d:,.0f}) and 25x shelf. Never average down into an invalidated thesis.
          </div>
        </div>
      </div>


      <!-- INTERACTIVE 1% RISK BUDGET CALCULATOR (PORTFOLIO SLIDER) -->
      <div class="calc-card">
        <div class="calc-top-row">
          <div class="calc-top-label">
            <span>🧮</span>
            <span>Portfolio Risk Calculator</span>
          </div>
          <div class="calc-money-input">
            <span>$</span>
            <input id="portfolio-input" type="number" min="0" max="1000000" step="500" value="10000" oninput="onPortfolioChange(this.value)">
          </div>
        </div>

        <input id="portfolio-slider" class="calc-slider" type="range" min="1000" max="100000" step="500" value="10000" oninput="onPortfolioChange(this.value)" aria-label="Portfolio size slider">

        <div class="calc-breakdown-grid">
          <div>
            <div class="calc-metric-lbl">1% Max Risk Cap</div>
            <div class="calc-metric-val" id="calc-risk-cap" style="color: var(--warning);">$100</div>
            <div class="calc-metric-sub">Max allowed dollar loss on thesis invalidation</div>
          </div>
          <div style="text-align: right;">
            <div class="calc-metric-lbl">Spot Capital Deploy</div>
            <div class="calc-metric-val" id="calc-deploy-amt" style="color: {'var(--warning)' if sizing == 0 else 'var(--primary)'};">
              {"$0 (100% USDT)" if sizing == 0 else f"${int(10000 * 0.30):,} Spot BTC"}
            </div>
            <div class="calc-metric-sub" id="calc-deploy-sub">
              {"Patience: Zero loss risk" if sizing == 0 else f"Capped at {sizing*100*0.4:.0f}% cash deploy"}
            </div>
          </div>
        </div>
      </div>

    </section>

    <!-- ======================================================== -->
    <!-- LEVEL 3: VERIFIED LIVE TELEMETRY & AI PROMPT ENGINE      -->
    <!-- ======================================================== -->
    <section class="card-panel" style="border: 2px solid var(--primary); box-shadow: 0 0 20px rgba(0, 255, 102, 0.1);">
      <div class="panel-header">
        <div class="panel-title" style="color: var(--primary);">
          <span>📊</span>
          <span>Verified Live Telemetry • AI Prompt Engine</span>
        </div>
        <span id="dict-expand-count" style="font-size: 9.5px; font-family: var(--font-mono); color: var(--text-muted); background: var(--bg-card-sub); padding: 2px 6px; border-radius: 4px;">4/4 expanded</span>
      </div>

      <p style="font-size: 11.5px; color: var(--text-muted); line-height: 1.45;">
        Don't rely blindly on our verdict. Click below to copy the verified live market positioning metrics and paste directly into <strong>ChatGPT, Claude, Grok, or Gemini</strong> for an instant second opinion.
      </p>

      <!-- 4 Organized Categories -->
      <div class="dict-categories-stack">

        <!-- 1. Price & Structure -->
        <div class="dict-cat-card" id="cat-card-1">
          <div class="dict-cat-header cat-title-1" onclick="toggleCategory(1)">
            <span>1. Price &amp; Structure</span>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="font-size: 9px; color: var(--text-muted);">MACRO HORIZON</span><span class="cat-chevron" id="cat-chev-1">▼</span></div>
          </div>
          <div class="dict-rows">
            <div class="dict-row"><span class="dict-lbl">Spot Price:</span><span id="d-spot-px-2" class="dict-val" style="color: #ffffff; font-weight: 900;">${spot_price:,.2f}</span></div>
            <div class="dict-row"><span class="dict-lbl">Daily VWAP:</span><span id="d-vwap" class="dict-val">${daily_vwap:,.2f}</span></div>
            <div class="dict-row"><span class="dict-lbl">Weekly VWAP:</span><span id="d-w-vwap" class="dict-val">${weekly_vwap:,.2f}</span></div>
            <div class="dict-row"><span class="dict-lbl">20D EMA:</span><span id="d-ema20" class="dict-val">${ema_20d:,.2f}</span></div>
            <div class="dict-row"><span class="dict-lbl">50D EMA:</span><span id="d-ema50" class="dict-val">${ema_50d:,.2f}</span></div>
            <div class="dict-row"><span class="dict-lbl">200D SMA:</span><span id="d-sma200" class="dict-val">${ma_200d:,.2f}</span></div>
            <div class="dict-row"><span class="dict-lbl">4H Swing Range:</span><span id="d-range" class="dict-val">${swing_low:,.0f} - ${swing_high:,.0f}</span></div>
            <div class="dict-row"><span class="dict-lbl">3D Base Floor:</span><span id="d-floor" class="dict-val">${base_floor:,.2f}</span></div>
          </div>
        </div>

        <!-- 2. Order Flow & CVD -->
        <div class="dict-cat-card" id="cat-card-2">
          <div class="dict-cat-header cat-title-2" onclick="toggleCategory(2)">
            <span>2. Order Flow &amp; CVD</span>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="font-size: 9px; color: var(--text-muted);">SPOT ABSORPTION</span><span class="cat-chevron" id="cat-chev-2">▼</span></div>
          </div>
          <div class="dict-rows">
            <div class="dict-row"><span class="dict-lbl">Spot CVD Ratio:</span><span id="d-cvd-ratio" class="dict-val accent">{spot_cvd_ratio:.2f}</span></div>
            <div class="dict-row"><span class="dict-lbl">24h Spot Volume:</span><span id="d-spot-vol" class="dict-val">{spot_vol:,.0f} BTC</span></div>
            <div class="dict-row"><span class="dict-lbl">Volume / 20D MA:</span><span id="d-vol-ratio" class="dict-val">{spot_vol_ratio:.2f}x</span></div>
            <div class="dict-row"><span class="dict-lbl">7D Spot CVD Slope:</span><span id="d-cvd-7d" class="dict-val">{spot_cvd_7d:+.0f}</span></div>
            <div class="dict-row"><span class="dict-lbl">14D Spot CVD Slope:</span><span id="d-cvd-14d" class="dict-val">{spot_cvd_14d:+.0f}</span></div>
            <div class="dict-row"><span class="dict-lbl">Perp CVD Trend:</span><span id="d-perp-trend" class="dict-val" style="text-transform: capitalize;">{perp_trend}</span></div>
            <div class="dict-row"><span class="dict-lbl">Order Depth Ratio:</span><span id="d-depth-ratio" class="dict-val">{bids_asks_depth:.2f}</span></div>
          </div>
        </div>

        <!-- 3. Derivatives Crowding -->
        <div class="dict-cat-card" id="cat-card-3">
          <div class="dict-cat-header cat-title-3" onclick="toggleCategory(3)">
            <span>3. Derivatives Crowding</span>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="font-size: 9px; color: var(--text-muted);">LEVERAGE EXPOSURE</span><span class="cat-chevron" id="cat-chev-3">▼</span></div>
          </div>
          <div class="dict-rows">
            <div class="dict-row"><span class="dict-lbl">Open Interest:</span><span id="d-oi" class="dict-val">{oi:,.0f} BTC</span></div>
            <div class="dict-row"><span class="dict-lbl">OI 24h Change:</span><span id="d-oi-24h" class="dict-val">{oi_24h:+.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">OI 1h Change:</span><span id="d-oi-1h" class="dict-val">{oi_1h:+.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">OI 4h Change:</span><span id="d-oi-4h" class="dict-val">{oi_4h:+.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">Funding Rate (8h):</span><span id="d-funding" class="dict-val">{funding_rate/100:+.4f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">Futures Basis Ann.:</span><span id="d-basis" class="dict-val">{basis:+.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">Retail Long/Short:</span><span id="d-ls-ratio" class="dict-val warn">{ls_ratio:.2f}</span></div>
          </div>
        </div>

        <!-- 4. Volatility & Magnets -->
        <div class="dict-cat-card" id="cat-card-4">
          <div class="dict-cat-header cat-title-4" onclick="toggleCategory(4)">
            <span>4. Volatility &amp; Magnets</span>
            <div style="display: flex; align-items: center; gap: 6px;"><span style="font-size: 9px; color: var(--text-muted);">LIQUIDITY DEPTH</span><span class="cat-chevron" id="cat-chev-4">▼</span></div>
          </div>
          <div class="dict-rows">
            <div class="dict-row"><span class="dict-lbl">1H ATR:</span><span id="d-atr" class="dict-val">${atr:,.2f}</span></div>
            <div class="dict-row"><span class="dict-lbl">ATR Compression:</span><span id="d-atr-comp" class="dict-val">{atr_comp:.1f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">4H Channel Width:</span><span id="d-width" class="dict-val">{range_width:.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">Upper Short Pool:</span><span id="d-upper-px" class="dict-val danger">${u_p:,.0f} (+{u_d:.2f}%)</span></div>
            <div class="dict-row"><span class="dict-lbl">Upper Pool Volume:</span><span id="d-upper-vol" class="dict-val">${u_vol:.1f}M</span></div>
            <div class="dict-row"><span class="dict-lbl">Lower Long Pool:</span><span id="d-lower-px" class="dict-val accent">${l_p:,.0f} (-{l_d:.2f}%)</span></div>
            <div class="dict-row"><span class="dict-lbl">Lower Pool Volume:</span><span id="d-lower-vol" class="dict-val">${l_vol:.1f}M</span></div>
          </div>
        </div>

      </div>

      <!-- Action Button at bottom of 4 Categories -->
      <button class="btn-copy-prompt" onclick="copyAIPrompt()">
        <span style="font-size: 16px;">📋</span>
        <span id="copy-btn-text">Copy Verified Data &amp; Prompt for AI</span>
      </button>
    </section>

    <!-- SEPARATOR: INSTITUTIONAL REFERENCE SUITE -->
    <div class="section-separator">
      <span>Institutional Reference Suite (Advanced)</span>
    </div>

    <!-- ======================================================== -->
    <!-- LEVEL 4: VISUAL LIQUIDATION HEATMAP (PROPORTIONAL BARS)  -->
    <!-- ======================================================== -->
    <section class="heatmap-visual-card">
      <div class="panel-header">
        <div class="panel-title" style="color: var(--warning);">
          <span>🔥</span>
          <span>Liquidation Heatmap &amp; Depth Map</span>
        </div>
        <span style="font-size: 9.5px; font-family: var(--font-mono); color: var(--text-muted); background: var(--bg-card-sub); padding: 2px 6px; border-radius: 4px;">
          10x - 100x Bands
        </span>
      </div>

      <div style="font-size: 10.5px; color: var(--text-muted); line-height: 1.4;">
        Bar width visually illustrates estimated forced-liquidation concentrations. Inside consolidation, price gravitates toward the widest cluster.
      </div>

      <!-- Proportional Bars Ladder -->
      <div class="visual-ladder-stack">
        <!-- 10x Shorts -->
        <div class="v-ladder-item short">
          <div class="v-row-meta">
            <span style="font-weight: 700; color: var(--danger);">10x Shorts (${p_10x_short:,.0f})</span>
            <span style="color: var(--text-muted);">+{d_10x_short:.2f}% • ~$85M</span>
          </div>
          <div class="bar-track"><div class="bar-fill-short" style="width: {w_10x_short}%;"></div></div>
        </div>

        <!-- 25x Shorts -->
        <div class="v-ladder-item short">
          <div class="v-row-meta">
            <span style="font-weight: 700; color: var(--danger);">25x Shorts (${p_25x_short:,.0f})</span>
            <span style="color: var(--text-muted);">+{d_25x_short:.2f}% • ~$110M</span>
          </div>
          <div class="bar-track"><div class="bar-fill-short" style="width: {w_25x_short}%;"></div></div>
        </div>

        <!-- 50-100x Shorts -->
        <div class="v-ladder-item short">
          <div class="v-row-meta">
            <span style="font-weight: 700; color: var(--danger);">50-100x Shorts (${u_p:,.0f})</span>
            <span style="color: var(--danger); font-weight: 800;">+{u_d:.2f}% • ${u_vol:.1f}M</span>
          </div>
          <div class="bar-track"><div class="bar-fill-short" style="width: {w_50_short}%;"></div></div>
        </div>

        <!-- Zero Axis Anchor -->
        <div class="v-ladder-item spot-zero">
          <div class="v-row-meta">
            <span style="font-weight: 900; color: var(--info);">● SPOT PRICE ZERO-AXIS</span>
            <span style="font-weight: 900; font-size: 13px; color: #ffffff;">${spot_price:,.2f}</span>
          </div>
          <div style="font-size: 9.5px; color: var(--info);">Current Microstructure Equilibrium Anchor</div>
        </div>

        <!-- 100x Longs Dominant Core -->
        <div class="v-ladder-item long dominant">
          <div class="v-row-meta">
            <span style="font-weight: 900; color: var(--primary);">🔥 100x Longs (${l_p:,.0f})</span>
            <span style="color: var(--primary); font-weight: 900;">-{l_d:.2f}% • ${l_vol:.1f}M</span>
          </div>
          <div class="bar-track"><div class="bar-fill-dominant" style="width: {w_100_long}%;"></div></div>
        </div>

        <!-- 25x Longs -->
        <div class="v-ladder-item long">
          <div class="v-row-meta">
            <span style="font-weight: 700; color: var(--primary);">25x Longs (${p_25x_long:,.0f})</span>
            <span style="color: var(--text-muted);">-{d_25x_long:.2f}% • ~$140M</span>
          </div>
          <div class="bar-track"><div class="bar-fill-long" style="width: {w_25x_long}%;"></div></div>
        </div>

        <!-- 10x Longs -->
        <div class="v-ladder-item long">
          <div class="v-row-meta">
            <span style="font-weight: 700; color: var(--primary);">10x Longs (${p_10x_long:,.0f})</span>
            <span style="color: var(--text-muted);">-{d_10x_long:.2f}% • ~$95M</span>
          </div>
          <div class="bar-track"><div class="bar-fill-long" style="width: {w_10x_long}%;"></div></div>
        </div>
      </div>

      <!-- Skew Summary Chips -->
      <div class="skew-chips-row">
        <div class="skew-chip">
          <span style="color: var(--text-muted); font-size: 9px; text-transform: uppercase; font-weight: 800; display: block;">Immediate Skew (100x)</span>
          <span style="font-size: 14px; font-weight: 900; color: var(--warning); font-family: var(--font-mono);">{imm_ratio:.1f}x Skew</span>
          <span style="font-size: 9.5px; color: var(--text-muted); display: block;">Lower: ${l_vol:.1f}M vs Upper: ${u_vol:.1f}M</span>
        </div>
        <div class="skew-chip">
          <span style="color: var(--text-muted); font-size: 9px; text-transform: uppercase; font-weight: 800; display: block;">Total Ladder Skew</span>
          <span style="font-size: 14px; font-weight: 900; color: var(--primary); font-family: var(--font-mono);">{tot_ratio:.2f}x Downside</span>
          <span style="font-size: 9.5px; color: var(--text-muted); display: block;">Total Lower (~${tot_l_vol:.0f}M) dominates</span>
        </div>
      </div>

      <!-- Reconciled LSCE Status Box -->
      <div style="background: {lsce_badge_bg}; border: 1px solid {lsce_badge_border}; border-radius: 10px; padding: 11px;">
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
          <span style="font-size: 14px;">{lsce_badge_icon}</span>
          <span style="font-size: 10px; font-weight: 800; text-transform: uppercase; color: var(--text-muted);">
            Liquidation Sweep Confirmation Engine (LSCE)
          </span>
        </div>
        <div style="font-size: 12px; font-weight: 900; color: {lsce_badge_color}; margin-bottom: 4px;">
          {lsce_badge_title}
        </div>
        <div style="font-size: 11px; color: var(--text-main); line-height: 1.35; background: rgba(0,0,0,0.3); padding: 6px 8px; border-radius: 6px;">
          {lsce_detail}
        </div>
      </div>
    </section>

    <!-- SIX-FACTOR DECISION HIERARCHY -->
    <section class="card-panel">
      <div class="panel-header">
        <div class="panel-title">
          <span>🧠</span>
          <span>Magnet Decision Analysis</span>
        </div>
        <span style="font-size: 9.5px; color: var(--text-muted);">Pool Size &gt; CVD &gt; Crowding &gt; ATR</span>
      </div>

      <div class="factors-grid">
        <div class="factor-item"><strong style="color: var(--text-muted); font-size: 10px; display: block;">1. Cluster Magnitude:</strong>{f1}</div>
        <div class="factor-item"><strong style="color: var(--text-muted); font-size: 10px; display: block;">2. Spot vs. Perp CVD:</strong>{f2}</div>
        <div class="factor-item"><strong style="color: var(--text-muted); font-size: 10px; display: block;">3. Crowding Fuel:</strong>{f3}</div>
        <div class="factor-item"><strong style="color: var(--text-muted); font-size: 10px; display: block;">4. Macro Structure:</strong>{f4}</div>
        <div class="factor-item"><strong style="color: var(--text-muted); font-size: 10px; display: block;">5. Distance Asymmetry:</strong>{f5}</div>
        <div class="factor-item"><strong style="color: var(--text-muted); font-size: 10px; display: block;">6. Volatility Regime (ATR):</strong>{f6}</div>
      </div>

      <div style="background: rgba(255, 184, 0, 0.08); border: 1px solid rgba(255, 184, 0, 0.3); border-radius: 8px; padding: 9px 11px; font-size: 11px;">
        <span style="color: var(--warning); font-weight: 800; text-transform: uppercase;">Dominant Gravitational Bias:</span>
        <div style="color: #ffffff; font-weight: 700; margin-top: 2px;">{dom_reason}</div>
      </div>
    </section>

    <!-- MICROSTRUCTURE GAUGES & 5-REGIME MATRIX -->
    <section class="card-panel">
      <div class="panel-header">
        <div class="panel-title">
          <span>⚡</span>
          <span>Microstructure Telemetry Gauges</span>
        </div>
      </div>

      <div class="gauges-grid">
        <div class="gauge-card">
          <div class="gauge-lbl">Spot CVD Ratio</div>
          <div class="gauge-val" id="g-cvd">{spot_cvd_ratio:.2f}</div>
          <div class="gauge-sub">Taker Buy/Sell</div>
        </div>
        <div class="gauge-card">
          <div class="gauge-lbl">Perp CVD Flow</div>
          <div class="gauge-val" id="g-perp" style="text-transform: capitalize;">{perp_trend}</div>
          <div class="gauge-sub">Futures Trend</div>
        </div>
        <div class="gauge-card">
          <div class="gauge-lbl">Open Interest</div>
          <div class="gauge-val" id="g-oi-chg">{oi_24h:+.2f}%</div>
          <div class="gauge-sub" id="g-oi">{oi:,.0f} BTC</div>
        </div>
        <div class="gauge-card">
          <div class="gauge-lbl">Funding Rate (8h)</div>
          <div class="gauge-val" id="g-funding">{funding_rate/100:+.4f}%</div>
          <div class="gauge-sub">{funding_rate_ann:.1f}% Ann.</div>
        </div>
        <div class="gauge-card">
          <div class="gauge-lbl">Futures Basis</div>
          <div class="gauge-val" id="g-basis">{basis:.1f}%</div>
          <div class="gauge-sub">Annualized Spread</div>
        </div>
        <div class="gauge-card">
          <div class="gauge-lbl">Retail Long/Short</div>
          <div class="gauge-val" id="g-ls" style="color: var(--warning);">{ls_ratio:.2f}</div>
          <div class="gauge-sub">Account Ratio</div>
        </div>
      </div>

      <!-- 5-Regime Radar Framework Matrix -->
      <div style="margin-top: 6px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <span style="font-size: 10px; font-weight: 800; text-transform: uppercase; color: var(--text-muted);">
            5-Regime Framework Matrix
          </span>
          <a href="https://aikeluargalee-tech.github.io/btc-magnet-monitor/regimes.html" target="_blank" style="font-size: 10px; color: var(--info); text-decoration: none; font-weight: 700;">
            Math Guide &rarr;
          </a>
        </div>
        <div class="matrix-grid">
          <div class="matrix-item {'active' if regime_id == 'SPOT_LED_EXPANSION' else ''}">1. Spot Expansion</div>
          <div class="matrix-item {'active' if regime_id == 'LEVERAGED_FRAGILE_UPSIDE' else ''}">2. Leveraged Trap</div>
          <div class="matrix-item {'active' if regime_id == 'RANGE_LIQUIDATION_MAGNET' else ''}">3. Range / Magnet</div>
          <div class="matrix-item {'active' if regime_id == 'CASCADE_FORCED_DELEVERAGING' else ''}">4. Cascade</div>
          <div class="matrix-item {'active' if regime_id == 'DISTRIBUTION_BEAR_CONTINUATION' else ''}">5. Distribution</div>
        </div>
      </div>
    </section>

  </div>

  <!-- STICKY BOTTOM QUICK-AUDIT BAR -->
  <div class="sticky-audit-bar">
    <div class="sticky-ticker">
      <span class="sticky-px" id="sticky-spot-px">${spot_price:,.0f}</span>
      <span class="sticky-state" id="sticky-state-lbl">{'REMAIN USDT (0.0x)' if sizing == 0 else f'ROTATE BTC ({sizing:.2f}x)'}</span>
    </div>
    <button class="sticky-btn" onclick="copyAIPrompt()">
      <span>📋</span>
      <span id="sticky-btn-text">Copy AI Audit Prompt</span>
    </button>
  </div>

  <!-- TOAST NOTIFICATION -->
  <div id="toast" class="toast-overlay">
    <span>📋</span>
    <span id="toast-msg">AI Prompt copied to clipboard!</span>
  </div>

  <script>
    let currentAIPrompt = {escaped_prompt};
    
    let currentSizing = {sizing};
    let experienceMode = 'beginner';

    // EXPERIENCE MODE (BEGINNER VS DESK)
    function setExperienceMode(mode) {{
      experienceMode = mode;
      const bBtn = document.getElementById('btn-mode-beginner');
      const dBtn = document.getElementById('btn-mode-desk');
      const caption = document.getElementById('mode-caption-text');
      const countEl = document.getElementById('dict-expand-count');

      if (mode === 'beginner') {{
        if (bBtn) bBtn.classList.add('active');
        if (dBtn) dBtn.classList.remove('active');
        if (caption) caption.textContent = 'Beginner mode: Executive decision & plain rationale first. Switch to Desk for full data expansion.';
        for (let i = 2; i <= 4; i++) {{
          const card = document.getElementById('cat-card-' + i);
          if (card) card.classList.add('collapsed');
        }}
        const card1 = document.getElementById('cat-card-1');
        if (card1) card1.classList.remove('collapsed');
        if (countEl) countEl.textContent = '1/4 open (Tap to view)';
      }} else {{
        if (dBtn) dBtn.classList.add('active');
        if (bBtn) bBtn.classList.remove('active');
        if (caption) caption.textContent = 'Desk (Pro) mode: Institutional execution telemetry & full liquidation depth ladder expanded.';
        for (let i = 1; i <= 4; i++) {{
          const card = document.getElementById('cat-card-' + i);
          if (card) card.classList.remove('collapsed');
        }}
        if (countEl) countEl.textContent = '4/4 expanded';
      }}
      try {{ localStorage.setItem('btc_magnet_mode', mode); }} catch(e) {{}}
    }}

    function toggleCategory(catId) {{
      const card = document.getElementById('cat-card-' + catId);
      if (card) {{
        card.classList.toggle('collapsed');
        updateAccordionCount();
      }}
    }}

    function updateAccordionCount() {{
      let openCount = 0;
      for (let i = 1; i <= 4; i++) {{
        const card = document.getElementById('cat-card-' + i);
        if (card && !card.classList.contains('collapsed')) openCount++;
      }}
      const countEl = document.getElementById('dict-expand-count');
      if (countEl) {{
        countEl.textContent = openCount + '/4 ' + (openCount === 4 ? 'expanded' : 'open');
      }}
    }}

    // PORTFOLIO 1% RISK BUDGET CALCULATOR
    function onPortfolioChange(val) {{
      const p = Math.max(0, Number(val) || 0);
      const inputEl = document.getElementById('portfolio-input');
      const sliderEl = document.getElementById('portfolio-slider');
      if (inputEl && inputEl.value !== String(p)) inputEl.value = p;
      if (sliderEl && Number(sliderEl.value) !== Math.min(100000, Math.max(1000, p))) {{
        sliderEl.value = Math.min(100000, Math.max(1000, p));
      }}

      const riskCap = p * 0.01;
      const riskEl = document.getElementById('calc-risk-cap');
      if (riskEl) {{
        riskEl.textContent = '$' + riskCap.toLocaleString('en-US', {{maximumFractionDigits: 0}});
      }}

      const deployEl = document.getElementById('calc-deploy-amt');
      const subEl = document.getElementById('calc-deploy-sub');
      if (deployEl && subEl) {{
        if (currentSizing === 0) {{
          deployEl.textContent = '$0 (100% USDT)';
          deployEl.style.color = 'var(--warning)';
          subEl.textContent = 'Patience: Zero loss risk';
        }} else {{
          const deployAmt = Math.round(p * 0.30);
          deployEl.textContent = '$' + deployAmt.toLocaleString('en-US') + ' Spot BTC';
          deployEl.style.color = 'var(--primary)';
          subEl.textContent = 'Authorized: 30% cash deploy';
        }}
      }}
    }}

    let lastSnapshotTime = new Date("{ts_iso}");

    // THEME SWITCHER
    const themes = ['theme-nvg', 'theme-binance', 'theme-ibm', 'theme-slate'];
    const themeLabels = {{ 'theme-nvg': 'NVG', 'theme-binance': 'BINANCE', 'theme-ibm': 'IBM', 'theme-slate': 'SLATE' }};
    
    let currentThemeIdx = 0;

    function cycleTheme() {{
      currentThemeIdx = (currentThemeIdx + 1) % themes.length;
      document.body.className = themes[currentThemeIdx];
      document.getElementById('theme-btn').textContent = themeLabels[themes[currentThemeIdx]];
      try {{ localStorage.setItem('btc_magnet_theme', themes[currentThemeIdx]); }} catch(e) {{}}
    }}

    try {{
      try {{
      const savedMode = localStorage.getItem('btc_magnet_mode');
      if (savedMode === 'desk') setExperienceMode('desk');
      else setExperienceMode('beginner');
    }} catch(e) {{}}
    
      const savedTheme = localStorage.getItem('btc_magnet_theme');
      if (savedTheme && themes.includes(savedTheme)) {{
        currentThemeIdx = themes.indexOf(savedTheme);
        document.body.className = savedTheme;
        document.getElementById('theme-btn').textContent = themeLabels[savedTheme];
      }}
    }} catch(e) {{}}

    // COPY AI PROMPT
    async function copyAIPrompt() {{
      const btnText = document.getElementById('copy-btn-text');
      const stickyBtn = document.getElementById('sticky-btn-text');
      const originalText = btnText ? btnText.textContent : 'Copy Verified Data & Prompt for AI';
      try {{
        await navigator.clipboard.writeText(currentAIPrompt);
        if (navigator.vibrate) navigator.vibrate(50);
        if (btnText) btnText.textContent = '✓ Verified Data & Prompt Copied!';
        if (stickyBtn) stickyBtn.textContent = '✓ Copied!';
        showToast("📋 AI Prompt copied! Paste into Claude / ChatGPT / Grok");
        setTimeout(() => {{
          if (btnText) btnText.textContent = originalText;
          if (stickyBtn) stickyBtn.textContent = 'Copy AI Audit Prompt';
        }}, 2500);
      }} catch (err) {{
        const ta = document.createElement('textarea');
        ta.value = currentAIPrompt;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        if (btnText) btnText.textContent = '✓ Verified Data & Prompt Copied!';
        if (stickyBtn) stickyBtn.textContent = '✓ Copied!';
        showToast("📋 AI Prompt copied to clipboard!");
        setTimeout(() => {{
          if (btnText) btnText.textContent = originalText;
          if (stickyBtn) stickyBtn.textContent = 'Copy AI Audit Prompt';
        }}, 2500);
      }}
    }}

    function showToast(msg) {{
      const t = document.getElementById('toast');
      const m = document.getElementById('toast-msg');
      m.textContent = msg;
      t.classList.add('active');
      setTimeout(() => {{ t.classList.remove('active'); }}, 3000);
    }}

    // DATA FRESHNESS SENTINEL
    function updateFreshness() {{
      const now = new Date();
      const sec = Math.max(0, Math.round((now - lastSnapshotTime) / 1000));
      const el = document.getElementById('data-age-tag');
      if (el) {{
        el.textContent = (sec < 60 ? (sec + 's ago') : (Math.floor(sec / 60) + 'm ago'));
      }}
    }}
    setInterval(updateFreshness, 5000);
    updateFreshness();

    // LIVE REST API POLLING (every 45s)
    async function pollLiveFeed() {{
      try {{
        const url = './regime.json?t=' + Date.now();
        const res = await fetch(url, {{ cache: 'no-store' }});
        if (!res.ok) return;
        const data = await res.json();
        if (data.timestamp) lastSnapshotTime = new Date(data.timestamp);
        updateFreshness();

        const m = data.metrics || {{}};
        const r = data.regime || {{}};

        if (m.price) {{
          const pStr = '$' + Number(m.price).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
          if (document.getElementById('d-spot-px')) document.getElementById('d-spot-px').textContent = pStr;
          if (document.getElementById('d-spot-px-2')) document.getElementById('d-spot-px-2').textContent = pStr;
          if (document.getElementById('sticky-spot-px')) document.getElementById('sticky-spot-px').textContent = '$' + Number(m.price).toLocaleString('en-US', {{maximumFractionDigits: 0}});
        }}
        if (m.daily_vwap && m.price) {{
          const delta = ((m.price - m.daily_vwap) / m.daily_vwap) * 100;
          const el = document.getElementById('d-vwap-delta');
          if (el) {{
            el.textContent = (delta >= 0 ? '+' : '') + delta.toFixed(2) + '%';
            el.style.color = delta >= 0 ? 'var(--primary)' : 'var(--danger)';
          }}
        }}
        if (m.spot_cvd_ratio !== undefined) {{
          if (document.getElementById('d-cvd-ratio')) document.getElementById('d-cvd-ratio').textContent = Number(m.spot_cvd_ratio).toFixed(2);
          if (document.getElementById('g-cvd')) document.getElementById('g-cvd').textContent = Number(m.spot_cvd_ratio).toFixed(2);
        }}
        if (m.funding_rate !== undefined) {{
          const fStr = (m.funding_rate * 100 >= 0 ? '+' : '') + (m.funding_rate * 100).toFixed(4) + '%';
          if (document.getElementById('d-funding')) document.getElementById('d-funding').textContent = fStr;
          if (document.getElementById('g-funding')) document.getElementById('g-funding').textContent = fStr;
        }}
        if (m.open_interest !== undefined) {{
          const oiStr = Number(m.open_interest).toLocaleString('en-US', {{maximumFractionDigits: 0}}) + ' BTC';
          if (document.getElementById('d-oi')) document.getElementById('d-oi').textContent = oiStr;
          if (document.getElementById('g-oi')) document.getElementById('g-oi').textContent = oiStr;
        }}
        if (r.name && document.getElementById('regime-name')) {{
          document.getElementById('regime-name').textContent = r.name;
        }}
      }} catch (err) {{
        console.warn('Poll failed:', err);
      }}
    }}
    setInterval(pollLiveFeed, 45000);

    if ('serviceWorker' in navigator) {{
      navigator.serviceWorker.register('./sw.js').catch(() => {{}});
    }}
  </script>
</body>
</html>"""
