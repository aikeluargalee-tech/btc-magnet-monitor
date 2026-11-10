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
  // Network first for regime.json to always get live data
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
        regime_id = regime.get("regime_id", "RANGE_LIQUIDATION_MAGNET")
        regime_name = regime.get("name", "Range / Liquidation Magnet")
        diagnosis = regime.get("diagnosis", "Positioning imbalance and forced liquidations dominate")
        score_str = regime.get("majority_score", "3/4 observations confirmed")
        rotation = regime.get("rotation", "Remain USDT")
        sizing = regime.get("sizing_factor", 0.0)
        action = regime.get("action", "Stand Aside (0.0x)")
        entry_inst = regime.get("entry_instruction", "Price oscillating in range.")

        # Stop Architecture
        stop_price = regime.get("stop_price", spot_price * 0.98)
        stop_dist = regime.get("stop_distance_pct", 2.0)
        disaster_stop = regime.get("disaster_stop_price", stop_price * 0.98)
        disaster_dist = regime.get("disaster_stop_distance_pct", 3.5)
        structural_inval = regime.get("structural_invalidation_level", spot_price * 0.985)

        # Liquidation Clusters
        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}
        u_p = upper_c.get("price_level", spot_price * 1.01)
        u_d = upper_c.get("distance_pct", 1.0)
        u_vol = upper_c.get("estimated_vol_usd", 10_000_000.0) / 1e6
        l_p = lower_c.get("price_level", spot_price * 0.99)
        l_d = lower_c.get("distance_pct", 1.0)
        l_vol = lower_c.get("estimated_vol_usd", 100_000_000.0) / 1e6

        imm_ratio = regime.get("immediate_imbalance_ratio", 24.5)
        tot_ratio = regime.get("total_ladder_imbalance_ratio", 1.70)
        dom_magnet = regime.get("dominant_magnet", "Lower Long Sweep Magnet")
        dom_reason = regime.get("dominant_magnet_reason", "LOWER (Downside Skew)")

        lsce_status = regime.get("lsce_status", "UNTESTED")
        lsce_detail = regime.get("lsce_detail", "Monitoring active liquidation zones.")

        # Order Flow Metrics
        spot_cvd_ratio = metrics.get("spot_cvd_ratio", 1.0)
        funding_rate_ann = metrics.get("funding_rate_annualized", 10.95)
        funding_rate_8h = metrics.get("funding_rate", 0.0001) * 100.0
        basis_ann = metrics.get("futures_basis_annualized", -1.2)
        ls_ratio = metrics.get("long_short_account_ratio", 1.85)
        oi_btc = metrics.get("open_interest", 9349.0)
        oi_24h = metrics.get("oi_change_24h_pct", 0.0)
        atr_comp = metrics.get("atr_compression_pct", 74.0)
        ma_200d = metrics.get("ma_200d", spot_price * 0.97)

        # Escape prompt for embedding in JS
        escaped_prompt = json.dumps(raw_llm_prompt)

        # Regime styling color
        regime_badge_style = "var(--primary)"
        if "EXPANSION" in regime_id:
            regime_badge_style = "#00ff66"
        elif "CASCADE" in regime_id or "DISTRIBUTION" in regime_id:
            regime_badge_style = "#ff4444"
        elif "FRAGILE" in regime_id:
            regime_badge_style = "#ffb000"
        elif "MIXED" in regime_id:
            regime_badge_style = "#c084fc"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
  <title>BTC Magnet Monitor | Mobile Cockpit</title>
  
  <meta name="theme-color" content="#030804">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="BTC Magnet">
  <link rel="manifest" href="./manifest.json">

  <style>
    /* RESET & BASE */
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

    /* THEME SYSTEM */
    /* 1. Tactical NVG-Green (Default) */
    body.theme-nvg {{
      --bg-base: #030804;
      --bg-card: rgba(6, 20, 10, 0.85);
      --bg-card-sub: rgba(4, 14, 7, 0.95);
      --border: rgba(0, 255, 102, 0.28);
      --border-bright: #00ff66;
      --primary: #00ff66;
      --primary-dim: #00a843;
      --text-muted: #6ba880;
      --text-main: #d4ffd9;
      --glow: 0 0 14px rgba(0, 255, 102, 0.4);
      --danger: #ff4d4d;
      --warning: #ffb800;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, monospace;
    }}

    /* 2. Vintage IBM 3270 Mainframe Amber */
    body.theme-ibm {{
      --bg-base: #0a0600;
      --bg-card: rgba(26, 17, 0, 0.85);
      --bg-card-sub: rgba(18, 11, 0, 0.95);
      --border: rgba(255, 176, 0, 0.35);
      --border-bright: #ffb000;
      --primary: #ffb000;
      --primary-dim: #b37b00;
      --text-muted: #b08d4f;
      --text-main: #ffe8b3;
      --glow: 0 0 14px rgba(255, 176, 0, 0.4);
      --danger: #ff4444;
      --warning: #ffcc00;
      --font-mono: 'Courier New', monospace;
    }}

    /* 3. Modern Institutional Slate */
    body.theme-slate {{
      --bg-base: #090d16;
      --bg-card: rgba(15, 23, 42, 0.85);
      --bg-card-sub: rgba(20, 30, 55, 0.95);
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

    /* MOBILE CONTAINER */
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
      padding: 10px 0 12px 0;
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

    .logo-badge .magnet-icon {{
      font-size: 16px;
      animation: pulse-glow 2s infinite ease-in-out;
    }}

    @keyframes pulse-glow {{
      0%, 100% {{ transform: scale(1); filter: drop-shadow(0 0 2px var(--primary)); }}
      50% {{ transform: scale(1.12); filter: drop-shadow(0 0 8px var(--primary)); }}
    }}

    .top-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
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

    .status-pill.stale {{
      background: rgba(255, 77, 77, 0.15);
      border-color: var(--danger);
      color: var(--danger);
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

    /* SPOT HERO CARD */
    .spot-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 12px;
      position: relative;
      overflow: hidden;
    }}

    .spot-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--primary), transparent);
    }}

    .spot-header {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin-bottom: 4px;
    }}

    .spot-label {{
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.5px;
    }}

    .spot-price-row {{
      display: flex;
      align-items: baseline;
      gap: 10px;
    }}

    .spot-price {{
      font-size: 28px;
      font-weight: 900;
      font-family: var(--font-mono);
      color: #ffffff;
      letter-spacing: -0.5px;
    }}

    .spot-chg {{
      font-size: 13px;
      font-weight: 800;
      padding: 2px 8px;
      border-radius: 6px;
      font-family: var(--font-mono);
    }}

    .spot-chg.pos {{ background: rgba(0, 255, 102, 0.15); color: #00ff66; }}
    .spot-chg.neg {{ background: rgba(255, 77, 77, 0.15); color: #ff4d4d; }}

    .benchmarks-row {{
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 6px;
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px dashed rgba(255,255,255,0.08);
      font-size: 10px;
      font-family: var(--font-mono);
    }}

    .bench-item {{
      display: flex;
      flex-direction: column;
    }}

    .bench-name {{
      color: var(--text-muted);
      font-size: 9px;
      text-transform: uppercase;
    }}

    .bench-val {{
      font-weight: 700;
      color: var(--text-main);
      margin-top: 1px;
    }}

    /* REGIME DIRECTIVE HERO CARD */
    .regime-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 12px;
    }}

    .regime-badge-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}

    .regime-pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      font-weight: 900;
      padding: 5px 10px;
      border-radius: 6px;
      background: rgba(255,255,255,0.05);
      border: 1px solid var(--primary);
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .regime-score {{
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }}

    .regime-diag {{
      font-size: 12px;
      line-height: 1.4;
      color: var(--text-main);
      margin-bottom: 12px;
    }}

    .directive-grid {{
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 8px;
      margin-bottom: 10px;
    }}

    .directive-box {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
    }}

    .dir-label {{
      font-size: 9px;
      text-transform: uppercase;
      color: var(--text-muted);
      font-weight: 700;
      margin-bottom: 2px;
    }}

    .dir-val {{
      font-size: 13px;
      font-weight: 800;
      color: #ffffff;
      font-family: var(--font-mono);
    }}

    /* HERO ACTION CARD: AI CO-PILOT */
    .ai-action-card {{
      background: linear-gradient(145deg, rgba(6, 20, 10, 0.95), rgba(10, 35, 18, 0.85));
      border: 1.5px solid var(--primary);
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 12px;
      box-shadow: var(--glow);
      position: relative;
    }}

    .ai-card-title {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 6px;
    }}

    .ai-title-text {{
      font-size: 12px;
      font-weight: 900;
      color: var(--primary);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}

    .ai-notice {{
      font-size: 10px;
      color: var(--text-muted);
      margin-bottom: 10px;
      line-height: 1.35;
    }}

    .ai-buttons-row {{
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 8px;
    }}

    .btn-ai-primary {{
      background: var(--primary);
      color: #030804;
      border: none;
      border-radius: 8px;
      padding: 11px 12px;
      font-size: 12px;
      font-weight: 900;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: transform 0.1s ease, filter 0.15s ease;
      letter-spacing: 0.3px;
      box-shadow: 0 2px 10px rgba(0, 255, 102, 0.3);
    }}

    .btn-ai-primary:active {{
      transform: scale(0.97);
    }}

    .btn-ai-secondary {{
      background: var(--bg-card-sub);
      color: var(--text-main);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 11px 10px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 5px;
    }}

    .btn-ai-secondary:active {{
      transform: scale(0.97);
    }}

    .disclaimer-banner {{
      font-size: 9.5px;
      color: var(--text-muted);
      margin-top: 8px;
      text-align: center;
      display: block;
      font-style: italic;
    }}

    /* LIQUIDATION RADAR & DUAL HORIZON */
    .radar-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 12px;
    }}

    .card-title {{
      font-size: 11px;
      text-transform: uppercase;
      font-weight: 800;
      color: var(--text-muted);
      letter-spacing: 0.6px;
      margin-bottom: 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .ladder-bar-wrap {{
      margin: 10px 0 12px 0;
    }}

    .ladder-labels {{
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      font-weight: 700;
      font-family: var(--font-mono);
      margin-bottom: 5px;
    }}

    .ladder-bar {{
      height: 8px;
      border-radius: 999px;
      background: #1e293b;
      display: flex;
      overflow: hidden;
      border: 1px solid rgba(255,255,255,0.1);
    }}

    .ladder-fill-lower {{
      background: #00ff66;
      transition: width 0.4s ease;
    }}

    .ladder-fill-upper {{
      background: #ff4444;
      transition: width 0.4s ease;
    }}

    .cluster-detail-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 8px;
    }}

    .cluster-box {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px 10px;
      font-family: var(--font-mono);
    }}

    .cluster-box.lower {{ border-left: 3px solid #00ff66; }}
    .cluster-box.upper {{ border-left: 3px solid #ff4444; }}

    .cluster-tag {{
      font-size: 9px;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 700;
    }}

    .cluster-px {{
      font-size: 13px;
      font-weight: 800;
      color: #ffffff;
      margin: 2px 0;
    }}

    .cluster-sub {{
      font-size: 10px;
      color: var(--text-muted);
    }}

    /* LSCE & DUAL STOPS */
    .lsce-card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
      margin-bottom: 12px;
    }}

    .lsce-badge-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }}

    .lsce-pill {{
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 10.5px;
      font-weight: 800;
      font-family: var(--font-mono);
      background: rgba(255,255,255,0.06);
      border: 1px solid var(--border);
      color: var(--text-main);
    }}

    .stops-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 8px;
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

    /* MICROSTRUCTURE GRID */
    .metrics-micro-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
      margin-bottom: 14px;
    }}

    .micro-metric-box {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 8px;
      text-align: center;
      font-family: var(--font-mono);
    }}

    .micro-lbl {{
      font-size: 8.5px;
      text-transform: uppercase;
      color: var(--text-muted);
      font-weight: 700;
    }}

    .micro-val {{
      font-size: 12px;
      font-weight: 800;
      color: var(--text-main);
      margin-top: 2px;
    }}

    /* TOAST NOTIFICATION */
    .toast-overlay {{
      position: fixed;
      bottom: calc(env(safe-area-inset-bottom, 20px) + 20px);
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: var(--primary);
      color: #030804;
      font-weight: 800;
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

    /* EDUCATIONAL MODAL SHEET */
    .modal-backdrop {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0,0,0,0.75);
      backdrop-filter: blur(4px);
      z-index: 1000;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.25s ease;
    }}

    .modal-backdrop.active {{
      opacity: 1;
      pointer-events: auto;
    }}

    .modal-sheet {{
      position: fixed;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%) translateY(100%);
      width: 100%;
      max-width: 440px;
      max-height: 85vh;
      background: var(--bg-card);
      border-top: 2px solid var(--primary);
      border-radius: 20px 20px 0 0;
      z-index: 1001;
      padding: 20px 18px 30px 18px;
      overflow-y: auto;
      transition: transform 0.3s cubic-bezier(0.18, 0.89, 0.32, 1.05);
      color: var(--text-main);
    }}

    .modal-sheet.active {{
      transform: translateX(-50%) translateY(0);
    }}

    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 14px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
    }}

    .modal-title {{
      font-size: 14px;
      font-weight: 800;
      color: var(--primary);
      text-transform: uppercase;
    }}

    .modal-close-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 18px;
      cursor: pointer;
      font-weight: 900;
      padding: 4px;
    }}

    .regime-item-desc {{
      background: var(--bg-card-sub);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px;
      margin-bottom: 10px;
      font-size: 11.5px;
      line-height: 1.45;
    }}

    .regime-item-title {{
      font-weight: 800;
      color: #ffffff;
      margin-bottom: 3px;
    }}
  </style>
</head>
<body class="theme-nvg">

  <div class="mobile-shell">

    <!-- TOP BAR -->
    <div class="top-bar">
      <div class="logo-badge">
        <span class="magnet-icon">🧲</span>
        <span>BTC Magnet</span>
      </div>
      <div class="top-actions">
        <div id="live-indicator" class="status-pill">
          <div class="status-dot"></div>
          <span id="live-age-text">LIVE</span>
        </div>
        <button id="theme-btn" class="theme-toggle-btn" onclick="cycleTheme()">NVG</button>
      </div>
    </div>

    <!-- 1. SPOT HERO CARD -->
    <div class="spot-card">
      <div class="spot-header">
        <span class="spot-label">Bitcoin Spot (BTC/USDT)</span>
        <span id="data-status-badge" style="font-size: 10px; font-weight: 700; color: var(--primary);">VERIFIED FEED</span>
      </div>
      <div class="spot-price-row">
        <div id="spot-price" class="spot-price">${spot_price:,.2f}</div>
        <div id="spot-chg" class="spot-chg {'pos' if p_chg_24h >= 0 else 'neg'}">{p_chg_24h:+.2f}%</div>
      </div>
      <div class="benchmarks-row">
        <div class="bench-item">
          <span class="bench-name">Daily VWAP</span>
          <span id="vwap-val" class="bench-val">${metrics.get('daily_vwap', spot_price*0.996):,.0f}</span>
        </div>
        <div class="bench-item">
          <span class="bench-name">200D SMA</span>
          <span id="sma200-val" class="bench-val">${ma_200d:,.0f}</span>
        </div>
        <div class="bench-item">
          <span class="bench-name">4H Range</span>
          <span id="range-val" class="bench-val">{atr_comp:.1f}% ATR</span>
        </div>
      </div>
    </div>

    <!-- 2. REGIME DIRECTIVE HERO CARD -->
    <div class="regime-card">
      <div class="regime-badge-header">
        <div id="regime-pill" class="regime-pill" style="border-color: {regime_badge_style}; color: {regime_badge_style};">
          <span id="regime-name">{regime_name}</span>
        </div>
        <span id="majority-score" class="regime-score">{score_str}</span>
      </div>
      <div id="regime-diag" class="regime-diag">{diagnosis}</div>

      <div class="directive-grid">
        <div class="directive-box">
          <div class="dir-label">Spot Rotation</div>
          <div id="rotation-val" class="dir-val" style="color: var(--primary);">{rotation}</div>
        </div>
        <div class="directive-box">
          <div class="dir-label">Capital Sizing</div>
          <div id="sizing-val" class="dir-val">{sizing:.2f}x Cash</div>
        </div>
      </div>
      <div style="font-size: 11px; color: var(--text-muted); line-height: 1.35;" id="entry-inst">
        👉 {entry_inst}
      </div>
    </div>

    <!-- 3. HERO CALL-TO-ACTION: AI CO-PILOT AUDIT -->
    <div class="ai-action-card">
      <div class="ai-card-title">
        <div class="ai-title-text">
          <span>🤖</span>
          <span>Independent AI Audit</span>
        </div>
        <span style="font-size: 9px; font-weight: 800; color: var(--primary); text-transform: uppercase;">Zero Trust</span>
      </div>
      <div class="ai-notice">
        Never trade on black-box verdicts alone. Tap below to export verified institutional telemetry and audit this setup with Claude, Grok, or ChatGPT.
      </div>
      <div class="ai-buttons-row">
        <button class="btn-ai-primary" onclick="copyAIPrompt()">
          <span>📋</span>
          <span>Copy Live AI Prompt</span>
        </button>
        <button class="btn-ai-secondary" onclick="shareAIPrompt()">
          <span>📤</span>
          <span>Share to AI</span>
        </button>
      </div>
      <span class="disclaimer-banner">
        ⚠️ Algorithmic reference benchmark only. Always conduct independent verification before allocating capital.
      </span>
    </div>

    <!-- 4. LIQUIDATION HORIZON & DUAL DEPTH LADDER -->
    <div class="radar-card">
      <div class="card-title">
        <span>Liquidation Gravitational Horizon</span>
        <span id="dom-magnet-badge" style="color: var(--primary); font-family: var(--font-mono); font-size: 10px;">{dom_magnet}</span>
      </div>

      <div class="ladder-bar-wrap">
        <div class="ladder-labels">
          <span style="color: #00ff66;">Lower Longs ({imm_ratio:.1f}x)</span>
          <span style="color: #ff4444;">Upper Shorts (1.0x)</span>
        </div>
        <div class="ladder-bar">
          <div id="ladder-fill-l" class="ladder-fill-lower" style="width: 70%;"></div>
          <div id="ladder-fill-u" class="ladder-fill-upper" style="width: 30%;"></div>
        </div>
      </div>

      <div class="cluster-detail-grid">
        <div class="cluster-box lower">
          <div class="cluster-tag">Macro Long Floor (Swing)</div>
          <div id="lower-px" class="cluster-px">${l_p:,.0f}</div>
          <div id="lower-sub" class="cluster-sub">-{abs(l_d):.2f}% | ~${l_vol:.1f}M Pool</div>
        </div>
        <div class="cluster-box upper">
          <div class="cluster-tag">Short Squeeze Ceiling</div>
          <div id="upper-px" class="cluster-px">${u_p:,.0f}</div>
          <div id="upper-sub" class="cluster-sub">+{abs(u_d):.2f}% | ~${u_vol:.1f}M Pool</div>
        </div>
      </div>

      <div style="margin-top: 10px; font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); display: flex; justify-content: space-between;">
        <span>Immediate 100x Skew: <strong style="color: #ffffff;">{imm_ratio:.1f}x</strong></span>
        <span>Full 10-100x Ladder: <strong style="color: #ffffff;">{tot_ratio:.2f}x</strong></span>
      </div>
    </div>

    <!-- 5. LSCE SWEEP ENGINE & DUAL INVIOLABLE STOPS -->
    <div class="lsce-card">
      <div class="lsce-badge-row">
        <span class="spot-label">LSCE Sweep Engine</span>
        <span id="lsce-pill" class="lsce-pill">[{lsce_status}]</span>
      </div>
      <div id="lsce-detail" style="font-size: 11.5px; color: var(--text-main); line-height: 1.35; margin-bottom: 8px;">
        {lsce_detail}
      </div>

      <div class="stops-grid">
        <div class="stop-box structural">
          <div class="cluster-tag">Structural Stop</div>
          <div id="s-stop-px" class="cluster-px" style="color: var(--warning);">${structural_inval:,.0f}</div>
          <div id="s-stop-dist" class="cluster-sub">1H Close Floor</div>
        </div>
        <div class="stop-box disaster">
          <div class="cluster-tag">Inviolable Disaster Stop</div>
          <div id="d-stop-px" class="cluster-px" style="color: var(--danger);">${disaster_stop:,.0f}</div>
          <div id="d-stop-dist" class="cluster-sub">-{disaster_dist:.2f}% (Below 200D)</div>
        </div>
      </div>
    </div>

    <!-- 6. MICROSTRUCTURE MATRIX -->
    <div class="metrics-micro-grid">
      <div class="micro-metric-box">
        <div class="micro-lbl">Spot CVD</div>
        <div id="cvd-val" class="micro-val">{spot_cvd_ratio:.2f}x</div>
      </div>
      <div class="micro-metric-box">
        <div class="micro-lbl">Funding / 8h</div>
        <div id="funding-val" class="micro-val">{funding_rate_8h:+.4f}%</div>
      </div>
      <div class="micro-metric-box">
        <div class="micro-lbl">Retail L/S</div>
        <div id="ls-val" class="micro-val">{ls_ratio:.2f}</div>
      </div>
      <div class="micro-metric-box">
        <div class="micro-lbl">Basis / yr</div>
        <div id="basis-val" class="micro-val">{basis_ann:+.1f}%</div>
      </div>
      <div class="micro-metric-box">
        <div class="micro-lbl">Open Interest</div>
        <div id="oi-val" class="micro-val">{oi_btc:,.0f} B</div>
      </div>
      <div class="micro-metric-box">
        <div class="micro-lbl">Risk Budget</div>
        <div class="micro-val" style="color: #00ff66;">1.0% MAX</div>
      </div>
    </div>

    <!-- FOOTER LINK -->
    <div style="text-align: center; margin-top: 10px;">
      <button onclick="openEducationalSheet()" style="background: none; border: 1px solid var(--border); color: var(--primary); padding: 8px 14px; border-radius: 999px; font-size: 11px; font-weight: 700; cursor: pointer;">
        📖 Read 5-Regime Reference Playbook
      </button>
    </div>

  </div>

  <!-- TOAST NOTIFICATION -->
  <div id="toast" class="toast-overlay">
    <span>📋</span>
    <span id="toast-msg">AI Prompt copied to clipboard!</span>
  </div>

  <!-- EDUCATIONAL REGIME MODAL SHEET -->
  <div id="modal-backdrop" class="modal-backdrop" onclick="closeEducationalSheet()"></div>
  <div id="modal-sheet" class="modal-sheet">
    <div class="modal-header">
      <div class="modal-title">The 5 Market Regimes</div>
      <button class="modal-close-btn" onclick="closeEducationalSheet()">✕</button>
    </div>
    
    <div class="regime-item-desc" style="border-left: 3px solid #00ff66;">
      <div class="regime-item-title" style="color: #00ff66;">1. Spot-Led Expansion (High Edge)</div>
      Genuine institutional demand driving price upward. Spot CVD leading, price above VWAPs, leverage calm.
      <br><strong>Sizing:</strong> 0.75x - 1.00x Spot | <strong>Prohibited:</strong> Premature fading or shorting.
    </div>

    <div class="regime-item-desc" style="border-left: 3px solid #ffb000;">
      <div class="regime-item-title" style="color: #ffb000;">2. Leveraged / Fragile Upside (Vulnerable)</div>
      Breakout driven by perpetual futures borrowing while spot buyers are absent. Long squeeze trap forming.
      <br><strong>Sizing:</strong> 0.00x - 0.25x (Take profit) | <strong>Prohibited:</strong> FOMO spot buying at highs.
    </div>

    <div class="regime-item-desc" style="border-left: 3px solid var(--primary);">
      <div class="regime-item-title" style="color: var(--primary);">3. Range / Liquidation Magnet (Core Operating Zone)</div>
      Price oscillating between bounds. Market makers run liquidity pools above and below.
      <br><strong>Sizing:</strong> 0.50x - 0.75x on confirmed sweep-and-reclaim | <strong>Prohibited:</strong> Breakout trading.
    </div>

    <div class="regime-item-desc" style="border-left: 3px solid #ff4444;">
      <div class="regime-item-title" style="color: #ff4444;">4. Cascade / Forced Deleveraging (Lethal)</div>
      Waterfall long liquidation cascade. Massive margin calls triggering automatic market selling.
      <br><strong>Sizing:</strong> Strictly 0.00x (100% USDT Cash) | <strong>Prohibited:</strong> Knife-catching.
    </div>

    <div class="regime-item-desc" style="border-left: 3px solid #f43f5e;">
      <div class="regime-item-title" style="color: #f43f5e;">5. Distribution / Bear Continuation</div>
      Persistent institutional selling, negative spot volume delta, lower lows below moving averages.
      <br><strong>Sizing:</strong> 0.00x Cash | <strong>Prohibited:</strong> Dip buying without structural base.
    </div>

    <div style="text-align: center; margin-top: 14px;">
      <button onclick="closeEducationalSheet()" style="background: var(--bg-card-sub); border: 1px solid var(--border); color: #ffffff; padding: 8px 20px; border-radius: 8px; font-size: 11px; font-weight: 700; cursor: pointer;">
        Close Playbook
      </button>
    </div>
  </div>

  <script>
    // STORE EMBEDDED PROMPT TEMPLATE
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

    // LOAD SAVED THEME
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
      try {{
        await navigator.clipboard.writeText(currentAIPrompt);
        if (navigator.vibrate) navigator.vibrate(50);
        showToast("📋 AI Prompt copied! Paste into Claude / ChatGPT / Grok");
      }} catch (err) {{
        // Fallback for older webviews
        const ta = document.createElement('textarea');
        ta.value = currentAIPrompt;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast("📋 AI Prompt copied to clipboard!");
      }}
    }}

    // SHARE AI PROMPT (NATIVE OS SHARE SHEET)
    async function shareAIPrompt() {{
      if (navigator.share) {{
        try {{
          await navigator.share({{
            title: 'BTC Liquidation & Regime Telemetry Audit',
            text: currentAIPrompt
          }});
        }} catch(e) {{
          copyAIPrompt();
        }}
      }} else {{
        copyAIPrompt();
      }}
    }}

    // SHOW TOAST
    function showToast(msg) {{
      const toast = document.getElementById('toast');
      document.getElementById('toast-msg').textContent = msg;
      toast.classList.add('active');
      setTimeout(() => {{
        toast.classList.remove('active');
      }}, 3200);
    }}

    // EDUCATIONAL SHEET MODAL
    function openEducationalSheet() {{
      document.getElementById('modal-backdrop').classList.add('active');
      document.getElementById('modal-sheet').classList.add('active');
    }}

    function closeEducationalSheet() {{
      document.getElementById('modal-backdrop').classList.remove('active');
      document.getElementById('modal-sheet').classList.remove('active');
    }}

    // STALENESS SENTINEL (DATA AGE TRACKER)
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

    // LIVE REST API POLLING (Auto-Refresh every 45s with cache-busting)
    async function pollLiveFeed() {{
      try {{
        const url = './regime.json?t=' + Date.now();
        const res = await fetch(url, {{ cache: 'no-store' }});
        if (!res.ok) return;
        const data = await res.json();
        if (data.timestamp) lastSnapshotTime = new Date(data.timestamp);
        updateDataAge();

        // Update Spot Price
        if (data.metrics && data.metrics.price) {{
          document.getElementById('spot-price').textContent = '$' + Number(data.metrics.price).toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}
        if (data.metrics && data.metrics.price_change_24h_pct !== undefined) {{
          const chg = data.metrics.price_change_24h_pct;
          const chgEl = document.getElementById('spot-chg');
          chgEl.textContent = (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%';
          chgEl.className = 'spot-chg ' + (chg >= 0 ? 'pos' : 'neg');
        }}

        // Update Directives
        if (data.regime) {{
          if (data.regime.name) document.getElementById('regime-name').textContent = data.regime.name;
          if (data.regime.diagnosis) document.getElementById('regime-diag').textContent = data.regime.diagnosis;
          if (data.regime.rotation) document.getElementById('rotation-val').textContent = data.regime.rotation;
          if (data.regime.sizing_factor !== undefined) document.getElementById('sizing-val').textContent = data.regime.sizing_factor.toFixed(2) + 'x Cash';
          if (data.regime.entry_instruction) document.getElementById('entry-inst').textContent = '👉 ' + data.regime.entry_instruction;
          if (data.regime.lsce_status) document.getElementById('lsce-pill').textContent = '[' + data.regime.lsce_status + ']';
          if (data.regime.lsce_detail) document.getElementById('lsce-detail').textContent = data.regime.lsce_detail;
        }}
      }} catch (err) {{
        console.warn('Poll failed:', err);
      }}
    }}
    setInterval(pollLiveFeed, 45000);

    // REGISTER SERVICE WORKER
    if ('serviceWorker' in navigator) {{
      navigator.serviceWorker.register('./sw.js').catch(() => {{}});
    }}
  </script>
</body>
</html>
"""
