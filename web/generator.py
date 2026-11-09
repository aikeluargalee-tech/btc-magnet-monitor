import json
import os
import datetime
from typing import Dict, Any, Tuple

class WebGenerator:
    """Generates the static JSON API feed and the mobile-responsive HTML dashboard for GitHub Pages."""

    def __init__(self, output_dir: str = "dist"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        # 1. Write raw JSON feed for the mobile app
        json_path = os.path.join(self.output_dir, "regime.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # 2. Render modern mobile-responsive HUD HTML
        html_content = self._render_html(payload)
        html_path = os.path.join(self.output_dir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return json_path, html_path

    def _render_html(self, data: Dict[str, Any]) -> str:
        regime = data.get("regime", {})
        metrics = data.get("metrics", {})
        risk = data.get("risk", {})

        cfg = regime.get("config", "Config A")
        name = regime.get("name", "Unknown")
        diagnosis = regime.get("diagnosis", "")
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

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}

        # 6-Factor Multi-Factor Magnet Preference Details
        magnet_factors = regime.get("magnet_factors", {})
        f1 = magnet_factors.get("factor_1_size", "Evaluating cluster size disparity...")
        f2 = magnet_factors.get("factor_2_spot_leadership", "Evaluating spot vs derivatives CVD...")
        f3 = magnet_factors.get("factor_3_crowding_fuel", "Evaluating funding and positioning crowding...")
        f4 = magnet_factors.get("factor_4_regime_structure", "Evaluating regime structure...")
        f5 = magnet_factors.get("factor_5_asymmetry", "Evaluating cluster distance asymmetry...")
        f6 = magnet_factors.get("factor_6_atr_volatility", "Evaluating ATR compression...")

        # IBM Retro Phosphor Palette
        # Classic IBM 3270: Green Phosphor (#00ff66) / Amber Phosphor (#ffb000) / Red Alert (#ff3b30)
        if "USDT -> BTC" in rotation:
            theme_color = "#00ff66"  # IBM Green Phosphor
            theme_glow = "rgba(0, 255, 102, 0.4)"
            status_tag = "[BUY / ACCUMULATE]"
            box_style = "border-[#00ff66] shadow-[0_0_20px_rgba(0,255,102,0.25)] text-[#00ff66]"
        elif "BTC -> USDT" in rotation:
            theme_color = "#ff3333"  # IBM Alert Red
            theme_glow = "rgba(255, 51, 51, 0.4)"
            status_tag = "[SELL / DEFENSIVE]"
            box_style = "border-[#ff3333] shadow-[0_0_20px_rgba(255,51,51,0.25)] text-[#ff3333]"
        else:
            theme_color = "#ffb000"  # IBM Amber Phosphor
            theme_glow = "rgba(255, 176, 0, 0.4)"
            status_tag = "[HOLD / 100% CASH]"
            box_style = "border-[#ffb000] shadow-[0_0_20px_rgba(255,176,0,0.25)] text-[#ffb000]"

        matched_html = "".join([f"<div class='leading-relaxed'>&gt; [OK] {item}</div>" for item in regime.get("matched_criteria", [])])

        price = metrics.get("price", 0.0)
        funding_rate = metrics.get("funding_rate", 0.0) * 100
        spot_cvd_ratio = metrics.get("spot_cvd_ratio", 1.0)
        oi_change_24h = metrics.get("oi_change_24h_pct", 0.0)
        basis = metrics.get("futures_basis_annualized", 0.0)
        atr = metrics.get("atr", 0.0)
        ls_ratio = metrics.get("long_short_account_ratio", 1.0)
        current_oi = metrics.get("open_interest", 0.0)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>IBM 3270 // BTC MAGNET MONITOR</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,400;0,600;0,700;1,400&family=Share+Tech+Mono&display=swap" rel="stylesheet">
  <style>
    :root {{
      --phosphor-green: #00ff66;
      --phosphor-amber: #ffb000;
      --phosphor-cyan: #00e5ff;
      --ibm-blue: #0f62fe;
      --crt-bg: #030708;
    }}
    body {{
      font-family: 'IBM Plex Mono', 'Share Tech Mono', monospace;
      background-color: var(--crt-bg);
      color: #00ff66;
      text-shadow: 0 0 4px rgba(0, 255, 102, 0.45);
    }}
    /* CRT Scanlines Overlay */
    body::before {{
      content: " ";
      display: block;
      position: fixed;
      top: 0; left: 0; bottom: 0; right: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.35) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
      z-index: 999;
      background-size: 100% 3px, 6px 100%;
      pointer-events: none;
      opacity: 0.85;
    }}
    /* Subtle CRT Flicker & Glow */
    .crt-glow {{
      text-shadow: 0 0 6px {theme_glow};
    }}
    .ibm-border {{
      border: 1px solid #1a3a2a;
      background-color: rgba(3, 15, 10, 0.85);
    }}
    .ibm-header-bar {{
      background: linear-gradient(90deg, #003318 0%, #001f0f 100%);
      border-bottom: 1px solid #00ff66;
    }}
    @keyframes blink {{
      0%, 49% {{ opacity: 1; }}
      50%, 100% {{ opacity: 0; }}
    }}
    .cursor-blink {{
      animation: blink 1s infinite;
    }}
    /* Scrollbar */
    ::-webkit-scrollbar {{
      width: 6px;
      height: 6px;
    }}
    ::-webkit-scrollbar-track {{
      background: #020504;
    }}
    ::-webkit-scrollbar-thumb {{
      background: #00ff66;
    }}
  </style>
</head>
<body class="min-h-screen pb-12 antialiased selection:bg-[#00ff66] selection:text-black">

  <!-- IBM 3270 Mainframe Header -->
  <header class="border-b border-[#00ff66]/40 bg-[#020b06] px-4 py-2 sticky top-0 z-50">
    <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between text-xs gap-2">
      <div class="flex items-center gap-3">
        <span class="bg-[#00ff66] text-black font-bold px-2 py-0.5 tracking-wider">IBM-3270</span>
        <span class="text-[#00ff66] font-bold tracking-widest text-sm">BTC MAGNET MONITOR // SYSTEM/370</span>
        <span class="hidden sm:inline text-slate-500">|</span>
        <span class="hidden sm:inline text-[#00e5ff] text-[11px]">DISP: 80x25 HIGH-RES</span>
      </div>
      <div class="flex items-center gap-4 text-xs">
        <span class="text-[#00ff66] hidden sm:inline">SPOT: <strong class="text-white text-sm">${price:,.2f}</strong></span>
        <span class="border border-[#00ff66]/60 px-2 py-0.5 text-[#00ff66] bg-[#002211] flex items-center gap-1.5">
          <span class="w-2 h-2 bg-[#00ff66] rounded-full inline-block cursor-blink"></span> ONLINE
        </span>
      </div>
    </div>
  </header>

  <!-- Sub-Header Status Line -->
  <div class="bg-[#010804] border-b border-[#1a3a2a] px-4 py-1.5 text-[11px] text-[#00ff66]/70">
    <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
      <div>TERMINAL ADDR: 0xBTC_MAG // CHANNEL: BINANCE+DERIBIT_FEED // AUTOSCAN: 30M</div>
      <div>UTC: {data.get("timestamp", "")[:19]}Z</div>
    </div>
  </div>

  <main class="max-w-6xl mx-auto px-4 pt-6 space-y-6">

    <!-- Top ASCII Banner -->
    <pre class="text-[9px] sm:text-[11px] leading-[11px] sm:leading-[13px] text-[#00ff66] overflow-x-auto whitespace-pre font-bold border border-[#1a3a2a] p-3 bg-[#010a05]">
 ██████╗ ████████╗ ██████╗    ███╗   ███╗ █████╗  ██████╗ ███╗   ██╗███████╗████████╗
 ██╔══██╗╚══██╔══╝██╔════╝    ████╗ ████║██╔══██╗██╔════╝ ████╗  ██║██╔════╝╚══██╔══╝
 ██████╔╝   ██║   ██║         ██╔████╔██║███████║██║  ███╗██╔██╗ ██║█████╗     ██║   
 ██╔══██╗   ██║   ██║         ██║╚██╔╝██║██╔══██║██║   ██║██║╚██╗██║██╔══╝     ██║   
 ██████╔╝   ██║   ╚██████╗    ██║ └───██║██║  ██║╚██████╔╝██║ ╚████║███████╗   ██║   
 ╚═════╝    ╚═╝    ╚═════╝    ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝   ╚═╝   
 [QUANTITATIVE MICROSTRUCTURE REGIME DIAGNOSTIC & OBSERVABLE POSITIONING SYSTEM]
    </pre>

    <!-- Main Diagnostic Frame -->
    <div class="border-2 {box_style} p-5 bg-[#020d07] crt-glow">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-current pb-4">
        <div>
          <div class="text-xs tracking-widest uppercase opacity-80 mb-1">
            &gt;&gt;&gt; ACTIVE REGIME CLASSIFICATION // FACT MATRIX &lt;&lt;&lt;
          </div>
          <h2 class="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <span class="bg-current text-black px-2 py-0.5 font-black text-xl sm:text-2xl">{cfg}</span>
            <span>{name}</span>
          </h2>
          <div class="text-sm mt-1 text-slate-300">
            DIAGNOSIS: <span class="font-bold underline text-white">{diagnosis}</span> | TIER: <span class="text-[#00e5ff]">{regime.get("suitability", "Active")}</span>
          </div>
        </div>

        <!-- Big Retro Rotation Directive Box -->
        <div class="border-2 border-current p-4 bg-black/60 flex flex-col items-center justify-center min-w-[280px]">
          <div class="text-[11px] tracking-widest uppercase font-bold text-slate-300 mb-1">
            SPOT ROTATION DIRECTIVE
          </div>
          <div class="text-2xl font-black tracking-wider text-white">
            &gt; {rotation} &lt;
          </div>
          <div class="text-xs font-bold mt-1 text-slate-200">
            SIZING FACTOR: <span class="bg-current text-black px-1.5 py-0.5">{sizing}x</span> {status_tag}
          </div>
        </div>
      </div>

      <!-- Action Protocol & Stop Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-5">
        <div class="border border-[#1a3a2a] p-3 bg-black/50">
          <div class="text-xs text-[#00e5ff] font-bold uppercase mb-1">&gt; 01. ACTION PROTOCOL</div>
          <div class="text-sm font-bold text-white mb-1.5">{action}</div>
          <div class="text-xs text-slate-300 leading-relaxed">{entry_inst}</div>
        </div>

        <div class="border border-[#1a3a2a] p-3 bg-black/50">
          <div class="text-xs text-[#ff3333] font-bold uppercase mb-1">&gt; 02. INVIOLABLE STOP-LOSS</div>
          <div class="text-sm font-bold text-[#ff3333] mb-1.5">${stop_price:,.2f} ({stop_dist:.2f}% DIST)</div>
          <div class="text-xs text-slate-300 leading-relaxed">{stop_rule}</div>
        </div>

        <div class="border border-[#1a3a2a] p-3 bg-black/50">
          <div class="text-xs text-[#ffb000] font-bold uppercase mb-1">&gt; 03. RISK BUDGET VALIDATION</div>
          <div class="text-sm font-bold mb-1.5 {'text-[#00ff66]' if risk.get('risk_budget_ok') else 'text-[#ff3333]'}">
            {"[STATUS: PASSED / RISK OK]" if risk.get("risk_budget_ok") else "[STATUS: REJECTED / OVERBUDGET]"}
          </div>
          <div class="text-xs text-slate-300 leading-relaxed">{risk.get("actionable_trade_instruction", "")}</div>
        </div>
      </div>
    </div>

    <!-- Liquidation Magnet Module (ASCII Style + 6-Factor Logic Sub-Panel) -->
    <div class="border border-[#00ff66]/40 p-5 bg-[#020b06]">
      <div class="flex flex-wrap items-center justify-between border-b border-[#1a3a2a] pb-3 mb-4 gap-2">
        <div class="font-bold text-sm tracking-wider flex items-center gap-2">
          <span>[+] LIQUIDATION MAGNET PROXIMITY &amp; GRAVITATIONAL OVERRIDE</span>
          <span class="text-xs text-[#00e5ff] font-normal">// 6-FACTOR CHECKLIST</span>
        </div>
        <div class="text-xs border border-[#ffb000] px-2.5 py-1 text-[#ffb000] bg-[#1a1200] max-w-full">
          DOMINANT MAGNET: <strong class="underline text-white font-bold">{dom_reason}</strong>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Upper Short Magnet -->
        <div class="border border-[#ff3333]/50 p-4 bg-[#0a0202]">
          <div class="flex items-center justify-between text-xs mb-2">
            <span class="text-[#ff3333] font-bold">&gt;&gt; UPPER SHORT LIQUIDATION MAGNET</span>
            <span class="bg-[#ff3333] text-black font-bold px-1.5">+{upper_c.get('distance_pct', 0.0):.2f}% (+{upper_c.get('distance_atr', 0.0):.2f} ATR)</span>
          </div>
          <div class="text-3xl font-bold text-white mb-1">
            ${upper_c.get('price_level', 0.0):,.2f}
          </div>
          <div class="text-xs text-slate-400">
            EST. LIQUIDATION VOLUME: <span class="text-[#ff3333] font-bold">${upper_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M USD</span>
          </div>
          <!-- ASCII Progress Bar -->
          <div class="mt-3 text-xs text-[#ff3333] font-mono">
            PULL: [{("=" * int(min(20, max(2, upper_c.get('distance_pct', 1.0) * 3)))).ljust(20, "-")}]
          </div>
        </div>

        <!-- Lower Long Magnet -->
        <div class="border border-[#00ff66]/50 p-4 bg-[#010c05]">
          <div class="flex items-center justify-between text-xs mb-2">
            <span class="text-[#00ff66] font-bold">&gt;&gt; LOWER LONG LIQUIDATION MAGNET</span>
            <span class="bg-[#00ff66] text-black font-bold px-1.5">-{lower_c.get('distance_pct', 0.0):.2f}% (-{lower_c.get('distance_atr', 0.0):.2f} ATR)</span>
          </div>
          <div class="text-3xl font-bold text-white mb-1">
            ${lower_c.get('price_level', 0.0):,.2f}
          </div>
          <div class="text-xs text-slate-400">
            EST. LIQUIDATION VOLUME: <span class="text-[#00ff66] font-bold">${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M USD</span>
          </div>
          <!-- ASCII Progress Bar -->
          <div class="mt-3 text-xs text-[#00ff66] font-mono">
            PULL: [{("=" * int(min(20, max(2, lower_c.get('distance_pct', 1.0) * 3)))).ljust(20, "-")}]
          </div>
        </div>
      </div>

      <!-- Explicit 6-Factor Magnet Preference Override Sub-Panel -->
      <div class="mt-4 border border-[#1a3a2a] p-4 bg-black/80 font-mono text-xs">
        <div class="flex flex-wrap items-center justify-between text-[#00e5ff] border-b border-[#1a3a2a] pb-2 mb-3 gap-2">
          <span class="font-bold tracking-wider">[+] MAGNET PREFERENCE LOGIC // 6 OVERRIDE FACTORS IN HIERARCHY</span>
          <span class="text-[10px] text-slate-400">ORDER: 1.SIZE &gt; 2.SPOT_CVD &gt; 3.CROWDING &gt; 4.REGIME &gt; 5.ASYMMETRY &gt; 6.ATR</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-[11px] text-slate-300">
          <div class="p-2 border border-[#112a1e] bg-[#020b06]">
            <strong class="text-[#00ff66] block mb-0.5">&gt; 1. CLUSTER SIZE / MAGNITUDE:</strong>
            <span class="leading-relaxed">{f1}</span>
          </div>
          <div class="p-2 border border-[#112a1e] bg-[#020b06]">
            <strong class="text-[#00ff66] block mb-0.5">&gt; 2. SPOT VS DERIVATIVES LEADERSHIP:</strong>
            <span class="leading-relaxed">{f2}</span>
          </div>
          <div class="p-2 border border-[#112a1e] bg-[#020b06]">
            <strong class="text-[#00ff66] block mb-0.5">&gt; 3. CROWDING &amp; FUEL (FUNDING + OI):</strong>
            <span class="leading-relaxed">{f3}</span>
          </div>
          <div class="p-2 border border-[#112a1e] bg-[#020b06]">
            <strong class="text-[#00ff66] block mb-0.5">&gt; 4. REGIME / HTF STRUCTURE:</strong>
            <span class="leading-relaxed">{f4}</span>
          </div>
          <div class="p-2 border border-[#112a1e] bg-[#020b06]">
            <strong class="text-[#00ff66] block mb-0.5">&gt; 5. ASYMMETRY COMPARISON:</strong>
            <span class="leading-relaxed">{f5}</span>
          </div>
          <div class="p-2 border border-[#112a1e] bg-[#020b06]">
            <strong class="text-[#00ff66] block mb-0.5">&gt; 6. ATR VOLATILITY REGIME:</strong>
            <span class="leading-relaxed">{f6}</span>
          </div>
        </div>

        <div class="mt-3 pt-2.5 border-t border-[#1a3a2a] text-xs">
          <span class="text-[#ffb000] font-bold">&gt;&gt;&gt; DECISIVE PREFERENCE OUTCOME:</span>
          <span class="text-white font-bold ml-1.5">{dom_reason}</span>
        </div>
      </div>
    </div>

    <!-- Microstructure Telemetry Grid -->
    <div class="border border-[#00ff66]/40 p-5 bg-[#020b06]">
      <div class="text-xs font-bold uppercase tracking-wider text-[#00e5ff] mb-4 pb-2 border-b border-[#1a3a2a]">
        &gt; SYSTEM TELEMETRY GAUGES // 6-FACTOR POSITIONING MATRIX
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
        
        <div class="border border-[#1a3a2a] p-3 bg-black/60">
          <div class="text-[10px] text-slate-400 uppercase">SPOT CVD RATIO</div>
          <div class="text-lg font-bold text-white mt-1">{spot_cvd_ratio:.2f}</div>
          <div class="text-[10px] text-[#00ff66]">Taker Vol Delta</div>
        </div>

        <div class="border border-[#1a3a2a] p-3 bg-black/60">
          <div class="text-[10px] text-slate-400 uppercase">PERP CVD FLOW</div>
          <div class="text-lg font-bold text-white mt-1 uppercase">{metrics.get("perp_cvd_trend", "Flat")}</div>
          <div class="text-[10px] text-slate-400">Futures Delta</div>
        </div>

        <div class="border border-[#1a3a2a] p-3 bg-black/60">
          <div class="text-[10px] text-slate-400 uppercase">OPEN INTEREST 24H</div>
          <div class="text-lg font-bold {'text-[#00ff66]' if oi_change_24h > 0 else 'text-[#ff3333]'} mt-1">{oi_change_24h:+.2f}%</div>
          <div class="text-[10px] text-slate-400">{current_oi:,.0f} BTC</div>
        </div>

        <div class="border border-[#1a3a2a] p-3 bg-black/60">
          <div class="text-[10px] text-slate-400 uppercase">FUNDING (8H / ANN)</div>
          <div class="text-lg font-bold text-white mt-1">{funding_rate:.3f}%</div>
          <div class="text-[10px] text-[#ffb000]">{metrics.get("funding_rate_annualized", 0.0):.1f}% Ann.</div>
        </div>

        <div class="border border-[#1a3a2a] p-3 bg-black/60">
          <div class="text-[10px] text-slate-400 uppercase">BASIS SPREAD</div>
          <div class="text-lg font-bold text-white mt-1">{basis:.1f}%</div>
          <div class="text-[10px] text-slate-400">Contango/Backw</div>
        </div>

        <div class="border border-[#1a3a2a] p-3 bg-black/60">
          <div class="text-[10px] text-slate-400 uppercase">RETAIL L/S RATIO</div>
          <div class="text-lg font-bold text-white mt-1">{ls_ratio:.2f}</div>
          <div class="text-[10px] text-slate-400">Long Crowding</div>
        </div>

      </div>
    </div>

    <!-- Diagnostic Observation & Evidence Log -->
    <div class="border border-[#00ff66]/40 p-5 bg-[#020b06] text-xs">
      <div class="font-bold text-[#00ff66] uppercase tracking-wider mb-2 pb-1 border-b border-[#1a3a2a]">
        &gt; DIAGNOSTIC OBSERVATION LOG &amp; EVIDENCE TRACE
      </div>
      <p class="text-slate-300 leading-relaxed mb-4">{notes}</p>
      
      <div class="border border-[#1a3a2a] p-3 bg-black/70 font-mono text-[11px] text-[#00ff66] space-y-1">
        <div class="text-slate-500 mb-1">// QUANTITATIVE FACT MATCHES //</div>
        {matched_html}
      </div>
    </div>

    <!-- Retro Terminal Footer -->
    <footer class="border-t border-[#1a3a2a] pt-4 text-center text-xs text-slate-500 space-y-2">
      <div class="flex flex-wrap justify-center items-center gap-4 text-[11px]">
        <span>[F1: LIVE_DATA]</span>
        <a href="regime.json" class="text-[#00e5ff] hover:underline">[F2: REST_API: regime.json]</a>
        <a href="https://github.com/aikeluargalee-tech/btc-magnet-monitor" class="text-[#00ff66] hover:underline" target="_blank">[F3: GITHUB_REPO]</a>
      </div>
      <div class="text-[10px] text-slate-600">
        IBM 3270 CRT EMULATION // ARCHITECTURE: GITHUB ACTIONS SCHEDULED CRON // HOSTED ON GITHUB PAGES CDN
      </div>
      <div class="text-[11px] text-[#00ff66]/70">
        CURSOR READY <span class="cursor-blink inline-block bg-[#00ff66] w-2 h-3.5 align-middle ml-1"></span>
      </div>
    </footer>

  </main>
</body>
</html>"""
        return html
