"""Mobile Web Generator & PWA Engine for BTC Magnet Monitor.

Generates the dedicated, responsive mobile cockpit (app.html), PWA manifest,
and service worker for zero-friction mobile deployment.
"""

from __future__ import annotations

import json
import datetime
from typing import Any, Dict


class MobileWebGenerator:
    """Renders the standalone Institutional Mobile Cockpit PWA."""

    @staticmethod
    def render_manifest() -> str:
        """Generates PWA web manifest."""
        manifest = {
            "name": "BTC Magnet Monitor",
            "short_name": "BTC Magnet",
            "description": "Institutional 5-Regime Radar & Liquidation Gravity Mobile Cockpit",
            "start_url": "./app.html",
            "display": "standalone",
            "background_color": "#030804",
            "theme_color": "#030804",
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Crect width='100' height='100' rx='20' fill='%23030804'/%3E%3Cpath d='M30 25 C30 15, 70 15, 70 25 L70 50 C70 65, 30 65, 30 50 Z' fill='none' stroke='%2300ff66' stroke-width='10'/%3E%3Crect x='25' y='20' width='10' height='15' fill='%23ff4444'/%3E%3Crect x='65' y='20' width='10' height='15' fill='%2338bdf8'/%3E%3C/svg%3E",
                    "sizes": "192x192 512x512",
                    "type": "image/svg+xml",
                    "purpose": "any maskable"
                }
            ]
        }
        return json.dumps(manifest, indent=2)

    @staticmethod
    def render_service_worker() -> str:
        """Generates service worker for caching and offline operation."""
        return """// BTC Magnet Service Worker
const CACHE_NAME = 'btc-magnet-v1';
const ASSETS = [
  './app.html',
  './manifest.json',
  './regimes.html'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
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
    return;
  }
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});
"""

    def render_mobile_app(self, data: Dict[str, Any], raw_llm_prompt: str = "") -> str:
        """Renders the complete self-contained app.html file."""
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})
        ts_iso = data.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())

        spot_price = metrics.get("price", 74800.0)
        p_chg_24h = metrics.get("price_change_24h_pct", 0.0)
        daily_vwap = metrics.get("daily_vwap", spot_price * 0.998)
        weekly_vwap = metrics.get("weekly_vwap", spot_price * 0.995)
        ema_20d = metrics.get("ema_20d", spot_price * 1.025)
        ema_50d = metrics.get("ema_50d", spot_price * 1.042)
        ma_200d = metrics.get("ma_200d", spot_price * 0.978)
        swing_high = metrics.get("swing_high_4h", spot_price * 1.015)
        swing_low = metrics.get("swing_low_4h", spot_price * 0.985)
        base_floor = metrics.get("base_floor", spot_price * 0.98)

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
        basis = metrics.get("futures_basis_annualized", -1.22)
        ls_ratio = metrics.get("long_short_account_ratio", 1.85)

        atr = metrics.get("atr", 472.49)
        atr_comp = metrics.get("atr_compression_pct", 74.0)
        range_width = ((swing_high - swing_low) / max(spot_price, 1.0)) * 100

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_p = upper_c.get("price_level", 74880.0)
        u_d = upper_c.get("distance_pct", 0.07)
        u_vol = upper_c.get("estimated_vol_usd", 4_200_000.0) / 1e6
        l_p = lower_c.get("price_level", 74760.0)
        l_d = lower_c.get("distance_pct", 0.09)
        l_vol = lower_c.get("estimated_vol_usd", 102_800_000.0) / 1e6

        regime_id = regime.get("regime_id", "RANGE_LIQUIDATION_MAGNET")
        regime_name = regime.get("name", "Range / Liquidation Magnet")
        diagnosis = regime.get("diagnosis", "Positioning imbalance and forced liquidations dominate")
        score_str = regime.get("majority_score", "3/4 observations confirmed")
        rotation = regime.get("rotation", "Remain USDT")
        sizing = regime.get("sizing_factor", 0.0)
        action = regime.get("action", "Stand Aside (0.0x)")

        stop_price = regime.get("stop_price", spot_price * 0.98)
        stop_dist = regime.get("stop_distance_pct", 2.0)
        disaster_stop = regime.get("disaster_stop_price", stop_price * 0.98)
        disaster_dist = regime.get("disaster_stop_distance_pct", 3.5)
        structural_inval = regime.get("structural_invalidation_level", swing_low)

        imm_ratio = regime.get("immediate_imbalance_ratio", 24.5)
        tot_ratio = regime.get("total_ladder_imbalance_ratio", 1.70)
        dom_magnet = regime.get("dominant_magnet", "Lower Long Sweep Magnet")
        lsce_status = regime.get("lsce_status", "UNTESTED")
        lsce_detail = regime.get("lsce_detail", "Monitoring active liquidation zones.")

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
      user-select: none;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      background-color: #020402;
      color: #e2e8f0;
      overflow-x: hidden;
      transition: background-color 0.25s ease, color 0.25s ease;
    }}

    /* THEMES */
    body.theme-nvg {{
      --bg-base: #030804;
      --bg-card: rgba(6, 20, 10, 0.92);
      --bg-card-sub: rgba(4, 14, 7, 0.96);
      --border: rgba(0, 255, 102, 0.28);
      --border-bright: #00ff66;
      --primary: #00ff66;
      --primary-dim: #00a843;
      --text-muted: #6ba880;
      --text-main: #d4ffd9;
      --glow: 0 0 14px rgba(0, 255, 102, 0.35);
      --danger: #ff4d4d;
      --warning: #ffb800;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}

    body.theme-ibm {{
      --bg-base: #0a0600;
      --bg-card: rgba(26, 17, 0, 0.92);
      --bg-card-sub: rgba(18, 11, 0, 0.96);
      --border: rgba(255, 176, 0, 0.35);
      --border-bright: #ffb000;
      --primary: #ffb000;
      --primary-dim: #b37b00;
      --text-muted: #b08d4f;
      --text-main: #ffe8b3;
      --glow: 0 0 14px rgba(255, 176, 0, 0.35);
      --danger: #ff4444;
      --warning: #ffcc00;
      --font-mono: 'Courier New', monospace;
    }}

    body.theme-slate {{
      --bg-base: #090d16;
      --bg-card: rgba(15, 23, 42, 0.92);
      --bg-card-sub: rgba(20, 30, 55, 0.96);
      --border: rgba(56, 189, 248, 0.28);
      --border-bright: #38bdf8;
      --primary: #38bdf8;
      --primary-dim: #0284c7;
      --text-muted: #7c93b3;
      --text-main: #f1f5f9;
      --glow: 0 0 14px rgba(56, 189, 248, 0.35);
      --danger: #f87171;
      --warning: #fbbf24;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}

    .mobile-shell {{
      width: 100%;
      max-width: 440px;
      min-height: 100vh;
      background: var(--bg-base);
      display: flex;
      flex-direction: column;
      position: relative;
      padding: env(safe-area-inset-top, 10px) 14px calc(env(safe-area-inset-bottom, 12px) + 24px) 14px;
      border-left: 1px solid var(--border);
      border-right: 1px solid var(--border);
      box-shadow: 0 0 40px rgba(0,0,0,0.8);
    }}

    /* TOP BAR */
    .top-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0 12px 0;
      border-bottom: 1px solid var(--border);
      margin-bottom: 12px;
    }}

    .logo-badge {{
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 800;
      letter-spacing: 0.8px;
      color: var(--primary);
      text-transform: uppercase;
    }}

    .status-pill {{
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 999px;
      background: rgba(0, 255, 102, 0.12);
      border: 1px solid var(--primary);
      color: var(--primary);
      font-family: var(--font-mono);
    }}

    .status-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: currentColor;
      box-shadow: 0 0 6px currentColor;
    }}

    .theme-toggle-btn {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 5px 8px;
      border-radius: 6px;
      font-size: 11px;
      cursor: pointer;
      font-weight: 700;
    }}

    /* ======================================================== */
    /* PART 1: TOP HERO — LIVE TELEMETRY DATA DICTIONARY CARD   */
    /* ======================================================== */
    .top-hero-dictionary {{
      background: var(--bg-card);
      border: 1.5px solid var(--primary);
      border-radius: 14px;
      padding: 16px 14px;
      margin-bottom: 14px;
      box-shadow: var(--glow);
      position: relative;
      overflow: hidden;
    }}

    .dict-badge {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 10.5px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--primary);
      margin-bottom: 2px;
    }}

    .dict-sub-feed {{
      font-size: 10px;
      color: var(--text-muted);
      font-family: var(--font-mono);
      margin-bottom: 8px;
    }}

    .dict-headline {{
      font-size: 17px;
      font-weight: 900;
      color: #ffffff;
      line-height: 1.25;
      margin-bottom: 6px;
      letter-spacing: -0.2px;
    }}

    .dict-lead-text {{
      font-size: 11.5px;
      color: var(--text-main);
      line-height: 1.45;
      margin-bottom: 12px;
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
      font-size: 11px;
      font-weight: 900;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      padding-bottom: 6px;
      margin-bottom: 6px;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .cat-title-1 {{ color: #38bdf8; }}
    .cat-title-2 {{ color: #00ff66; }}
    .cat-title-3 {{ color: #ffb000; }}
    .cat-title-4 {{ color: #ff4d4d; }}

    .dict-rows {{
      display: flex;
      flex-direction: column;
      gap: 5px;
      font-family: var(--font-mono);
      font-size: 11px;
    }}

    .dict-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      line-height: 1.25;
    }}

    .dict-lbl {{
      color: var(--text-muted);
    }}

    .dict-val {{
      font-weight: 700;
      color: #ffffff;
    }}

    .dict-val.accent {{ color: var(--primary); }}
    .dict-val.warn {{ color: var(--warning); }}
    .dict-val.danger {{ color: var(--danger); }}

    /* SECTION DIVIDER */
    .section-separator {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 12px 0 10px 0;
      font-size: 10px;
      font-weight: 800;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 1.0px;
    }}

    .section-separator::before, .section-separator::after {{
      content: '';
      flex: 1;
      height: 1px;
      background: var(--border);
    }}

    /* REGIME REFERENCE CARD (BELOW TOP HERO) */
    .regime-summary-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      margin-bottom: 12px;
    }}

    .regime-pill-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;
    }}

    .regime-pill {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 11px;
      font-weight: 900;
      padding: 4px 8px;
      border-radius: 6px;
      border: 1px solid var(--primary);
      color: var(--primary);
      text-transform: uppercase;
    }}

    /* DUAL STOPS & LSCE CARD */
    .dual-stops-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 14px;
      margin-bottom: 12px;
    }}

    .stops-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 6px;
    }}

    .stop-box {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      font-family: var(--font-mono);
    }}

    .stop-box.structural {{ border-top: 2px solid var(--warning); }}
    .stop-box.disaster {{ border-top: 2px solid var(--danger); }}

    /* TOAST */
    .toast-overlay {{
      position: fixed;
      bottom: calc(env(safe-area-inset-bottom, 20px) + 20px);
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: var(--primary);
      color: #030804;
      font-weight: 900;
      font-size: 12px;
      padding: 10px 18px;
      border-radius: 999px;
      box-shadow: 0 4px 20px rgba(0, 255, 102, 0.6);
      transition: transform 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.28);
      z-index: 9999;
      pointer-events: none;
      display: flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }}

    .toast-overlay.active {{
      transform: translateX(-50%) translateY(0);
    }}
  </style>
</head>
<body class="theme-nvg">

  <div class="mobile-shell">

    <!-- TOP HEADER -->
    <div class="top-bar">
      <div class="logo-badge">
        <span style="font-size: 16px;">🧲</span>
        <span>BTC Magnet</span>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <div id="live-indicator" class="status-pill">
          <div class="status-dot"></div>
          <span id="live-age-text">LIVE</span>
        </div>
        <button id="theme-btn" class="theme-toggle-btn" onclick="cycleTheme()">NVG</button>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- PART 1: TOP HERO — REQUESTED DATA DICTIONARY & AI PROMPT -->
    <!-- ======================================================== -->
    <div class="top-hero-dictionary">
      <div class="dict-badge">
        <span>📊</span>
        <span>LIVE TELEMETRY DATA DICTIONARY • AI PROMPT ENGINE</span>
      </div>
      <div class="dict-sub-feed">(Real-Time On-Exchange Feeds)</div>

      <h1 class="dict-headline">Analyze Market Data with Your Own AI</h1>
      <p class="dict-lead-text">
        Don't rely blindly on our verdict. Review the live metrics below and click the button to copy verified data directly into <strong>ChatGPT, Claude, Grok, or Gemini</strong> for an instant second opinion.
      </p>

      <!-- 4 Organized Categories -->
      <div class="dict-categories-stack">

        <!-- 1. Price & Structure -->
        <div class="dict-cat-card">
          <div class="dict-cat-header cat-title-1">
            <span>1. Price & Structure</span>
            <span style="font-size: 9px; color: var(--text-muted);">MACRO HORIZON</span>
          </div>
          <div class="dict-rows">
            <div class="dict-row"><span class="dict-lbl">Spot Price:</span><span id="d-spot-px" class="dict-val" style="color: #ffffff; font-weight: 900;">${spot_price:,.2f}</span></div>
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

      <!-- Button at bottom of 4. Volatility & Magnets -->
      <button class="btn-copy-prompt" onclick="copyAIPrompt()">
        <span style="font-size: 15px;">📋</span>
        <span id="copy-btn-text">Copy Data & Prompt for AI</span>
      </button>
    </div>

    <!-- SEPARATOR: ALGORITHMIC REFERENCE BENCHMARK -->
    <div class="section-separator">
      <span>Algorithmic Reference Benchmark</span>
    </div>

    <!-- REGIME DIAGNOSIS SUMMARY -->
    <div class="regime-summary-card">
      <div class="regime-pill-header">
        <div class="regime-pill">
          <span id="regime-name">{regime_name}</span>
        </div>
        <span id="majority-score" style="font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);">{score_str}</span>
      </div>
      <div id="regime-diag" style="font-size: 12px; color: var(--text-main); line-height: 1.4; margin-bottom: 8px;">
        {diagnosis}
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-family: var(--font-mono); font-size: 11px;">
        <div style="background: var(--bg-card-sub); padding: 6px 8px; border-radius: 6px; border: 1px solid var(--border);">
          <div style="font-size: 9px; color: var(--text-muted);">Rotation</div>
          <div id="rotation-val" style="font-weight: 800; color: var(--primary);">{rotation}</div>
        </div>
        <div style="background: var(--bg-card-sub); padding: 6px 8px; border-radius: 6px; border: 1px solid var(--border);">
          <div style="font-size: 9px; color: var(--text-muted);">Sizing</div>
          <div id="sizing-val" style="font-weight: 800; color: #ffffff;">{sizing:.2f}x Cash</div>
        </div>
      </div>
    </div>

    <!-- DUAL INVIOLABLE STOPS -->
    <div class="dual-stops-card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span style="font-size: 10px; font-weight: 800; color: var(--text-muted); text-transform: uppercase;">Inviolable Dual Stops</span>
        <span id="lsce-pill" style="font-size: 10px; font-family: var(--font-mono); color: var(--text-main);">[{lsce_status}]</span>
      </div>
      <div class="stops-grid">
        <div class="stop-box structural">
          <div style="font-size: 8.5px; color: var(--text-muted); text-transform: uppercase;">Structural Stop</div>
          <div id="s-stop-px" style="font-size: 13px; font-weight: 800; color: var(--warning);">${structural_inval:,.0f}</div>
          <div style="font-size: 9.5px; color: var(--text-muted);">1H Close Floor</div>
        </div>
        <div class="stop-box disaster">
          <div style="font-size: 8.5px; color: var(--text-muted); text-transform: uppercase;">Disaster Hard Stop</div>
          <div id="d-stop-px" style="font-size: 13px; font-weight: 800; color: var(--danger);">${disaster_stop:,.0f}</div>
          <div id="d-stop-dist" style="font-size: 9.5px; color: var(--text-muted);">-{disaster_dist:.2f}% (Below 200D)</div>
        </div>
      </div>
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
      const toast = document.getElementById('toast');
      document.getElementById('toast-msg').textContent = msg;
      toast.classList.add('active');
      setTimeout(() => {{
        toast.classList.remove('active');
      }}, 3200);
    }}

    // STALENESS SENTINEL
    function updateDataAge() {{
      const now = new Date();
      const diffMs = now - lastSnapshotTime;
      const diffMin = Math.floor(diffMs / 60000);
      const indicator = document.getElementById('live-indicator');
      const ageText = document.getElementById('live-age-text');

      if (diffMin <= 15) {{
        indicator.className = 'status-pill';
        ageText.textContent = diffMin <= 1 ? 'LIVE' : diffMin + 'm ago';
      }} else if (diffMin <= 45) {{
        indicator.className = 'status-pill';
        ageText.textContent = diffMin + 'm delayed';
      }} else {{
        indicator.className = 'status-pill stale';
        ageText.textContent = diffMin + 'm STALE';
      }}
    }}
    setInterval(updateDataAge, 10000);
    updateDataAge();

    // LIVE POLLING (every 45s)
    async function pollLiveFeed() {{
      try {{
        const url = './regime.json?t=' + Date.now();
        const res = await fetch(url, {{ cache: 'no-store' }});
        if (!res.ok) return;
        const data = await res.json();
        if (data.timestamp) lastSnapshotTime = new Date(data.timestamp);
        updateDataAge();

        const m = data.metrics || {{}};
        const r = data.regime || {{}};

        if (m.price) document.getElementById('d-spot-px').textContent = '$' + Number(m.price).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.daily_vwap) document.getElementById('d-vwap').textContent = '$' + Number(m.daily_vwap).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.weekly_vwap) document.getElementById('d-w-vwap').textContent = '$' + Number(m.weekly_vwap).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.ema_20d) document.getElementById('d-ema20').textContent = '$' + Number(m.ema_20d).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.ema_50d) document.getElementById('d-ema50').textContent = '$' + Number(m.ema_50d).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        if (m.ma_200d) document.getElementById('d-sma200').textContent = '$' + Number(m.ma_200d).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        
        if (m.spot_cvd_ratio !== undefined) document.getElementById('d-cvd-ratio').textContent = Number(m.spot_cvd_ratio).toFixed(2);
        if (m.funding_rate !== undefined) document.getElementById('d-funding').textContent = (m.funding_rate * 100 >= 0 ? '+' : '') + (m.funding_rate * 100).toFixed(4) + '%';
        if (m.open_interest !== undefined) document.getElementById('d-oi').textContent = Number(m.open_interest).toLocaleString('en-US', {{maximumFractionDigits: 0}}) + ' BTC';
        
        if (r.name) document.getElementById('regime-name').textContent = r.name;
        if (r.diagnosis) document.getElementById('regime-diag').textContent = r.diagnosis;
        if (r.rotation) document.getElementById('rotation-val').textContent = r.rotation;
        if (r.sizing_factor !== undefined) document.getElementById('sizing-val').textContent = r.sizing_factor.toFixed(2) + 'x Cash';
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
</html>
"""
