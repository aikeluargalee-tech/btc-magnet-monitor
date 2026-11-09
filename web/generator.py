import json
import os
import datetime
from typing import Dict, Any, Tuple

class WebGenerator:
    """Generates the static JSON API feed and the clean black-background dashboard for GitHub Pages."""

    def __init__(self, output_dir: str = "dist"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        # 1. Write raw JSON feed for the mobile app
        json_path = os.path.join(self.output_dir, "regime.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # 2. Render modern clean black-background dashboard HTML
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
        data_quality = regime.get("data_quality", "LIVE")

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

        # Modern Black Background Accent Styles
        if cfg == "DATA_INCOMPLETE":
            rotation_badge_bg = "bg-amber-950/60"
            rotation_border = "border-amber-500/60"
            rotation_text = "text-amber-400"
            pill_tag = "DATA INCOMPLETE / STAND ASIDE"
            hero_glow = "shadow-[0_0_40px_-10px_rgba(245,158,11,0.2)]"
        elif "USDT -> BTC" in rotation:
            rotation_badge_bg = "bg-emerald-950/60"
            rotation_border = "border-emerald-500/60"
            rotation_text = "text-emerald-400"
            pill_tag = "DEPLOY SPOT LONG"
            hero_glow = "shadow-[0_0_40px_-10px_rgba(16,185,129,0.15)]"
        elif "BTC -> USDT" in rotation:
            rotation_badge_bg = "bg-rose-950/60"
            rotation_border = "border-rose-500/60"
            rotation_text = "text-rose-400"
            pill_tag = "DEFENSIVE EXIT / HARVEST"
            hero_glow = "shadow-[0_0_40px_-10px_rgba(239,68,68,0.15)]"
        else:
            rotation_badge_bg = "bg-amber-950/60"
            rotation_border = "border-amber-500/60"
            rotation_text = "text-amber-400"
            pill_tag = "REMAIN 100% USDT"
            hero_glow = "shadow-[0_0_40px_-10px_rgba(245,158,11,0.15)]"

        matched_html = "".join([f"<li class='flex items-start gap-2 text-slate-300 text-xs'><span class='text-emerald-400 font-bold'>✓</span><span>{item}</span></li>" for item in regime.get("matched_criteria", [])])

        price = metrics.get("price", 0.0)
        funding_rate = metrics.get("funding_rate", 0.0) * 100
        spot_cvd_ratio = metrics.get("spot_cvd_ratio", 1.0)
        oi_change_24h = metrics.get("oi_change_24h_pct", 0.0)
        basis = metrics.get("futures_basis_annualized", 0.0)
        ls_ratio = metrics.get("long_short_account_ratio", 1.0)
        current_oi = metrics.get("open_interest", 0.0)
        spot_source = metrics.get("spot_data_source", "Binance Vision API")
        futures_source = metrics.get("futures_data_source", "Deribit & Kraken Futures")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BTC Magnet Monitor | Liquidation &amp; Regime Radar</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background-color: #000000;
      color: #e2e8f0;
    }}
    .mono {{
      font-family: 'JetBrains Mono', monospace;
    }}
  </style>
</head>
<body class="min-h-screen bg-black text-slate-200 pb-16 antialiased">

  <!-- Top Navigation Bar -->
  <header class="border-b border-zinc-800 bg-black/90 backdrop-blur sticky top-0 z-50 px-4 py-3">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-lg bg-zinc-900 border border-zinc-700 flex items-center justify-center text-lg">
          🧲
        </div>
        <div>
          <h1 class="font-bold text-base tracking-tight text-white flex items-center gap-2">
            BTC MAGNET MONITOR
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700">v1.3</span>
          </h1>
          <p class="text-xs text-zinc-400">Observable Positioning Mechanics &amp; Regime Radar</p>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div class="text-right hidden sm:block">
          <div class="text-[10px] font-mono uppercase text-zinc-400">BTC Spot Price</div>
          <div class="text-sm font-bold mono text-white">${price:,.2f}</div>
        </div>
        <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono font-medium {'bg-emerald-950/50 text-emerald-400 border border-emerald-800/60' if data_quality == 'LIVE' else 'bg-amber-950/50 text-amber-400 border border-amber-800/60'}">
          <span class="w-1.5 h-1.5 rounded-full {'bg-emerald-400' if data_quality == 'LIVE' else 'bg-amber-400'} animate-pulse"></span>
          <span>{data_quality} DATA FEED</span>
        </div>
      </div>
    </div>
  </header>

  <!-- Data Provenance & Status Bar -->
  <div class="border-b border-zinc-900 bg-zinc-950 px-4 py-1.5 text-xs text-zinc-400">
    <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2 font-mono text-[11px]">
      <div>SOURCES: {spot_source} &bull; {futures_source} &bull; CADENCE: 30M</div>
      <div>LAST SCAN: {data.get("timestamp", "")[:19]} UTC</div>
    </div>
  </div>

  <main class="max-w-6xl mx-auto px-4 pt-6 space-y-6">

    <!-- Primary Action Hero Card -->
    <div class="rounded-xl border border-zinc-800 bg-zinc-950 p-6 {hero_glow}">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-5 pb-6 border-b border-zinc-800/80">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <span class="px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-zinc-800 text-zinc-200 border border-zinc-700">
              {cfg}
            </span>
            <span class="px-2 py-0.5 rounded text-xs font-medium bg-zinc-900 text-zinc-400 border border-zinc-800">
              {regime.get("suitability", "Active")}
            </span>
          </div>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {name}: <span class="text-zinc-300 font-normal">{diagnosis}</span>
          </h2>
        </div>

        <!-- Spot Rotation Directive Box -->
        <div class="p-4 rounded-xl border {rotation_border} {rotation_badge_bg} flex flex-col items-center justify-center min-w-[270px]">
          <div class="text-[10px] font-mono uppercase tracking-wider text-zinc-400 mb-1">
            Spot Rotation Directive
          </div>
          <div class="text-2xl font-black mono text-white flex items-center gap-2">
            {rotation}
          </div>
          <div class="text-xs font-mono {rotation_text} mt-1 font-semibold">
            Sizing Factor: {sizing}x &bull; {pill_tag}
          </div>
        </div>
      </div>

      <!-- Protocol Action, Stop, and Risk Budget Details -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-5">
        <div class="bg-black p-4 rounded-lg border border-zinc-800">
          <div class="text-[11px] text-zinc-400 font-mono uppercase mb-1">Action Protocol</div>
          <div class="text-sm font-bold text-white mb-1.5">{action}</div>
          <p class="text-xs text-zinc-400 leading-relaxed">{entry_inst}</p>
        </div>

        <div class="bg-black p-4 rounded-lg border border-zinc-800">
          <div class="text-[11px] text-zinc-400 font-mono uppercase mb-1">Inviolable Stop-Loss</div>
          <div class="text-sm font-bold mono text-rose-400 mb-1.5">${stop_price:,.2f} ({stop_dist:.2f}% distance)</div>
          <p class="text-xs text-zinc-400 leading-relaxed">{stop_rule}</p>
        </div>

        <div class="bg-black p-4 rounded-lg border border-zinc-800">
          <div class="text-[11px] text-zinc-400 font-mono uppercase mb-1">Risk Budget Verification</div>
          <div class="text-sm font-bold mb-1.5 {'text-emerald-400' if risk.get('risk_budget_ok') else 'text-rose-400'}">
            {"✓ Approved (Fits 1% Risk Budget)" if risk.get("risk_budget_ok") else "⚠️ Warning: Stop Exceeds Risk Budget"}
          </div>
          <p class="text-xs text-zinc-400 leading-relaxed">{risk.get("actionable_trade_instruction", "")}</p>
        </div>
      </div>
    </div>

    <!-- Liquidation Magnet Module (Explicitly labeled as Modeled Pools) -->
    <div class="rounded-xl border border-zinc-800 bg-zinc-950 p-6 space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800/80 pb-4">
        <div>
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            🧲 Modeled Liquidity Pools (Algorithmic Leverage Estimates)
          </h3>
          <p class="text-xs text-zinc-400">Estimated forced stop clusters anchored to 4H swing extremes (10x, 25x, 50x, 100x)</p>
        </div>
        <div class="px-3 py-1.5 rounded-lg border border-amber-600/50 bg-amber-950/40 text-amber-300 text-xs font-mono">
          <span class="text-zinc-400">DOMINANT MAGNET:</span> <strong>{dom_reason}</strong>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Upper Short Magnet -->
        <div class="bg-black p-4 rounded-lg border border-zinc-800">
          <div class="flex items-center justify-between text-xs mb-2">
            <span class="text-rose-400 font-bold uppercase tracking-wide">▲ Upper Short Liquidity Pool</span>
            <span class="mono font-semibold text-white bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">
              +{upper_c.get('distance_pct', 0.0):.2f}% (+{upper_c.get('distance_atr', 0.0):.2f} ATR)
            </span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold mono text-white">
            ${upper_c.get('price_level', 0.0):,.2f}
          </div>
          <div class="text-xs text-zinc-400 mt-1">
            Modeled Liquidity Pool: <span class="font-bold text-slate-200 mono">${upper_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M</span> <span class="text-[10px] text-zinc-500">(Estimate)</span>
          </div>
          <div class="w-full bg-zinc-900 h-1.5 rounded-full mt-3 overflow-hidden">
            <div class="bg-rose-500 h-full rounded-full" style="width: min(100%, {max(15, upper_c.get('distance_pct', 1.0) * 15)}%);"></div>
          </div>
        </div>

        <!-- Lower Long Magnet -->
        <div class="bg-black p-4 rounded-lg border border-zinc-800">
          <div class="flex items-center justify-between text-xs mb-2">
            <span class="text-emerald-400 font-bold uppercase tracking-wide">▼ Lower Long Liquidity Pool</span>
            <span class="mono font-semibold text-white bg-zinc-900 px-2 py-0.5 rounded border border-zinc-800">
              -{lower_c.get('distance_pct', 0.0):.2f}% (-{lower_c.get('distance_atr', 0.0):.2f} ATR)
            </span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold mono text-white">
            ${lower_c.get('price_level', 0.0):,.2f}
          </div>
          <div class="text-xs text-zinc-400 mt-1">
            Modeled Liquidity Pool: <span class="font-bold text-slate-200 mono">${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M</span> <span class="text-[10px] text-zinc-500">(Estimate)</span>
          </div>
          <div class="w-full bg-zinc-900 h-1.5 rounded-full mt-3 overflow-hidden">
            <div class="bg-emerald-500 h-full rounded-full" style="width: min(100%, {max(15, lower_c.get('distance_pct', 1.0) * 15)}%);"></div>
          </div>
        </div>
      </div>

      <!-- 6-Factor Multi-Factor Magnet Preference Override Sub-Panel -->
      <div class="mt-4 border border-zinc-800 rounded-lg p-4 bg-black">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-zinc-800 pb-2 mb-3 gap-1">
          <span class="text-xs font-mono font-bold text-zinc-200 uppercase tracking-wider">Magnet Preference Logic (6-Factor Override Engine)</span>
          <span class="text-[10px] text-zinc-500 font-mono">Priority: Size &gt; Spot CVD &gt; Crowding &gt; Regime &gt; Asymmetry &gt; ATR</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs text-zinc-300">
          <div class="p-2.5 rounded bg-zinc-950 border border-zinc-800/80">
            <strong class="text-zinc-400 font-mono text-[11px] block mb-1">1. Cluster Size / Magnitude:</strong>
            <span class="text-slate-200 leading-relaxed">{f1}</span>
          </div>
          <div class="p-2.5 rounded bg-zinc-950 border border-zinc-800/80">
            <strong class="text-zinc-400 font-mono text-[11px] block mb-1">2. Spot vs. Derivatives Leadership:</strong>
            <span class="text-slate-200 leading-relaxed">{f2}</span>
          </div>
          <div class="p-2.5 rounded bg-zinc-950 border border-zinc-800/80">
            <strong class="text-zinc-400 font-mono text-[11px] block mb-1">3. Crowding &amp; Fuel (Funding + OI):</strong>
            <span class="text-slate-200 leading-relaxed">{f3}</span>
          </div>
          <div class="p-2.5 rounded bg-zinc-950 border border-zinc-800/80">
            <strong class="text-zinc-400 font-mono text-[11px] block mb-1">4. Regime / HTF Structure:</strong>
            <span class="text-slate-200 leading-relaxed">{f4}</span>
          </div>
          <div class="p-2.5 rounded bg-zinc-950 border border-zinc-800/80">
            <strong class="text-zinc-400 font-mono text-[11px] block mb-1">5. Distance Asymmetry:</strong>
            <span class="text-slate-200 leading-relaxed">{f5}</span>
          </div>
          <div class="p-2.5 rounded bg-zinc-950 border border-zinc-800/80">
            <strong class="text-zinc-400 font-mono text-[11px] block mb-1">6. ATR Volatility Regime:</strong>
            <span class="text-slate-200 leading-relaxed">{f6}</span>
          </div>
        </div>

        <div class="mt-3 pt-3 border-t border-zinc-800 flex items-start gap-2 text-xs">
          <span class="text-amber-400 font-bold font-mono">DECISIVE OUTCOME:</span>
          <span class="text-white font-medium">{dom_reason}</span>
        </div>
      </div>
    </div>

    <!-- Microstructure Telemetry Grid -->
    <div class="rounded-xl border border-zinc-800 bg-zinc-950 p-6 space-y-4">
      <h3 class="text-base font-bold text-white">Market Microstructure Telemetry</h3>
      <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        
        <div class="bg-black p-3 rounded-lg border border-zinc-800">
          <div class="text-[10px] font-mono text-zinc-400 uppercase">Spot CVD Ratio</div>
          <div class="text-lg font-bold mono text-white mt-1">{spot_cvd_ratio:.2f}</div>
          <div class="text-[10px] text-zinc-500">Candle Taker Delta</div>
        </div>

        <div class="bg-black p-3 rounded-lg border border-zinc-800">
          <div class="text-[10px] font-mono text-zinc-400 uppercase">Perp CVD Flow</div>
          <div class="text-lg font-bold mono text-white mt-1 capitalize">{metrics.get("perp_cvd_trend", "Flat")}</div>
          <div class="text-[10px] text-zinc-500">Futures Delta Trend</div>
        </div>

        <div class="bg-black p-3 rounded-lg border border-zinc-800">
          <div class="text-[10px] font-mono text-zinc-400 uppercase">Open Interest 24h</div>
          <div class="text-lg font-bold mono {'text-emerald-400' if oi_change_24h > 0 else 'text-rose-400'} mt-1">{oi_change_24h:+.2f}%</div>
          <div class="text-[10px] text-zinc-500">{current_oi:,.0f} BTC</div>
        </div>

        <div class="bg-black p-3 rounded-lg border border-zinc-800">
          <div class="text-[10px] font-mono text-zinc-400 uppercase">Funding Rate</div>
          <div class="text-lg font-bold mono text-white mt-1">{funding_rate:.3f}%</div>
          <div class="text-[10px] text-amber-400/90">{metrics.get("funding_rate_annualized", 0.0):.1f}% Ann.</div>
        </div>

        <div class="bg-black p-3 rounded-lg border border-zinc-800">
          <div class="text-[10px] font-mono text-zinc-400 uppercase">Futures Basis</div>
          <div class="text-lg font-bold mono text-white mt-1">{basis:.1f}%</div>
          <div class="text-[10px] text-zinc-500">Annualized Spread</div>
        </div>

        <div class="bg-black p-3 rounded-lg border border-zinc-800">
          <div class="text-[10px] font-mono text-zinc-400 uppercase">Retail L/S Ratio</div>
          <div class="text-lg font-bold mono text-white mt-1">{ls_ratio:.2f}</div>
          <div class="text-[10px] text-zinc-500">Long Crowding</div>
        </div>

      </div>
    </div>

    <!-- Diagnostic Observation Log -->
    <div class="rounded-xl border border-zinc-800 bg-zinc-950 p-6 space-y-3">
      <h3 class="text-base font-bold text-white">Diagnostic Observation &amp; Evidence Trace</h3>
      <p class="text-xs text-zinc-300 leading-relaxed">{notes}</p>
      
      <div class="bg-black p-3 rounded-lg border border-zinc-800 mt-3">
        <div class="text-[11px] font-mono uppercase text-zinc-400 mb-2 font-semibold">Matched Microstructure Facts</div>
        <ul class="space-y-1.5">
          {matched_html}
        </ul>
      </div>
    </div>

    <!-- API Feed & Footer -->
    <footer class="border-t border-zinc-800 pt-6 text-center text-xs text-zinc-400 space-y-2">
      <div class="flex flex-wrap justify-center items-center gap-4 text-xs font-mono">
        <a href="regime.json" class="text-emerald-400 hover:text-emerald-300 underline font-medium">REST API: regime.json</a>
        <span>&bull;</span>
        <a href="https://github.com/aikeluargalee-tech/btc-magnet-monitor" class="text-zinc-300 hover:text-white underline font-medium" target="_blank">GitHub Repository</a>
      </div>
      <div class="text-[11px] text-zinc-500">
        Automated via GitHub Actions scheduled cron &bull; Deployed on GitHub Pages CDN &bull; Zero Server Cost
      </div>
    </footer>

  </main>
</body>
</html>"""
        return html
