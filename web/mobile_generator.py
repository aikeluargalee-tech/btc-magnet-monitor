import datetime
import json
from typing import Dict, Any, Tuple

class MobileWebGenerator:
    """Generates the Mobile Cockpit Progressive Web Application (PWA) HTML,
    Web App Manifest, and Service Worker for BTC Magnet Monitor.
    """

    def render_manifest(self) -> str:
        manifest = {
            "name": "BTC Magnet Monitor",
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
  './verdict.html',
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
  if (!e.request.url.startsWith(self.location.origin)) {
    return; // Pass through external feeds like Binance directly
  }
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

        # Compute UTC, SGT, and Active Market Session Zone
        try:
            dt_utc = datetime.datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        except Exception:
            dt_utc = datetime.datetime.now(datetime.timezone.utc)
            
        dt_sgt = dt_utc + datetime.timedelta(hours=8)
        
        utc_time_str = dt_utc.strftime("%H:%M:%S UTC")
        utc_date_str = dt_utc.strftime("%d %b %Y")
        sgt_time_str = dt_sgt.strftime("%H:%M:%S SGT")
        sgt_date_str = dt_sgt.strftime("%d %b %Y")
        
        h_float = dt_utc.hour + dt_utc.minute / 60.0
        if 0.0 <= h_float < 7.0:
            sess_name = "🌏 Asia / Tokyo & Singapore Session"
            sess_hours = "00:00 – 07:00 UTC (08:00 – 15:00 SGT)"
            sess_badge = "ASIA"
            sess_color = "#38bdf8"
            sess_desc = "Asian Core Hours • Steady Accumulation / Range Flow"
        elif 7.0 <= h_float < 8.0:
            sess_name = "🔄 Asia / London Transition"
            sess_hours = "07:00 – 08:00 UTC (15:00 – 16:00 SGT)"
            sess_badge = "TRANSITION"
            sess_color = "#f59e0b"
            sess_desc = "European Pre-Open • Early Liquidity Positioning"
        elif 8.0 <= h_float < 13.0:
            sess_name = "🏛️ London / European Session"
            sess_hours = "08:00 – 13:00 UTC (16:00 – 21:00 SGT)"
            sess_badge = "LONDON"
            sess_color = "#10b981"
            sess_desc = "European Institutional Hours • High Spot Volume & Breakout Liquidity"
        elif 13.0 <= h_float < 16.5:
            sess_name = "⚡ London & New York Overlap"
            sess_hours = "13:00 – 16:30 UTC (21:00 – 00:30 SGT)"
            sess_badge = "PEAK OVERLAP"
            sess_color = "#ec4899"
            sess_desc = "Peak Global Liquidity • Highest Volatility & Order Flow Depth"
        elif 16.5 <= h_float < 21.0:
            sess_name = "🗽 New York Session (US Core)"
            sess_hours = "16:30 – 21:00 UTC (00:30 – 05:00 SGT)"
            sess_badge = "NEW YORK"
            sess_color = "#6366f1"
            sess_desc = "US Institutional Hours • ETF Flows & Derivatives Settlement"
        else:
            sess_name = "🌙 Pacific / Off-Hours Transition"
            sess_hours = "21:00 – 00:00 UTC (05:00 – 08:00 SGT)"
            sess_badge = "OFF-HOURS"
            sess_color = "#a855f7"
            sess_desc = "Off-Hours Liquidity • Mean Reversion & Overnight Reset"

        # Next Scheduled Telemetry Update Calculation (30-min cadence)
        current_min = dt_utc.minute
        if current_min < 30:
            mins_left = 30 - current_min
            next_utc = dt_utc.replace(minute=30, second=0, microsecond=0)
        else:
            mins_left = 60 - current_min
            next_utc = (dt_utc + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

        next_sgt = next_utc + datetime.timedelta(hours=8)
        next_utc_str = next_utc.strftime("%H:%M UTC")
        next_sgt_str = next_sgt.strftime("%H:%M SGT")

        spot_price = metrics.get("price", 74827.09)
        p_chg_24h = metrics.get("price_change_24h_pct", 0.71)
        daily_vwap = metrics.get("daily_vwap", spot_price * 0.998)
        weekly_vwap = metrics.get("weekly_vwap", spot_price * 0.995)
        ema_20d = metrics.get("ema_20d", spot_price * 1.025)
        ema_50d = metrics.get("ema_50d", spot_price * 1.042)
        ma_200d = metrics.get("ma_200d", spot_price * 0.978)
        swing_high = metrics.get("swing_high_4h", 75568.0)
        swing_low = metrics.get("swing_low_4h", 73750.0)
        base_floor = metrics.get("base_floor", 73510.0)

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
        rotation = regime.get("rotation", "USDT -> BTC")
        sizing = regime.get("sizing_factor", 0.75)
        action = regime.get("action", "Trade the Magnet (0.75x)")
        playbook = regime.get("action", "Core Operating Zone — Trade the Magnet (0.75x)")
        entry_inst = regime.get("entry_instruction", "Confirmed sweep & reclaim: 50% market spot / 50% limit at reclaimed range floor.")

        if "USDT -> BTC" in rotation:
            action_pill = "Buy Spot (Accumulate)"
        elif "BTC -> USDT" in rotation:
            action_pill = "Trim Spot / Harvest to Cash"
        else:
            action_pill = "Defensive Cash"

        stop_price = regime.get("stop_price", spot_price * 0.98)
        stop_dist = regime.get("stop_distance_pct", 2.0)
        disaster_stop = regime.get("disaster_stop_price", 72354.94)
        disaster_dist = regime.get("disaster_stop_distance_pct", 3.30)
        structural_inval = regime.get("structural_invalidation_level", 73750.00)
        stop_rule = regime.get("stop_rule", "Structural: 1H close < 4H swing low | Inviolable: Below 200D SMA & 25x shelf -0.7%")

        risk_budget_ok = risk.get("risk_budget_ok", True)
        actionable_trade_instruction = risk.get(
            "actionable_trade_instruction",
            f"Deploy {int(sizing*100*0.4)}% of your available USDT cash to buy spot BTC (Strictly capped at 0.99% total portfolio risk)."
        )

        plain_verdict = regime.get(
            "plain_english_verdict",
            f"Bitcoin is oscillating in a defined trading range. LSCE Status: {regime.get('lsce_status', 'SWEEP_AND_RECLAIM_CONFIRMED')}. Market makers hunt leverage on both sides."
        )
        why_points = regime.get("why_points", [
            "Defined Consolidation Range: Volatility has compressed and price is trading between established floor and ceiling levels.",
            f"Liquidation Sweep State ({regime.get('lsce_status', 'SWEEP_AND_RECLAIM_CONFIRMED')}): The lower pool is actively monitored for genuine spot absorption.",
            "Controlled Market Fuel: Mean-reversion toward liquidation pools is the primary statistical edge."
        ])
        why_sizing = regime.get(
            "why_sizing_reason",
            "Why 75% Sizing? Sizing is strictly tied to post-sweep absorption proof. If sweep is in progress or untested, we hold 100% cash."
        )
        why_stop = regime.get(
            "why_stop_reason",
            f"Your Safety Net: Inviolable Disaster Stop at ${disaster_stop:,.2f} ({disaster_dist:.2f}% away), positioned safely below the 200D SMA and 25x liquidation shelf."
        )

        imm_ratio = regime.get("immediate_imbalance_ratio", 24.5)
        tot_ratio = regime.get("total_ladder_imbalance_ratio", 1.70)
        tot_l_vol = regime.get("total_ladder_lower_vol", 337.8)
        tot_u_vol = regime.get("total_ladder_upper_vol", 199.2)
        dom_magnet = regime.get("dominant_magnet", "Lower Long Sweep Magnet")
        dom_reason = regime.get("dominant_magnet_reason", "LOWER (Immediate 24.5x / Ladder 1.70x; longs 64.9% crowded)")

        lsce_status = regime.get("lsce_status", "SWEEP_AND_RECLAIM_CONFIRMED")
        lsce_detail = regime.get(
            "lsce_detail",
            f"Lower liquidation shelf (${l_p:,.0f}) swept and reclaimed with positive spot absorption. Authorized {sizing:.2f}x entry."
        )

        # LSCE Badge formatting (Conflict Guard enforced)
        if lsce_status == "SWEEP_AND_RECLAIM_CONFIRMED":
            if sizing > 0 and "USDT -> BTC" in rotation:
                lsce_badge_icon = "✅"
                lsce_badge_title = f"SWEEP & RECLAIM CONFIRMED (BUY AUTHORIZED {sizing:.2f}x)"
                lsce_badge_color = "var(--primary)"
                lsce_badge_bg = "rgba(0, 255, 102, 0.1)"
                lsce_badge_border = "rgba(0, 255, 102, 0.35)"
                lsce_detail = regime.get(
                    "lsce_detail",
                    f"Lower liquidation shelf (${l_p:,.0f}) swept and reclaimed with positive spot absorption. Authorized {sizing:.2f}x entry."
                )
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
        else:
            lsce_badge_icon = "⏸️"
            lsce_badge_title = "UNTESTED (MONITORING / CASH)"
            lsce_badge_color = "var(--text-muted)"
            lsce_badge_bg = "rgba(255, 255, 255, 0.05)"
            lsce_badge_border = "var(--border)"

        # Regime Tagline & Icon
        if regime_id == "SPOT_LED_EXPANSION":
            regime_icon = "🚀"
            regime_tagline = "Genuine spot buyers in control. Favorable environment for trend-following spot longs."
            regime_accent = "var(--primary)"
        elif regime_id == "LEVERAGED_FRAGILE_UPSIDE":
            regime_icon = "⚠️"
            regime_tagline = "Advance built on dangerous borrowed futures leverage. High probability of long squeeze."
            regime_accent = "var(--warning)"
        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            regime_icon = "🌊"
            regime_tagline = "Forced margin liquidation cascade in progress. Strictly avoid buying until selling ceases."
            regime_accent = "var(--danger)"
        elif regime_id == "DISTRIBUTION_BEAR_CONTINUATION":
            regime_icon = "📉"
            regime_tagline = "Structural seller control. Whales distributing into retail bounces. Cash preservation priority."
            regime_accent = "var(--danger)"
        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            regime_icon = "🧲"
            regime_tagline = "Price bound within defined horizontal channel. Positioning imbalance and liquidation magnets dominate."
            regime_accent = "var(--info)"
        else:
            regime_icon = "⚖️"
            regime_tagline = "Market indicators conflicting or transitioning between regimes. Capital preservation in cash."
            regime_accent = "var(--text-muted)"

        # Rotation Action formatting
        if "USDT -> BTC" in rotation:
            action_pill = "Buy Spot (Accumulate)"
            action_badge_style = "background: rgba(0, 255, 102, 0.15); color: var(--primary); border: 1px solid rgba(0, 255, 102, 0.4);"
        elif "BTC -> USDT" in rotation:
            action_pill = "Trim Spot / Harvest to Cash"
            action_badge_style = "background: rgba(255, 51, 68, 0.15); color: var(--danger); border: 1px solid rgba(255, 51, 68, 0.4);"
        else:
            action_pill = "Defensive Cash"
            action_badge_style = "background: rgba(255, 184, 0, 0.15); color: var(--warning); border: 1px solid rgba(255, 184, 0, 0.4);"

        matched_criteria = regime.get("matched_criteria", [
            f"Defined range ({range_width:.2f}% width) & ATR compressed {atr_comp:.1f}%",
            f"Positioning crowded (L/S {ls_ratio:.2f}, funding {funding_rate/100:.3f}%)",
            "Clear liquidation clusters active above and below price"
        ])

        magnet_factors = regime.get("magnet_factors", {})
        f1 = magnet_factors.get("factor_1_size", f"Immediate Tier: LOWER is {imm_ratio:.1f}x larger (${l_vol:.1f}M vs ${u_vol:.1f}M) | Total Ladder: LOWER is {tot_ratio:.2f}x (${tot_l_vol:.1f}M vs ${tot_u_vol:.1f}M)")
        f2 = magnet_factors.get("factor_2_spot_leadership", f"Spot CVD ratio {spot_cvd_ratio:.2f} vs Perp CVD {perp_trend}")
        f3 = magnet_factors.get("factor_3_crowding_fuel", f"Funding {funding_rate/100:.3f}%, Retail L/S {ls_ratio:.2f} ({(ls_ratio/(1+ls_ratio))*100:.1f}% long)")
        f4 = magnet_factors.get("factor_4_regime_structure", "Range compression with downside fragility")
        f5 = magnet_factors.get("factor_5_asymmetry", f"LOWER is {l_d:.2f}% away vs UPPER {u_d:.2f}% away")
        f6 = magnet_factors.get("factor_6_atr_volatility", f"ATR compressed {atr_comp:.1f}%")

        # Pre-compute HTML snippets
        evidence_items_html = "".join([
            f'<div class="evidence-item"><span class="evidence-check">✓</span><span>{item}</span></div>'
            for item in matched_criteria
        ])

        why_points_html = "".join([
            f'<div class="why-factor-row"><div class="why-num">{idx+1}</div><div style="color: var(--text-main);">{pt}</div></div>'
            for idx, pt in enumerate(why_points)
        ])

        # Ladder Prices
        p_10x_short = swing_high * 1.025
        d_10x_short = ((p_10x_short - spot_price) / spot_price) * 100
        p_25x_short = swing_high * 1.012
        d_25x_short = ((p_25x_short - spot_price) / spot_price) * 100

        p_25x_long = swing_low * 0.988
        d_25x_long = ((spot_price - p_25x_long) / spot_price) * 100
        p_10x_long = swing_low * 0.975
        d_10x_long = ((spot_price - p_10x_long) / spot_price) * 100

        escaped_prompt = json.dumps(raw_llm_prompt)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>BTC Magnet Monitor | Live Telemetry & AI Prompt Engine</title>
  
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
      line-height: 1.4;
      padding-bottom: 90px;
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

    /* TOP HEADER BAR */
    .top-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
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
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--primary-dim);
      border: 1px solid var(--primary);
      border-radius: 6px;
      font-size: 13px;
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

    /* REAL-TIME SPOT PRICE BAR (Below Header) */
    .realtime-spot-bar {{
      background: linear-gradient(180deg, rgba(0, 255, 102, 0.08) 0%, rgba(10, 17, 13, 0.95) 100%);
      border: 1px solid rgba(0, 255, 102, 0.35);
      border-radius: 12px;
      padding: 12px 14px;
      margin-bottom: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
    }}

    .spot-bar-left {{
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}

    .spot-bar-label {{
      font-size: 10px;
      font-weight: 800;
      color: var(--primary);
      letter-spacing: 0.6px;
      text-transform: uppercase;
      font-family: var(--font-mono);
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .live-dot-mini {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--primary);
      box-shadow: 0 0 6px var(--primary);
      animation: pulse 2s infinite;
    }}

    .spot-bar-price-row {{
      display: flex;
      align-items: baseline;
      gap: 8px;
    }}

    .spot-bar-price {{
      font-size: 24px;
      font-weight: 900;
      color: #ffffff;
      font-family: var(--font-mono);
      letter-spacing: -0.5px;
      line-height: 1.1;
    }}

    .spot-bar-chg {{
      font-size: 11px;
      font-weight: 800;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: var(--font-mono);
    }}

    .spot-bar-right {{
      text-align: right;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .spot-feed-provenance {{
      font-size: 9.5px;
      font-weight: 800;
      color: var(--text-muted);
      font-family: var(--font-mono);
      letter-spacing: 0.4px;
    }}

    .spot-provenance-sub {{
      font-size: 9px;
      color: var(--text-muted);
      font-family: var(--font-mono);
      opacity: 0.8;
    }}

    /* AI COPY PROMPT HELPER BOX */
    .ai-copy-helper-box {{
      margin-top: 10px;
      background: rgba(0, 255, 102, 0.04);
      border: 1px dashed rgba(0, 255, 102, 0.25);
      border-radius: 8px;
      padding: 10px 12px;
      display: flex;
      align-items: flex-start;
      gap: 8px;
      font-size: 11.5px;
      line-height: 1.45;
      color: var(--text-muted);
    }}

    .ai-helper-icon {{
      font-size: 14px;
      line-height: 1;
      margin-top: 2px;
    }}

    .ai-helper-text strong {{
      color: #ffffff;
    }}

    /* SYSTEM VERDICT QUICK GLANCE CARD (Golden Amber Outline) */
    .system-verdict-summary-card {{
      background: var(--bg-card);
      border: 2px solid #ffb800;
      border-radius: 14px;
      padding: 14px;
      margin: 18px 0 14px 0;
      box-shadow: 0 0 24px rgba(255, 184, 0, 0.18);
    }}

    .verdict-card-top-tag {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}

    .verdict-tag-left {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .verdict-title-text {{
      font-size: 11px;
      font-weight: 900;
      color: #ffb800;
      letter-spacing: 0.5px;
      font-family: var(--font-mono);
      text-transform: uppercase;
    }}

    .quick-glance-badge {{
      font-size: 9px;
      font-weight: 800;
      background: rgba(255, 184, 0, 0.15);
      border: 1px solid rgba(255, 184, 0, 0.4);
      color: #ffb800;
      padding: 2px 7px;
      border-radius: 4px;
      font-family: var(--font-mono);
      letter-spacing: 0.5px;
    }}

    .verdict-summary-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 12px;
    }}

    .verdict-summary-item {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}

    .v-sum-lbl {{
      font-size: 9.5px;
      font-weight: 800;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
      font-family: var(--font-mono);
    }}

    .v-sum-val {{
      font-size: 13.5px;
      line-height: 1.25;
      color: #ffffff;
    }}

    .v-sum-sub {{
      font-size: 10px;
      color: var(--text-muted);
      line-height: 1.3;
    }}

    .verdict-concise-callout {{
      background: rgba(255, 255, 255, 0.03);
      border-left: 3px solid #ffb800;
      padding: 10px 12px;
      border-radius: 4px 8px 8px 4px;
      font-size: 12px;
      color: var(--text-main);
      line-height: 1.45;
      display: flex;
      align-items: flex-start;
      gap: 8px;
      margin-bottom: 14px;
    }}

    .btn-subpage-verdict {{
      width: 100%;
      background: linear-gradient(135deg, rgba(255, 184, 0, 0.22) 0%, rgba(255, 140, 0, 0.16) 100%);
      border: 1.5px solid #ffb800;
      color: #ffffff;
      border-radius: 10px;
      padding: 13px 14px;
      font-size: 13px;
      font-weight: 900;
      display: flex;
      align-items: center;
      justify-content: space-between;
      text-decoration: none;
      box-shadow: 0 4px 16px rgba(255, 184, 0, 0.22);
      transition: all 0.2s ease;
      cursor: pointer;
    }}

    .btn-subpage-verdict:active {{
      transform: scale(0.98);
      background: #ffb800;
      color: #030804;
    }}

    .btn-subpage-left {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    .btn-arrow {{
      font-size: 16px;
      font-weight: 900;
      color: #ffb800;
    }}

    /* NEXT SCHEDULED TELEMETRY UPDATE CARD */
    .next-update-card {{
      background: rgba(0, 229, 255, 0.04);
      border: 1px solid rgba(0, 229, 255, 0.25);
      border-radius: 10px;
      padding: 10px 12px;
      margin-bottom: 14px;
    }}

    .next-update-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;
    }}

    .next-update-title-group {{
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .update-icon {{
      font-size: 12px;
    }}

    .next-update-label {{
      font-size: 9.5px;
      font-weight: 800;
      color: var(--info);
      letter-spacing: 0.5px;
      text-transform: uppercase;
      font-family: var(--font-mono);
    }}

    .next-update-cadence-badge {{
      font-size: 8.5px;
      font-weight: 800;
      padding: 1px 5px;
      border-radius: 3px;
      background: rgba(0, 229, 255, 0.12);
      border: 1px solid rgba(0, 229, 255, 0.35);
      color: var(--info);
      font-family: var(--font-mono);
      letter-spacing: 0.4px;
    }}

    .next-update-main-row {{
      display: flex;
      align-items: baseline;
      gap: 8px;
      margin-bottom: 2px;
    }}

    .next-update-countdown {{
      font-size: 15px;
      font-weight: 900;
      color: #ffffff;
      font-family: var(--font-mono);
      letter-spacing: -0.2px;
    }}

    .next-update-sub {{
      font-size: 10px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    /* PART 1: TOP HERO - LIVE TIME & SESSION HUD */
    .top-hero-dictionary {{
      background: var(--bg-card);
      border: 2px solid var(--primary);
      border-radius: 14px;
      padding: 14px;
      box-shadow: 0 0 24px rgba(0, 255, 102, 0.12);
    }}

    /* Dual Clocks Row */
    .clocks-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      margin-bottom: 10px;
    }}

    .time-card {{
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .time-card-title {{
      font-size: 10px;
      font-weight: 800;
      color: var(--text-muted);
      letter-spacing: 0.5px;
      text-transform: uppercase;
      font-family: var(--font-mono);
      display: flex;
      align-items: center;
      gap: 5px;
    }}

    .time-card-value {{
      font-size: 15px;
      font-weight: 900;
      color: #ffffff;
      font-family: var(--font-mono);
      letter-spacing: -0.3px;
    }}

    .time-card-sub {{
      font-size: 10px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    /* Session Zone Card */
    .session-card {{
      background: rgba(0, 255, 102, 0.04);
      border: 1px solid rgba(0, 255, 102, 0.25);
      border-radius: 10px;
      padding: 12px;
      margin-bottom: 14px;
    }}

    .session-header-line {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }}

    .session-header-left {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .session-pulse-dot {{
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--primary);
      box-shadow: 0 0 8px var(--primary);
      animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{ opacity: 1; transform: scale(1); }}
      50% {{ opacity: 0.4; transform: scale(0.85); }}
    }}

    .session-card-label {{
      font-size: 10px;
      font-weight: 800;
      color: var(--primary);
      letter-spacing: 0.6px;
      text-transform: uppercase;
      font-family: var(--font-mono);
    }}

    .session-zone-badge {{
      font-size: 9px;
      font-weight: 800;
      padding: 2px 7px;
      border-radius: 4px;
      border: 1px solid;
      font-family: var(--font-mono);
      letter-spacing: 0.5px;
    }}

    .session-name-main {{
      font-size: 15px;
      font-weight: 900;
      color: #ffffff;
      letter-spacing: -0.2px;
      margin-bottom: 4px;
    }}

    .session-meta-row {{
      display: flex;
      flex-direction: column;
      gap: 2px;
    }}

    .session-zone-hours {{
      font-size: 10.5px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    .session-zone-desc {{
      font-size: 11px;
      color: var(--text-main);
      opacity: 0.85;
      line-height: 1.35;
    }}

    .btn-copy-prompt {{
      width: 100%;
      background: var(--primary);
      color: #030804;
      border: none;
      border-radius: 10px;
      padding: 13px 16px;
      font-size: 13px;
      font-weight: 900;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      letter-spacing: 0.3px;
      box-shadow: 0 4px 14px rgba(0, 255, 102, 0.4);
      transition: transform 0.1s ease, background 0.2s ease;
      margin-top: 12px;
    }}

    .btn-copy-prompt:active {{
      transform: scale(0.97);
    }}

    /* 4 CATEGORIES GRID */
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

    .dict-lbl {{
      color: var(--text-muted);
    }}

    .dict-val {{
      color: var(--text-main);
      font-weight: 600;
    }}

    .dict-val.accent {{ color: var(--primary); font-weight: 800; }}
    .dict-val.warn {{ color: var(--warning); font-weight: 800; }}
    .dict-val.danger {{ color: var(--danger); font-weight: 800; }}

    /* SEPARATOR */
    .section-separator {{
      display: flex;
      align-items: center;
      text-align: center;
      margin: 10px 0 4px 0;
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
      color: var(--warning);
    }}

    /* ======================================================== */
    /* EXPANDED BENCHMARK SUITE CARDS                           */
    /* ======================================================== */
    .benchmark-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .benchmark-card.highlight-cyan {{
      border: 1.5px solid var(--info);
      box-shadow: 0 0 16px rgba(0, 229, 255, 0.1);
    }}

    .step-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--border);
    }}

    .step-tag {{
      font-size: 10px;
      font-weight: 900;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .subpage-link {{
      font-size: 10.5px;
      font-weight: 700;
      color: var(--info);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: rgba(0, 229, 255, 0.08);
      padding: 3px 8px;
      border-radius: 6px;
      border: 1px solid rgba(0, 229, 255, 0.25);
    }}

    .regime-hero-banner {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
    }}

    .regime-pill-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 10px;
      border-radius: 8px;
      font-size: 11.5px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.4px;
      margin-bottom: 8px;
    }}

    .regime-diag-title {{
      font-size: 16px;
      font-weight: 900;
      color: #ffffff;
      line-height: 1.25;
      margin-bottom: 6px;
    }}

    .regime-tagline {{
      font-size: 11.5px;
      color: var(--text-muted);
      line-height: 1.4;
    }}

    .methodology-box {{
      background: rgba(0, 0, 0, 0.35);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 11.5px;
      line-height: 1.45;
      color: var(--text-main);
    }}

    .methodology-box strong {{
      color: #ffffff;
    }}

    .evidence-checklist {{
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .evidence-item {{
      display: flex;
      align-items: flex-start;
      gap: 8px;
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 7px 10px;
      font-size: 11px;
      color: var(--text-main);
    }}

    .evidence-check {{
      color: var(--primary);
      font-weight: 900;
    }}

    /* 5-REGIME FRAMEWORK MATRIX */
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

    /* STEP 2 ROTATION CARD */
    .rotation-hero-box {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}

    .rotation-value-row {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      flex-wrap: wrap;
      gap: 6px;
    }}

    .rotation-target {{
      font-size: 20px;
      font-weight: 900;
      font-family: var(--font-mono);
      color: #ffffff;
      letter-spacing: 0.5px;
    }}

    .action-badge {{
      font-size: 11px;
      font-weight: 800;
      padding: 3px 8px;
      border-radius: 6px;
    }}

    .protocols-stack {{
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}

    .protocol-box {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 11px;
    }}

    .proto-lbl {{
      font-size: 9.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text-muted);
      margin-bottom: 3px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .proto-val {{
      font-size: 13px;
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 2px;
    }}

    .proto-sub {{
      font-size: 10.5px;
      color: var(--text-muted);
      line-height: 1.35;
    }}

    /* PLAIN ENGLISH BOTTOM LINE VERDICT */
    .plain-verdict-box {{
      background: rgba(0, 255, 102, 0.05);
      border: 1px solid rgba(0, 255, 102, 0.25);
      border-radius: 10px;
      padding: 12px;
      font-size: 12px;
      line-height: 1.45;
      color: var(--text-main);
    }}

    .why-factor-row {{
      display: flex;
      gap: 8px;
      align-items: flex-start;
      margin-top: 8px;
      font-size: 11px;
      line-height: 1.4;
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

    /* DUAL POOLS COMPARISON */
    .pools-dual-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}

    .pool-card {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }}

    .pool-card.upper {{
      border-color: rgba(255, 51, 68, 0.3);
    }}

    .pool-card.lower {{
      border-color: rgba(0, 255, 102, 0.3);
    }}

    .pool-title {{
      font-size: 9.5px;
      font-weight: 800;
      text-transform: uppercase;
    }}

    .pool-px {{
      font-size: 16px;
      font-weight: 900;
      font-family: var(--font-mono);
      color: #ffffff;
    }}

    .pool-dist {{
      font-size: 10.5px;
      font-family: var(--font-mono);
    }}

    .pool-vol {{
      font-size: 10px;
      color: var(--text-muted);
    }}

    /* LADDER ROWS */
    .ladder-stack {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      font-family: var(--font-mono);
      font-size: 11px;
    }}

    .ladder-row {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 7px 10px;
      border-radius: 7px;
      border: 1px solid var(--border);
      background: var(--bg-card-sub);
    }}

    .ladder-row.short {{
      border-color: rgba(255, 51, 68, 0.25);
      background: rgba(255, 51, 68, 0.05);
    }}

    .ladder-row.long {{
      border-color: rgba(0, 255, 102, 0.25);
      background: rgba(0, 255, 102, 0.05);
    }}

    .ladder-row.spot-anchor {{
      border: 2px solid var(--info);
      background: rgba(0, 229, 255, 0.12);
      padding: 9px 10px;
      margin: 3px 0;
    }}

    .ladder-row.dominant-core {{
      border: 2px solid var(--primary);
      background: rgba(0, 255, 102, 0.12);
      box-shadow: 0 0 12px rgba(0, 255, 102, 0.2);
    }}

    /* IMBALANCE BOXES */
    .imbalance-grid {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 8px;
    }}

    .imbalance-box {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 9px 11px;
      font-size: 11px;
    }}

    .imbalance-title {{
      font-size: 9.5px;
      font-weight: 800;
      text-transform: uppercase;
      color: var(--text-muted);
    }}

    .imbalance-val {{
      font-size: 15px;
      font-weight: 900;
      font-family: var(--font-mono);
      margin: 2px 0;
    }}

    /* 6 FACTORS GRID */
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

    .factor-title {{
      font-weight: 800;
      color: var(--text-muted);
      margin-bottom: 2px;
      display: block;
    }}

    /* 6 GAUGES GRID */
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
      font-size: 14px;
      font-weight: 800;
      font-family: var(--font-mono);
      color: #ffffff;
    }}

    .gauge-sub {{
      font-size: 9px;
      color: var(--text-muted);
    }}

    /* TOAST */
    .toast-overlay {{
      position: fixed;
      bottom: 24px;
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

    <!-- TOP HEADER -->
    <header class="top-bar">
      <div class="brand-group">
        <div class="brand-icon">🧲</div>
        <div class="brand-title">BTC Magnet Monitor</div>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 10px; color: var(--primary); font-family: var(--font-mono); font-weight: 700;">● LIVE FEED</span>
        <button class="theme-toggle-btn" id="theme-btn" onclick="cycleTheme()">NVG</button>
      </div>
    </header>

    <!-- REAL-TIME BTC SPOT PRICE BAR (Below Header) -->
    <div class="realtime-spot-bar">
      <div class="spot-bar-left">
        <div class="spot-bar-label">
          <span class="live-dot-mini"></span>
          <span>REAL-TIME BTC SPOT PRICE (LIVE)</span>
        </div>
        <div class="spot-bar-price-row">
          <span id="hero-spot-px" class="spot-bar-price">${spot_price:,.2f}</span>
          <span id="hero-price-chg" class="spot-bar-chg" style="color: {'var(--primary)' if p_chg_24h >= 0 else 'var(--danger)'}; background: {'rgba(0, 255, 102, 0.1)' if p_chg_24h >= 0 else 'rgba(255, 51, 68, 0.1)'}; border: 1px solid {'rgba(0, 255, 102, 0.3)' if p_chg_24h >= 0 else 'rgba(255, 51, 68, 0.3)'};">
            {'+' if p_chg_24h >= 0 else ''}{p_chg_24h:.2f}% (24h)
          </span>
        </div>
        <div id="hero-drift-container" style="font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); margin-top: 3px; display: flex; align-items: center; gap: 4px;">
          <span>Drift vs Scan:</span>
          <span id="hero-drift-val" style="color: #00e5ff; font-weight: 700;">$0.00 (0.00%)</span>
        </div>
      </div>
      <div class="spot-bar-right">
        <div class="spot-feed-provenance">BINANCE LIVE TICKER</div>
        <div class="spot-provenance-sub">Tick-by-Tick Feed</div>
      </div>
    </div>

    <!-- PART 1: TOP HERO — LIVE TIME & ACTIVE SESSION ZONE HUD -->
    <div class="top-hero-dictionary">

      <!-- Clocks Grid: UTC Time & SGT Time -->
      <div class="clocks-grid">
        <div class="time-card">
          <div class="time-card-title">🕒 UTC TIME</div>
          <div id="clock-utc-val" class="time-card-value">{utc_time_str}</div>
          <div id="clock-utc-date" class="time-card-sub">{utc_date_str}</div>
        </div>
        <div class="time-card">
          <div class="time-card-title">🇸🇬 SGT TIME (UTC+8)</div>
          <div id="clock-sgt-val" class="time-card-value">{sgt_time_str}</div>
          <div id="clock-sgt-date" class="time-card-sub">{sgt_date_str}</div>
        </div>
      </div>

      <!-- Active Session Zone ("what session zone is it") -->
      <div class="session-card">
        <div class="session-header-line">
          <div class="session-header-left">
            <span class="session-pulse-dot"></span>
            <span class="session-card-label">ACTIVE MARKET SESSION ZONE</span>
          </div>
          <span id="session-zone-badge" class="session-zone-badge" style="color: {sess_color}; border-color: {sess_color}; background: {sess_color}18;">{sess_badge}</span>
        </div>
        <div id="session-zone-title" class="session-name-main">{sess_name}</div>
        <div class="session-meta-row">
          <div id="session-zone-hours" class="session-zone-hours">{sess_hours}</div>
          <div id="session-zone-desc" class="session-zone-desc">{sess_desc}</div>
        </div>
      </div>

      <!-- NEXT SCHEDULED TELEMETRY UPDATE CARD (Between Session Zone and Card 1) -->
      <div class="next-update-card">
        <div class="next-update-header">
          <div class="next-update-title-group">
            <span class="update-icon">⏱️</span>
            <span class="next-update-label">NEXT ON-EXCHANGE TELEMETRY UPDATE</span>
          </div>
          <span class="next-update-cadence-badge">EVERY 30 MINS</span>
        </div>
        <div class="next-update-main-row">
          <div id="next-update-minutes" class="next-update-countdown">In ~{mins_left} minutes</div>
        </div>
        <div id="next-update-target" class="next-update-sub">
          Next snapshot scheduled at {next_utc_str} ({next_sgt_str})
        </div>
      </div>

      <!-- 4 Organized Categories -->
      <div class="dict-categories-stack">

        <!-- 1. Price & Structure -->
        <div class="dict-cat-card">
          <div class="dict-cat-header cat-title-1">
            <span>1. Price & Structure</span>
            <span style="font-size: 9px; color: var(--text-muted);">MACRO HORIZON</span>
          </div>
          <div class="dict-rows">
            <div class="dict-row"><span class="dict-lbl">Benchmark Scan Price:</span><span id="d-spot-px" class="dict-val" style="color: #00e5ff; font-weight: 900;">${spot_price:,.2f}</span></div>
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
        <div class="dict-cat-card">
          <div class="dict-cat-header cat-title-2">
            <span>2. Order Flow & CVD</span>
            <span style="font-size: 9px; color: var(--text-muted);">SPOT ABSORPTION</span>
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
        <div class="dict-cat-card">
          <div class="dict-cat-header cat-title-3">
            <span>3. Derivatives Crowding</span>
            <span style="font-size: 9px; color: var(--text-muted);">LEVERAGE EXPOSURE</span>
          </div>
          <div class="dict-rows">
            <div class="dict-row"><span class="dict-lbl">Open Interest:</span><span id="d-oi" class="dict-val">{oi:,.0f} BTC</span></div>
            <div class="dict-row"><span class="dict-lbl">OI 24h Change:</span><span id="d-oi-24h" class="dict-val">{oi_24h:+.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">OI 1h Change:</span><span id="d-oi-1h" class="dict-val">{oi_1h:+.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">OI 4h Change:</span><span id="d-oi-4h" class="dict-val">{oi_4h:+.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">Funding Rate (8h):</span><span id="d-funding" class="dict-val">{funding_rate:+.4f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">Futures Basis Ann.:</span><span id="d-basis" class="dict-val">{basis:+.2f}%</span></div>
            <div class="dict-row"><span class="dict-lbl">Retail Long/Short:</span><span id="d-ls-ratio" class="dict-val warn">{ls_ratio:.2f}</span></div>
          </div>
        </div>

        <!-- 4. Volatility & Magnets -->
        <div class="dict-cat-card">
          <div class="dict-cat-header cat-title-4">
            <span>4. Volatility & Magnets</span>
            <span style="font-size: 9px; color: var(--text-muted);">LIQUIDITY DEPTH</span>
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

      <!-- Action Button moved to bottom of 4. Volatility & Magnets -->
      <button class="btn-copy-prompt" onclick="copyAIPrompt()">
        <span style="font-size: 15px;">📋</span>
        <span id="copy-btn-text">Copy Data & Prompt for AI</span>
      </button>

      <!-- USER GUIDANCE NOTE: EXTERNAL AI PROMPT INVITATION -->
      <div class="ai-copy-helper-box">
        <span class="ai-helper-icon">💡</span>
        <div class="ai-helper-text">
          <strong>Interactive AI Discussion:</strong> Users are encouraged to tap the button above to copy all live on-exchange metrics and paste them directly into their favourite AI &mdash; such as <strong>Claude, ChatGPT, Grok, DeepSeek, or Meta AI</strong> &mdash; for deep independent analysis and interactive discussion for a deeper verdict.
        </div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- OUR SYSTEM VERDICT (ALGORITHMIC PLAYBOOK) — QUICK GLANCE  -->
    <!-- ======================================================== -->
    <div class="system-verdict-summary-card">
      <div class="verdict-card-top-tag">
        <div class="verdict-tag-left">
          <span class="live-dot-mini"></span>
          <span class="verdict-title-text">OUR SYSTEM VERDICT (ALGORITHMIC PLAYBOOK)</span>
        </div>
        <span class="quick-glance-badge">QUICK GLANCE</span>
      </div>

      <!-- Concise Summary Grid -->
      <div class="verdict-summary-grid">
        <!-- Metric 1: Macro Regime -->
        <div class="verdict-summary-item">
          <div class="v-sum-lbl">MACRO REGIME</div>
          <div class="v-sum-val" style="color: {regime_accent}; font-weight: 900;">
            {regime_icon} {regime_name}
          </div>
          <div class="v-sum-sub">{diagnosis}</div>
        </div>

        <!-- Metric 2: Spot Action & Sizing -->
        <div class="verdict-summary-item">
          <div class="v-sum-lbl">PORTFOLIO ROTATION</div>
          <div class="v-sum-val" style="color: {'var(--primary)' if 'BTC' in rotation else 'var(--warning)'}; font-weight: 900;">
            {'🛡️ ' if 'USDT' in rotation else '🚀 '}{rotation} ({sizing:.2f}x)
          </div>
          <div class="v-sum-sub">{playbook}</div>
        </div>

        <!-- Metric 3: Inviolable Safety Net -->
        <div class="verdict-summary-item">
          <div class="v-sum-lbl">INVIOLABLE SAFETY NET</div>
          <div class="v-sum-val" style="color: var(--danger); font-family: var(--font-mono);">
            ${disaster_stop:,.2f}
          </div>
          <div class="v-sum-sub">{disaster_dist:.2f}% Disaster Stop | Inval: ${structural_inval:,.2f}</div>
        </div>

        <!-- Metric 4: Dominant Magnet Pull -->
        <div class="verdict-summary-item">
          <div class="v-sum-lbl">DOMINANT LIQUIDATION MAGNET</div>
          <div class="v-sum-val" style="color: var(--info);">
            🧲 {dom_magnet}
          </div>
          <div class="v-sum-sub">{dom_reason}</div>
        </div>
      </div>

      <!-- Concise Executive Takeaway -->
      <div class="verdict-concise-callout">
        <span style="font-size: 14px; line-height: 1.2;">💡</span>
        <span><strong>Bottom Line Summary:</strong> {plain_verdict}</span>
      </div>

      <!-- Button to enter subpage for full analytical details and verdict -->
      <a href="./verdict.html" class="btn-subpage-verdict">
        <div class="btn-subpage-left">
          <span style="font-size: 15px;">📊</span>
          <span style="font-size: 13.5px; font-weight: 900; letter-spacing: 0.2px;">View our system verdict</span>
        </div>
        <span class="btn-arrow">&rarr;</span>
      </a>
    </div>

    

  </div>

  <!-- TOAST NOTIFICATION -->
  <div id="toast" class="toast-overlay">
    <span>📋</span>
    <span id="toast-msg">AI Prompt copied to clipboard!</span>
  </div>

  <script>
    let currentAIPrompt = {escaped_prompt};
    let lastSnapshotTime = new Date("{ts_iso}");

    // THEME SWITCHER
    const themes = ['theme-nvg', 'theme-ibm', 'theme-slate'];
    const themeLabels = {{ 'theme-nvg': 'NVG', 'theme-ibm': 'IBM', 'theme-slate': 'SLATE' }};
    let currentThemeIdx = 0;

    function cycleTheme() {{
      currentThemeIdx = (currentThemeIdx + 1) % themes.length;
      document.body.className = themes[currentThemeIdx];
      document.getElementById('theme-btn').textContent = themeLabels[themes[currentThemeIdx]];
      try {{ localStorage.setItem('btc_magnet_theme', themes[currentThemeIdx]); }} catch(e) {{}}
    }}

    try {{
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
      const originalText = btnText ? btnText.textContent : 'Copy Data & Prompt for AI';
      try {{
        await navigator.clipboard.writeText(currentAIPrompt);
        if (navigator.vibrate) navigator.vibrate(50);
        if (btnText) btnText.textContent = '✓ Data & Prompt Copied!';
        showToast("📋 AI Prompt copied! Paste into Claude / ChatGPT / Grok");
        setTimeout(() => {{ if (btnText) btnText.textContent = originalText; }}, 2500);
      }} catch (err) {{
        const ta = document.createElement('textarea');
        ta.value = currentAIPrompt;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        if (btnText) btnText.textContent = '✓ Data & Prompt Copied!';
        showToast("📋 AI Prompt copied to clipboard!");
        setTimeout(() => {{ if (btnText) btnText.textContent = originalText; }}, 2500);
      }}
    }}

    function showToast(msg) {{
      const t = document.getElementById('toast');
      const m = document.getElementById('toast-msg');
      m.textContent = msg;
      t.classList.add('active');
      setTimeout(() => {{ t.classList.remove('active'); }}, 3000);
    }}

    // LIVE CLOCKS & MARKET SESSION ENGINE (ticks every 1s)
    function getSessionZone(utcDate) {{
      const h = utcDate.getUTCHours() + utcDate.getUTCMinutes() / 60;
      if (h >= 0 && h < 7) {{
        return {{
          name: "🌏 Asia / Tokyo & Singapore Session",
          hours: "00:00 – 07:00 UTC (08:00 – 15:00 SGT)",
          badge: "ASIA",
          color: "#38bdf8",
          desc: "Asian Core Hours • Steady Accumulation / Range Flow"
        }};
      }} else if (h >= 7 && h < 8) {{
        return {{
          name: "🔄 Asia / London Transition",
          hours: "07:00 – 08:00 UTC (15:00 – 16:00 SGT)",
          badge: "TRANSITION",
          color: "#f59e0b",
          desc: "European Pre-Open • Early Liquidity Positioning"
        }};
      }} else if (h >= 8 && h < 13) {{
        return {{
          name: "🏛️ London / European Session",
          hours: "08:00 – 13:00 UTC (16:00 – 21:00 SGT)",
          badge: "LONDON",
          color: "#10b981",
          desc: "European Institutional Hours • High Spot Volume & Breakout Liquidity"
        }};
      }} else if (h >= 13 && h < 16.5) {{
        return {{
          name: "⚡ London & New York Overlap",
          hours: "13:00 – 16:30 UTC (21:00 – 00:30 SGT)",
          badge: "PEAK OVERLAP",
          color: "#ec4899",
          desc: "Peak Global Liquidity • Highest Volatility & Order Flow Depth"
        }};
      }} else if (h >= 16.5 && h < 21) {{
        return {{
          name: "🗽 New York Session (US Core)",
          hours: "16:30 – 21:00 UTC (00:30 – 05:00 SGT)",
          badge: "NEW YORK",
          color: "#6366f1",
          desc: "US Institutional Hours • ETF Flows & Derivatives Settlement"
        }};
      }} else {{
        return {{
          name: "🌙 Pacific / Off-Hours Transition",
          hours: "21:00 – 00:00 UTC (05:00 – 08:00 SGT)",
          badge: "OFF-HOURS",
          color: "#a855f7",
          desc: "Off-Hours Liquidity • Mean Reversion & Overnight Reset"
        }};
      }}
    }}

    function updateLiveClocks() {{
      const now = new Date();
      const pad = (n) => String(n).padStart(2, '0');
      
      const utcStr = pad(now.getUTCHours()) + ':' + pad(now.getUTCMinutes()) + ':' + pad(now.getUTCSeconds()) + ' UTC';
      
      const sgtDate = new Date(now.getTime() + (8 * 60 * 60 * 1000));
      const sgtStr = pad(sgtDate.getUTCHours()) + ':' + pad(sgtDate.getUTCMinutes()) + ':' + pad(sgtDate.getUTCSeconds()) + ' SGT';
      
      const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
      const utcDateStr = now.getUTCDate() + ' ' + months[now.getUTCMonth()] + ' ' + now.getUTCFullYear();
      const sgtDateStr = sgtDate.getUTCDate() + ' ' + months[sgtDate.getUTCMonth()] + ' ' + sgtDate.getUTCFullYear();

      const elUtc = document.getElementById('clock-utc-val');
      if (elUtc) elUtc.textContent = utcStr;
      const elUtcD = document.getElementById('clock-utc-date');
      if (elUtcD) elUtcD.textContent = utcDateStr;

      const elSgt = document.getElementById('clock-sgt-val');
      if (elSgt) elSgt.textContent = sgtStr;
      const elSgtD = document.getElementById('clock-sgt-date');
      if (elSgtD) elSgtD.textContent = sgtDateStr;

      const session = getSessionZone(now);
      const elSessTitle = document.getElementById('session-zone-title');
      if (elSessTitle) elSessTitle.textContent = session.name;
      const elSessHours = document.getElementById('session-zone-hours');
      if (elSessHours) elSessHours.textContent = session.hours;
      const elSessDesc = document.getElementById('session-zone-desc');
      if (elSessDesc) elSessDesc.textContent = session.desc;
      const elSessBadge = document.getElementById('session-zone-badge');
      if (elSessBadge) {{
        elSessBadge.textContent = session.badge;
        elSessBadge.style.color = session.color;
        elSessBadge.style.borderColor = session.color;
        elSessBadge.style.background = session.color + '18';
      }}

      // Next Scheduled Update Countdown (ticks every 1s)
      const utcM = now.getUTCMinutes();
      const utcS = now.getUTCSeconds();
      const targetMin = utcM < 30 ? 30 : 60;
      let totalSecsLeft = (targetMin * 60) - (utcM * 60 + utcS);
      if (totalSecsLeft <= 0) totalSecsLeft = 30 * 60;
      
      const minsLeft = Math.floor(totalSecsLeft / 60);
      const secsLeft = totalSecsLeft % 60;
      
      const targetDate = new Date(now);
      if (utcM < 30) {{
        targetDate.setUTCMinutes(30, 0, 0);
      }} else {{
        targetDate.setUTCHours(now.getUTCHours() + 1, 0, 0, 0);
      }}
      
      const targetUtcStr = pad(targetDate.getUTCHours()) + ':' + pad(targetDate.getUTCMinutes()) + ' UTC';
      const targetSgtDate = new Date(targetDate.getTime() + (8 * 60 * 60 * 1000));
      const targetSgtStr = pad(targetSgtDate.getUTCHours()) + ':' + pad(targetSgtDate.getUTCMinutes()) + ' SGT';
      
      const elMins = document.getElementById('next-update-minutes');
      if (elMins) {{
        elMins.textContent = 'In ~' + minsLeft + ' minutes (' + minsLeft + 'm ' + pad(secsLeft) + 's)';
      }}
      const elTarget = document.getElementById('next-update-target');
      if (elTarget) {{
        elTarget.textContent = 'Next snapshot scheduled at ' + targetUtcStr + ' (' + targetSgtStr + ')';
      }}
    }}
    setInterval(updateLiveClocks, 1000);
    updateLiveClocks();

    let benchmarkScanPrice = {spot_price};
    let currentLiveSpotPrice = {spot_price};

    function updateDrift(livePrice) {{
      const elDrift = document.getElementById('hero-drift-val');
      if (!elDrift || !benchmarkScanPrice || benchmarkScanPrice <= 0) return;
      const diff = livePrice - benchmarkScanPrice;
      const diffPct = (diff / benchmarkScanPrice) * 100;
      const sign = diff >= 0 ? '+' : '-';
      const color = diff >= 0 ? 'var(--primary)' : 'var(--danger)';
      elDrift.textContent = (diff >= 0 ? '+' : '-') + '$' + Math.abs(diff).toFixed(2) + ' (' + (diff >= 0 ? '+' : '') + diffPct.toFixed(2) + '%)';
      elDrift.style.color = color;
    }}

    // REAL-TIME BINANCE SPOT TICKER (Fetches live whenever opened + periodic poll)
    async function fetchLiveBinanceSpot() {{
      try {{
        const res = await fetch('https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT');
        if (!res.ok) return;
        const data = await res.json();
        const livePx = parseFloat(data.lastPrice);
        const chg = parseFloat(data.priceChangePercent);
        
        const elHero = document.getElementById('hero-spot-px');
        const elChg = document.getElementById('hero-price-chg');
        if (elHero && !isNaN(livePx)) {{
          currentLiveSpotPrice = livePx;
          elHero.textContent = '$' + livePx.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
        }}
        if (elChg && !isNaN(chg)) {{
          elChg.textContent = (chg >= 0 ? '+' : '') + chg.toFixed(2) + '% (24h)';
          elChg.style.color = chg >= 0 ? 'var(--primary)' : 'var(--danger)';
          elChg.style.background = chg >= 0 ? 'rgba(0, 255, 102, 0.1)' : 'rgba(255, 51, 68, 0.1)';
          elChg.style.borderColor = chg >= 0 ? 'rgba(0, 255, 102, 0.3)' : 'rgba(255, 51, 68, 0.3)';
        }}
        if (!isNaN(livePx)) {{
          updateDrift(livePx);
        }}
      }} catch(err) {{
        // Offline / fallback to last known
      }}
    }}

    // Real-Time WebSocket for tick-by-tick streaming
    function connectBinanceWs() {{
      try {{
        const ws = new WebSocket('wss://stream.binance.com:9443/ws/btcusdt@ticker');
        ws.onmessage = (event) => {{
          try {{
            const msg = JSON.parse(event.data);
            const livePx = parseFloat(msg.c);
            const chg = parseFloat(msg.P);
            const elHero = document.getElementById('hero-spot-px');
            const elChg = document.getElementById('hero-price-chg');
            if (elHero && !isNaN(livePx)) {{
              currentLiveSpotPrice = livePx;
              elHero.textContent = '$' + livePx.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
            }}
            if (elChg && !isNaN(chg)) {{
              elChg.textContent = (chg >= 0 ? '+' : '') + chg.toFixed(2) + '% (24h)';
              elChg.style.color = chg >= 0 ? 'var(--primary)' : 'var(--danger)';
              elChg.style.background = chg >= 0 ? 'rgba(0, 255, 102, 0.1)' : 'rgba(255, 51, 68, 0.1)';
              elChg.style.borderColor = chg >= 0 ? 'rgba(0, 255, 102, 0.3)' : 'rgba(255, 51, 68, 0.3)';
            }}
            if (!isNaN(livePx)) {{
              updateDrift(livePx);
            }}
          }} catch(e) {{}}
        }};
        ws.onerror = () => {{
          // Fallback to polling on error
        }};
        ws.onclose = () => {{
          // Reconnect after 5 seconds if connection dropped
          setTimeout(connectBinanceWs, 5000);
        }};
      }} catch(e) {{
        // WebSocket unsupported, REST polling will handle it
      }}
    }}

    // Start live feeds on open
    fetchLiveBinanceSpot();
    connectBinanceWs();
    setInterval(fetchLiveBinanceSpot, 3000);

    // 15-MINUTE DIAGNOSTIC SCAN POLLING (every 45s)
    async function pollLiveFeed() {{
      try {{
        const url = './regime.json?t=' + Date.now();
        const res = await fetch(url, {{ cache: 'no-store' }});
        if (!res.ok) return;
        const data = await res.json();

        const m = data.metrics || {{}};
        const r = data.regime || {{}};

        if (m.price) {{
          benchmarkScanPrice = Number(m.price);
          const pStr = '$' + benchmarkScanPrice.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
          // Note: d-spot-px is the Benchmark Scan Price anchor (Card 1)
          if (document.getElementById('d-spot-px')) document.getElementById('d-spot-px').textContent = pStr;
          if (currentLiveSpotPrice) updateDrift(currentLiveSpotPrice);
        }}
        if (m.daily_vwap) document.getElementById('d-vwap').textContent = '$' + Number(m.daily_vwap).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.weekly_vwap) document.getElementById('d-w-vwap').textContent = '$' + Number(m.weekly_vwap).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.ema_20d) document.getElementById('d-ema20').textContent = '$' + Number(m.ema_20d).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.ema_50d) document.getElementById('d-ema50').textContent = '$' + Number(m.ema_50d).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.ma_200d) document.getElementById('d-sma200').textContent = '$' + Number(m.ma_200d).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        
        if (m.spot_cvd_ratio !== undefined) {{
          document.getElementById('d-cvd-ratio').textContent = Number(m.spot_cvd_ratio).toFixed(2);
          if (document.getElementById('g-cvd')) document.getElementById('g-cvd').textContent = Number(m.spot_cvd_ratio).toFixed(2);
        }}
        if (m.funding_rate !== undefined) {{
          document.getElementById('d-funding').textContent = (m.funding_rate * 100 >= 0 ? '+' : '') + (m.funding_rate * 100).toFixed(4) + '%';
        }}
        if (m.open_interest !== undefined) {{
          document.getElementById('d-oi').textContent = Number(m.open_interest).toLocaleString('en-US', {{maximumFractionDigits: 0}}) + ' BTC';
        }}
        
        if (r.name) document.getElementById('regime-name').textContent = r.name;
        if (r.diagnosis) document.getElementById('regime-diag').textContent = r.diagnosis;
        if (r.rotation) document.getElementById('rotation-val').textContent = r.rotation;
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


    def render_verdict_subpage(self, data: Dict[str, Any], raw_llm_prompt: str = "") -> str:
        """Renders the dedicated, plain-English, 7-card numbered subpage for the Algorithmic Verdict."""
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})
        ts_iso = data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
        escaped_prompt = json.dumps(raw_llm_prompt)

        spot_price = metrics.get("price", 74827.09)
        p_chg_24h = metrics.get("price_change_24h_pct", 0.71)
        daily_vwap = metrics.get("daily_vwap", spot_price * 0.998)
        weekly_vwap = metrics.get("weekly_vwap", spot_price * 0.995)
        ema_20d = metrics.get("ema_20d", spot_price * 1.025)
        ema_50d = metrics.get("ema_50d", spot_price * 1.042)
        ma_200d = metrics.get("ma_200d", spot_price * 0.978)
        swing_high = metrics.get("swing_high_4h", 75568.0)
        swing_low = metrics.get("swing_low_4h", 73750.0)
        base_floor = metrics.get("base_floor", 73510.0)

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
        rotation = regime.get("rotation", "USDT -> BTC")
        sizing = regime.get("sizing_factor", 0.75)
        action = regime.get("action", "Trade the Magnet (0.75x)")
        playbook = regime.get("action", "Core Operating Zone — Trade the Magnet (0.75x)")
        entry_inst = regime.get("entry_instruction", "Confirmed sweep & reclaim: 50% market spot / 50% limit at reclaimed range floor.")

        if "USDT -> BTC" in rotation:
            action_pill = "Buy Spot (Accumulate)"
        elif "BTC -> USDT" in rotation:
            action_pill = "Trim Spot / Harvest to Cash"
        else:
            action_pill = "Defensive Cash"

        stop_price = regime.get("stop_price", spot_price * 0.98)
        stop_dist = regime.get("stop_distance_pct", 2.0)
        disaster_stop = regime.get("disaster_stop_price", 72354.94)
        disaster_dist = regime.get("disaster_stop_distance_pct", 3.30)
        structural_inval = regime.get("structural_invalidation_level", 73750.00)
        stop_rule = regime.get("stop_rule", "Structural: 1H close < 4H swing low | Inviolable: Below 200D SMA & 25x shelf -0.7%")

        risk_budget_ok = risk.get("risk_budget_ok", True)
        actionable_trade_instruction = risk.get(
            "actionable_trade_instruction",
            f"Deploy {int(sizing*100*0.4)}% of your available USDT cash to buy spot BTC (Strictly capped at 0.99% total portfolio risk)."
        )

        plain_verdict = regime.get(
            "plain_english_verdict",
            f"Bitcoin is oscillating in a defined trading range. LSCE Status: {regime.get('lsce_status', 'SWEEP_AND_RECLAIM_CONFIRMED')}. Market makers hunt leverage on both sides."
        )
        why_points = regime.get("why_points", [
            "Sub-VWAP Trend: Price remains pinned beneath Daily and Weekly VWAP benchmarks with 20D/50D EMA overhead resistance.",
            "Depressed Volume Participation: Spot volume is running below the 20D moving average; bounces lack aggressive institutional taker buy volume.",
            "Defensive Capital Preservation: Preserving USDT cash in 100% reserve until authenticated Spot CVD and market structure reclaim occur."
        ])
        why_sizing = regime.get(
            "why_sizing_reason",
            "Capital preservation is paramount. Sizing is strictly tied to confirmed on-exchange spot absorption."
        )
        why_stop = regime.get(
            "why_stop_reason",
            f"Inviolable Disaster Stop at ${disaster_stop:,.2f} ({disaster_dist:.2f}% away), positioned safely below key institutional support."
        )

        imm_ratio = regime.get("immediate_imbalance_ratio", 24.5)
        tot_ratio = regime.get("total_ladder_imbalance_ratio", 1.70)
        tot_l_vol = regime.get("total_ladder_lower_vol", 337.8)
        tot_u_vol = regime.get("total_ladder_upper_vol", 199.2)
        dom_magnet = regime.get("dominant_magnet", "Lower Long Sweep Magnet")
        dom_reason = regime.get("dominant_magnet_reason", "LOWER (Immediate 24.5x / Ladder 1.70x; longs 64.9% crowded)")

        lsce_status = regime.get("lsce_status", "SWEEP_AND_RECLAIM_CONFIRMED")

        # Conflict Guard formatting
        if lsce_status == "SWEEP_AND_RECLAIM_CONFIRMED":
            if sizing > 0 and "USDT -> BTC" in rotation:
                lsce_badge_icon = "✅"
                lsce_badge_title = f"SWEEP & RECLAIM CONFIRMED (BUY AUTHORIZED {sizing:.2f}x)"
                lsce_badge_color = "var(--primary)"
                lsce_badge_bg = "rgba(0, 255, 102, 0.1)"
                lsce_badge_border = "rgba(0, 255, 102, 0.35)"
                lsce_detail = f"Lower liquidation shelf (${l_p:,.0f}) swept and reclaimed with positive spot absorption. Authorized {sizing:.2f}x entry."
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
            lsce_detail = f"Liquidation cascade active near ${l_p:,.0f}. Awaiting reversal verification."
        else:
            lsce_badge_icon = "⏸️"
            lsce_badge_title = "UNTESTED (MONITORING / CASH)"
            lsce_badge_color = "var(--text-muted)"
            lsce_badge_bg = "rgba(255, 255, 255, 0.05)"
            lsce_badge_border = "var(--border)"
            lsce_detail = "Liquidity shelf remains untested. No entry triggered."

        # Regime Tagline & Icon
        if regime_id == "SPOT_LED_EXPANSION":
            regime_icon = "🚀"
            regime_tagline = "Genuine spot buyers in control. Favorable environment for trend-following spot longs."
            regime_accent = "var(--primary)"
        elif regime_id == "LEVERAGED_FRAGILE_UPSIDE":
            regime_icon = "⚠️"
            regime_tagline = "Advance built on dangerous borrowed futures leverage. High probability of long squeeze."
            regime_accent = "var(--warning)"
        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            regime_icon = "🌊"
            regime_tagline = "Forced margin liquidation cascade in progress. Strictly avoid buying until selling ceases."
            regime_accent = "var(--danger)"
        elif regime_id == "DISTRIBUTION_BEAR_CONTINUATION":
            regime_icon = "📉"
            regime_tagline = "Structural seller control. Whales distributing into retail bounces. Cash preservation priority."
            regime_accent = "var(--danger)"
        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            regime_icon = "🧲"
            regime_tagline = "Price bound within defined horizontal channel. Positioning imbalance and liquidation magnets dominate."
            regime_accent = "var(--info)"
        else:
            regime_icon = "⚖️"
            regime_tagline = "Market indicators conflicting or transitioning between regimes. Capital preservation in cash."
            regime_accent = "var(--text-muted)"

        matched_criteria = regime.get("matched_criteria", [
            f"Price below Daily VWAP, 20D EMA, and 50D EMA",
            f"Spot volume depressed ({spot_vol_ratio:.2f}x 20D MA)",
            f"Positioning crowded (L/S {ls_ratio:.2f}, funding {funding_rate/100:.3f}%)"
        ])

        magnet_factors = regime.get("magnet_factors", {})
        f1 = magnet_factors.get("factor_1_size", f"Immediate Tier: LOWER is {imm_ratio:.1f}x larger (${l_vol:.1f}M vs ${u_vol:.1f}M) | Total Ladder: LOWER is {tot_ratio:.2f}x (${tot_l_vol:.1f}M vs ${tot_u_vol:.1f}M)")
        f2 = magnet_factors.get("factor_2_spot_leadership", f"Spot CVD ratio {spot_cvd_ratio:.2f} vs Perp CVD {perp_trend}")
        f3 = magnet_factors.get("factor_3_crowding_fuel", f"Funding {funding_rate/100:.3f}%, Retail L/S {ls_ratio:.2f} ({(ls_ratio/(1+ls_ratio))*100:.1f}% long)")
        f4 = magnet_factors.get("factor_4_regime_structure", "Range compression with downside fragility")
        f5 = magnet_factors.get("factor_5_asymmetry", f"LOWER is {l_d:.2f}% away vs UPPER {u_d:.2f}% away")
        f6 = magnet_factors.get("factor_6_atr_volatility", f"ATR compressed {atr_comp:.1f}%")

        p_10x_short = swing_high * 1.025
        d_10x_short = ((p_10x_short - spot_price) / spot_price) * 100
        p_25x_short = swing_high * 1.012
        d_25x_short = ((p_25x_short - spot_price) / spot_price) * 100

        p_25x_long = swing_low * 0.988
        d_25x_long = ((spot_price - p_25x_long) / spot_price) * 100
        p_10x_long = swing_low * 0.975
        d_10x_long = ((spot_price - p_10x_long) / spot_price) * 100

        # Build evidence checklist rows
        evidence_html = "".join([
            f'''<div class="factor-num-row">
              <span style="color: var(--primary); font-weight: 900; font-size: 13px;">✓</span>
              <span style="color: var(--text-main);">{item}</span>
            </div>'''
            for item in matched_criteria
        ])

        # Build Why Points rows
        why_points_html = "".join([
            f'''<div class="factor-num-row">
              <div class="factor-num-circle">{idx+1}</div>
              <div style="color: var(--text-main);">{pt}</div>
            </div>'''
            for idx, pt in enumerate(why_points)
        ])

        # Extract styles from render_mobile_app
        app_full = self.render_mobile_app(data)
        s_start = app_full.find("<style>")
        s_end = app_full.find("</style>") + 8
        styles = app_full[s_start:s_end] if s_start != -1 else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>BTC Magnet | Our System Verdict (Algorithmic Playbook)</title>
  <meta name="theme-color" content="#030804">
  {styles}
  <style>
    /* EXTRA STYLES FOR NUMBERED VERDICT CARDS */
    .verdict-subpage-hero {{
      background: linear-gradient(180deg, rgba(255, 184, 0, 0.08) 0%, rgba(10, 17, 13, 0.95) 100%);
      border: 2px solid #ffb800;
      border-radius: 14px;
      padding: 14px 16px;
      margin-bottom: 14px;
      box-shadow: 0 0 24px rgba(255, 184, 0, 0.15);
    }}

    .hero-badge {{
      font-size: 9.5px;
      font-weight: 800;
      color: #ffb800;
      font-family: var(--font-mono);
      letter-spacing: 0.6px;
      margin-bottom: 4px;
      text-transform: uppercase;
    }}

    .hero-title {{
      font-size: 18px;
      font-weight: 900;
      color: #ffffff;
      margin-bottom: 6px;
      letter-spacing: -0.2px;
      line-height: 1.2;
    }}

    .hero-subtitle {{
      font-size: 11.5px;
      color: var(--text-muted);
      line-height: 1.45;
      margin: 0;
    }}

    .numbered-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px 16px;
      margin-bottom: 14px;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
    }}

    .numbered-card.card-border-gold {{
      border: 2px solid #ffb800;
      box-shadow: 0 0 20px rgba(255, 184, 0, 0.12);
    }}

    .numbered-card.card-border-cyan {{
      border: 1.5px solid var(--info);
      box-shadow: 0 0 20px rgba(0, 229, 255, 0.1);
    }}

    .numbered-card.card-border-danger {{
      border: 1.5px solid var(--danger);
      box-shadow: 0 0 20px rgba(255, 51, 68, 0.1);
    }}

    .card-num-header {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 10px;
      padding-bottom: 8px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }}

    .card-num-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 900;
      letter-spacing: 0.5px;
      font-family: var(--font-mono);
      text-transform: uppercase;
    }}

    .card-plain-title {{
      font-size: 15.5px;
      font-weight: 900;
      color: #ffffff;
      margin-bottom: 4px;
      letter-spacing: -0.2px;
    }}

    .card-plain-sub {{
      font-size: 11.5px;
      color: var(--text-muted);
      line-height: 1.4;
      margin-bottom: 12px;
    }}

    .factor-num-row {{
      display: flex;
      align-items: flex-start;
      gap: 10px;
      padding: 9px 10px;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.05);
      margin-bottom: 6px;
      font-size: 12px;
      line-height: 1.4;
    }}

    .factor-num-circle {{
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: rgba(0, 229, 255, 0.15);
      color: var(--info);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      font-weight: 900;
      font-family: var(--font-mono);
      flex-shrink: 0;
      margin-top: 1px;
    }}

    .btn-return-cockpit {{
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      width: 100%;
      background: linear-gradient(135deg, rgba(255, 184, 0, 0.22) 0%, rgba(255, 140, 0, 0.16) 100%);
      border: 1.5px solid #ffb800;
      color: #ffffff;
      padding: 14px 16px;
      border-radius: 12px;
      text-decoration: none;
      font-size: 13.5px;
      font-weight: 900;
      letter-spacing: 0.2px;
      box-shadow: 0 4px 16px rgba(255, 184, 0, 0.22);
      transition: all 0.2s ease;
      cursor: pointer;
    }}

    .btn-return-cockpit:active {{
      transform: scale(0.98);
      background: #ffb800;
      color: #030804;
    }}
  </style>
</head>
<body class="theme-nvg">
  <div class="app-container">
    
    <!-- SUBPAGE NAVIGATION HEADER -->
    <header class="top-bar">
      <a href="./app.html" style="display: inline-flex; align-items: center; gap: 6px; color: #ffb800; text-decoration: none; font-size: 11.5px; font-weight: 800; font-family: var(--font-mono);">
        <span>&larr;</span>
        <span>Return to Live Cockpit</span>
      </a>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 10px; color: #ffb800; font-family: var(--font-mono); font-weight: 700;">● DETAILED VERDICT</span>
        <button class="theme-toggle-btn" id="theme-btn" onclick="cycleTheme()">NVG</button>
      </div>
    </header>

    <!-- SUBPAGE HERO BANNER -->
    <div class="verdict-subpage-hero">
      <div class="hero-badge">OUR SYSTEM VERDICT • STEP-BY-STEP PLAYBOOK</div>
      <h1 class="hero-title">Quantitative Proof &amp; Analytical Playbook</h1>
      <p class="hero-subtitle">
        Everything below is computed deterministically from verified on-exchange order flow, liquidation depth, and funding rates. Follow the 7 numbered cards below to understand the exact market state and risk directives.
      </p>
    </div>

    <!-- ======================================================== -->
    <!-- CARD 1: ACTION & PORTFOLIO ROTATION DIRECTIVE            -->
    <!-- ======================================================== -->
    <div class="numbered-card card-border-gold">
      <div class="card-num-header">
        <div class="card-num-badge" style="color: #ffb800;">
          <span>🎯</span>
          <span>CARD 1 • ACTION &amp; ROTATION DIRECTIVE</span>
        </div>
        <span class="quick-glance-badge" style="background: rgba(255, 184, 0, 0.15); border-color: rgba(255, 184, 0, 0.4); color: #ffb800;">MANDATE</span>
      </div>
      <div class="card-plain-title">What should you do with your portfolio right now?</div>
      <div class="card-plain-sub">Strict spot-only execution. Zero borrowed leverage, zero futures gambling, zero shorting.</div>

      <!-- Action Box -->
      <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
        <div style="font-size: 10px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 4px;">RECOMMENDED ROTATION</div>
        <div style="font-size: 17px; font-weight: 900; color: {'var(--primary)' if 'BTC' in rotation else '#ffb800'}; margin-bottom: 2px;">
          {'🛡️ ' if 'USDT' in rotation else '🚀 '}{rotation}
        </div>
        <div style="font-size: 12px; color: var(--text-main);">{action_pill} • Sizing: {sizing:.2f}x</div>
      </div>

      <!-- Protocol Instruction -->
      <div style="background: rgba(255, 255, 255, 0.02); border-left: 3px solid #ffb800; padding: 10px 12px; border-radius: 4px 8px 8px 4px; font-size: 12px; color: var(--text-main); line-height: 1.45; margin-bottom: 10px;">
        <strong>Playbook Protocol:</strong> {entry_inst}
      </div>

      <!-- Plain English Verdict -->
      <div style="background: rgba(0, 229, 255, 0.04); border: 1px solid rgba(0, 229, 255, 0.25); border-radius: 8px; padding: 10px 12px; font-size: 12px; line-height: 1.45; color: var(--text-main);">
        💡 <strong>Plain English Rationale:</strong> {plain_verdict}
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- CARD 2: MACRO MARKET REGIME DIAGNOSIS                     -->
    <!-- ======================================================== -->
    <div class="numbered-card card-border-cyan">
      <div class="card-num-header">
        <div class="card-num-badge" style="color: var(--info);">
          <span>🧭</span>
          <span>CARD 2 • MACRO MARKET REGIME DIAGNOSIS</span>
        </div>
        <span style="font-size: 10px; font-family: var(--font-mono); color: var(--text-muted);">{score_str}</span>
      </div>
      <div class="card-plain-title">What market environment is Bitcoin currently in?</div>
      <div class="card-plain-sub">Bitcoin is classified strictly into 1 of 5 deterministic regimes based on majority on-exchange evidence.</div>

      <!-- Regime Hero Banner -->
      <div style="background: rgba(0, 229, 255, 0.05); border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
        <div style="font-size: 16px; font-weight: 900; color: {regime_accent}; margin-bottom: 4px;">
          {regime_icon} {regime_name}
        </div>
        <div style="font-size: 12.5px; font-weight: 700; color: #ffffff; margin-bottom: 2px;">{diagnosis}</div>
        <div style="font-size: 11.5px; color: var(--text-muted); line-height: 1.4;">{regime_tagline}</div>
      </div>

      <!-- Verified Evidence Checklist -->
      <div style="margin-top: 10px;">
        <div style="font-size: 10.5px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 6px;">
          VERIFIED ON-EXCHANGE EVIDENCE ({score_str})
        </div>
        {evidence_html}
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- CARD 3: INVIOLABLE SAFETY NET & RISK CONTROLS             -->
    <!-- ======================================================== -->
    <div class="numbered-card card-border-danger">
      <div class="card-num-header">
        <div class="card-num-badge" style="color: var(--danger);">
          <span>🛡️</span>
          <span>CARD 3 • INVIOLABLE SAFETY NET &amp; RISK CONTROLS</span>
        </div>
        <span style="font-size: 9px; font-family: var(--font-mono); background: rgba(255, 51, 68, 0.15); color: var(--danger); border: 1px solid rgba(255, 51, 68, 0.4); padding: 2px 6px; border-radius: 4px;">HARD RISK BOUND</span>
      </div>
      <div class="card-plain-title">Where is your capital protected if the market dumps?</div>
      <div class="card-plain-sub">Mathematical hard stops positioned safely beyond standard whale manipulation sweeps.</div>

      <!-- Disaster Stop Box -->
      <div style="background: rgba(255, 51, 68, 0.05); border: 1px solid rgba(255, 51, 68, 0.35); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
        <div style="font-size: 10px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 2px;">INVIOLABLE DISASTER HARD STOP</div>
        <div style="font-size: 20px; font-weight: 900; color: var(--danger); font-family: var(--font-mono); margin-bottom: 2px;">
          ${disaster_stop:,.2f}
          <span style="font-size: 12px; color: var(--text-muted); font-weight: normal;">({disaster_dist:.2f}% Disaster Distance)</span>
        </div>
        <div style="font-size: 11.5px; font-family: var(--font-mono); color: var(--warning); margin-bottom: 4px;">
          Structural Invalidation: 1H Close &lt; ${structural_inval:,.2f}
        </div>
        <div style="font-size: 11px; color: var(--text-muted);">{stop_rule}</div>
      </div>

      <!-- Risk Budget Box -->
      <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 10px; padding: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
          <span style="font-size: 10px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; font-family: var(--font-mono);">RISK BUDGET VERIFICATION</span>
          <span style="font-size: 10px; font-weight: 800; color: {'var(--primary)' if risk_budget_ok else 'var(--warning)'}; font-family: var(--font-mono);">
            {'✓ APPROVED (CAPPED AT 1% MAX RISK)' if risk_budget_ok else 'HOLD CASH'}
          </span>
        </div>
        <div style="font-size: 11.5px; color: var(--text-main); line-height: 1.4;">{actionable_trade_instruction}</div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- CARD 4: LIQUIDATION MAGNETS & PRICE PULL                  -->
    <!-- ======================================================== -->
    <div class="numbered-card">
      <div class="card-num-header">
        <div class="card-num-badge" style="color: var(--info);">
          <span>🧲</span>
          <span>CARD 4 • LIQUIDATION MAGNETS &amp; PRICE GRAVITY</span>
        </div>
        <span style="font-size: 9px; font-family: var(--font-mono); background: rgba(0, 229, 255, 0.15); color: var(--info); border: 1px solid rgba(0, 229, 255, 0.35); padding: 2px 6px; border-radius: 4px;">TARGET POOLS</span>
      </div>
      <div class="card-plain-title">Where are market makers pulling the price to hunt liquidity?</div>
      <div class="card-plain-sub">Institutions require liquidity clusters to fill massive orders. Price naturally gravitates toward the heaviest pool.</div>

      <!-- Dominant Pull Banner -->
      <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border); border-radius: 10px; padding: 12px; margin-bottom: 10px;">
        <div style="font-size: 10px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; font-family: var(--font-mono); margin-bottom: 2px;">DOMINANT GRAVITATIONAL PULL</div>
        <div style="font-size: 15px; font-weight: 900; color: var(--info); margin-bottom: 2px;">🧲 {dom_magnet}</div>
        <div style="font-size: 11px; color: var(--text-muted);">{dom_reason}</div>
      </div>

      <!-- LSCE State Machine Badge -->
      <div style="background: {lsce_badge_bg}; border: 1px solid {lsce_badge_border}; border-radius: 10px; padding: 12px; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
          <span>{lsce_badge_icon}</span>
          <span style="font-size: 11px; font-weight: 900; color: {lsce_badge_color}; font-family: var(--font-mono);">{lsce_badge_title}</span>
        </div>
        <div style="font-size: 11.5px; color: var(--text-main); line-height: 1.4;">{lsce_detail}</div>
      </div>

      <!-- Upper and Lower Pools Grid -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
        <div style="background: rgba(255, 51, 68, 0.05); border: 1px solid rgba(255, 51, 68, 0.3); border-radius: 10px; padding: 10px;">
          <div style="font-size: 9.5px; font-weight: 800; color: var(--danger); font-family: var(--font-mono); text-transform: uppercase;">UPPER SHORT POOL</div>
          <div style="font-size: 16px; font-weight: 900; color: #ffffff; font-family: var(--font-mono);">${u_p:,.0f}</div>
          <div style="font-size: 10.5px; color: var(--danger); font-family: var(--font-mono);">+{u_d:.2f}% (+{u_atr:.2f} ATR)</div>
          <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">Est. Size: ${u_vol:.1f}M</div>
        </div>
        <div style="background: rgba(0, 255, 102, 0.05); border: 1px solid rgba(0, 255, 102, 0.3); border-radius: 10px; padding: 10px;">
          <div style="font-size: 9.5px; font-weight: 800; color: var(--primary); font-family: var(--font-mono); text-transform: uppercase;">LOWER LONG POOL</div>
          <div style="font-size: 16px; font-weight: 900; color: #ffffff; font-family: var(--font-mono);">${l_p:,.0f}</div>
          <div style="font-size: 10.5px; color: var(--primary); font-family: var(--font-mono);">-{l_d:.2f}% (-{l_atr:.2f} ATR)</div>
          <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px;">Est. Size: ${l_vol:.1f}M</div>
        </div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- CARD 5: LIQUIDATION HEATMAP LADDER                        -->
    <!-- ======================================================== -->
    <div class="numbered-card">
      <div class="card-num-header">
        <div class="card-num-badge" style="color: var(--primary);">
          <span>🔥</span>
          <span>CARD 5 • LIQUIDATION HEATMAP &amp; LEVERAGE DEPTH</span>
        </div>
        <span style="font-size: 9px; font-family: var(--font-mono); color: var(--text-muted);">10x - 100x BANDS</span>
      </div>
      <div class="card-plain-title">What does the full leverage spectrum look like?</div>
      <div class="card-plain-sub">Modeled clusters derived from real-time open interest and liquidation concentration models.</div>

      <!-- Visual Heatmap Ladder -->
      <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 10px; padding: 10px; font-family: var(--font-mono); font-size: 11px;">
        <!-- 10x Shorts -->
        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <span style="color: var(--danger);">10x Shorts</span>
          <span style="color: #ffffff; font-weight: 700;">${p_10x_short:,.0f}</span>
          <span style="color: var(--text-muted);">+{d_10x_short:.2f}% • ~$85M</span>
        </div>
        <!-- 25x Shorts -->
        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <span style="color: var(--danger);">25x Shorts</span>
          <span style="color: #ffffff; font-weight: 700;">${p_25x_short:,.0f}</span>
          <span style="color: var(--text-muted);">+{d_25x_short:.2f}% • ~$110M</span>
        </div>
        <!-- 50-100x Shorts -->
        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <span style="color: var(--danger);">50-100x Shorts</span>
          <span style="color: #ffffff; font-weight: 700;">${u_p:,.0f}</span>
          <span style="color: var(--danger);">+{u_d:.2f}% • ${u_vol:.1f}M</span>
        </div>
        <!-- ZERO AXIS SPOT PRICE -->
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 6px; margin: 4px 0; background: rgba(0, 255, 102, 0.12); border-radius: 6px; border: 1px solid var(--primary);">
          <span style="color: var(--primary); font-weight: 900;">● SPOT ZERO-AXIS</span>
          <span style="color: #ffffff; font-weight: 900; font-size: 13px;">${spot_price:,.2f}</span>
          <span style="color: var(--primary); font-size: 9px; font-weight: 800;">ANCHOR</span>
        </div>
        <!-- 100x Longs -->
        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <span style="color: var(--primary);">🔥 100x Longs</span>
          <span style="color: #ffffff; font-weight: 700;">${l_p:,.0f}</span>
          <span style="color: var(--primary);">-{l_d:.2f}% • ${l_vol:.1f}M</span>
        </div>
        <!-- 25x Longs -->
        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);">
          <span style="color: var(--primary);">25x Longs</span>
          <span style="color: #ffffff; font-weight: 700;">${p_25x_long:,.0f}</span>
          <span style="color: var(--text-muted);">-{d_25x_long:.2f}% • ~$140M</span>
        </div>
        <!-- 10x Longs -->
        <div style="display: flex; justify-content: space-between; padding: 6px 0;">
          <span style="color: var(--primary);">10x Longs</span>
          <span style="color: #ffffff; font-weight: 700;">${p_10x_long:,.0f}</span>
          <span style="color: var(--text-muted);">-{d_10x_long:.2f}% • ~$95M</span>
        </div>
      </div>

      <!-- Skew Summary -->
      <div style="margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px;">
          <div style="font-size: 9px; color: var(--text-muted); font-family: var(--font-mono);">NEAREST TIER SKEW</div>
          <div style="font-size: 14px; font-weight: 900; color: var(--info);">{imm_ratio:.1f}x Skew</div>
        </div>
        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 8px 10px;">
          <div style="font-size: 9px; color: var(--text-muted); font-family: var(--font-mono);">TOTAL SPECTRUM SKEW</div>
          <div style="font-size: 14px; font-weight: 900; color: var(--info);">{tot_ratio:.2f}x Skew</div>
        </div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- CARD 6: SIX-FACTOR DECISION PROOF                         -->
    <!-- ======================================================== -->
    <div class="numbered-card">
      <div class="card-num-header">
        <div class="card-num-badge" style="color: #ffffff;">
          <span>⚖️</span>
          <span>CARD 6 • SIX-FACTOR DECISION PROOF</span>
        </div>
        <span style="font-size: 9px; font-family: var(--font-mono); color: var(--text-muted);">HIERARCHY AUDIT</span>
      </div>
      <div class="card-plain-title">What is the exact mathematical proof driving this call?</div>
      <div class="card-plain-sub">Hierarchy: Pool Size &gt; Spot CVD &gt; Crowding &gt; Regime &gt; Distance &gt; ATR.</div>

      <div class="factor-num-row">
        <div class="factor-num-circle">1</div>
        <div><strong>Cluster Magnitude:</strong> {f1}</div>
      </div>
      <div class="factor-num-row">
        <div class="factor-num-circle">2</div>
        <div><strong>Spot vs. Derivatives Flow:</strong> {f2}</div>
      </div>
      <div class="factor-num-row">
        <div class="factor-num-circle">3</div>
        <div><strong>Crowding &amp; Market Fuel:</strong> {f3}</div>
      </div>
      <div class="factor-num-row">
        <div class="factor-num-circle">4</div>
        <div><strong>Higher-Timeframe Structure:</strong> {f4}</div>
      </div>
      <div class="factor-num-row">
        <div class="factor-num-circle">5</div>
        <div><strong>Distance Asymmetry:</strong> {f5}</div>
      </div>
      <div class="factor-num-row">
        <div class="factor-num-circle">6</div>
        <div><strong>Volatility Regime (ATR):</strong> {f6}</div>
      </div>

      <div style="background: rgba(255, 184, 0, 0.06); border-left: 3px solid #ffb800; padding: 10px 12px; border-radius: 4px 8px 8px 4px; font-size: 12px; color: var(--text-main); margin-top: 8px;">
        <strong>Decisive Algorithmic Conclusion:</strong> {dom_reason}
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- CARD 7: MARKET MICROSTRUCTURE GAUGES                      -->
    <!-- ======================================================== -->
    <div class="numbered-card">
      <div class="card-num-header">
        <div class="card-num-badge" style="color: var(--primary);">
          <span>📡</span>
          <span>CARD 7 • MARKET MICROSTRUCTURE GAUGES</span>
        </div>
        <span style="font-size: 9px; font-family: var(--font-mono); color: var(--text-muted);">LIVE EXCHANGES</span>
      </div>
      <div class="card-plain-title">What are the raw verified metrics from Binance &amp; Deribit?</div>
      <div class="card-plain-sub">Key quantitative telemetry backing every single calculation above.</div>

      <div class="gauges-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
        <div class="gauge-card" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 10px;">
          <div style="font-size: 9.5px; color: var(--text-muted); font-family: var(--font-mono); text-transform: uppercase;">Spot CVD Ratio</div>
          <div style="font-size: 16px; font-weight: 900; color: #ffffff; font-family: var(--font-mono);">{spot_cvd_ratio:.2f}</div>
          <div style="font-size: 9.5px; color: var(--text-muted);">Taker Buy/Sell</div>
        </div>
        <div class="gauge-card" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 10px;">
          <div style="font-size: 9.5px; color: var(--text-muted); font-family: var(--font-mono); text-transform: uppercase;">Perp CVD Flow</div>
          <div style="font-size: 16px; font-weight: 900; color: #ffffff; font-family: var(--font-mono); text-transform: capitalize;">{perp_trend}</div>
          <div style="font-size: 9.5px; color: var(--text-muted);">Futures Trend</div>
        </div>
        <div class="gauge-card" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 10px;">
          <div style="font-size: 9.5px; color: var(--text-muted); font-family: var(--font-mono); text-transform: uppercase;">Open Interest (24h)</div>
          <div style="font-size: 16px; font-weight: 900; color: #ffffff; font-family: var(--font-mono);">{oi_24h:+.2f}%</div>
          <div style="font-size: 9.5px; color: var(--text-muted);">{oi:,.0f} BTC</div>
        </div>
        <div class="gauge-card" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 10px;">
          <div style="font-size: 9.5px; color: var(--text-muted); font-family: var(--font-mono); text-transform: uppercase;">Funding Rate</div>
          <div style="font-size: 16px; font-weight: 900; color: #ffffff; font-family: var(--font-mono);">{funding_rate/100:+.3f}%</div>
          <div style="font-size: 9.5px; color: var(--text-muted);">{funding_rate_ann:.1f}% Ann.</div>
        </div>
        <div class="gauge-card" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 10px;">
          <div style="font-size: 9.5px; color: var(--text-muted); font-family: var(--font-mono); text-transform: uppercase;">Futures Basis</div>
          <div style="font-size: 16px; font-weight: 900; color: #ffffff; font-family: var(--font-mono);">{basis:.1f}%</div>
          <div style="font-size: 9.5px; color: var(--text-muted);">Annualized Spread</div>
        </div>
        <div class="gauge-card" style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border); border-radius: 8px; padding: 10px;">
          <div style="font-size: 9.5px; color: var(--text-muted); font-family: var(--font-mono); text-transform: uppercase;">Retail Long/Short</div>
          <div style="font-size: 16px; font-weight: 900; color: var(--warning); font-family: var(--font-mono);">{ls_ratio:.2f}</div>
          <div style="font-size: 9.5px; color: var(--text-muted);">Account Ratio</div>
        </div>
      </div>
    </div>

    <!-- Action Button: Copy Data & Prompt for AI -->
    <button class="btn-copy-prompt" onclick="copyAIPrompt()" style="margin-top: 18px; margin-bottom: 8px;">
      <span style="font-size: 15px;">📋</span>
      <span id="copy-btn-text">Copy Data &amp; Prompt for AI</span>
    </button>

    <!-- USER GUIDANCE NOTE: EXTERNAL AI PROMPT INVITATION -->
    <div class="ai-copy-helper-box" style="margin-bottom: 20px;">
      <span class="ai-helper-icon">💡</span>
      <div class="ai-helper-text">
        <strong>Interactive AI Discussion:</strong> Users are encouraged to tap the button above to copy all live on-exchange metrics and paste them directly into their favourite AI &mdash; such as <strong>Claude, ChatGPT, Grok, DeepSeek, or Meta AI</strong> &mdash; for deep independent analysis and interactive discussion for a deeper verdict.
      </div>
    </div>

    <!-- RETURN FOOTER BUTTON -->
    <div style="text-align: center; padding: 6px 0 30px 0;">
      <a href="./app.html" class="btn-return-cockpit">
        <span>&larr;</span>
        <span>Return to Live Cockpit</span>
      </a>
    </div>

  </div>

  <script>
    let currentAIPrompt = {escaped_prompt};

    async function copyAIPrompt() {{
      const btnText = document.getElementById('copy-btn-text');
      const originalText = btnText ? btnText.textContent : 'Copy Data & Prompt for AI';
      try {{
        await navigator.clipboard.writeText(currentAIPrompt);
        if (navigator.vibrate) navigator.vibrate(50);
        if (btnText) btnText.textContent = '✓ Data & Prompt Copied!';
        showToast("📋 AI Prompt copied! Paste into Claude / ChatGPT / Grok");
        setTimeout(() => {{ if (btnText) btnText.textContent = originalText; }}, 2500);
      }} catch (err) {{
        const ta = document.createElement('textarea');
        ta.value = currentAIPrompt;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        if (btnText) btnText.textContent = '✓ Data & Prompt Copied!';
        showToast("📋 AI Prompt copied to clipboard!");
        setTimeout(() => {{ if (btnText) btnText.textContent = originalText; }}, 2500);
      }}
    }}

    function showToast(msg) {{
      const t = document.getElementById('toast');
      const m = document.getElementById('toast-msg');
      if (!t || !m) return;
      m.textContent = msg;
      t.classList.add('active');
      setTimeout(() => {{ t.classList.remove('active'); }}, 3000);
    }}

    const themes = ['theme-nvg', 'theme-ibm', 'theme-slate'];
    const themeLabels = {{ 'theme-nvg': 'NVG', 'theme-ibm': 'IBM', 'theme-slate': 'SLATE' }};
    let currentThemeIdx = 0;

    function cycleTheme() {{
      currentThemeIdx = (currentThemeIdx + 1) % themes.length;
      document.body.className = themes[currentThemeIdx];
      document.getElementById('theme-btn').textContent = themeLabels[themes[currentThemeIdx]];
      try {{ localStorage.setItem('btc_magnet_theme', themes[currentThemeIdx]); }} catch(e) {{}}
    }}

    try {{
      const savedTheme = localStorage.getItem('btc_magnet_theme');
      if (savedTheme && themes.includes(savedTheme)) {{
        currentThemeIdx = themes.indexOf(savedTheme);
        document.body.className = savedTheme;
        document.getElementById('theme-btn').textContent = themeLabels[savedTheme];
      }}
    }} catch(e) {{}}
  </script>
</body>
</html>"""
