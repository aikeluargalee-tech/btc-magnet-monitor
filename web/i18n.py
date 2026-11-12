"""Multi-language (i18n) bundle & dynamic translator for BTC Magnet Monitor.

Supports 6 offline-ready UI languages across entry.html, text.html/app.html,
index.html, and regimes.html, plus Verdict 1 AI response language directives:
  - en: English
  - zh: Simplified Chinese (简体中文)
  - id: Bahasa Indonesia
  - ko: Korean (한국어)
  - ja: Japanese (日本語)
  - fr: French (Français)
"""
from __future__ import annotations

import json
from typing import Dict, Tuple


SUPPORTED_LANGS: Tuple[str, ...] = ("en", "zh", "id", "ko", "ja", "fr")

LANG_BUTTONS = [
    {"code": "en", "short": "EN", "name": "English"},
    {"code": "zh", "short": "中文", "name": "简体中文"},
    {"code": "id", "short": "ID", "name": "Bahasa Indonesia"},
    {"code": "ko", "short": "한국어", "name": "한국어"},
    {"code": "ja", "short": "日本語", "name": "日本語"},
    {"code": "fr", "short": "FR", "name": "Français"},
]

AI_PROMPT_DIRECTIVES: Dict[str, str] = {
    "en": "",
    "zh": (
        "\n\n[RESPONSE LANGUAGE DIRECTIVE]:\n"
        "Selected User Language: Simplified Chinese (简体中文).\n"
        "Please write your complete Verdict 1 analysis, key structural drivers, "
        "Loop A / Loop B plan, and risk gates in natural Simplified Chinese (简体中文). "
        "Keep exact BTC dollar levels, percentages, and raw telemetry values unchanged."
    ),
    "id": (
        "\n\n[RESPONSE LANGUAGE DIRECTIVE]:\n"
        "Selected User Language: Bahasa Indonesia.\n"
        "Please write your complete Verdict 1 analysis, key structural drivers, "
        "Loop A / Loop B plan, and risk gates in natural Bahasa Indonesia. "
        "Keep exact BTC dollar levels, percentages, and raw telemetry values unchanged."
    ),
    "ko": (
        "\n\n[RESPONSE LANGUAGE DIRECTIVE]:\n"
        "Selected User Language: Korean (한국어).\n"
        "Please write your complete Verdict 1 analysis, key structural drivers, "
        "Loop A / Loop B plan, and risk gates in natural Korean (한국어). "
        "Keep exact BTC dollar levels, percentages, and raw telemetry values unchanged."
    ),
    "ja": (
        "\n\n[RESPONSE LANGUAGE DIRECTIVE]:\n"
        "Selected User Language: Japanese (日本語).\n"
        "Please write your complete Verdict 1 analysis, key structural drivers, "
        "Loop A / Loop B plan, and risk gates in natural Japanese (日本語). "
        "Keep exact BTC dollar levels, percentages, and raw telemetry values unchanged."
    ),
    "fr": (
        "\n\n[RESPONSE LANGUAGE DIRECTIVE]:\n"
        "Selected User Language: French (Français).\n"
        "Please write your complete Verdict 1 analysis, key structural drivers, "
        "Loop A / Loop B plan, and risk gates in natural French (Français). "
        "Keep exact BTC dollar levels, percentages, and raw telemetry values unchanged."
    ),
}

# Static text & HTML keys keyed cleanly by identifier
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # Shared Header / Footer / Navigation
        "brand_sub_entry": "Liquidity Magnets • 5-Regime Radar",
        "brand_pill_entry": "BIDIRECTIONAL RADAR • LIVE MAGNET LEVELS • AI TELEMETRY",
        "brand_badge_radar": "5-Regime Radar",
        "brand_sub_desktop": "Observable Positioning Mechanics & Regime Intelligence",
        "nav_desktop_btn": "🖥️ Full Dashboard",
        "nav_mobile_btn": "📱 Mobile Terminal",
        "hdr_btc_price": "Bitcoin Price",
        "footer_monitor_terminal": "Monitor Terminal",
        "footer_regimes_math": "5 Regimes & Math",
        "footer_regimes_guide": "5 Regimes Guide",
        "footer_full_dashboard": "Full 5-Panel Dashboard",
        "footer_privacy": "Privacy Policy",
        "footer_disclaimer": "Informational market telemetry only. Not financial advice.",
        "footer_research_disclaimer": "Strictly for informational and risk research purposes. Not financial advice.",

        # Entry Page
        "entry_video1_cap": "BULL vs BEAR • ORDER-BOOK PRESSURE",
        "entry_video2_cap": "LIQUIDITY DEPTH BREAKOUT • BIDS vs ASKS",
        "sound_off": "🔇 SOUND OFF",
        "sound_on": "🔊 SOUND ON",
        "entry_enter_btn": "Enter BTC Magnet Monitor →",
        "entry_enter_sub": "Live BTC Spot Price • Order-Book Magnet Ladder • Verdict 1 vs Verdict 2",
        "entry_pm_title": "Bull vs. Bear Pressure Meter",
        "entry_pm_live_badge": "● LIVE BOOK",
        "entry_pm_bar1": "1. Order-Book Depth (±1.5%)",
        "entry_pm_bar2": "2. Aggressive Flow (24H CVD)",
        "entry_pm_bar3": "3. Crowd Leverage Skew (L/S)",
        "entry_snap_title": "Live Telemetry Snapshot",
        "entry_snap_price": "BTC Spot Price",
        "entry_snap_magnet": "Dominant Magnet",
        "entry_snap_regime": "Active Macro Regime",
        "entry_snap_scan": "Latest Radar Scan",
        "entry_snap_cadence": "Cadence: Every 30m (:02/:32 UTC)",
        "entry_v1_title": "Why & How This App Helps You",
        "entry_v1_badge": "#1 FEATURE • VERDICT 1",
        "entry_v1_intro_html": (
            'Cut through emotional noise and lagging indicators. BTC Magnet Monitor gives you raw order-book gravity, '
            'liquidity magnets, and <strong class="c-amber">1-Tap AI Telemetry</strong> before you commit size:'
        ),
        "entry_v1_step1_html": (
            '<span class="step-badge step-badge-amber">1</span>'
            '<strong class="c-amber">Verdict 1 &bull; Copy Telemetry for AI (#1 Feature):</strong> '
            'One tap copies clean, zero-bias market telemetry (closed-4H OHLCV, VWAP, OI, funding &amp; liquidity walls) '
            'into ChatGPT, Claude, Gemini, or Grok for an independent structural read.'
        ),
        "entry_v1_step2_html": (
            '<span class="step-badge">2</span>'
            '<strong class="c-cyan">Compare With Verdict 2 (Built-In Engine):</strong> '
            'Cross-check your own AI&rsquo;s Verdict 1 side-by-side against our deterministic 5-Regime Radar, '
            'Loop A / Loop B magnet levels, and risk gates.'
        ),
        "entry_v1_step3_html": (
            '<span class="step-badge">3</span>'
            '<strong class="c-green">Live Microstructure Advantage:</strong> '
            'Track real-time Bids vs. Asks pressure, Taker delta, and crowd skew across all strategies so you see '
            'where liquidity stops or squeezes before moving.'
        ),

        # Text Terminal Header & Quick Nav
        "text_header_sub": "Bidirectional Liquidity Telemetry Terminal",
        "text_mode_label": "MODE: 5-REGIME MAGNET RADAR (BIDIRECTIONAL)",
        "qnav_spot": "Spot",
        "qnav_feeds": "Feeds",
        "qnav_regime": "Regime",
        "qnav_v1": "V1 AI",
        "qnav_v2": "V2 Engine",
        "qnav_check": "↻ Check",

        # Panel Headers & Shared Sections
        "p1_title": "Panel 1 • Real-Time BTC Spot Price (Live)",
        "p2_title_text": "Panel 2 • On-Exchange Telemetry (Raw vs Modeled)",
        "p2_title_index": "Panel 2 • On-Exchange Telemetry & Modeled Pools",
        "p2_sub_index": "Real-Time Market Microstructure Feeds",
        "p2_cat1": "1. Closed 4H Structure",
        "p2_cat2": "2. Order Flow & CVD",
        "p2_cat3": "3. Derivatives Crowding",
        "p2_cat4": "4. Range & Magnets",
        "p3_title": "Panel 3 • Macro Market Regime Diagnosis",
        "p3_question": "What market environment is Bitcoin currently in?",
        "p3_sub": "Bitcoin is classified strictly into 1 of 5 deterministic regimes (or Transition / Mixed when conflicted).",
        "p3_learn_btn": "Learn About the 5 Regimes & Math",
        "p3_active_badge": "Active Market Regime",
        "p3_rule_confirm": "Rule Match Confirmation:",
        "p3_evidence_hdr": "Verified On-Exchange Evidence",
        "p3_matrix_hdr": "5-Regime Radar Framework Matrix",

        # Bridge & Verdicts
        "bridge_title_text": "Bridge • Verdict 1 vs Verdict 2",
        "bridge_badge_index": "⚖️ Bridge • Two Independent Verdicts",
        "bridge_h3_index": "Verdict 1 (Your Own AI) vs Verdict 2 (Built-In Engine)",
        "bridge_desc_index": "Panels 1–3 give you closed-bar market facts with zero advice. Generate Verdict 1 in your AI and cross-check it against Verdict 2 below.",
        "v1_hdr_text": "Verdict 1 • Your Own AI (Copy)",
        "v1_tag_index": "Verdict 1 • Your Own AI (Zero System Bias)",
        "v1_h2_index": "Generate Verdict 1 with Your Own AI",
        "v1_desc_index": "One clean export containing closed-4H market facts, modeled liquidation bands, and your optional watermarks—with Verdict 2 hidden so your AI stays 100% objective.",
        "v1_btn_text": "🧪 COPY TELEMETRY FOR AI",
        "v1_btn_index": "Copy Blind Telemetry for AI",
        "v1_wb_summary": "▸ Optional: P_buy / P_sell (Local)",
        "v1_wb_summary_index": "▸ Optional: Add P_buy / P_sell Inventory Watermarks (Local Only)",
        "v1_wb_buy_lbl": "Loop A Cost ($P_buy)",
        "v1_wb_sell_lbl": "Loop B Sale ($P_sell)",
        "v1_wb_storage": "Saved only in browser localStorage",
        "v1_wb_clear": "Clear",
        "v1_step1_title": "Copy Upgraded Blind Telemetry",
        "v1_step1_desc": "Exports closed-4H structure, CVD, OI, and modeled pools + your watermarks—without leaking Verdict 2.",
        "v1_step2_title": "Paste into Any Major LLM",
        "v1_step2_desc": "Works directly in Claude, ChatGPT, Grok, Qwen, or Gemini with bidirectional market telemetry built in.",
        "v1_step3_title": "Cross-Check Verdict 1 vs Verdict 2",
        "v1_step3_desc": "Compare your AI's independent Loop A (buy washout) & Loop B (sell squeeze) levels against Verdict 2 below.",
        "v1_preview_summary": "🧪 Preview Upgraded Blind Telemetry Prompt",
        "v1_expand_hint": "Click to expand",
        "v2_hdr_text": "Verdict 2 • Built-In Radar Engine",
        "v2_tag_index": "Verdict 2 • Built-In Radar Engine",
        "v2_h2_index": "Built-In System Verdict",
        "v2_desc_index": "Closed-4H deterministic regime call, Loop A & Loop B magnet zones, symmetric LSCE sweep/squeeze gate, 10x–100x modeled heatmap, and bidirectional swing hold rules.",
        "v2_reminder_title": "Always Generate Verdict 1 (Your AI) & Compare:",
        "v2_reminder_desc": "Verdict 2 is a fixed deterministic rule baseline. Copy Verdict 1 into your own AI for deeper context and compare both verdicts.",
        "v2_reminder_link": "↑ Compare via Verdict 1",
        "v2_why_title": "Why This Bidirectional Call?",
        "v2_factors_hdr": "The 3 Key Market Factors Driving This Call",
        "v2_sizing_hdr": "Bidirectional Sizing & Patience",
        "v2_patience_hdr": "Risk Gates & Patience Rules",
        "v2_lsce_hdr": "Bidirectional Liquidation Sweep Engine (LSCE • Closed 4H)",
        "v2_upper_pool": "Upper Short Pool (Loop B Target)",
        "v2_lower_pool": "Lower Long Pool (Loop A Target)",

        # Regimes Guide
        "reg_badge": "Bidirectional Radar Architecture • Observable Positioning Mechanics",
        "reg_h1": "5-Regime Radar & Bidirectional Liquidity Protocol",
        "reg_intro": "How the Bidirectional Protocol maps closed-4H liquidity magnets, positioning skew, and two-sided liquidity reserves across all five market regimes.",
        "reg_back_live": "← Back to Live Monitor",
        "reg_return_live": "← Return to Live BTC Magnet Monitor",
        "reg_sec1_h2": "1. Core Philosophy: Bidirectional Liquidity & Risk Gates",
        "reg_sec2_h2": "2. How the Closed-4H Majority-Voting Engine Works",
        "reg_sec3_h2": "3. The 5 Market Regimes + Bidirectional Triggers",
        "reg_sec4_h2": "4. Modeled Liquidation Pool & Closed-4H Scaling Methodology",
        "reg_sec5_h2": "5. Bidirectional LSCE State Machine & Gate Rules",

        # Dynamic Status & Toasts
        "toast_copied_v1": "✓ Copied Verdict 1 AI Telemetry!",
        "toast_cleared_wb": "✓ Local watermarks cleared",
        "age_banner_live": "LIVE SPOT FEED ACTIVE",
    },
    "zh": {
        "brand_sub_entry": "流动性磁铁 • 五态市场雷达",
        "brand_pill_entry": "双向磁铁雷达 • 实时流动水位 • AI 客观遥测",
        "brand_badge_radar": "五态雷达",
        "brand_sub_desktop": "可观测持仓机制与多维市场状态研判",
        "nav_desktop_btn": "🖥️ 完整看板",
        "nav_mobile_btn": "📱 移动终端",
        "hdr_btc_price": "比特币现价",
        "footer_monitor_terminal": "监控终端",
        "footer_regimes_math": "五态模型与算法",
        "footer_regimes_guide": "五态指南",
        "footer_full_dashboard": "完整五面板看板",
        "footer_privacy": "隐私政策",
        "footer_disclaimer": "仅作市场结构遥测参考，不构成投资建议。",
        "footer_research_disclaimer": "仅供信息展示与风险研究使用，不构成任何投资建议。",

        "entry_video1_cap": "多空博弈 • 盘口挂单压力",
        "entry_video2_cap": "深度突破 • 买盘 vs 卖盘流动性",
        "sound_off": "🔇 静音",
        "sound_on": "🔊 开启声音",
        "entry_enter_btn": "进入 BTC Magnet 监控终端 →",
        "entry_enter_sub": "BTC 实时现价 • 订单簿磁铁阶梯 • 结论一 vs 结论二",
        "entry_pm_title": "多空实时压力仪表",
        "entry_pm_live_badge": "● 实时盘口",
        "entry_pm_bar1": "1. 盘口深度 (±1.5%)",
        "entry_pm_bar2": "2. 主动成交净流 (24H CVD)",
        "entry_pm_bar3": "3. 全网多空拥挤度 (L/S)",
        "entry_snap_title": "实时遥测快照",
        "entry_snap_price": "BTC 实时现货价",
        "entry_snap_magnet": "主导流动性磁铁",
        "entry_snap_regime": "当前宏观状态",
        "entry_snap_scan": "最新雷达扫描",
        "entry_snap_cadence": "扫描频率：每 30 分钟 (:02/:32 UTC)",
        "entry_v1_title": "本应用如何帮到您",
        "entry_v1_badge": "核心功能 • 结论一 AI",
        "entry_v1_intro_html": (
            '摆脱情绪噪音与滞后指标。BTC Magnet Monitor 为您提供真实的盘口引力分布、清算磁铁与'
            '<strong class="c-amber">一键 AI 客观遥测</strong>，助您在下单前看清结构：'
        ),
        "entry_v1_step1_html": (
            '<span class="step-badge step-badge-amber">1</span>'
            '<strong class="c-amber">结论一 &bull; 一键复制遥测给 AI（核心功能）：</strong>'
            '一键复制零偏见的客观行情数据（已收盘 4H K线、VWAP、OI 持仓、资金费率与盘口挂单墙），直接粘贴进 ChatGPT、Claude、Gemini 或 Grok 获取独立结构评估。'
        ),
        "entry_v1_step2_html": (
            '<span class="step-badge">2</span>'
            '<strong class="c-cyan">对照结论二（内置规则引擎）：</strong>'
            '将您自己 AI 给出的结论一，与系统内置的五态雷达、Loop A / Loop B 磁铁触发区及风控闸门并排验证。'
        ),
        "entry_v1_step3_html": (
            '<span class="step-badge">3</span>'
            '<strong class="c-green">实时微观结构优势：</strong>'
            '实时监测买盘 vs 卖盘厚度、主动吃单差值及多空拥挤斜率，无论任何交易策略，先看清流动性止损与挤压位置再行动。'
        ),

        "text_header_sub": "双向流动性磁铁遥测终端",
        "text_mode_label": "模式：五态磁铁雷达（双向观察）",
        "qnav_spot": "现价",
        "qnav_feeds": "数据源",
        "qnav_regime": "状态",
        "qnav_v1": "结论一 AI",
        "qnav_v2": "结论二",
        "qnav_check": "↻ 刷新",

        "p1_title": "面板 1 • BTC 实时现货价格 (Live)",
        "p2_title_text": "面板 2 • 交易所微观遥测（原始 vs 估算）",
        "p2_title_index": "面板 2 • 交易所微观遥测与估算清算池",
        "p2_sub_index": "实时市场微观结构数据流",
        "p2_cat1": "1. 已收盘 4H 结构",
        "p2_cat2": "2. 订单流与 CVD",
        "p2_cat3": "3. 合约拥挤度",
        "p2_cat4": "4. 振幅与磁铁分布",
        "p3_title": "面板 3 • 宏观市场状态诊断",
        "p3_question": "当前比特币处于哪种市场环境？",
        "p3_sub": "系统严格将行情划分为 5 种确定性状态之一（指标冲突时归入过渡/混合态）。",
        "p3_learn_btn": "查看五态模型与数学原理",
        "p3_active_badge": "当前市场状态",
        "p3_rule_confirm": "规则匹配确认：",
        "p3_evidence_hdr": "已验证链上/交易所规则证据",
        "p3_matrix_hdr": "五态雷达分类矩阵",

        "bridge_title_text": "桥接 • 结论一 vs 结论二",
        "bridge_badge_index": "⚖️ 桥接 • 双独立研判对照",
        "bridge_h3_index": "结论一（您的 AI）vs 结论二（内置引擎）",
        "bridge_desc_index": "面板 1-3 仅呈现无偏见的客观已收盘数据。先用您自己的 AI 生成结论一，再与下方系统结论二交叉核对。",
        "v1_hdr_text": "结论一 • 复制给您的 AI",
        "v1_tag_index": "结论一 • 您的专属 AI（零系统偏见）",
        "v1_h2_index": "使用您的 AI 生成结论一",
        "v1_desc_index": "一键导出已收盘 4H 事实、估算清算带与可选成本水位——结论二完全隐藏，确保您的 AI 保持 100% 客观。",
        "v1_btn_text": "🧪 一键复制遥测给 AI",
        "v1_btn_index": "复制客观遥测提示词给 AI",
        "v1_wb_summary": "▸ 可选：填入 P_buy / P_sell 水位（仅存本地）",
        "v1_wb_summary_index": "▸ 可选：填入 P_buy / P_sell 持仓参考价（仅存本地）",
        "v1_wb_buy_lbl": "Loop A 买入价 ($P_buy)",
        "v1_wb_sell_lbl": "Loop B 卖出价 ($P_sell)",
        "v1_wb_storage": "仅保存在本设备 localStorage",
        "v1_wb_clear": "清除",
        "v1_step1_title": "复制客观盲测遥测",
        "v1_step1_desc": "导出已收盘 4H 结构、CVD、OI 与估算清算池数据（含可选参考价），绝不泄露结论二。",
        "v1_step2_title": "粘贴至任意主流 AI",
        "v1_step2_desc": "直接兼容 Claude、ChatGPT、Grok、通义千问或 Gemini，内置完整双向市场遥测上下文。",
        "v1_step3_title": "对比结论一与结论二",
        "v1_step3_desc": "将 AI 给出的独立 Loop A（下洗买点）与 Loop B（挤压卖点）同下方内置引擎对照确认。",
        "v1_preview_summary": "🧪 预览即将复制给 AI 的完整遥测词",
        "v1_expand_hint": "点击展开",
        "v2_hdr_text": "结论二 • 内置雷达引擎",
        "v2_tag_index": "结论二 • 内置雷达引擎",
        "v2_h2_index": "系统内置诊断结论",
        "v2_desc_index": "基于已收盘 4H 确定性状态、Loop A/B 磁铁区间、LSCE 双向扫荡确认闸门与 10x–100x 清算热力图。",
        "v2_reminder_title": "建议始终先生成结论一（您的 AI）再对照：",
        "v2_reminder_desc": "结论二仅作固定规则基线。先将结论一复制给您的 AI 深度推理，双结论共振时把握更高。",
        "v2_reminder_link": "↑ 回到结论一（复制给 AI）",
        "v2_why_title": "为何给出当前双向判断？",
        "v2_factors_hdr": "驱动本次判断的 3 项核心市场因子",
        "v2_sizing_hdr": "双向仓位节奏与耐心纪律",
        "v2_patience_hdr": "风控闸门与持有纪律",
        "v2_lsce_hdr": "双向流动性扫荡确认引擎（LSCE • 已收盘 4H）",
        "v2_upper_pool": "上方空头清算池（Loop B 目标）",
        "v2_lower_pool": "下方多头清算池（Loop A 目标）",

        "reg_badge": "双向雷达架构 • 可观测持仓与流动性机制",
        "reg_h1": "五态市场雷达与双向流动性协议",
        "reg_intro": "详解双向协议如何结合已收盘 4H 流动性磁铁、仓位拥挤斜率与双边储备应对五类市场阶段。",
        "reg_back_live": "← 返回实时监控面板",
        "reg_return_live": "← 返回 BTC Magnet 实时监控",
        "reg_sec1_h2": "1. 核心理念：双向流动性与风控确认闸门",
        "reg_sec2_h2": "2. 已收盘 4H 多数投票引擎如何运行",
        "reg_sec3_h2": "3. 五类市场状态与双向触发机制",
        "reg_sec4_h2": "4. 清算池估算与已收盘 4H 尺度模型说明",
        "reg_sec5_h2": "5. 双向 LSCE 状态机与确认规则",

        "toast_copied_v1": "✓ 已复制结论一 AI 遥测（AI 将用简体中文回复）",
        "toast_cleared_wb": "✓ 已清除本地参考价",
        "age_banner_live": "实时现货数据流运行中",
    },
    "id": {
        "brand_sub_entry": "Magnet Likuiditas • Radar 5-Regime",
        "brand_pill_entry": "RADAR DUA ARAH • LEVEL MAGNET LIVE • TELEMETRI AI",
        "brand_badge_radar": "Radar 5-Regime",
        "brand_sub_desktop": "Mekanik Posisi Terobservasi & Intelijen Regime",
        "nav_desktop_btn": "🖥️ Dashboard Lengkap",
        "nav_mobile_btn": "📱 Terminal Mobile",
        "hdr_btc_price": "Harga Bitcoin",
        "footer_monitor_terminal": "Terminal Monitor",
        "footer_regimes_math": "5 Regime & Rumus",
        "footer_regimes_guide": "Panduan 5 Regime",
        "footer_full_dashboard": "Dashboard 5 Panel",
        "footer_privacy": "Kebijakan Privasi",
        "footer_disclaimer": "Hanya telemetri pasar informasional. Bukan saran keuangan.",
        "footer_research_disclaimer": "Khusus untuk tujuan informasi dan riset risiko. Bukan nasihat keuangan.",

        "entry_video1_cap": "BULL vs BEAR • TEKANAN ORDER-BOOK",
        "entry_video2_cap": "BREAKOUT KEDALAMAN • BIDS vs ASKS",
        "sound_off": "🔇 SUARA MATI",
        "sound_on": "🔊 SUARA AKTIF",
        "entry_enter_btn": "Masuk ke BTC Magnet Monitor →",
        "entry_enter_sub": "Harga Spot BTC Live • Tangga Magnet Order-Book • Verdict 1 vs Verdict 2",
        "entry_pm_title": "Meter Tekanan Bull vs. Bear",
        "entry_pm_live_badge": "● BUKU LIVE",
        "entry_pm_bar1": "1. Kedalaman Order-Book (±1.5%)",
        "entry_pm_bar2": "2. Arus Agresif (CVD 24J)",
        "entry_pm_bar3": "3. Kemiringan Leverage Crowd (L/S)",
        "entry_snap_title": "Snapshot Telemetri Live",
        "entry_snap_price": "Harga Spot BTC",
        "entry_snap_magnet": "Magnet Dominan",
        "entry_snap_regime": "Regime Makro Aktif",
        "entry_snap_scan": "Pemindaian Radar Terbaru",
        "entry_snap_cadence": "Jadwal: Setiap 30m (:02/:32 UTC)",
        "entry_v1_title": "Mengapa & Bagaimana Aplikasi Ini Membantu Anda",
        "entry_v1_badge": "FITUR #1 • VERDICT 1",
        "entry_v1_intro_html": (
            'Singkirkan gangguan emosi dan indikator lambat. BTC Magnet Monitor memberi Anda gravitasi order-book asli, '
            'magnet likuiditas, dan <strong class="c-amber">Telemetri AI 1-Ketuk</strong> sebelum Anda mengambil posisi:'
        ),
        "entry_v1_step1_html": (
            '<span class="step-badge step-badge-amber">1</span>'
            '<strong class="c-amber">Verdict 1 &bull; Salin Telemetri untuk AI (Fitur #1):</strong> '
            'Satu ketuk menyalin data pasar bersih bebas bias (4H tertutup, VWAP, OI, funding &amp; dinding likuiditas) '
            'ke ChatGPT, Claude, Gemini, atau Grok untuk analisis struktural independen.'
        ),
        "entry_v1_step2_html": (
            '<span class="step-badge">2</span>'
            '<strong class="c-cyan">Bandingkan dengan Verdict 2 (Mesin Bawaan):</strong> '
            'Cocokkan Verdict 1 dari AI Anda berdampingan dengan Radar 5-Regime deterministik, '
            'level magnet Loop A / Loop B, dan gerbang risiko.'
        ),
        "entry_v1_step3_html": (
            '<span class="step-badge">3</span>'
            '<strong class="c-green">Keunggulan Mikrostruktur Live:</strong> '
            'Pantau tekanan Bids vs. Asks real-time, delta taker, dan kemiringan crowd agar Anda melihat area '
            'likuiditas berhenti atau squeeze sebelum bergerak.'
        ),

        "text_header_sub": "Terminal Telemetri Likuiditas Dua Arah",
        "text_mode_label": "MODE: RADAR MAGNET 5-REGIME (DUA ARAH)",
        "qnav_spot": "Spot",
        "qnav_feeds": "Data",
        "qnav_regime": "Regime",
        "qnav_v1": "V1 AI",
        "qnav_v2": "V2 Mesin",
        "qnav_check": "↻ Cek",

        "p1_title": "Panel 1 • Harga Spot BTC Real-Time (Live)",
        "p2_title_text": "Panel 2 • Telemetri Bursa (Mentah vs Model)",
        "p2_title_index": "Panel 2 • Telemetri Bursa & Pool Likuiditas",
        "p2_sub_index": "Feed Mikrostruktur Pasar Real-Time",
        "p2_cat1": "1. Struktur 4H Tertutup",
        "p2_cat2": "2. Arus Order & CVD",
        "p2_cat3": "3. Posisi Derivatif",
        "p2_cat4": "4. Rentang & Magnet",
        "p3_title": "Panel 3 • Diagnosis Regime Makro Pasar",
        "p3_question": "Bitcoin sedang berada di lingkungan pasar apa saat ini?",
        "p3_sub": "Bitcoin diklasifikasikan ketat ke dalam 1 dari 5 regime deterministik (atau Transisi / Campuran bila berkonflik).",
        "p3_learn_btn": "Pelajari 5 Regime & Matematika",
        "p3_active_badge": "Regime Pasar Aktif",
        "p3_rule_confirm": "Konfirmasi Kecocokan Aturan:",
        "p3_evidence_hdr": "Bukti On-Exchange Terverifikasi",
        "p3_matrix_hdr": "Matriks Kerangka Radar 5-Regime",

        "bridge_title_text": "Jembatan • Verdict 1 vs Verdict 2",
        "bridge_badge_index": "⚖️ Jembatan • Dua Vonis Independen",
        "bridge_h3_index": "Verdict 1 (AI Anda) vs Verdict 2 (Mesin Bawaan)",
        "bridge_desc_index": "Panel 1–3 hanya menyajikan fakta pasar bar tertutup tanpa saran. Hasilkan Verdict 1 di AI Anda lalu bandingkan dengan Verdict 2 di bawah.",
        "v1_hdr_text": "Verdict 1 • AI Anda Sendiri (Salin)",
        "v1_tag_index": "Verdict 1 • AI Anda (Bebas Bias Sistem)",
        "v1_h2_index": "Hasilkan Verdict 1 dengan AI Anda Sendiri",
        "v1_desc_index": "Ekspor bersih fakta 4H tertutup, pita likuidasi model, dan watermark opsional—dengan Verdict 2 disembunyikan agar AI tetap 100% objektif.",
        "v1_btn_text": "🧪 SALIN TELEMETRI UNTUK AI",
        "v1_btn_index": "Salin Telemetri Netral untuk AI",
        "v1_wb_summary": "▸ Opsional: Harga P_buy / P_sell (Lokal)",
        "v1_wb_summary_index": "▸ Opsional: Tambah Watermark P_buy / P_sell (Lokal Saja)",
        "v1_wb_buy_lbl": "Harga Beli Loop A ($P_buy)",
        "v1_wb_sell_lbl": "Harga Jual Loop B ($P_sell)",
        "v1_wb_storage": "Hanya disimpan di localStorage browser",
        "v1_wb_clear": "Hapus",
        "v1_step1_title": "Salin Telemetri Netral Terbaru",
        "v1_step1_desc": "Mengekspor struktur 4H, CVD, OI, dan pool model + watermark Anda—tanpa membocorkan Verdict 2.",
        "v1_step2_title": "Tempel ke LLM Mana Saja",
        "v1_step2_desc": "Bekerja langsung di Claude, ChatGPT, Grok, Qwen, atau Gemini dengan konteks pasar dua arah bawaan.",
        "v1_step3_title": "Silang-Cek Verdict 1 vs Verdict 2",
        "v1_step3_desc": "Bandingkan level independen Loop A (beli sapuan bawah) & Loop B (jual squeeze atas) dari AI Anda dengan Verdict 2.",
        "v1_preview_summary": "🧪 Pratinjau Prompt Telemetri AI",
        "v1_expand_hint": "Klik untuk buka",
        "v2_hdr_text": "Verdict 2 • Mesin Radar Bawaan",
        "v2_tag_index": "Verdict 2 • Mesin Radar Bawaan",
        "v2_h2_index": "Vonis Sistem Bawaan",
        "v2_desc_index": "Klasifikasi 4H deterministik, zona magnet Loop A & Loop B, gerbang konfirmasi sapuan LSCE, dan peta panas 10x–100x.",
        "v2_reminder_title": "Selalu Hasilkan Verdict 1 (AI Anda) & Bandingkan:",
        "v2_reminder_desc": "Verdict 2 adalah tolok ukur aturan tetap. Salin Verdict 1 ke AI Anda untuk analisis konteks lebih dalam.",
        "v2_reminder_link": "↑ Bandingkan lewat Verdict 1",
        "v2_why_title": "Mengapa Sinyal Dua Arah Ini?",
        "v2_factors_hdr": "3 Faktor Pasar Utama Penggerak Sinyal",
        "v2_sizing_hdr": "Ukuran Posisi & Kesabaran Dua Arah",
        "v2_patience_hdr": "Gerbang Risiko & Aturan Kesabaran",
        "v2_lsce_hdr": "Mesin Konfirmasi Sapuan Likuiditas (LSCE • 4H Tertutup)",
        "v2_upper_pool": "Pool Short Atas (Target Loop B)",
        "v2_lower_pool": "Pool Long Bawah (Target Loop A)",

        "reg_badge": "Arsitektur Radar Dua Arah • Mekanik Posisi Terobservasi",
        "reg_h1": "Radar 5-Regime & Protokol Likuiditas Dua Arah",
        "reg_intro": "Bagaimana Protokol Dua Arah memetakan magnet likuiditas 4H tertutup, kemiringan posisi, dan cadangan dua sisi di kelima regime pasar.",
        "reg_back_live": "← Kembali ke Monitor Live",
        "reg_return_live": "← Kembali ke BTC Magnet Monitor",
        "reg_sec1_h2": "1. Filosofi Inti: Likuiditas Dua Arah & Gerbang Risiko",
        "reg_sec2_h2": "2. Cara Kerja Mesin Pemungutan Suara Mayoritas 4H",
        "reg_sec3_h2": "3. 5 Regime Pasar & Pemicu Dua Arah",
        "reg_sec4_h2": "4. Metodologi Model Pool Likuiditas & Skala 4H",
        "reg_sec5_h2": "5. Mesin Status LSCE & Aturan Gerbang",

        "toast_copied_v1": "✓ Telemetri AI Verdict 1 disalin (AI menjawab Bahasa Indonesia)",
        "toast_cleared_wb": "✓ Watermark lokal dibersihkan",
        "age_banner_live": "FEED SPOT LIVE AKTIF",
    },
    "ko": {
        "brand_sub_entry": "유동성 마그넷 • 5국면 레이더",
        "brand_pill_entry": "양방향 레이더 • 실시간 마그넷 레벨 • AI 텔레메트리",
        "brand_badge_radar": "5국면 레이더",
        "brand_sub_desktop": "관측 가능한 포지셔닝 역학 및 시장 국면 인텔리전스",
        "nav_desktop_btn": "🖥️ 전체 대시보드",
        "nav_mobile_btn": "📱 모바일 터미널",
        "hdr_btc_price": "비트코인 현재가",
        "footer_monitor_terminal": "모니터 터미널",
        "footer_regimes_math": "5국면 & 수식",
        "footer_regimes_guide": "5국면 가이드",
        "footer_full_dashboard": "전체 5패널 대시보드",
        "footer_privacy": "개인정보처리방침",
        "footer_disclaimer": "정보 제공 목적의 시장 텔레메트리이며 투자 조언이 아닙니다.",
        "footer_research_disclaimer": "정보 및 리스크 연구 목적 전용입니다. 투자 자문이 아닙니다.",

        "entry_video1_cap": "매수 vs 매도 • 호가창 압력",
        "entry_video2_cap": "유동성 깊이 돌파 • 매수벽 vs 매도벽",
        "sound_off": "🔇 음소거",
        "sound_on": "🔊 사운드 켜짐",
        "entry_enter_btn": "BTC Magnet 모니터 입장 →",
        "entry_enter_sub": "BTC 실시간 현물가 • 호가 마그넷 래더 • Verdict 1 vs Verdict 2",
        "entry_pm_title": "매수 vs 매도 실시간 압력 게이지",
        "entry_pm_live_badge": "● 실시간 호가",
        "entry_pm_bar1": "1. 호가창 깊이 (±1.5%)",
        "entry_pm_bar2": "2. 공격적 체결 흐름 (24H CVD)",
        "entry_pm_bar3": "3. 군중 쏠림 비율 (L/S)",
        "entry_snap_title": "실시간 텔레메트리 스냅샷",
        "entry_snap_price": "BTC 현물 가격",
        "entry_snap_magnet": "주요 유동성 마그넷",
        "entry_snap_regime": "현재 거시 국면",
        "entry_snap_scan": "최신 레이더 스캔",
        "entry_snap_cadence": "갱신 주기: 매 30분 (:02/:32 UTC)",
        "entry_v1_title": "이 앱이 트레이딩에 주는 도움",
        "entry_v1_badge": "핵심 기능 #1 • VERDICT 1",
        "entry_v1_intro_html": (
            '감정적 노이즈와 후행 지표를 걸러내세요. BTC Magnet Monitor는 포지션 진입 전 실제 호가 중력, '
            '유동성 마그넷, 그리고 <strong class="c-amber">원터치 AI 텔레메트리</strong>를 제공합니다:'
        ),
        "entry_v1_step1_html": (
            '<span class="step-badge step-badge-amber">1</span>'
            '<strong class="c-amber">Verdict 1 &bull; AI용 텔레메트리 복사 (핵심 #1):</strong> '
            '한 번의 탭으로 편향 없는 순수 시장 데이터(마감된 4H 봉, VWAP, OI, 펀딩비, 유동성 벽)를 복사해 '
            'ChatGPT, Claude, Gemini, Grok에서 독립적인 구조 분석을 받으세요.'
        ),
        "entry_v1_step2_html": (
            '<span class="step-badge">2</span>'
            '<strong class="c-cyan">Verdict 2(내장 엔진)와 교차 검증:</strong> '
            '내 AI가 내놓은 Verdict 1을 내장 5국면 레이더, Loop A / Loop B 마그넷 구간 및 리스크 게이트와 나란히 대조하세요.'
        ),
        "entry_v1_step3_html": (
            '<span class="step-badge">3</span>'
            '<strong class="c-green">실시간 미시구조 우위:</strong> '
            '어떤 매매 전략을 쓰든 움직이기 전에 실시간 매수벽 vs 매도벽 힘, 체결 델타, L/S 쏠림을 먼저 확인하세요.'
        ),

        "text_header_sub": "양방향 유동성 텔레메트리 터미널",
        "text_mode_label": "모드: 5국면 마그넷 레이더 (양방향)",
        "qnav_spot": "현물",
        "qnav_feeds": "피드",
        "qnav_regime": "국면",
        "qnav_v1": "V1 AI",
        "qnav_v2": "V2 엔진",
        "qnav_check": "↻ 새로고침",

        "p1_title": "패널 1 • 실시간 BTC 현물 가격 (Live)",
        "p2_title_text": "패널 2 • 거래소 텔레메트리 (원본 vs 추정)",
        "p2_title_index": "패널 2 • 거래소 텔레메트리 & 추정 청산 풀",
        "p2_sub_index": "실시간 시장 미시구조 데이터 피드",
        "p2_cat1": "1. 마감 4H 구조",
        "p2_cat2": "2. 주문 흐름 & CVD",
        "p2_cat3": "3. 파생상품 쏠림",
        "p2_cat4": "4. 변동폭 & 마그넷",
        "p3_title": "패널 3 • 거시 시장 국면 진단",
        "p3_question": "현재 비트코인은 어떤 시장 국면에 있습니까?",
        "p3_sub": "비트코인은 5가지 결정론적 국면 중 하나(또는 지표 충돌 시 전환/혼합)로 엄격히 분류됩니다.",
        "p3_learn_btn": "5국면 모델 & 수식 보기",
        "p3_active_badge": "활성 시장 국면",
        "p3_rule_confirm": "규칙 일치 확인:",
        "p3_evidence_hdr": "검증된 거래소 근거 체크리스트",
        "p3_matrix_hdr": "5국면 레이더 프레임워크 매트릭스",

        "bridge_title_text": "브리지 • Verdict 1 vs Verdict 2",
        "bridge_badge_index": "⚖️ 브리지 • 두 가지 독립 판정",
        "bridge_h3_index": "Verdict 1 (내 AI 판정) vs Verdict 2 (내장 엔진)",
        "bridge_desc_index": "패널 1–3은 조언 없이 마감된 객관적 사실만 보여줍니다. 내 AI로 Verdict 1을 생성한 뒤 아래 Verdict 2와 교차 확인하세요.",
        "v1_hdr_text": "Verdict 1 • 내 AI로 분석 (복사)",
        "v1_tag_index": "Verdict 1 • 나만의 AI (시스템 편향 제로)",
        "v1_h2_index": "내 AI로 Verdict 1 생성하기",
        "v1_desc_index": "마감 4H 데이터, 모델링된 청산 구간, 선택적 기준가를 한 번에 복사합니다. Verdict 2는 숨겨져 AI가 100% 객관적으로 판단합니다.",
        "v1_btn_text": "🧪 AI용 텔레메트리 복사",
        "v1_btn_index": "AI용 블라인드 텔레메트리 복사",
        "v1_wb_summary": "▸ 선택사항: P_buy / P_sell 기준가 (로컬 저장)",
        "v1_wb_summary_index": "▸ 선택사항: P_buy / P_sell 보유 기준가 입력 (기기 내 저장)",
        "v1_wb_buy_lbl": "Loop A 매수가 ($P_buy)",
        "v1_wb_sell_lbl": "Loop B 매도가 ($P_sell)",
        "v1_wb_storage": "브라우저 localStorage에만 저장됨",
        "v1_wb_clear": "초기화",
        "v1_step1_title": "블라인드 텔레메트리 복사",
        "v1_step1_desc": "Verdict 2 노출 없이 마감 4H 구조, CVD, OI, 모델링 청산 풀 + 개인 기준가를 내보냅니다.",
        "v1_step2_title": "주요 AI에 바로 붙여넣기",
        "v1_step2_desc": "Claude, ChatGPT, Grok, Qwen, Gemini 어디서나 양방향 시장 컨텍스트와 함께 바로 동작합니다.",
        "v1_step3_title": "Verdict 1 vs Verdict 2 대조",
        "v1_step3_desc": "AI가 도출한 Loop A(하단 스윕 매수) 및 Loop B(상단 스퀴즈 매도) 구간을 아래 Verdict 2와 비교하세요.",
        "v1_preview_summary": "🧪 복사될 AI 블라인드 프롬프트 미리보기",
        "v1_expand_hint": "클릭하여 펼치기",
        "v2_hdr_text": "Verdict 2 • 내장 레이더 엔진",
        "v2_tag_index": "Verdict 2 • 내장 레이더 엔진",
        "v2_h2_index": "내장 시스템 판정",
        "v2_desc_index": "마감 4H 기반 국면 진단, Loop A & Loop B 마그넷 존, 대칭 LSCE 스윕 게이트 및 10x–100x 히트맵을 제공합니다.",
        "v2_reminder_title": "항상 Verdict 1(내 AI)을 먼저 생성하고 비교하세요:",
        "v2_reminder_desc": "Verdict 2는 고정 규칙 기준선입니다. Verdict 1을 AI에 붙여넣어 심층 해석을 함께 확인하세요.",
        "v2_reminder_link": "↑ Verdict 1로 이동 (AI 복사)",
        "v2_why_title": "이번 양방향 판단의 근거",
        "v2_factors_hdr": "판정을 이끈 3가지 핵심 시장 요인",
        "v2_sizing_hdr": "양방향 비중 조절 & 인내 규칙",
        "v2_patience_hdr": "리스크 게이트 & 보유 규율",
        "v2_lsce_hdr": "양방향 청산 스윕 확인 엔진 (LSCE • 마감 4H)",
        "v2_upper_pool": "상단 숏 청산 풀 (Loop B 목표)",
        "v2_lower_pool": "하단 롱 청산 풀 (Loop A 목표)",

        "reg_badge": "양방향 레이더 아키텍처 • 관측 가능한 포지셔닝 역학",
        "reg_h1": "5국면 레이더 & 양방향 유동성 프로토콜",
        "reg_intro": "양방향 프로토콜이 5가지 시장 국면 전반에서 마감 4H 유동성 마그넷과 포지션 쏠림을 해석하는 방식입니다.",
        "reg_back_live": "← 실시간 모니터로 돌아가기",
        "reg_return_live": "← BTC Magnet 모니터로 돌아가기",
        "reg_sec1_h2": "1. 핵심 철학: 양방향 유동성 & 리스크 게이트",
        "reg_sec2_h2": "2. 마감 4H 다수결 투표 엔진 작동 방식",
        "reg_sec3_h2": "3. 5가지 시장 국면 + 양방향 트리거",
        "reg_sec4_h2": "4. 추정 청산 풀 & 마감 4H 스케일링 방법론",
        "reg_sec5_h2": "5. 양방향 LSCE 상태 머신 & 게이트 규칙",

        "toast_copied_v1": "✓ Verdict 1 AI 텔레메트리 복사됨 (한국어 응답 지시 포함)",
        "toast_cleared_wb": "✓ 로컬 기준가가 초기화되었습니다",
        "age_banner_live": "실시간 현물 피드 가동 중",
    },
    "ja": {
        "brand_sub_entry": "流動性マグネット • 5レジームレーダー",
        "brand_pill_entry": "双方向レーダー • リアルタイム磁石帯 • AIテレメトリ",
        "brand_badge_radar": "5レジームレーダー",
        "brand_sub_desktop": "観測可能なポジション構造と相場レジーム分析",
        "nav_desktop_btn": "🖥️ フルダッシュボード",
        "nav_mobile_btn": "📱 モバイル端末",
        "hdr_btc_price": "ビットコイン現物価格",
        "footer_monitor_terminal": "モニター端末",
        "footer_regimes_math": "5レジームと数理",
        "footer_regimes_guide": "5レジーム解説",
        "footer_full_dashboard": "5パネル画面へ",
        "footer_privacy": "プライバシーポリシー",
        "footer_disclaimer": "情報提供目的の市場テレメトリであり、投資助言ではありません。",
        "footer_research_disclaimer": "情報・リスク研究用途専用です。投資助言ではありません。",

        "entry_video1_cap": "ブル vs ベア • 板オーダー圧力",
        "entry_video2_cap": "板厚ブレイクアウト • 買い板 vs 売り板",
        "sound_off": "🔇 ミュート中",
        "sound_on": "🔊 音声オン",
        "entry_enter_btn": "BTC Magnet モニターへ進む →",
        "entry_enter_sub": "BTC リアルタイム現物 • 板マグネット梯子 • Verdict 1 vs Verdict 2",
        "entry_pm_title": "ブル vs ベア リアルタイム圧力メーター",
        "entry_pm_live_badge": "● LIVE 板情報",
        "entry_pm_bar1": "1. 板デプス比較 (±1.5%)",
        "entry_pm_bar2": "2. 成行フロー推移 (24H CVD)",
        "entry_pm_bar3": "3. 群集偏り (L/S比率)",
        "entry_snap_title": "リアルタイム・テレメトリ概要",
        "entry_snap_price": "BTC 現物価格",
        "entry_snap_magnet": "優勢マグネット",
        "entry_snap_regime": "現在のマクロ局面",
        "entry_snap_scan": "最新レーダースキャン",
        "entry_snap_cadence": "更新頻度：30分ごと (:02/:32 UTC)",
        "entry_v1_title": "このアプリがあなたをどう助けるか",
        "entry_v1_badge": "主力機能 #1 • VERDICT 1",
        "entry_v1_intro_html": (
            '感情的なノイズや遅行指標に振り回されないために。BTC Magnet Monitor はポジション判断の前に、'
            '板の引力・流動性マグネット・<strong class="c-amber">ワンタップ AI テレメトリ</strong>を届けます：'
        ),
        "entry_v1_step1_html": (
            '<span class="step-badge step-badge-amber">1</span>'
            '<strong class="c-amber">Verdict 1 &bull; AI向けテレメトリコピー（主力機能）：</strong> '
            'ワンタップでバイアスゼロの確定4H足データ・VWAP・OI・資金調達率・板厚をコピーし、'
            'ChatGPT / Claude / Gemini / Grok に貼るだけで中立的な構造診断を得られます。'
        ),
        "entry_v1_step2_html": (
            '<span class="step-badge">2</span>'
            '<strong class="c-cyan">Verdict 2（内蔵エンジン）と突き合わせ：</strong> '
            'あなたのAIが出した Verdict 1 を、決定論的5レジームレーダーや Loop A / Loop B 水準・リスクゲートと並べて検証できます。'
        ),
        "entry_v1_step3_html": (
            '<span class="step-badge">3</span>'
            '<strong class="c-green">リアルタイム板構造の優位性：</strong> '
            'どの手法であっても、動く前にリアルタイムの買い板 vs 売り板、成行デルタ、ロング/ショートの偏りを一目で把握できます。'
        ),

        "text_header_sub": "双方向流動性テレメトリ端末",
        "text_mode_label": "モード：5レジーム・マグネットレーダー（双方向）",
        "qnav_spot": "現物",
        "qnav_feeds": "データ",
        "qnav_regime": "局面",
        "qnav_v1": "V1 AI",
        "qnav_v2": "V2 エンジン",
        "qnav_check": "↻ 更新確認",

        "p1_title": "パネル 1 • BTC リアルタイム現物価格 (Live)",
        "p2_title_text": "パネル 2 • 取引所テレメトリ（生データ vs 推定）",
        "p2_title_index": "パネル 2 • 取引所テレメトリ & 推定清算プール",
        "p2_sub_index": "リアルタイム市場マイクロストラクチャー",
        "p2_cat1": "1. 確定 4H 構造",
        "p2_cat2": "2. 注文フロー & CVD",
        "p2_cat3": "3. デリバティブ偏り",
        "p2_cat4": "4. レンジ & マグネット",
        "p3_title": "パネル 3 • マクロ市場レジーム診断",
        "p3_question": "現在ビットコインはどの相場環境にありますか？",
        "p3_sub": "確定した4H指標に基づき、厳密に5つの決定論的レジーム（または競合時は移行・混合）に分類します。",
        "p3_learn_btn": "5レジームと算出ロジックを見る",
        "p3_active_badge": "現在の市場レジーム",
        "p3_rule_confirm": "ルール一致スコア：",
        "p3_evidence_hdr": "検証済みオンエクスチェンジ根拠",
        "p3_matrix_hdr": "5レジーム・フレームワーク一覧",

        "bridge_title_text": "ブリッジ • Verdict 1 vs Verdict 2",
        "bridge_badge_index": "⚖️ ブリッジ • 2つの独立判定",
        "bridge_h3_index": "Verdict 1（あなたのAI）vs Verdict 2（内蔵エンジン）",
        "bridge_desc_index": "パネル1〜3は助言を含まない確定データのみを提示します。AIでVerdict 1を生成し、下のVerdict 2と照合してください。",
        "v1_hdr_text": "Verdict 1 • AIで判定（コピー）",
        "v1_tag_index": "Verdict 1 • あなたのAI（システムバイアス無し）",
        "v1_h2_index": "自身のAIで Verdict 1 を生成",
        "v1_desc_index": "確定4Hデータ・推定清算帯・任意コスト基準値をひとまとめに出力。Verdict 2 は隠されるためAIは100%中立に評価します。",
        "v1_btn_text": "🧪 AI用テレメトリをコピー",
        "v1_btn_index": "AI向けブラインド・テレメトリをコピー",
        "v1_wb_summary": "▸ 任意：P_buy / P_sell 基準値（端末内のみ）",
        "v1_wb_summary_index": "▸ 任意：P_buy / P_sell 保有基準価格を入力（ローカル保存）",
        "v1_wb_buy_lbl": "Loop A 買値 ($P_buy)",
        "v1_wb_sell_lbl": "Loop B 売値 ($P_sell)",
        "v1_wb_storage": "ブラウザの localStorage のみに保存",
        "v1_wb_clear": "クリア",
        "v1_step1_title": "ブラインド・テレメトリをコピー",
        "v1_step1_desc": "Verdict 2 を伏せたまま確定4H構造・CVD・OI・推定プールと基準値を書き出します。",
        "v1_step2_title": "主要LLMにそのまま貼り付け",
        "v1_step2_desc": "Claude、ChatGPT、Grok、Qwen、Gemini すべてで双方向マーケットコンテキストが即機能します。",
        "v1_step3_title": "Verdict 1 と Verdict 2 を照合",
        "v1_step3_desc": "AIが算出した Loop A（下ヒゲ回収）と Loop B（踏み上げ利確）の水準を下の Verdict 2 と比較します。",
        "v1_preview_summary": "🧪 コピーされるAI向けプロンプトを確認",
        "v1_expand_hint": "クリックして展開",
        "v2_hdr_text": "Verdict 2 • 内蔵レーダーエンジン",
        "v2_tag_index": "Verdict 2 • 内蔵レーダーエンジン",
        "v2_h2_index": "内蔵システム判定",
        "v2_desc_index": "確定4Hレジーム判定、Loop A/B マグネット帯、対称LSCEスイープゲート、10x–100x推定ヒートマップ。",
        "v2_reminder_title": "常に Verdict 1（あなたのAI）を生成して比較：",
        "v2_reminder_desc": "Verdict 2 は固定ルールの基準線です。Verdict 1 をAIに貼り付けて多角的な分析と比較してください。",
        "v2_reminder_link": "↑ Verdict 1 へ戻る（AIコピー）",
        "v2_why_title": "この双方向判定の根拠",
        "v2_factors_hdr": "判定を導いた3つの主要市場ファクター",
        "v2_sizing_hdr": "双方向サイジングと待機規律",
        "v2_patience_hdr": "リスクゲートと忍耐ルール",
        "v2_lsce_hdr": "双方向スイープ確認エンジン (LSCE • 確定 4H)",
        "v2_upper_pool": "上側ショート清算プール (Loop B 目標)",
        "v2_lower_pool": "下側ロング清算プール (Loop A 目標)",

        "reg_badge": "双方向レーダー構造 • 観測可能なポジション力学",
        "reg_h1": "5レジームレーダー & 双方向流動性プロトコル",
        "reg_intro": "確定4Hの流動性マグネット・建玉偏り・両側リザーブを5つの市場フェーズでどう解釈するかを解説します。",
        "reg_back_live": "← ライブモニターへ戻る",
        "reg_return_live": "← BTC Magnet モニターへ戻る",
        "reg_sec1_h2": "1. 基本哲学：双方向流動性とリスクゲート",
        "reg_sec2_h2": "2. 確定4H・多数決判定エンジンの仕組み",
        "reg_sec3_h2": "3. 5つの市場レジームと双方向トリガー",
        "reg_sec4_h2": "4. 推定清算プールと確定4Hスケール算出法",
        "reg_sec5_h2": "5. 双方向 LSCE ステートマシンとゲート条件",

        "toast_copied_v1": "✓ Verdict 1 AIテレメトリをコピーしました（日本語回答指示付き）",
        "toast_cleared_wb": "✓ ローカル基準値をクリアしました",
        "age_banner_live": "リアルタイム現物フィード稼働中",
    },
    "fr": {
        "brand_sub_entry": "Aimants de Liquidité • Radar 5-Régimes",
        "brand_pill_entry": "RADAR BIDIRECTIONNEL • NIVEAUX LIVE • TÉLÉMÉTRIE IA",
        "brand_badge_radar": "Radar 5-Régimes",
        "brand_sub_desktop": "Mécanique de Positionnement Observable & Intelligence de Régime",
        "nav_desktop_btn": "🖥️ Tableau Complet",
        "nav_mobile_btn": "📱 Terminal Mobile",
        "hdr_btc_price": "Prix du Bitcoin",
        "footer_monitor_terminal": "Terminal Moniteur",
        "footer_regimes_math": "5 Régimes & Calculs",
        "footer_regimes_guide": "Guide 5 Régimes",
        "footer_full_dashboard": "Tableau 5 Panneaux",
        "footer_privacy": "Confidentialité",
        "footer_disclaimer": "Télémétrie de marché à titre informatif uniquement. Pas un conseil financier.",
        "footer_research_disclaimer": "Strictement à des fins d'information et d'analyse du risque. Pas un conseil financier.",

        "entry_video1_cap": "HAUSSIER vs BAISSIER • PRESSION CARNET",
        "entry_video2_cap": "RUPTURE DE PROFONDEUR • BIDS vs ASKS",
        "sound_off": "🔇 SON COUPÉ",
        "sound_on": "🔊 SON ACTIF",
        "entry_enter_btn": "Ouvrir BTC Magnet Monitor →",
        "entry_enter_sub": "Prix Spot BTC Live • Échelle de Liquidité • Verdict 1 vs Verdict 2",
        "entry_pm_title": "Jauge de Pression Bull vs. Bear",
        "entry_pm_live_badge": "● CARNET LIVE",
        "entry_pm_bar1": "1. Profondeur du Carnet (±1,5 %)",
        "entry_pm_bar2": "2. Flux Agressif (CVD 24H)",
        "entry_pm_bar3": "3. Biais Levier Foule (L/S)",
        "entry_snap_title": "Aperçu Télémétrie Live",
        "entry_snap_price": "Prix Spot BTC",
        "entry_snap_magnet": "Aimant Dominant",
        "entry_snap_regime": "Régime Macro Actif",
        "entry_snap_scan": "Dernier Scan Radar",
        "entry_snap_cadence": "Cadence : Toutes les 30 min (:02/:32 UTC)",
        "entry_v1_title": "Pourquoi & Comment Cette App Vous Aide",
        "entry_v1_badge": "ATOUT N°1 • VERDICT 1",
        "entry_v1_intro_html": (
            'Éliminez le bruit émotionnel et les indicateurs retardés. BTC Magnet Monitor vous donne la gravité réelle du carnet, '
            'les aimants de liquidité et une <strong class="c-amber">Télémétrie IA en 1 clic</strong> avant d&rsquo;engager du capital :'
        ),
        "entry_v1_step1_html": (
            '<span class="step-badge step-badge-amber">1</span>'
            '<strong class="c-amber">Verdict 1 &bull; Copier la Télémétrie pour l&rsquo;IA (Atout n°1) :</strong> '
            'Un seul clic copie des données de marché neutres sans biais (4H clôturé, VWAP, OI, funding et murs d&rsquo;ordres) '
            'vers ChatGPT, Claude, Gemini ou Grok pour une lecture structurelle indépendante.'
        ),
        "entry_v1_step2_html": (
            '<span class="step-badge">2</span>'
            '<strong class="c-cyan">Comparer avec Verdict 2 (Moteur Intégré) :</strong> '
            'Confrontez le Verdict 1 de votre IA à notre Radar 5-Régimes déterministe, aux zones Loop A / Loop B et aux filtres de risque.'
        ),
        "entry_v1_step3_html": (
            '<span class="step-badge">3</span>'
            '<strong class="c-green">Avantage Microstructure en Direct :</strong> '
            'Suivez la pression Bids vs. Asks en temps réel, le delta preneur et le biais L/S pour repérer où la liquidité bloque ou déclenche un squeeze.'
        ),

        "text_header_sub": "Terminal de Télémétrie de Liquidité Bidirectionnelle",
        "text_mode_label": "MODE : RADAR AIMANT 5-RÉGIMES (BIDIRECTIONNEL)",
        "qnav_spot": "Spot",
        "qnav_feeds": "Flux",
        "qnav_regime": "Régime",
        "qnav_v1": "V1 IA",
        "qnav_v2": "V2 Moteur",
        "qnav_check": "↻ Vérif.",

        "p1_title": "Panneau 1 • Prix Spot BTC Temps Réel (Live)",
        "p2_title_text": "Panneau 2 • Télémétrie Bourse (Brut vs Modélisé)",
        "p2_title_index": "Panneau 2 • Télémétrie Bourse & Pools Modélisés",
        "p2_sub_index": "Flux de Microstructure de Marché en Direct",
        "p2_cat1": "1. Structure 4H Clôturée",
        "p2_cat2": "2. Flux d'Ordres & CVD",
        "p2_cat3": "3. Concentration Dérivés",
        "p2_cat4": "4. Canal & Aimants",
        "p3_title": "Panneau 3 • Diagnostic de Régime Macro",
        "p3_question": "Dans quel environnement de marché le Bitcoin évolue-t-il ?",
        "p3_sub": "Bitcoin est classé strictement dans 1 des 5 régimes déterministes (ou Transition / Mixte en cas de conflit).",
        "p3_learn_btn": "Découvrir les 5 Régimes & Modèle",
        "p3_active_badge": "Régime Actif",
        "p3_rule_confirm": "Confirmation des Règles :",
        "p3_evidence_hdr": "Preuves On-Exchange Vérifiées",
        "p3_matrix_hdr": "Matrice du Radar 5-Régimes",

        "bridge_title_text": "Pont • Verdict 1 vs Verdict 2",
        "bridge_badge_index": "⚖️ Pont • Deux Verdicts Indépendants",
        "bridge_h3_index": "Verdict 1 (Votre IA) vs Verdict 2 (Moteur Intégré)",
        "bridge_desc_index": "Les panneaux 1–3 fournissent uniquement des faits clôturés sans biais. Générez Verdict 1 dans votre IA puis comparez avec Verdict 2.",
        "v1_hdr_text": "Verdict 1 • Votre Propre IA (Copier)",
        "v1_tag_index": "Verdict 1 • Votre Propre IA (Zéro Biais)",
        "v1_h2_index": "Générer le Verdict 1 avec Votre IA",
        "v1_desc_index": "Un export propre contenant les faits 4H clôturés, les bandes de liquidation et vos seuils optionnels — avec Verdict 2 masqué pour garder l'IA 100 % objective.",
        "v1_btn_text": "🧪 COPIER LA TÉLÉMÉTRIE POUR L'IA",
        "v1_btn_index": "Copier la Télémétrie Neutre pour l'IA",
        "v1_wb_summary": "▸ Optionnel : Seuils P_buy / P_sell (Local)",
        "v1_wb_summary_index": "▸ Optionnel : Ajouter vos Seuils P_buy / P_sell (Local)",
        "v1_wb_buy_lbl": "Coût Loop A ($P_buy)",
        "v1_wb_sell_lbl": "Vente Loop B ($P_sell)",
        "v1_wb_storage": "Enregistré uniquement dans votre navigateur",
        "v1_wb_clear": "Effacer",
        "v1_step1_title": "Copier la Télémétrie Neutre",
        "v1_step1_desc": "Exporte structure 4H, CVD, OI et pools modélisés + vos seuils sans dévoiler Verdict 2.",
        "v1_step2_title": "Coller dans n'importe quelle IA",
        "v1_step2_desc": "Compatible directement avec Claude, ChatGPT, Grok, Qwen ou Gemini avec contexte bidirectionnel.",
        "v1_step3_title": "Croiser Verdict 1 vs Verdict 2",
        "v1_step3_desc": "Comparez les niveaux Loop A et Loop B de votre IA face aux calculs déterministes ci-dessous.",
        "v1_preview_summary": "🧪 Aperçu du Prompt de Télémétrie IA",
        "v1_expand_hint": "Cliquer pour déplier",
        "v2_hdr_text": "Verdict 2 • Moteur Radar Intégré",
        "v2_tag_index": "Verdict 2 • Moteur Radar Intégré",
        "v2_h2_index": "Verdict Système Intégré",
        "v2_desc_index": "Régime déterministe 4H clôturé, zones aimants Loop A & Loop B, porte LSCE symétrique et carte thermique 10x–100x.",
        "v2_reminder_title": "Générez toujours Verdict 1 (Votre IA) pour comparer :",
        "v2_reminder_desc": "Verdict 2 est une base de règles fixes. Copiez Verdict 1 dans votre IA pour une analyse contextuelle approfondie.",
        "v2_reminder_link": "↑ Revenir au Verdict 1 (Copier pour IA)",
        "v2_why_title": "Pourquoi ce Signal Bidirectionnel ?",
        "v2_factors_hdr": "Les 3 Facteurs Clés de Marché",
        "v2_sizing_hdr": "Dimensionnement & Patience Bidirectionnelle",
        "v2_patience_hdr": "Filtres de Risque & Règles de Patience",
        "v2_lsce_hdr": "Moteur de Balayage Bidirectionnel (LSCE • 4H Clôturé)",
        "v2_upper_pool": "Pool Short Supérieur (Cible Loop B)",
        "v2_lower_pool": "Pool Long Inférieur (Cible Loop A)",

        "reg_badge": "Architecture Radar Bidirectionnelle • Positionnement Observable",
        "reg_h1": "Radar 5-Régimes & Protocole de Liquidité Bidirectionnelle",
        "reg_intro": "Comment le Protocole Bidirectionnel cartographie les aimants 4H clôturés, les biais de levier et les réserves dans les cinq régimes.",
        "reg_back_live": "← Retour au Moniteur Live",
        "reg_return_live": "← Retour à BTC Magnet Monitor",
        "reg_sec1_h2": "1. Philosophie : Liquidité Bidirectionnelle & Filtres de Risque",
        "reg_sec2_h2": "2. Fonctionnement du Moteur de Vote Majoritaire 4H",
        "reg_sec3_h2": "3. Les 5 Régimes de Marché & Déclencheurs",
        "reg_sec4_h2": "4. Méthodologie des Pools Modélisés & Échelle 4H",
        "reg_sec5_h2": "5. Automate d'États LSCE & Règles d'Activation",

        "toast_copied_v1": "✓ Télémétrie IA Verdict 1 copiée (réponse IA en français)",
        "toast_cleared_wb": "✓ Seuils locaux effacés",
        "age_banner_live": "FLUX SPOT EN DIRECT ACTIF",
    },
}

# Dynamic exact/substring phrase replacements applied by i18n.js for live JS telemetry
PHRASE_MAP: Dict[str, Dict[str, str]] = {
    "zh": {
        "Spot-Led Expansion": "现货主导扩张",
        "Leveraged Fragile Upside": "杠杆脆弱上行（注意挤兑风险）",
        "Range / Liquidation Magnet": "区间震荡 / 清算磁铁区间",
        "Cascade / Forced Deleveraging": "连环强平 / 剧烈去杠杆",
        "Distribution / Bear Continuation": "派发主导 / 空头延续",
        "Transition / Mixed": "过渡震荡 / 多空信号混合",
        "Lower Long Sweep Magnet": "下方多头止损磁铁",
        "Upper Short Squeeze Magnet": "上方空头挤压磁铁",
        "Balanced / Symmetric Two-Way Magnet": "双向均衡磁铁",
        "Hold Both Sides": "双向观望储备",
        "ASIA ACCUMULATION": "亚洲盘累积时段",
        "LONDON ACTIVE": "伦敦盘活跃时段",
        "NEW YORK CORE": "纽约核心波动时段",
        "US CLOSE / ASIA PRE-OPEN": "美盘尾声 / 亚盘前过渡",
        "Freshness: Verified ≤40m Window": "快照状态：40 分钟窗口内已验证",
        "DATA UNAVAILABLE": "数据暂不可用",
        "Strong Bull Depth": "买盘深度明显占优",
        "Bear Ask Wall Dominant": "上方卖压墙明显占优",
        "Balanced Order Book": "买卖盘口相对均衡",
        "Spot Buyers Aggressive": "现货主动买盘占优",
        "Spot Sellers Dominant": "现货主动抛压占优",
        "Mixed Spot Taker Flow": "主动买卖流均衡博弈",
        "Crowd leans long": "散户/全网多头拥挤（警惕下洗）",
        "Crowd leans short": "散户/全网空头拥挤（警惕逼空）",
        "Balanced Positioning": "多空持仓比例相对平衡",
    },
    "id": {
        "Spot-Led Expansion": "Ekspansi Dipimpin Spot",
        "Leveraged Fragile Upside": "Kenaikan Rapuh Berbasis Leverage",
        "Range / Liquidation Magnet": "Rentang / Magnet Likuidasi",
        "Cascade / Forced Deleveraging": "Kaskade / Deleveraging Paksa",
        "Distribution / Bear Continuation": "Distribusi / Kelanjutan Bear",
        "Transition / Mixed": "Transisi / Campuran",
        "Lower Long Sweep Magnet": "Magnet Sapuan Long Bawah",
        "Upper Short Squeeze Magnet": "Magnet Squeeze Short Atas",
        "Balanced / Symmetric Two-Way Magnet": "Magnet Dua Arah Seimbang",
        "Hold Both Sides": "Tahan Kedua Sisi",
        "ASIA ACCUMULATION": "AKUMULASI SESI ASIA",
        "LONDON ACTIVE": "SESI LONDON AKTIF",
        "NEW YORK CORE": "INTI SESI NEW YORK",
        "US CLOSE / ASIA PRE-OPEN": "PENUTUPAN AS / PRA-ASIA",
        "Freshness: Verified ≤40m Window": "Status: Terverifikasi ≤40m",
        "DATA UNAVAILABLE": "DATA TIDAK TERSEDIA",
        "Strong Bull Depth": "Kedalaman Bull Kuat",
        "Bear Ask Wall Dominant": "Dinding Jual Bear Dominan",
        "Balanced Order Book": "Order-Book Seimbang",
        "Spot Buyers Aggressive": "Pembeli Spot Agresif",
        "Spot Sellers Dominant": "Penjual Spot Dominan",
        "Mixed Spot Taker Flow": "Arus Taker Spot Campuran",
        "Crowd leans long": "Mayoritas posisi Long padat",
        "Crowd leans short": "Mayoritas posisi Short padat",
        "Balanced Positioning": "Posisi Seimbang",
    },
    "ko": {
        "Spot-Led Expansion": "현물 주도 상승 확장",
        "Leveraged Fragile Upside": "레버리지 취약 상승 (스퀴즈 경계)",
        "Range / Liquidation Magnet": "박스권 / 청산 마그넷 구간",
        "Cascade / Forced Deleveraging": "연쇄 강제 청산 / 디레버리징",
        "Distribution / Bear Continuation": "물량 분배 / 하락 추세 지속",
        "Transition / Mixed": "전환 구간 / 혼조 시그널",
        "Lower Long Sweep Magnet": "하단 롱 스윕 마그넷",
        "Upper Short Squeeze Magnet": "상단 숏 스퀴즈 마그넷",
        "Balanced / Symmetric Two-Way Magnet": "양방향 균형 마그넷",
        "Hold Both Sides": "양측 관망 대기",
        "ASIA ACCUMULATION": "아시아 누적 세션",
        "LONDON ACTIVE": "런던 활성 세션",
        "NEW YORK CORE": "뉴욕 핵심 변동 세션",
        "US CLOSE / ASIA PRE-OPEN": "미국 마감 / 아시아 개장 전",
        "Freshness: Verified ≤40m Window": "상태: 40분 윈도우 내 검증됨",
        "DATA UNAVAILABLE": "데이터 미제공",
        "Strong Bull Depth": "매수 호가 깊이 우위",
        "Bear Ask Wall Dominant": "상단 매도벽 압도",
        "Balanced Order Book": "호가창 균형 상태",
        "Spot Buyers Aggressive": "현물 매수세 적극적",
        "Spot Sellers Dominant": "현물 매도 압력 우위",
        "Mixed Spot Taker Flow": "현물 체결 흐름 혼조",
        "Crowd leans long": "대중 롱 포지션 과밀",
        "Crowd leans short": "대중 숏 포지션 과밀",
        "Balanced Positioning": "포지션 비율 균형",
    },
    "ja": {
        "Spot-Led Expansion": "現物主導の上昇トレンド",
        "Leveraged Fragile Upside": "レバレッジ主導の脆弱な上昇",
        "Range / Liquidation Magnet": "レンジ相場 / 清算マグネット帯",
        "Cascade / Forced Deleveraging": "連鎖ロスカット / 強制デレバレッジ",
        "Distribution / Bear Continuation": "ディストリビューション / 下落継続",
        "Transition / Mixed": "移行フェーズ / シグナル混在",
        "Lower Long Sweep Magnet": "下側ロング狩りマグネット",
        "Upper Short Squeeze Magnet": "上側ショート踏み上げマグネット",
        "Balanced / Symmetric Two-Way Magnet": "双方向バランス型マグネット",
        "Hold Both Sides": "両サイド様子見",
        "ASIA ACCUMULATION": "アジア時間・蓄積帯",
        "LONDON ACTIVE": "ロンドンアクティブ時間",
        "NEW YORK CORE": "ニューヨーク中核時間",
        "US CLOSE / ASIA PRE-OPEN": "NY引け / アジア時間前",
        "Freshness: Verified ≤40m Window": "鮮度：40分以内で検証済み",
        "DATA UNAVAILABLE": "データ利用不可",
        "Strong Bull Depth": "買い板デプス優勢",
        "Bear Ask Wall Dominant": "売り板壁が優勢",
        "Balanced Order Book": "板バランス均衡",
        "Spot Buyers Aggressive": "現物成行買いが積極的",
        "Spot Sellers Dominant": "現物売りが優勢",
        "Mixed Spot Taker Flow": "現物成行フロー拮抗",
        "Crowd leans long": "ロング偏重（下振れ注意）",
        "Crowd leans short": "ショート偏重（踏み上げ注意）",
        "Balanced Positioning": "ポジション比率均衡",
    },
    "fr": {
        "Spot-Led Expansion": "Expansion Menée par le Spot",
        "Leveraged Fragile Upside": "Hausse Fragile par Effet de Levier",
        "Range / Liquidation Magnet": "Range / Aimant de Liquidation",
        "Cascade / Forced Deleveraging": "Cascade / Désendettement Forcé",
        "Distribution / Bear Continuation": "Distribution / Poursuite Baissière",
        "Transition / Mixed": "Transition / Signaux Mixtes",
        "Lower Long Sweep Magnet": "Aimant Balayage Long Inférieur",
        "Upper Short Squeeze Magnet": "Aimant Squeeze Short Supérieur",
        "Balanced / Symmetric Two-Way Magnet": "Aimant Bidirectionnel Équilibré",
        "Hold Both Sides": "Attente des Deux Côtés",
        "ASIA ACCUMULATION": "ACCUMULATION ASIE",
        "LONDON ACTIVE": "SESSION LONDRES ACTIVE",
        "NEW YORK CORE": "CŒUR DE SESSION NEW YORK",
        "US CLOSE / ASIA PRE-OPEN": "CLÔTURE US / PRÉ-ASIE",
        "Freshness: Verified ≤40m Window": "Statut : Vérifié dans les ≤40 min",
        "DATA UNAVAILABLE": "DONNÉES INDISPONIBLES",
        "Strong Bull Depth": "Forte Profondeur Acheteuse",
        "Bear Ask Wall Dominant": "Mur Vendeur Dominant",
        "Balanced Order Book": "Carnet Équilibré",
        "Spot Buyers Aggressive": "Acheteurs Spot Agressifs",
        "Spot Sellers Dominant": "Vendeurs Spot Dominants",
        "Mixed Spot Taker Flow": "Flux Taker Spot Mitigé",
        "Crowd leans long": "Foule surexposée Long",
        "Crowd leans short": "Foule surexposée Short",
        "Balanced Positioning": "Positionnement Équilibré",
    },
}


def render_i18n_js() -> str:
    """Emit self-contained client-side i18n module (dist/i18n.js)."""
    buttons_json = json.dumps(LANG_BUTTONS, ensure_ascii=False)
    translations_json = json.dumps(TRANSLATIONS, ensure_ascii=False)
    phrases_json = json.dumps(PHRASE_MAP, ensure_ascii=False)
    ai_dirs_json = json.dumps(AI_PROMPT_DIRECTIVES, ensure_ascii=False)

    return f"""/* BTC Magnet Monitor — Offline Multi-Language Engine (EN / ZH / ID / KO / JA / FR) */
(function () {{
  const STORAGE_KEY = 'btc_magnet_lang';
  const LANG_BUTTONS = {buttons_json};
  const TRANSLATIONS = {translations_json};
  const PHRASE_MAP = {phrases_json};
  const AI_DIRECTIVES = {ai_dirs_json};
  const VALID_SET = new Set(LANG_BUTTONS.map(function (b) {{ return b.code; }}));

  function readSavedLang() {{
    try {{
      const qs = new URLSearchParams(window.location.search || '');
      const qLang = (qs.get('lang') || '').toLowerCase().slice(0, 2);
      if (VALID_SET.has(qLang)) {{
        try {{ window.localStorage && localStorage.setItem(STORAGE_KEY, qLang); }} catch (e) {{}}
        return qLang;
      }}
      if (window.localStorage) {{
        const saved = (localStorage.getItem(STORAGE_KEY) || '').toLowerCase();
        if (VALID_SET.has(saved)) return saved;
      }}
    }} catch (e) {{}}
    return 'en';
  }}

  let currentLang = readSavedLang();

  function injectStyles() {{
    if (document.getElementById('btc-i18n-styles')) return;
    const st = document.createElement('style');
    st.id = 'btc-i18n-styles';
    st.textContent =
      '.btc-lang-bar{{display:flex;flex-wrap:wrap;align-items:center;gap:4px;}}' +
      '.btc-lang-pill{{background:#11141d;border:1px solid rgba(113,113,122,0.5);color:#d4d4d8;' +
      'font-family:inherit;font-size:10px;font-weight:700;padding:3px 7px;border-radius:999px;' +
      'cursor:pointer;line-height:1.2;transition:all .15s ease;user-select:none;}}' +
      '.btc-lang-pill:hover{{border-color:#38bdf8;color:#ffffff;}}' +
      '.btc-lang-pill.is-active{{background:rgba(16,185,129,0.18);border-color:#10b981;color:#6ee7b7;' +
      'box-shadow:0 0 10px rgba(16,185,129,0.25);}}' +
      '@media (max-width:480px){{.btc-lang-pill{{font-size:9px;padding:3px 6px;}}}}';
    document.head.appendChild(st);
  }}

  function renderSwitcherBars() {{
    const slots = document.querySelectorAll('[data-i18n-switcher]');
    slots.forEach(function (slot) {{
      slot.className = 'btc-lang-bar';
      slot.setAttribute('role', 'group');
      slot.setAttribute('aria-label', 'Language switcher');
      slot.innerHTML = '';
      LANG_BUTTONS.forEach(function (b) {{
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btc-lang-pill' + (b.code === currentLang ? ' is-active' : '');
        btn.setAttribute('data-lang', b.code);
        btn.setAttribute('title', b.name);
        btn.setAttribute('aria-pressed', b.code === currentLang ? 'true' : 'false');
        btn.textContent = b.short;
        btn.addEventListener('click', function () {{
          setLang(b.code);
        }});
        slot.appendChild(btn);
      }});
    }});
  }}

  function getText(key, fallback) {{
    const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.en;
    if (dict && Object.prototype.hasOwnProperty.call(dict, key)) return dict[key];
    if (TRANSLATIONS.en && Object.prototype.hasOwnProperty.call(TRANSLATIONS.en, key)) return TRANSLATIONS.en[key];
    return fallback !== undefined ? fallback : key;
  }}

  function translateTextString(str) {{
    if (!str || currentLang === 'en') return str;
    const phrases = PHRASE_MAP[currentLang];
    if (!phrases) return str;
    let out = String(str);
    Object.keys(phrases).forEach(function (src) {{
      if (out.indexOf(src) !== -1) {{
        out = out.split(src).join(phrases[src]);
      }}
    }});
    return out;
  }}

  function applyStaticNodes(root) {{
    const scope = root || document;
    scope.querySelectorAll('[data-i18n]').forEach(function (el) {{
      const key = el.getAttribute('data-i18n');
      if (!key) return;
      if (!el.hasAttribute('data-i18n-orig-text')) {{
        el.setAttribute('data-i18n-orig-text', el.textContent);
      }}
      if (currentLang === 'en') {{
        el.textContent = el.getAttribute('data-i18n-orig-text');
      }} else {{
        el.textContent = getText(key, el.getAttribute('data-i18n-orig-text'));
      }}
    }});
    scope.querySelectorAll('[data-i18n-html]').forEach(function (el) {{
      const key = el.getAttribute('data-i18n-html');
      if (!key) return;
      if (!el.hasAttribute('data-i18n-orig-html')) {{
        el.setAttribute('data-i18n-orig-html', el.innerHTML);
      }}
      if (currentLang === 'en') {{
        el.innerHTML = el.getAttribute('data-i18n-orig-html');
      }} else {{
        el.innerHTML = getText(key, el.getAttribute('data-i18n-orig-html'));
      }}
    }});
  }}

  function applyDynamicTelemetry(root) {{
    const scope = root || document;
    const dynamicSelectors = [
      '#entry-dom-magnet',
      '#entry-regime-name',
      '#depth-sub-lbl',
      '#flow-sub-lbl',
      '#ls-sub-lbl',
      '#entry-depth-badge',
      '#p3-conf-fresh',
      '#session-name',
      '#hdr-session',
      '#data-age-banner',
      '#confidence-freshness-tag',
      '#panel-3 h1',
      '#verdict-2 strong'
    ];
    dynamicSelectors.forEach(function (sel) {{
      scope.querySelectorAll(sel).forEach(function (el) {{
        if (el.hasAttribute('data-i18n') || el.hasAttribute('data-i18n-html')) return;
        const orig = el.getAttribute('data-i18n-orig-dyn') || el.textContent;
        if (!el.hasAttribute('data-i18n-orig-dyn')) {{
          el.setAttribute('data-i18n-orig-dyn', orig);
        }}
        if (currentLang === 'en') {{
          el.textContent = orig;
        }} else {{
          const next = translateTextString(orig);
          if (next !== el.textContent) el.textContent = next;
        }}
      }});
    }});

    // Keep audio buttons aligned with current muted state
    [['entry-hero-video', 'entry-sound-btn'], ['entry-badger-video', 'entry-badger-sound-btn']].forEach(function (pair) {{
      const v = document.getElementById(pair[0]);
      const b = document.getElementById(pair[1]);
      if (v && b) {{
        b.textContent = getText(v.muted ? 'sound_off' : 'sound_on');
      }}
    }});
  }}

  function apply(root) {{
    injectStyles();
    document.documentElement.setAttribute('lang', currentLang);
    renderSwitcherBars();
    applyStaticNodes(root);
    applyDynamicTelemetry(root);
  }}

  function setLang(langCode) {{
    const normalized = String(langCode || 'en').toLowerCase().slice(0, 2);
    if (!VALID_SET.has(normalized)) return;
    currentLang = normalized;
    try {{
      if (window.localStorage) localStorage.setItem(STORAGE_KEY, normalized);
    }} catch (e) {{}}
    apply(document);
    try {{
      window.dispatchEvent(new CustomEvent('btc-magnet:langchange', {{ detail: {{ lang: normalized }} }}));
    }} catch (e) {{}}
  }}

  function localizeBlindPrompt(rawPrompt) {{
    const base = String(rawPrompt || '');
    const dir = AI_DIRECTIVES[currentLang] || '';
    return dir ? (base + dir) : base;
  }}

  function setDynText(el, englishText) {{
    if (!el) return;
    const raw = String(englishText === undefined || englishText === null ? el.textContent : englishText);
    el.setAttribute('data-i18n-orig-dyn', raw);
    el.textContent = currentLang === 'en' ? raw : translateTextString(raw);
  }}

  function translateLiveNode(el) {{
    if (!el) return;
    setDynText(el, el.textContent);
  }}

  window.BtcMagnetI18n = {{
    getLang: function () {{ return currentLang; }},
    setLang: setLang,
    t: getText,
    translateText: translateTextString,
    setDynText: setDynText,
    translateLiveNode: translateLiveNode,
    localizeBlindPrompt: localizeBlindPrompt,
    apply: apply,
    supported: LANG_BUTTONS.map(function (b) {{ return b.code; }})
  }};

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', function () {{ apply(document); }});
  }} else {{
    apply(document);
  }}
}})();
"""
