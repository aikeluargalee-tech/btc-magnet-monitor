from typing import List, Tuple, Optional, Dict, Any
from engine.models import MarketMetrics, LiquidationCluster, RegimeResult

class RegimeClassifier:
    """
    Simplified 5-Regime Radar for the BTC Magnet Monitor:
      1. Spot-Led Expansion
      2. Leveraged / Fragile Upside
      3. Range / Liquidation Magnet (Core Operating Zone)
      4. Cascade / Forced Deleveraging
      5. Distribution / Bear Continuation
      Default: Transition / Mixed (when signals are unclear or mixed)
      
    Principles:
      - Regime diagnosis comes first: determines which playbook is authorized.
      - Majority-based scoring: 4 observable facts per regime; majority (>= 3 of 4) is sufficient.
      - Liquidation Magnet calculator is the primary tactical engine inside Regime 3.
      - Zero fabricated data: data incompleteness locks the system to cash.
    """

    def classify(self, m: Optional[MarketMetrics], clusters: List[LiquidationCluster]) -> RegimeResult:
        # Data integrity check
        if m is None or not clusters:
            return self._create_data_incomplete_result("Market metrics or liquidation clusters unavailable.")

        upper_cluster = next((c for c in clusters if c.side == "upper"), None)
        lower_cluster = next((c for c in clusters if c.side == "lower"), None)

        # Evaluate Liquidation Magnet (6-Factor Override Engine)
        dominant_magnet, magnet_title, magnet_reason, magnet_factors = self._evaluate_dominant_magnet(
            m, upper_cluster, lower_cluster
        )

        # Evaluate the 5 regimes (Majority-based: >= 3 of 4 matches)
        candidates = [
            self._eval_cascade(m),
            self._eval_leveraged_upside(m),
            self._eval_distribution_bear(m),
            self._eval_range_magnet(m, dominant_magnet, magnet_title),
            self._eval_spot_expansion(m),
        ]

        # Filter candidates meeting majority threshold (>= 3 matches)
        valid = [c for c in candidates if c["matches_count"] >= 3]

        if valid:
            # Sort by priority (safety first) and highest matches count
            valid.sort(key=lambda x: (x["priority"], -x["matches_count"]))
            best = valid[0]
        else:
            # Default to Transition / Mixed when signals are mixed or no clear majority
            best = self._eval_transition_mixed(m, candidates)

        # Calculate exact stop price and distance %
        stop_price, stop_dist_pct = self._calculate_stop(best["regime_id"], m)

        # Risk budget: swing trade limit is <= 3.5% stop distance
        risk_budget_ok = stop_dist_pct <= 3.5 and best["sizing_factor"] > 0

        # Percentage-based allocations
        sizing = best["sizing_factor"]
        max_spot_allocation = 80.0
        target_btc_pct = round(max_spot_allocation * sizing, 1)
        target_usdt_pct = round(100.0 - target_btc_pct, 1)
        recommended_cash_deploy = round(sizing * 100.0, 1)

        # Plain-English translation for beginners (95% audience)
        verdict, why_pts, why_sizing, why_stop = self._get_plain_english_breakdown(
            best["regime_id"], m, round(stop_price, 2), round(stop_dist_pct, 2), sizing, dominant_magnet
        )

        majority_score_str = f"{best['matches_count']}/4 observations confirmed"

        # Diagnostic notes
        notes = f"{best['diagnosis']}. Majority Evidence: {majority_score_str} ({', '.join(best['matched'])})."
        if best["regime_id"] == "RANGE_LIQUIDATION_MAGNET":
            notes += f" Active Magnet Playbook: {magnet_reason}"

        return RegimeResult(
            regime=best["name"],
            regime_id=best["regime_id"],
            name=best["name"],
            diagnosis=best["diagnosis"],
            playbook=best["playbook"],
            suitability=best["suitability"],
            sizing_factor=sizing,
            action=best["action"],
            rotation=best["rotation"],
            entry_instruction=best["entry_instruction"],
            stop_rule=best["stop_rule"],
            stop_price=round(stop_price, 2),
            stop_distance_pct=round(stop_dist_pct, 2),
            nearest_upper_cluster=upper_cluster,
            nearest_lower_cluster=lower_cluster,
            dominant_magnet=dominant_magnet,
            dominant_magnet_reason=magnet_title,
            magnet_factors=magnet_factors,
            risk_budget_ok=risk_budget_ok,
            recommended_cash_deploy_pct=recommended_cash_deploy,
            target_btc_allocation_pct=target_btc_pct,
            target_usdt_reserve_pct=target_usdt_pct,
            matched_criteria=best["matched"],
            majority_score=majority_score_str,
            config=best["name"],
            notes=notes,
            plain_english_verdict=verdict,
            why_points=why_pts,
            why_sizing_reason=why_sizing,
            why_stop_reason=why_stop,
            data_quality=m.data_quality
        )

    def _create_data_incomplete_result(self, reason: str) -> RegimeResult:
        """Returns safe default when critical exchange data is unavailable."""
        verdict, why_pts, why_sizing, why_stop = self._get_plain_english_breakdown(
            "DATA_INCOMPLETE", None, 0.0, 0.0, 0.0, "N/A"
        )
        return RegimeResult(
            regime="Data Incomplete",
            regime_id="DATA_INCOMPLETE",
            name="Data Incomplete",
            diagnosis="Critical market data feed unavailable. Trading verdict withheld for safety.",
            playbook="Stand Aside / Hold Cash",
            suitability="Restricted / Stand Aside",
            sizing_factor=0.0,
            action="Stand Aside / Hold Cash (0.0x)",
            rotation="Remain USDT",
            entry_instruction="Hold cash. Do not execute trades while market data integrity is compromised.",
            stop_rule="N/A (No active trade)",
            stop_price=0.0,
            stop_distance_pct=0.0,
            nearest_upper_cluster=None,
            nearest_lower_cluster=None,
            dominant_magnet="N/A",
            dominant_magnet_reason="DATA INCOMPLETE: Missing critical market metrics.",
            magnet_factors={},
            risk_budget_ok=False,
            recommended_cash_deploy_pct=0.0,
            target_btc_allocation_pct=0.0,
            target_usdt_reserve_pct=100.0,
            matched_criteria=[f"Data integrity alert: {reason}"],
            majority_score="0/4 data feeds active",
            config="Data Incomplete",
            notes=f"Trading verdict withheld. Reason: {reason}",
            plain_english_verdict=verdict,
            why_points=why_pts,
            why_sizing_reason=why_sizing,
            why_stop_reason=why_stop,
            data_quality="UNAVAILABLE"
        )

    # --- Evaluators for the 5 Regimes (4 Observable Facts Each; Majority >= 3) ---

    def _eval_spot_expansion(self, m: MarketMetrics) -> dict:
        """Regime 1: Spot-Led Expansion"""
        matched = []
        # 1. Price holding above Daily/Weekly VWAP or rising with structure
        if m.price > m.daily_vwap and (m.price > m.weekly_vwap or m.price > m.ema_20d):
            matched.append("Price holding above Daily/Weekly VWAP with constructive structure")
        # 2. Spot CVD leading or clearly positive
        if m.spot_cvd_ratio >= 1.15 or m.spot_cvd_slope_7d > 0:
            matched.append(f"Spot CVD leading positive (Ratio {m.spot_cvd_ratio:.2f})")
        # 3. Multi-day volume positive / expanding
        if m.spot_vol_ratio >= 1.10:
            matched.append(f"Spot volume expanding ({m.spot_vol_ratio:.2f}x 20D MA)")
        # 4. Funding not elevated, OI not surging hard
        if m.funding_rate <= 0.012 and m.oi_change_24h_pct <= 5.0:
            matched.append(f"Funding healthy ({m.funding_rate*100:.3f}%) & OI stable (+{m.oi_change_24h_pct:.2f}%)")

        sizing = 1.0 if len(matched) == 4 else 0.75

        return {
            "regime_id": "SPOT_LED_EXPANSION",
            "name": "Spot-Led Expansion",
            "diagnosis": "Genuine spot demand supporting upside",
            "playbook": f"Full / Near-Full Spot Long ({sizing:.2f}x)",
            "suitability": "Core Operating Zone (High Edge)",
            "priority": 4,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": sizing,
            "action": f"Buy Spot ({sizing:.2f}x)",
            "rotation": "USDT -> BTC",
            "entry_instruction": "Entry on structure hold or VWAP retest. 60% breakout confirmation / 40% limit at VWAP.",
            "stop_rule": "Recent 4H swing low - 0.6%"
        }

    def _eval_leveraged_upside(self, m: MarketMetrics) -> dict:
        """Regime 2: Leveraged / Fragile Upside"""
        matched = []
        # 1. Price rising but Spot CVD flat or lagging
        if m.price_change_24h_pct > 0.8 and m.spot_cvd_ratio < 1.12:
            matched.append(f"Price rising (+{m.price_change_24h_pct:.2f}%) but Spot CVD lagging ({m.spot_cvd_ratio:.2f})")
        # 2. Perp CVD and/or OI rising sharply
        if m.oi_change_24h_pct >= 4.0 or m.perp_cvd_trend == "surging" or m.oi_change_3d_pct >= 10.0:
            matched.append(f"Futures leverage expanding (OI +{m.oi_change_24h_pct:.2f}% 24h, Perp CVD {m.perp_cvd_trend})")
        # 3. Funding elevated or basis stretched
        if m.funding_rate >= 0.015 or m.futures_basis_annualized >= 12.0:
            matched.append(f"Funding elevated ({m.funding_rate*100:.3f}%) or basis wide ({m.futures_basis_annualized:.1f}%)")
        # 4. Spot volume not confirming
        if m.spot_vol_ratio < 1.0:
            matched.append(f"Spot volume failing to confirm ({m.spot_vol_ratio:.2f}x 20D MA)")

        return {
            "regime_id": "LEVERAGED_FRAGILE_UPSIDE",
            "name": "Leveraged / Fragile Upside",
            "diagnosis": "Upside driven mainly by leverage / positioning",
            "playbook": "Trim or Stand Aside (0.0x–0.25x)",
            "suitability": "High Risk / Trap Zone",
            "priority": 2,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": 0.0,
            "action": "Trim / Stand Aside (0.0x)",
            "rotation": "BTC -> USDT",
            "entry_instruction": "Strictly zero new buying. Harvest 33% profit directly into perp pump. Trail tight stop.",
            "stop_rule": "Tight trailing stop at 4H swing low"
        }

    def _eval_range_magnet(self, m: MarketMetrics, dom_magnet: str, dom_title: str) -> dict:
        """Regime 3: Range / Liquidation Magnet (Core Operating Zone)"""
        matched = []
        # 1. Price oscillating in a defined range or ATR compressed
        range_width_pct = (m.swing_high_4h - m.swing_low_4h) / m.price * 100
        if range_width_pct <= 4.5 or m.atr_compression_pct >= 30.0:
            matched.append(f"Defined range ({range_width_pct:.2f}% width) & ATR compressed {m.atr_compression_pct:.1f}%")
        # 2. Spot CVD mixed or not trending
        if 0.90 <= m.spot_cvd_ratio <= 1.15:
            matched.append(f"Spot CVD neutral/balanced (Ratio {m.spot_cvd_ratio:.2f})")
        # 3. Funding and OI showing crowding on one side
        if m.long_short_account_ratio >= 1.6 or m.funding_rate >= 0.008 or m.funding_rate <= -0.004:
            matched.append(f"Positioning crowded (L/S {m.long_short_account_ratio:.2f}, funding {m.funding_rate*100:.3f}%)")
        # 4. Clear liquidation clusters detected
        matched.append("Clear liquidation clusters active above and below price")

        sizing = 0.75

        # Tactical alignment inside range: rotate cash to BTC if dominant magnet is Upper or Base Absorption
        if "Upper" in dom_magnet or m.price <= (m.swing_low_4h + m.swing_high_4h) / 2:
            action = f"Trade the Magnet: Buy Spot ({sizing:.2f}x)"
            rotation = "USDT -> BTC"
            entry_inst = "Trade toward dominant magnet: 50% on 1H range reclaim / 50% limit at support low."
        else:
            action = "Range Resistance: Trim to Cash (0.0x)"
            rotation = "BTC -> USDT"
            entry_inst = "Price near range ceiling and lower magnet dominates. Harvest profit to USDT cash."
            sizing = 0.0

        return {
            "regime_id": "RANGE_LIQUIDATION_MAGNET",
            "name": "Range / Liquidation Magnet",
            "diagnosis": "Positioning imbalance and forced liquidations dominate",
            "playbook": f"Core Operating Zone — Trade the Magnet ({sizing:.2f}x)",
            "suitability": "Core Operating Zone (High Edge)",
            "priority": 3,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": sizing,
            "action": action,
            "rotation": rotation,
            "entry_instruction": entry_inst,
            "stop_rule": "Base consolidation floor / sweep wick low - 0.5%"
        }

    def _eval_cascade(self, m: MarketMetrics) -> dict:
        """Regime 4: Cascade / Forced Deleveraging"""
        matched = []
        # 1. Sharp price drop with large liquidations
        if m.price_change_1h_pct <= -2.8 or m.price_change_24h_pct <= -6.0:
            matched.append(f"Sharp price drop ({m.price_change_1h_pct:.2f}% 1h / {m.price_change_24h_pct:.2f}% 24h)")
        # 2. OI crashing
        if m.oi_change_1h_pct <= -3.5 or m.oi_change_4h_pct <= -7.0:
            matched.append(f"OI crashing ({m.oi_change_1h_pct:.2f}% 1h / {m.oi_change_4h_pct:.2f}% 4h)")
        # 3. Funding plunging negative
        if m.funding_rate <= -0.005:
            matched.append(f"Funding plunged deeply negative ({m.funding_rate*100:.3f}%)")
        # 4. Basis collapse or severe discount
        if m.futures_basis_annualized < 1.0:
            matched.append(f"Basis backwardation / collapse ({m.futures_basis_annualized:.1f}%)")

        return {
            "regime_id": "CASCADE_FORCED_DELEVERAGING",
            "name": "Cascade / Forced Deleveraging",
            "diagnosis": "Forced long unwind in progress",
            "playbook": "Wait (0.0x). Do not buy the waterfall.",
            "suitability": "Restricted / Danger Zone",
            "priority": 1,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": 0.0,
            "action": "Wait / Cash Only (0.0x)",
            "rotation": "Remain USDT",
            "entry_instruction": "Hold 100% cash. Wait for stabilization (OI flat, liquidations drop, local low reclaim).",
            "stop_rule": "Capitulation wick low - 1.0% (No active trade)"
        }

    def _eval_distribution_bear(self, m: MarketMetrics) -> dict:
        """Regime 5: Distribution / Bear Continuation"""
        matched = []
        # 1. Price below key VWAPs / EMAs or making lower structure
        if m.price < m.daily_vwap and m.price < m.ema_20d and m.price < m.ema_50d:
            matched.append("Price below Daily VWAP, 20D EMA, and 50D EMA")
        # 2. Spot CVD persistently weak or diverging negative
        if m.spot_cvd_slope_7d < 0 or m.spot_cvd_ratio <= 0.88:
            matched.append(f"Spot CVD persistently negative (Slope < 0 / Ratio {m.spot_cvd_ratio:.2f})")
        # 3. Bounces on light spot volume
        if m.spot_vol_ratio < 0.95:
            matched.append(f"Spot volume depressed ({m.spot_vol_ratio:.2f}x 20D MA)")
        # 4. Funding neutral-to-positive (trapped longs) or weak basis
        if m.funding_rate >= 0.002 or m.futures_basis_annualized < 4.0:
            matched.append(f"Trapped longs paying funding ({m.funding_rate*100:.3f}%) / compressed basis ({m.futures_basis_annualized:.1f}%)")

        return {
            "regime_id": "DISTRIBUTION_BEAR_CONTINUATION",
            "name": "Distribution / Bear Continuation",
            "diagnosis": "Weak demand or active distribution",
            "playbook": "Defensive / Cash (0.0x)",
            "suitability": "Restricted / Cash Zone",
            "priority": 2,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": 0.0,
            "action": "Defensive Cash (0.0x)",
            "rotation": "Remain USDT",
            "entry_instruction": "Strict Cash (100% USDT). Treat bounces as exit liquidity. Only reverse on structure + Spot CVD reclaim.",
            "stop_rule": "Invalidation: 1D close > 50D EMA with positive Spot CVD"
        }

    def _eval_transition_mixed(self, m: MarketMetrics, candidates: List[dict]) -> dict:
        """Default Fallback: Transition / Mixed (when no regime achieves majority >= 3)"""
        top_cand = max(candidates, key=lambda x: x["matches_count"])
        matched = [
            f"No single regime achieved a >=3/4 majority (Highest: {top_cand['name']} with {top_cand['matches_count']}/4)",
            "Market indicators are conflicting or transitioning between regimes"
        ]
        return {
            "regime_id": "TRANSITION_MIXED",
            "name": "Transition / Mixed",
            "diagnosis": "Signals mixed or transition between regimes",
            "playbook": "Stand Aside / Minimal Size (0.0x)",
            "suitability": "Neutral / Stand Aside",
            "priority": 5,
            "matches_count": top_cand["matches_count"],
            "matched": matched,
            "sizing_factor": 0.0,
            "action": "Stand Aside / Cash (0.0x)",
            "rotation": "Remain USDT",
            "entry_instruction": "Hold cash reserve. Wait for structural clarity or directional CVD confirmation before committing capital.",
            "stop_rule": "N/A (Holding 100% Cash Reserve)"
        }

    # --- 6-Factor Liquidation Magnet Override Engine ---

    def _evaluate_dominant_magnet(
        self,
        m: MarketMetrics,
        upper: Optional[LiquidationCluster],
        lower: Optional[LiquidationCluster]
    ) -> Tuple[str, str, str, dict]:
        """
        Evaluates Upper vs Lower Liquidation Magnet using the 6 Override Factors:
          1. Cluster Size / Magnitude Disparity
          2. Spot vs Derivatives Leadership (Spot CVD)
          3. Crowding and Fuel (Funding Rate + Retail L/S + OI Flow)
          4. Higher-Timeframe Market Structure (Range/Base vs Trend)
          5. Distance Asymmetry
          6. Volatility Regime (ATR Compression)
        All 6 factors actively contribute to the numerical gravitational score.
        """
        if not upper and not lower:
            return "Neutral / None", "NEUTRAL: No clear clusters", "No liquidation clusters detected.", {}
        if not upper:
            desc = f"LOWER (${lower.price_level:,.0f}, -{lower.distance_pct:.2f}%)"
            return "Lower Long Sweep Magnet", desc, f"Only lower cluster active (${lower.estimated_vol_usd/1e6:.1f}M at ${lower.price_level:,.0f}).", {}
        if not lower:
            desc = f"UPPER (${upper.price_level:,.0f}, +{upper.distance_pct:.2f}%)"
            return "Upper Short Squeeze Magnet", desc, f"Only upper cluster active (${upper.estimated_vol_usd/1e6:.1f}M at ${upper.price_level:,.0f}).", {}

        u_dist = max(0.04, upper.distance_pct)
        l_dist = max(0.04, lower.distance_pct)
        u_vol = max(1000.0, upper.estimated_vol_usd)
        l_vol = max(1000.0, lower.estimated_vol_usd)

        # Factor 1: Cluster Size / Magnitude
        size_ratio_l_to_u = l_vol / u_vol
        if size_ratio_l_to_u >= 3.0:
            f1_text = f"LOWER is {size_ratio_l_to_u:.1f}x larger (${l_vol/1e6:.1f}M vs ${u_vol/1e6:.1f}M); massive liquidity advantage"
        elif size_ratio_l_to_u <= 0.33:
            f1_text = f"UPPER is {1.0/size_ratio_l_to_u:.1f}x larger (${u_vol/1e6:.1f}M vs ${l_vol/1e6:.1f}M); strong liquidity advantage"
        else:
            f1_text = f"Balanced magnitudes (${u_vol/1e6:.1f}M UPPER vs ${l_vol/1e6:.1f}M LOWER; ratio {size_ratio_l_to_u:.1f}x)"

        # Factor 2: Spot vs Derivatives Leadership
        spot_override_upper = False
        spot_override_lower = False
        if m.spot_cvd_ratio >= 1.25:
            f2_text = f"Spot CVD positive ({m.spot_cvd_ratio:.2f}); genuine spot demand supports upside pull"
            spot_override_upper = True
        elif m.spot_cvd_ratio <= 0.85:
            f2_text = f"Spot CVD negative ({m.spot_cvd_ratio:.2f}); spot selling pressure reinforces downside gravity"
            spot_override_lower = True
        else:
            f2_text = f"Spot CVD neutral ({m.spot_cvd_ratio:.2f}); not overriding cluster size or distance"

        # Factor 3: Crowding & Fuel (Funding + L/S + OI)
        crowd_lower = False
        crowd_upper = False
        if m.funding_rate >= 0.008 and m.long_short_account_ratio >= 1.70:
            crowd_lower = True
            f3_text = f"Longs crowded (L/S {m.long_short_account_ratio:.2f}, funding {m.funding_rate*100:.3f}%); trapped longs provide fuel below"
        elif m.funding_rate <= -0.005:
            crowd_upper = True
            f3_text = f"Shorts crowded (funding negative {m.funding_rate*100:.3f}%); short liquidations provide upside fuel"
        else:
            f3_text = f"Funding controlled ({m.funding_rate*100:.3f}%), L/S ratio {m.long_short_account_ratio:.2f}; moderate crowding"

        # Factor 4: Regime / Higher-Timeframe Structure
        regime_upper_bias = False
        regime_lower_bias = False
        if m.price < m.ma_200d and m.price < m.daily_vwap:
            f4_text = "Price below VWAP & 200D MA; structural weight favors lower base retests"
            regime_lower_bias = True
        elif m.price > m.daily_vwap and m.price > m.weekly_vwap:
            f4_text = "Price above Daily & Weekly VWAP; structural momentum favors upper continuation"
            regime_upper_bias = True
        else:
            f4_text = "Range / base compression; positioning magnets dominate immediate travel"

        # Factor 5: Distance Asymmetry
        dist_ratio = l_dist / u_dist
        if 0.6 <= dist_ratio <= 1.6:
            f5_text = f"Distances roughly comparable ({u_dist:.2f}% UPPER vs {l_dist:.2f}% LOWER); size and crowding decide priority"
        elif dist_ratio > 1.6:
            f5_text = f"UPPER is closer ({u_dist:.2f}% vs {l_dist:.2f}%); proximity favors UPPER unless size disparity is extreme"
        else:
            f5_text = f"LOWER is closer ({l_dist:.2f}% vs {u_dist:.2f}%); proximity favors LOWER"

        # Factor 6: Volatility Regime (ATR)
        is_atr_compressed = m.atr_compression_pct >= 35.0
        if is_atr_compressed:
            f6_text = f"ATR compressed {m.atr_compression_pct:.1f}%; low volatility amplifies magnetic pull of nearest dense pool"
        else:
            f6_text = f"ATR normal ({m.atr:,.0f} USD); price has sufficient room for wider expansion"

        # --- Compute Gravitational Pull Score (All 6 Factors Active) ---
        pull_upper = (u_vol / 1e6) / (u_dist ** 1.15)
        pull_lower = (l_vol / 1e6) / (l_dist ** 1.15)

        if crowd_lower:
            pull_lower *= 1.85
        if crowd_upper:
            pull_upper *= 1.85

        if spot_override_upper:
            pull_upper *= 1.60
            pull_lower *= 0.70
        elif spot_override_lower:
            pull_lower *= 1.60
            pull_upper *= 0.70

        if size_ratio_l_to_u >= 5.0:
            pull_lower *= min(2.5, (size_ratio_l_to_u / 5.0) ** 0.5)
        elif size_ratio_l_to_u <= 0.2:
            pull_upper *= min(2.5, ((1.0 / size_ratio_l_to_u) / 5.0) ** 0.5)

        if regime_upper_bias:
            pull_upper *= 1.30
            pull_lower *= 0.85
        elif regime_lower_bias:
            pull_lower *= 1.30
            pull_upper *= 0.85

        if is_atr_compressed:
            if u_dist < l_dist:
                pull_upper *= 1.35
            else:
                pull_lower *= 1.35

        factors_dict = {
            "factor_1_size": f1_text,
            "factor_2_spot_leadership": f2_text,
            "factor_3_crowding_fuel": f3_text,
            "factor_4_regime_structure": f4_text,
            "factor_5_asymmetry": f5_text,
            "factor_6_atr_volatility": f6_text,
        }

        # Decision
        if pull_lower >= pull_upper:
            dominant_name = "Lower Long Sweep Magnet"
            if size_ratio_l_to_u >= 2.5 and u_dist < l_dist:
                reason_short = f"LOWER (Size {size_ratio_l_to_u:.1f}x larger outweighs distance edge; longs crowded)"
                reason_full = f"Lower cluster chosen: massive liquidity pool (${l_vol/1e6:.1f}M vs ${u_vol/1e6:.1f}M, {size_ratio_l_to_u:.1f}x) overrides minor upper proximity, amplified by crowded long positioning."
            elif l_dist <= u_dist:
                reason_short = f"LOWER (Nearest -{l_dist:.2f}% + larger volume ${l_vol/1e6:.1f}M; spot neutral)"
                reason_full = f"Lower cluster chosen: nearest distance (-{l_dist:.2f}%) combined with superior volume density (${l_vol/1e6:.1f}M)."
            else:
                reason_short = f"LOWER (Downside gravity score {pull_lower:.0f} vs {pull_upper:.0f}; crowding fuel below)"
                reason_full = f"Lower cluster chosen based on aggregate gravitational pull ({pull_lower:.0f} vs {pull_upper:.0f}) and trapped long leverage."
        else:
            dominant_name = "Upper Short Squeeze Magnet"
            if size_ratio_l_to_u <= 0.4 and l_dist < u_dist:
                reason_short = f"UPPER (Size {1.0/size_ratio_l_to_u:.1f}x larger outweighs distance edge; upside fuel)"
                reason_full = f"Upper cluster chosen: superior liquidation volume (${u_vol/1e6:.1f}M vs ${l_vol/1e6:.1f}M) outweighs minor lower proximity."
            elif u_dist <= l_dist and spot_override_upper:
                reason_short = f"UPPER (Nearest +{u_dist:.2f}% + Spot CVD confirming upside + compressed ATR)"
                reason_full = f"Upper cluster chosen: nearest proximity (+{u_dist:.2f}%) reinforced by positive spot CVD leadership."
            else:
                reason_short = f"UPPER (Nearest +{u_dist:.2f}% vs -{l_dist:.2f}%; compressed ATR favors path of least resistance)"
                reason_full = f"Upper cluster chosen as path of least resistance in compressed ATR regime."

        return dominant_name, reason_short, reason_full, factors_dict

    def _calculate_stop(self, regime_id: str, m: MarketMetrics) -> Tuple[float, float]:
        """Calculates stop price and distance % based on the exact regime protocol."""
        current_price = m.price
        stop_price = current_price * 0.97

        if regime_id == "SPOT_LED_EXPANSION":
            stop_price = m.swing_low_4h * (1.0 - 0.006)
        elif regime_id == "LEVERAGED_FRAGILE_UPSIDE":
            stop_price = m.swing_low_4h
        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            stop_price = m.capitulation_wick_low * (1.0 - 0.005)
        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            stop_price = m.capitulation_wick_low * (1.0 - 0.01)
        elif regime_id == "DISTRIBUTION_BEAR_CONTINUATION":
            stop_price = m.ema_50d * 1.01
        elif regime_id == "TRANSITION_MIXED":
            stop_price = current_price * 0.97

        stop_dist_pct = abs(current_price - stop_price) / current_price * 100
        return stop_price, stop_dist_pct

    def _get_plain_english_breakdown(
        self,
        regime_id: str,
        m: Optional[MarketMetrics],
        stop_price: float,
        stop_dist_pct: float,
        sizing: float,
        dominant_magnet: str
    ) -> Tuple[str, List[str], str, str]:
        """
        Translates quantitative findings into crystal-clear plain English for beginners.
        """
        if regime_id == "SPOT_LED_EXPANSION":
            verdict = "Real cash buyers are aggressively driving Bitcoin higher on strong volume. This is an authentic, institutional-led bull market expansion."
            why_points = [
                "True Spot Accumulation: Trading volume and spot buyer order flow are expanding together. This move is driven by real capital, not borrowed leverage.",
                "Healthy Speculative Conditions: Futures funding rates remain balanced and open interest is stable, confirming the rally is not over-leveraged.",
                "Structural Strength: Bitcoin is holding firmly above both daily and weekly trendlines, consistently making higher highs."
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? When real spot demand leads the market with low leverage, the odds heavily favor continuation. High allocation is mathematically warranted."
            why_stop = f"Your Safety Net: Stop is placed at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away). If the recent 4-hour low fails, exit to protect accumulated profits."

        elif regime_id == "LEVERAGED_FRAGILE_UPSIDE":
            verdict = "Warning: The price may look high, but this rally is built on dangerous borrowed futures debt rather than real spot buyers. High probability of a sharp correction."
            why_points = [
                "Artificial Buying Pressure: Futures leverage is expanding rapidly while actual spot cash buying is declining or flat.",
                "Excessive Speculation & High Fees: Borrowing rates have surged, showing that late retail traders are piling into hyper-leveraged longs.",
                "Fragile Ceiling: Once leverage runs out of fresh capital, cascading stop-outs will trigger a fast, painful downward flush."
            ]
            why_sizing = "Why 0% Sizing (Take Profit)? Never chase a rally built on borrowed leverage. The system directs you to buy zero new Bitcoin, harvest 33% profit into cash, and trail stops tightly."
            why_stop = f"Your Safety Net: Trail your protective stop tightly at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away). If price drops, lock in cash profits automatically."

        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            verdict = "Bitcoin is oscillating in a defined trading range. Market makers are hunting trapped leverage on both sides. This is the core operating zone to trade the Liquidation Magnet."
            why_points = [
                "Defined Consolidation Range: Volatility has compressed and price is trading between established floor and ceiling levels.",
                "Positioning Imbalance: One side of the market is overcrowded with leverage, creating a high-probability magnetic pull toward their liquidation orders.",
                "Controlled Market Fuel: Neither buyers nor sellers have full macro control, making mean-reversion toward liquidation pools the dominant statistical edge."
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? We are trading inside a range toward the dominant {dominant_magnet}. Allocating {sizing*100:.0f}% of cash secures an advantageous entry while preserving cash buffer."
            why_stop = f"Your Safety Net: Stop-loss is placed at ${stop_price:,.2f} ({stop_dist_pct:.2f}% below current price). If price breaks out of the range on the downside, exit immediately to keep loss minimal."

        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            verdict = "Emergency Waterfall: Over-leveraged traders are being forcibly liquidated in a domino effect. Stand completely aside and hold cash."
            why_points = [
                "Forced Liquidation Chain: Traders are getting margin called, and exchanges are automatically market-selling their collateral.",
                "Plunging Open Interest: Billions in speculative positions are being wiped out in minutes.",
                "Falling Knife Danger: Bids are vanishing and price is falling vertically. Trying to guess the exact bottom here is extremely dangerous."
            ]
            why_sizing = "Why 0% Sizing (100% Cash)? The system strictly enforces zero buying during active waterfalls. Wait until forced selling completely runs out of fuel."
            why_stop = "Your Safety Net: No active trades are placed during a cascade. 100% capital preservation in cash."

        elif regime_id == "DISTRIBUTION_BEAR_CONTINUATION":
            verdict = "Bitcoin is locked in an entrenched downtrend. Every small bounce is met with heavy selling. Cash is the only safe position."
            why_points = [
                "Sellers in Control: Price is trapped below key 20-day and 50-day moving averages and Daily VWAP, confirming persistent downward pressure.",
                "Depressed Spot Demand: Institutional buyers are on the sidelines; multi-week spot accumulation remains consistently negative.",
                "Dip-Buyer Traps: Retail traders trying to 'buy the dip' are consistently getting stopped out."
            ]
            why_sizing = "Why 0% Sizing (100% USDT Cash)? In a confirmed bear trend, your greatest edge is patience. Holding 100% cash guarantees complete capital preservation."
            why_stop = f"Your Safety Net: No buying permitted until Bitcoin definitively reclaims the 50-day moving average (${stop_price:,.2f}) with real spot volume."

        elif regime_id == "TRANSITION_MIXED":
            verdict = "Market signals are currently mixed or transitioning between regimes. The safest and highest-expectancy move is sitting patiently in cash."
            why_points = [
                "No Clear Majority: The market does not satisfy the required 3 out of 4 criteria for any single directional regime.",
                "Conflicting Indicators: Spot order flow, futures positioning, and price structure are giving mixed signals.",
                "Preserve Capital: In systematic trading, waiting for clarity has a higher mathematical expectancy than forcing trades in ambiguous conditions."
            ]
            why_sizing = "Why 0% Sizing (Hold Cash)? When the regime is not clear, size is set to zero. Never gamble capital when the market lacks a clean edge."
            why_stop = "Your Safety Net: N/A. 100% USDT cash reserve."

        else:  # DATA_INCOMPLETE
            verdict = "Market data feed is temporarily offline or incomplete. All trading recommendations are locked to protect your funds."
            why_points = [
                "Zero-Guesswork Policy: The monitor never invents or approximates missing exchange data.",
                "Capital Protection First: If live order flow or open interest data cannot be verified, the only responsible action is holding cash.",
                "Automatic Recovery: The system checks exchange feeds every 30 minutes and will resume once verified data is restored."
            ]
            why_sizing = "Why 0% Sizing? Never trade blind. Keep 100% of your portfolio in cash until data integrity is confirmed."
            why_stop = "N/A: No active trades are placed while data is incomplete."

        return verdict, why_points, why_sizing, why_stop
