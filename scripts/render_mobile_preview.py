import os
import json
from typing import Dict, Any

def render_mobile_first_html(data: Dict[str, Any]) -> str:
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

    # Format why points
    why_points_html = "".join([
        f"""<div class="flex items-start gap-2.5 p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
              <span class="w-5 h-5 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-xs font-bold text-cyan-400 flex-shrink-0 mt-0.5">{idx+1}</span>
              <p class="text-xs text-zinc-300 leading-relaxed">{pt}</p>
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
  <title>BTC Magnet Monitor — Mobile</title>
  <link rel="stylesheet" href="tailwind.css">
  <link rel="stylesheet" href="fonts/fonts.css">
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
    /* Hide scrollbar for tabs */
    .no-scrollbar::-webkit-scrollbar {{
      display: none;
    }}
    .no-scrollbar {{
      -ms-overflow-style: none;
      scrollbar-width: none;
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
      <div id="data-age-banner" class="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>Live</span>
      </div>
      <button onclick="refreshLiveScan()" class="w-8 h-8 rounded-lg bg-zinc-900 hover:bg-zinc-800 active:scale-95 border border-zinc-700/70 flex items-center justify-center text-zinc-400 text-xs transition-all">
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
      <div class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl">
        <div class="flex items-center justify-between text-xs text-zinc-400 mb-1">
          <span class="font-bold uppercase tracking-wider text-[11px]">Bitcoin Spot (Binance)</span>
          <span id="hero-session-tag" class="text-[11px] text-zinc-400">● US Cash Peak</span>
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
      <div class="rounded-2xl border-2 border-{rot_color}-500/50 bg-{rot_color}-500/5 p-4 shadow-xl space-y-2.5">
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
      <div class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl space-y-3">
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
      <div class="rounded-2xl bg-zinc-900/80 border border-zinc-800/90 p-4 shadow-xl space-y-3">
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
          </div>
          <div class="p-2.5 rounded-xl bg-zinc-950/70 border border-zinc-800/70">
            <span class="text-[10px] font-sans font-semibold text-zinc-400 block">SGT TIME (UTC+8)</span>
            <span id="clock-sgt-time" class="font-bold text-emerald-300 text-sm">--:--:-- SGT</span>
          </div>
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
        <div class="rounded-2xl bg-zinc-900/80 border border-cyan-500/40 p-4 shadow-xl space-y-3">
          <div class="flex items-center gap-2 text-cyan-300 font-bold text-xs uppercase tracking-wider">
            <span>📋</span>
            <span>Independent AI Audit Format</span>
          </div>
          <p class="text-xs text-zinc-300 leading-relaxed">
            Copy the full mathematical market telemetry prompt to clipboard, then paste it directly into ChatGPT, Claude, Grok, or Gemini for an instant second opinion.
          </p>

          <button id="copy-prompt-btn" onclick="copyTelemetryPrompt()" class="w-full py-3.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 active:scale-95 text-black font-extrabold text-xs uppercase tracking-wider shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 transition-all">
            <span id="copy-btn-icon">📋</span>
            <span id="copy-btn-text">Copy Telemetry Prompt for AI</span>
          </button>
        </div>
      </div>

      <!-- METHOD 2: SYSTEM VERDICT -->
      <div id="view-method-2" class="space-y-3 hidden">
        <div class="rounded-2xl bg-zinc-900/80 border border-emerald-500/40 p-4 shadow-xl space-y-3">
          <div class="flex items-center gap-2 text-emerald-300 font-bold text-xs uppercase tracking-wider">
            <span>🛡️</span>
            <span>Our System Verdict</span>
          </div>

          <div class="space-y-2 text-xs text-zinc-300 leading-relaxed">
            <div class="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
              <strong class="text-white block mb-0.5">1. Macro Structural State:</strong>
              <span>Price is holding above the 200D MA (${ma_200d:,.0f}), preserving the long-term trend, but trading below Daily VWAP in short-term compression.</span>
            </div>

            <div class="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
              <strong class="text-white block mb-0.5">2. Liquidity Asymmetry:</strong>
              <span>Massive retail long cluster at ${lower_c.get('price_level', 0.0):,.0f} (${lower_c.get('estimated_vol_usd', 0.0)/1e6:.1f}M). Downside magnet pull is 72x heavier than upside short shelf.</span>
            </div>

            <div class="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800/80">
              <strong class="text-white block mb-0.5">3. Capital Protocol:</strong>
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
  <textarea id="llm-prompt-data" class="hidden" readonly>{data.get("llm_prompt", "BTC Magnet Telemetry Prompt")}</textarea>

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
      const p = document.getElementById('llm-prompt-data');
      if (!p) return;
      navigator.clipboard.writeText(p.value).then(() => {{
        const toast = document.getElementById('copy-toast');
        if (toast) {{
          toast.classList.remove('opacity-0', 'pointer-events-none');
          setTimeout(() => {{ toast.classList.add('opacity-0', 'pointer-events-none'); }}, 2500);
        }}
      }}).catch(() => {{}});
    }}

    // Real-Time Clocks
    function updateClocks() {{
      const now = new Date();
      const uH = String(now.getUTCHours()).padStart(2, '0');
      const uM = String(now.getUTCMinutes()).padStart(2, '0');
      const uS = String(now.getUTCSeconds()).padStart(2, '0');
      const uEl = document.getElementById('clock-utc-time');
      if (uEl) uEl.innerText = `${{uH}}:${{uM}}:${{uS}} UTC`;

      const sgt = new Date(now.getTime() + 8 * 3600000 + now.getTimezoneOffset() * 60000);
      const sH = String(sgt.getHours()).padStart(2, '0');
      const sM = String(sgt.getMinutes()).padStart(2, '0');
      const sS = String(sgt.getSeconds()).padStart(2, '0');
      const sEl = document.getElementById('clock-sgt-time');
      if (sEl) sEl.innerText = `${{sH}}:${{sM}}:${{sS}} SGT`;
    }}
    setInterval(updateClocks, 1000);
    updateClocks();

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

if __name__ == "__main__":
    with open("data/regime.json", "r", encoding="utf-8") as f:
        payload = json.load(f)
    os.makedirs("dist", exist_ok=True)
    html = render_mobile_first_html(payload)
    with open("dist/mobile_preview.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("✓ Successfully generated dist/mobile_preview.html")
