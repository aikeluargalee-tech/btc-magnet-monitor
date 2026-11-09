import json
import os
import datetime
from typing import Dict, Any, Tuple

class WebGenerator:
    """Generates the static JSON API feed and a clean, conventional modern financial dashboard."""

    def __init__(self, output_dir: str = "dist"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, payload: Dict[str, Any]) -> Tuple[str, str]:
        # 1. Write raw JSON feed for the mobile app and third-party consumers
        json_path = os.path.join(self.output_dir, "regime.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        # 2. Render modern conventional dashboard HTML
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

        # Plain-English Explanations for Beginners (95% User Base)
        plain_verdict = regime.get("plain_english_verdict", "Analyzing current market conditions...")
        why_points = regime.get("why_points", [])
        why_sizing = regime.get("why_sizing_reason", f"Deploying {sizing*100:.0f}% of available cash based on regime risk parameters.")
        why_stop = regime.get("why_stop_reason", f"Safety stop anchored at ${stop_price:,.2f} ({stop_dist:.2f}% distance).")

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

        # Conventional Clean Theme Color Mappings
        if cfg == "DATA_INCOMPLETE":
            badge_bg = "bg-amber-500/10"
            badge_border = "border-amber-500/30"
            badge_text = "text-amber-400"
            pill_tag = "Data Incomplete • Stand Aside"
        elif "USDT -> BTC" in rotation:
            badge_bg = "bg-emerald-500/10"
            badge_border = "border-emerald-500/30"
            badge_text = "text-emerald-400"
            pill_tag = "Buy Spot (Accumulate)"
        elif "BTC -> USDT" in rotation:
            badge_bg = "bg-rose-500/10"
            badge_border = "border-rose-500/30"
            badge_text = "text-rose-400"
            pill_tag = "Defensive Exit (Harvest to Cash)"
        else:
            badge_bg = "bg-amber-500/10"
            badge_border = "border-amber-500/30"
            badge_text = "text-amber-400"
            pill_tag = "Hold 100% Cash Reserve"

        # Why Points HTML List
        why_points_html = "".join([
            f"""<div class='flex items-start gap-3 p-3.5 rounded-xl bg-zinc-950/80 border border-zinc-800/70'>
                 <span class='w-6 h-6 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-xs font-bold text-emerald-400 flex-shrink-0 mt-0.5'>{idx+1}</span>
                 <p class='text-xs sm:text-sm text-zinc-300 leading-relaxed font-normal'>{pt}</p>
               </div>"""
            for idx, pt in enumerate(why_points)
        ])

        matched_html = "".join([f"<li class='flex items-start gap-2.5 text-zinc-300 text-sm'><span class='text-emerald-400 font-semibold mt-0.5'>✓</span><span class='leading-relaxed'>{item}</span></li>" for item in regime.get("matched_criteria", [])])

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
  <title>BTC Magnet Monitor — Market Regime &amp; Liquidity Intelligence</title>
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
            <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-zinc-800/80 text-zinc-400 border border-zinc-700/60">v1.5</span>
          </div>
          <p class="text-xs text-zinc-400 hidden sm:block">Observable Positioning Mechanics &amp; Regime Radar</p>
        </div>
      </div>

      <div class="flex items-center gap-5">
        <div class="text-right">
          <div class="text-[11px] font-medium text-zinc-400">Bitcoin Price (USD)</div>
          <div class="text-base font-bold mono text-white">${price:,.2f}</div>
        </div>
        <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium {'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' if data_quality == 'LIVE' else 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}">
          <span class="w-2 h-2 rounded-full {'bg-emerald-400' if data_quality == 'LIVE' else 'bg-amber-400'} animate-pulse"></span>
          <span>{data_quality} Feed</span>
        </div>
      </div>
    </div>
  </header>

  <!-- Sub-Header Info Bar -->
  <div class="border-b border-zinc-800/50 bg-zinc-900/30 px-4 sm:px-6 py-2 text-xs text-zinc-400">
    <div class="max-w-6xl mx-auto flex flex-wrap items-center justify-between gap-2">
      <div>Data Feeds: <span class="text-zinc-300">{spot_source}</span> &bull; <span class="text-zinc-300">{futures_source}</span></div>
      <div>Last Scan: <span class="text-zinc-300 font-medium">{data.get("timestamp", "")[:19]} UTC</span> &bull; Updated Every 30 Minutes</div>
    </div>
  </div>

  <main class="max-w-6xl mx-auto px-4 sm:px-6 pt-6 space-y-6">

    <!-- Primary Recommendation Card -->
    <div class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6 sm:p-8 backdrop-blur-sm shadow-xl">
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6 pb-6 border-b border-zinc-800">
        <div>
          <div class="flex items-center gap-2.5 mb-2.5">
            <span class="px-3 py-1 rounded-md text-xs font-bold uppercase tracking-wider bg-zinc-800 text-zinc-200 border border-zinc-700">
              {cfg}
            </span>
            <span class="px-2.5 py-1 rounded-md text-xs font-medium bg-zinc-800/60 text-zinc-400 border border-zinc-700/50">
              {regime.get("suitability", "Active Operating Zone")}
            </span>
          </div>
          <h2 class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            {name}: <span class="text-zinc-400 font-normal">{diagnosis}</span>
          </h2>
          <p class="text-sm text-zinc-300 mt-2 max-w-2xl leading-relaxed">
            Market regime diagnosed through multi-exchange order flow, spot-vs-futures volume deltas, and open interest positioning.
          </p>
        </div>

        <!-- Call to Action Banner -->
        <div class="flex flex-col sm:flex-row lg:flex-col items-start sm:items-center lg:items-end justify-center gap-3 p-5 rounded-xl border {badge_border} {badge_bg} min-w-[280px]">
          <div class="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Recommended Action
          </div>
          <div class="text-xl sm:text-2xl font-extrabold tracking-tight text-white flex items-center gap-2">
            {rotation}
          </div>
          <div class="text-xs font-medium {badge_text}">
            {pill_tag} &bull; Sizing Factor: {sizing}x
          </div>
        </div>
      </div>

      <!-- Action Protocol, Stop Loss, and Risk Rules -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6">
        <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 space-y-1.5">
          <div class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Execution Protocol</div>
          <div class="text-base font-bold text-white">{action}</div>
          <p class="text-xs text-zinc-300 leading-relaxed pt-1">{entry_inst}</p>
        </div>

        <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 space-y-1.5">
          <div class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Inviolable Stop-Loss</div>
          <div class="text-base font-bold mono text-rose-400">${stop_price:,.2f} <span class="text-xs font-normal text-zinc-400">({stop_dist:.2f}% distance)</span></div>
          <p class="text-xs text-zinc-300 leading-relaxed pt-1">{stop_rule}</p>
        </div>

        <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 space-y-1.5">
          <div class="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Risk Management</div>
          <div class="text-base font-bold flex items-center gap-1.5 {'text-emerald-400' if risk.get('risk_budget_ok') else 'text-rose-400'}">
            {"✓ Approved (Within 1% Risk Budget)" if risk.get("risk_budget_ok") else "⚠️ Warning: Exceeds Risk Limit"}
          </div>
          <p class="text-xs text-zinc-300 leading-relaxed pt-1">{risk.get("actionable_trade_instruction", "")}</p>
        </div>
      </div>
    </div>

    <!-- Plain-English Breakdown Card (For 95% Beginners) -->
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
        <!-- 3 Key Reasons -->
        <div class="lg:col-span-2 space-y-3">
          <div class="text-xs font-bold uppercase tracking-wider text-zinc-400">The 3 Key Market Factors Driving This Call</div>
          <div class="space-y-2.5">
            {why_points_html}
          </div>
        </div>

        <!-- Sizing and Safety Net Column -->
        <div class="space-y-3.5">
          <!-- Why Sizing -->
          <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80 space-y-1.5">
            <div class="text-xs font-bold uppercase tracking-wider text-amber-400">Why This Exact Sizing?</div>
            <p class="text-xs text-zinc-300 leading-relaxed font-normal">{why_sizing}</p>
          </div>

          <!-- Where is Safety Net -->
          <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80 space-y-1.5">
            <div class="text-xs font-bold uppercase tracking-wider text-rose-400">Where Is Your Safety Net?</div>
            <p class="text-xs text-zinc-300 leading-relaxed font-normal">{why_stop}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Liquidation Magnets & Price Targets -->
    <div class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6 sm:p-8 space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-zinc-800 pb-4">
        <div>
          <h3 class="text-lg font-bold text-white flex items-center gap-2">
            <span>Liquidation Magnets &amp; Key Price Pools</span>
          </h3>
          <p class="text-xs text-zinc-400 mt-0.5">Modeled liquidation concentration zones derived from 10x, 25x, 50x, and 100x leverage bands</p>
        </div>
        <div class="px-3.5 py-1.5 rounded-full border border-amber-500/30 bg-amber-500/10 text-amber-300 text-xs font-medium">
          <span class="text-zinc-400">Dominant Magnet:</span> <strong class="text-white ml-1">{dom_reason}</strong>
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

    <!-- Market Microstructure Gauges -->
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
          <div class="text-lg font-bold mono text-white mt-1.5">{funding_rate:.3f}%</div>
          <div class="text-[11px] text-amber-400 mt-0.5">{metrics.get("funding_rate_annualized", 0.0):.1f}% Ann.</div>
        </div>

        <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80">
          <div class="text-[11px] text-zinc-400 uppercase tracking-wide">Futures Basis</div>
          <div class="text-lg font-bold mono text-white mt-1.5">{basis:.1f}%</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Annualized Spread</div>
        </div>

        <div class="bg-zinc-950/80 p-4 rounded-xl border border-zinc-800/80">
          <div class="text-[11px] text-zinc-400 uppercase tracking-wide">Retail Long/Short</div>
          <div class="text-lg font-bold mono text-white mt-1.5">{ls_ratio:.2f}</div>
          <div class="text-[11px] text-zinc-400 mt-0.5">Account Ratio</div>
        </div>

      </div>
    </div>

    <!-- Diagnostic Observation & Evidence Log -->
    <div class="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-6 sm:p-8 space-y-4">
      <h3 class="text-lg font-bold text-white">Diagnostic Rationale &amp; Evidence Trace</h3>
      <p class="text-sm text-zinc-300 leading-relaxed">{notes}</p>
      
      <div class="bg-zinc-950/80 p-5 rounded-xl border border-zinc-800/80 mt-4">
        <div class="text-xs uppercase font-semibold text-zinc-400 mb-3 tracking-wider">Verified Market Microstructure Facts</div>
        <ul class="space-y-2">
          {matched_html}
        </ul>
      </div>
    </div>

    <!-- About & How It Works (Educational Section for Beginners) -->
    <div class="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 sm:p-8 space-y-4">
      <h3 class="text-lg font-bold text-white">About BTC Magnet Monitor</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-5 text-xs text-zinc-300 leading-relaxed">
        <div class="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/70 space-y-2">
          <strong class="text-emerald-400 block font-semibold text-sm">1. Purpose: Spot Swing Trading</strong>
          <p>
            Designed exclusively for spot Bitcoin swing traders who hold USDT cash or BTC (never leverage, never futures shorting). It tells you when it is statistically favorable to deploy cash into BTC, and when to rotate back to USDT cash to preserve gains.
          </p>
        </div>
        <div class="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/70 space-y-2">
          <strong class="text-amber-400 block font-semibold text-sm">2. The Machinery: Positioning Mechanics</strong>
          <p>
            Rather than drawing lines or lagging chart indicators, the engine tracks order book depth, taker volume deltas (CVD), open interest leverage changes, and liquidation pools across major exchanges to diagnose the true market regime.
          </p>
        </div>
        <div class="p-4 rounded-xl bg-zinc-950/60 border border-zinc-800/70 space-y-2">
          <strong class="text-cyan-400 block font-semibold text-sm">3. Zero Data Guesswork</strong>
          <p>
            Runs completely automated every 30 minutes via GitHub Actions. All metrics are fetched live from institutional public APIs. If feeds are unavailable, the engine withholds its recommendation to keep your capital safe.
          </p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="border-t border-zinc-800/80 pt-8 text-center text-xs text-zinc-400 space-y-2.5">
      <div class="flex flex-wrap justify-center items-center gap-5 text-xs">
        <a href="regime.json" class="text-emerald-400 hover:text-emerald-300 underline font-medium">Public REST API (regime.json)</a>
        <span>&bull;</span>
        <a href="https://github.com/aikeluargalee-tech/btc-magnet-monitor" class="text-zinc-300 hover:text-white underline font-medium" target="_blank">Open Source Repository</a>
      </div>
      <div class="text-zinc-400">
        Automated via GitHub Actions scheduled cron &bull; Deployed on GitHub Pages CDN &bull; Zero Server Cost
      </div>
    </footer>

  </main>
</body>
</html>"""
        return html
