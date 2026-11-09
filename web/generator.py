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
        notes = regime.get("notes", "")

        upper_c = regime.get("nearest_upper_cluster") or {}
        lower_c = regime.get("nearest_lower_cluster") or {}

        # Theme accent color
        if "USDT -> BTC" in rotation:
            accent_color = "#10b981"  # Emerald Green
            rotation_bg = "rgba(16, 185, 129, 0.15)"
            rotation_border = "#10b981"
            rotation_badge = "bg-emerald-500/20 text-emerald-400 border-emerald-500/40"
        elif "BTC -> USDT" in rotation:
            accent_color = "#ef4444"  # Rose Red
            rotation_bg = "rgba(239, 68, 68, 0.15)"
            rotation_border = "#ef4444"
            rotation_badge = "bg-rose-500/20 text-rose-400 border-rose-500/40"
        else:
            accent_color = "#f59e0b"  # Amber
            rotation_bg = "rgba(245, 158, 11, 0.15)"
            rotation_border = "#f59e0b"
            rotation_badge = "bg-amber-500/20 text-amber-400 border-amber-500/40"

        matched_html = "".join([f"<li class='flex items-center gap-2'><span class='text-emerald-400'>✓</span> {item}</li>" for item in regime.get("matched_criteria", [])])

        price = metrics.get("price", 0.0)
        funding_rate = metrics.get("funding_rate", 0.0) * 100
        spot_cvd_ratio = metrics.get("spot_cvd_ratio", 1.0)
        oi_change_24h = metrics.get("oi_change_24h_pct", 0.0)
        basis = metrics.get("futures_basis_annualized", 0.0)
        atr = metrics.get("atr", 0.0)
        ls_ratio = metrics.get("long_short_account_ratio", 1.0)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BTC Magnet | Liquidation & Regime Radar</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: #0b0f17;
      color: #e2e8f0;
    }}
    .mono {{
      font-family: 'JetBrains Mono', monospace;
    }}
    .glow-box {{
      box-shadow: 0 0 35px -5px {accent_color}25;
    }}
  </style>
</head>
<body class="min-h-screen bg-[#0b0f17] text-slate-100 pb-16 antialiased">

  <!-- Navigation / Header -->
  <header class="border-b border-slate-800/80 bg-[#0e1422]/90 backdrop-blur sticky top-0 z-50 px-4 py-3">
    <div class="max-w-5xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-rose-500 flex items-center justify-center text-xl shadow-lg shadow-rose-500/20">
          🧲
        </div>
        <div>
          <h1 class="font-extrabold text-lg leading-tight tracking-tight flex items-center gap-2">
            BTC MAGNET <span class="text-xs px-2 py-0.5 rounded-full font-mono font-medium bg-slate-800 text-slate-400 border border-slate-700">v1.0</span>
          </h1>
          <p class="text-xs text-slate-400">Observable Positioning Mechanics</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <div class="text-right hidden sm:block">
          <div class="text-xs text-slate-400 font-mono">BTC SPOT PRICE</div>
          <div class="text-base font-bold mono text-white">${price:,.2f}</div>
        </div>
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> LIVE SCANNER
        </span>
      </div>
    </div>
  </header>

  <main class="max-w-5xl mx-auto px-4 pt-6 space-y-6">

    <!-- Primary Action Hero Card -->
    <div class="rounded-2xl border border-slate-800 bg-[#121929] p-6 glow-box">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <span class="px-3 py-1 rounded-md text-xs font-mono font-bold uppercase tracking-wider bg-slate-800 border border-slate-700 text-slate-300">
              {cfg}
            </span>
            <span class="px-2.5 py-0.5 rounded-md text-xs font-medium bg-slate-800/80 text-slate-400">
              {regime.get("suitability", "Active")}
            </span>
          </div>
          <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            {name}: <span class="text-slate-300 font-normal">{diagnosis}</span>
          </h2>
        </div>

        <!-- Big Rotation Badge -->
        <div class="p-4 rounded-xl border flex flex-col items-center justify-center min-w-[240px]" style="background-color: {rotation_bg}; border-color: {rotation_border};">
          <div class="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 mb-1">SPOT ROTATION DIRECTIVE</div>
          <div class="text-xl sm:text-2xl font-black mono text-white flex items-center gap-2">
            {rotation}
          </div>
          <div class="text-xs font-mono text-slate-300 mt-1">Sizing Factor: <span class="font-bold text-white">{sizing}x</span></div>
        </div>
      </div>

      <!-- Protocol Action & Stop Details -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
        <div class="bg-[#0b0f17] p-4 rounded-xl border border-slate-800">
          <div class="text-xs text-slate-400 font-mono uppercase mb-1">ACTION PROTOCOL</div>
          <div class="text-base font-bold text-white mb-1">{action}</div>
          <p class="text-xs text-slate-400 leading-relaxed">{entry_inst}</p>
        </div>

        <div class="bg-[#0b0f17] p-4 rounded-xl border border-slate-800">
          <div class="text-xs text-slate-400 font-mono uppercase mb-1">INVIOLABLE STOP-LOSS</div>
          <div class="text-base font-bold mono text-rose-400 mb-1">${stop_price:,.2f} ({stop_dist:.2f}% dist)</div>
          <p class="text-xs text-slate-400 leading-relaxed">{stop_rule}</p>
        </div>

        <div class="bg-[#0b0f17] p-4 rounded-xl border border-slate-800">
          <div class="text-xs text-slate-400 font-mono uppercase mb-1">RISK BUDGET VERIFICATION</div>
          <div class="text-base font-bold mb-1 flex items-center gap-2 {'text-emerald-400' if risk.get('risk_budget_ok') else 'text-rose-400'}">
            {"✓ APPROVED (Fits Budget)" if risk.get("risk_budget_ok") else "⚠️ WARNING / REJECTED"}
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">{risk.get("actionable_trade_instruction", "")}</p>
        </div>
      </div>
    </div>

    <!-- Liquidation Magnet Module -->
    <div class="rounded-2xl border border-slate-800 bg-[#121929] p-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-lg font-bold text-white flex items-center gap-2">
            🧲 Liquidation Magnet Proximity
          </h3>
          <p class="text-xs text-slate-400">Mechanical liquidity pools & forced stop clusters</p>
        </div>
        <span class="px-3 py-1 rounded-full text-xs font-mono font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
          DOMINANT: {dom_magnet}
        </span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Upper Short Cluster -->
        <div class="bg-[#0b0f17] p-4 rounded-xl border border-slate-800 relative overflow-hidden">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider">▲ UPPER SHORT LIQUIDATION MAGNET</span>
            <span class="text-xs mono font-bold text-white bg-slate-800 px-2 py-0.5 rounded">+{upper_c.get('distance_pct', 0.0):.2f}% ({upper_c.get('distance_atr', 0.0):.2f} ATR)</span>
          </div>
          <div class="text-2xl font-extrabold mono text-white">${upper_c.get('price_level', 0.0):,.2f}</div>
          <div class="text-xs text-slate-400 mt-1">Est. Liquidation Density: <span class="font-bold text-slate-200 mono">${upper_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M</span></div>
          <div class="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div class="bg-rose-500 h-full rounded-full" style="width: min(100%, {max(15, upper_c.get('distance_pct', 1.0) * 15)}%);"></div>
          </div>
        </div>

        <!-- Lower Long Cluster -->
        <div class="bg-[#0b0f17] p-4 rounded-xl border border-slate-800 relative overflow-hidden">
          <div class="flex items-center justify-between mb-2">
            <span class="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">▼ LOWER LONG LIQUIDATION MAGNET</span>
            <span class="text-xs mono font-bold text-white bg-slate-800 px-2 py-0.5 rounded">-{lower_c.get('distance_pct', 0.0):.2f}% ({lower_c.get('distance_atr', 0.0):.2f} ATR)</span>
          </div>
          <div class="text-2xl font-extrabold mono text-white">${lower_c.get('price_level', 0.0):,.2f}</div>
          <div class="text-xs text-slate-400 mt-1">Est. Liquidation Density: <span class="font-bold text-slate-200 mono">${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M</span></div>
          <div class="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
            <div class="bg-emerald-500 h-full rounded-full" style="width: min(100%, {max(15, lower_c.get('distance_pct', 1.0) * 15)}%);"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Microstructure Telemetry Grid -->
    <div class="rounded-2xl border border-slate-800 bg-[#121929] p-6">
      <h3 class="text-lg font-bold text-white mb-4">Market Microstructure Telemetry</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div class="bg-[#0b0f17] p-3 rounded-xl border border-slate-800">
          <div class="text-[11px] font-mono text-slate-400 uppercase">Spot CVD Ratio</div>
          <div class="text-lg font-bold mono text-white mt-1">{spot_cvd_ratio:.2f}</div>
          <div class="text-[10px] text-slate-400">Taker Buy/Sell</div>
        </div>

        <div class="bg-[#0b0f17] p-3 rounded-xl border border-slate-800">
          <div class="text-[11px] font-mono text-slate-400 uppercase">Perp CVD Trend</div>
          <div class="text-lg font-bold mono text-white mt-1 capitalize">{metrics.get("perp_cvd_trend", "Flat")}</div>
          <div class="text-[10px] text-slate-400">24h Delta Flow</div>
        </div>

        <div class="bg-[#0b0f17] p-3 rounded-xl border border-slate-800">
          <div class="text-[11px] font-mono text-slate-400 uppercase">Open Interest 24h</div>
          <div class="text-lg font-bold mono {'text-emerald-400' if oi_change_24h > 0 else 'text-rose-400'} mt-1">{oi_change_24h:+.2f}%</div>
          <div class="text-[10px] text-slate-400">Leverage Flow</div>
        </div>

        <div class="bg-[#0b0f17] p-3 rounded-xl border border-slate-800">
          <div class="text-[11px] font-mono text-slate-400 uppercase">Funding Rate</div>
          <div class="text-lg font-bold mono text-white mt-1">{funding_rate:.3f}%</div>
          <div class="text-[10px] text-slate-400">8h Perp Skew</div>
        </div>

        <div class="bg-[#0b0f17] p-3 rounded-xl border border-slate-800">
          <div class="text-[11px] font-mono text-slate-400 uppercase">Basis (Ann.)</div>
          <div class="text-lg font-bold mono text-white mt-1">{basis:.1f}%</div>
          <div class="text-[10px] text-slate-400">Spot-Futures Spread</div>
        </div>

        <div class="bg-[#0b0f17] p-3 rounded-xl border border-slate-800">
          <div class="text-[11px] font-mono text-slate-400 uppercase">Retail L/S Ratio</div>
          <div class="text-lg font-bold mono text-white mt-1">{ls_ratio:.2f}</div>
          <div class="text-[10px] text-slate-400">Long Crowding</div>
        </div>
      </div>
    </div>

    <!-- Diagnostic Rationale -->
    <div class="rounded-2xl border border-slate-800 bg-[#121929] p-6">
      <h3 class="text-base font-bold text-white mb-2">Diagnostic Observation & Rationale</h3>
      <p class="text-xs text-slate-300 leading-relaxed mb-4">{notes}</p>
      <div class="bg-[#0b0f17] p-3 rounded-xl border border-slate-800 text-xs text-slate-300">
        <div class="font-bold text-slate-400 uppercase font-mono mb-2">Matched Microstructure Criteria</div>
        <ul class="space-y-1">
          {matched_html}
        </ul>
      </div>
    </div>

    <!-- API Feed Link -->
    <div class="text-center pt-4">
      <p class="text-xs text-slate-400">
        Machine-readable API for mobile app: <a href="regime.json" class="text-rose-400 underline mono hover:text-rose-300">regime.json</a>
      </p>
      <p class="text-[11px] text-slate-400 mt-1 font-mono">Last updated: {data.get("timestamp", "")} (UTC)</p>
    </div>

  </main>
</body>
</html>"""
        return html
