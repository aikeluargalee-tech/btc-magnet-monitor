from typing import List, Tuple, Optional, Dict, Any
from engine.models import MarketMetrics, LiquidationCluster, RegimeResult, LSCEState

class RegimeClassifier:
    """
    Simplified 5-Regime Radar with Liquidation Sweep Confirmation Engine (LSCE):
      1. Spot-Led Expansion
      2. Leveraged / Fragile Upside
      3. Range / Liquidation Magnet (Core Operating Zone)
      4. Cascade / Forced Deleveraging
      5. Distribution / Bear Continuation
      Default: Transition / Mixed (when signals are conflicted or transitioning)

    Core Institutional Upgrades:
      - Logical Consistency: No conflicting 0.0x "Range Resistance" at mid-channel; conflicted signals cleanly map to Transition / Mixed.
      - Dual Imbalance Accounting: Distinguishes immediate cluster imbalance (100x vs 50-100x) from total leverage ladder imbalance (10x-100x).
      - Liquidation Sweep Confirmation Engine (LSCE): 4 deterministic states (UNTESTED, SWEEP_IN_PROGRESS, SWEEP_FAILED_BREAKDOWN, SWEEP_AND_RECLAIM_CONFIRMED).
      - Dual Inviolable Stops: Structural 1H candle close vs Disaster Hard Stop below 200D SMA & 25x shelf.
    """

    def classify(self, m: Optional[MarketMetrics], clusters: List[LiquidationCluster]) -> RegimeResult:
        if m is None or not clusters:
            return self._create_data_incomplete_result("Market metrics or liquidation clusters unavailable.")

        upper_cluster = next((c for c in clusters if c.side == "upper"), None)
        lower_cluster = next((c for c in clusters if c.side == "lower"), None)

        # 1. Evaluate Liquidation Sweep Confirmation Engine (LSCE)
        lsce = self._eval_lsce(m, lower_cluster, upper_cluster)

        # 2. Evaluate Liquidation Magnet & Unified 10x-100x Modeled Ladder
        (
            dominant_magnet,
            magnet_title,
            magnet_reason,
            magnet_factors,
            imm_ratio,
            tot_u_vol,
            tot_l_vol,
            tot_ratio,
            liquidation_ladder,
        ) = self._evaluate_dominant_magnet(m, upper_cluster, lower_cluster)

        # 3. Evaluate the 5 regimes (Majority-based: >= 3 of 4 matches)
        candidates = [
            self._eval_cascade(m),
            self._eval_leveraged_upside(m),
            self._eval_distribution_bear(m),
            self._eval_range_magnet(m, dominant_magnet, magnet_title, lsce),
            self._eval_spot_expansion(m),
        ]

        # Filter candidates meeting majority threshold (>= 3 matches)
        valid = [c for c in candidates if c["matches_count"] >= 3]

        # Check for conflicted signals: If Range matches but has strong distribution / backwardation overlay without reclaim
        is_conflicted = (
            m.price < m.daily_vwap and
            m.price < m.weekly_vwap and
            m.futures_basis_annualized < 0.0 and
            m.bids_asks_depth_ratio < 0.35 and
            lsce.status != "SWEEP_AND_RECLAIM_CONFIRMED"
        )

        if is_conflicted and any(c["regime_id"] == "RANGE_LIQUIDATION_MAGNET" for c in valid):
            # Demote Range to Transition / Mixed due to unresolved downside fragility (zero hardcoded prose numbers)
            cvd_desc = f"positive Spot CVD ({m.spot_cvd_ratio:.2f})" if m.spot_cvd_ratio >= 1.0 else f"weak Spot CVD ({m.spot_cvd_ratio:.2f})"
            conflict_txt = (
                f"Conflicted signals: {cvd_desc} countered by sub-VWAP price (${m.price:,.2f} vs "
                f"Daily ${m.daily_vwap:,.2f} / Weekly ${m.weekly_vwap:,.2f}), "
                f"futures backwardation ({m.futures_basis_annualized:+.2f}%), and "
                f"thin order-book bids ({m.bids_asks_depth_ratio:.2f} depth ratio)."
            )
            best = self._eval_transition_mixed(m, candidates, conflict_reason=conflict_txt)
        elif valid:
            valid.sort(key=lambda x: (x["priority"], -x["matches_count"]))
            best = valid[0]
        else:
            best = self._eval_transition_mixed(m, candidates)

        # 4. Calculate exact stop levels (Structural Invalidation vs Disaster Hard Stop)
        stop_price, stop_dist_pct, disaster_stop_price, disaster_dist_pct, struct_invalidation, stop_note = (
            self._calculate_stop(best["regime_id"], m)
        )

        # Risk budget compliance
        risk_budget_ok = disaster_dist_pct <= 4.5 and best["sizing_factor"] > 0 if best["rotation"] == "USDT -> BTC" else True

        # Percentage-based allocations
        sizing = best["sizing_factor"]
        max_spot_allocation = 80.0
        target_btc_pct = round(max_spot_allocation * sizing, 1)
        target_usdt_pct = round(100.0 - target_btc_pct, 1)
        recommended_cash_deploy = round(sizing * 100.0, 1)

        # Plain-English translation (all figures strictly bound to MarketMetrics & clusters)
        verdict, why_pts, why_sizing, why_stop = self._get_plain_english_breakdown(
            best["regime_id"],
            m,
            round(disaster_stop_price, 2),
            round(disaster_dist_pct, 2),
            sizing,
            dominant_magnet,
            lsce,
            lower_cluster,
        )

        if best["regime_id"] == "TRANSITION_MIXED":
            majority_score_str = f"Conflict Override ({len(best['matched'])}/4 conflict gates triggered)"
        else:
            majority_score_str = f"{best['matches_count']}/4 observations confirmed"
        notes = f"{best['diagnosis']}. Rule Score: {majority_score_str} ({', '.join(best['matched'])}). LSCE State: {lsce.status}."
        if best["regime_id"] == "RANGE_LIQUIDATION_MAGNET":
            notes += f" Active Magnet: {magnet_reason}"

        # Centralized Master Authorization Reconciliation (P0 State Guard):
        # A local sweep reclaim must NEVER claim "Authorized 0.75x entry" if macro portfolio allocation is 0.0x / Cash
        lsce_action_detail = lsce.action_verdict
        if (sizing == 0.0 or "USDT -> BTC" not in best["rotation"]) and lsce.status == "SWEEP_AND_RECLAIM_CONFIRMED":
            l_price_val = lower_cluster.price_level if lower_cluster else 0.0
            lsce_action_detail = f"Lower liquidation shelf (${l_price_val:,.0f}) swept, but new spot buying is strictly BLOCKED by macro regime ({best['name']}). Maintain 100% USDT Cash."

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
            stop_price=round(disaster_stop_price, 2),
            stop_distance_pct=round(disaster_dist_pct, 2),
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
            data_quality=m.data_quality,
            immediate_imbalance_ratio=round(imm_ratio, 1),
            total_ladder_lower_vol=round(tot_l_vol, 1),
            total_ladder_upper_vol=round(tot_u_vol, 1),
            total_ladder_imbalance_ratio=round(tot_ratio, 2),
            lsce_status=lsce.status,
            lsce_detail=lsce_action_detail,
            disaster_stop_price=round(disaster_stop_price, 2),
            disaster_stop_distance_pct=round(disaster_dist_pct, 2),
            structural_invalidation_level=round(struct_invalidation, 2),
            liquidation_ladder=liquidation_ladder,
            stop_placement_note=stop_note,
        )

    def _eval_lsce(
        self,
        m: MarketMetrics,
        lower: Optional[LiquidationCluster],
        upper: Optional[LiquidationCluster]
    ) -> LSCEState:
        """
        Liquidation Sweep Confirmation Engine (LSCE):
        Determines the exact execution phase of the nearest liquidation pool:
          1. UNTESTED: Price is >0.20% above the lower shelf; sweep not initiated.
          2. SWEEP_IN_PROGRESS: Price is within ±0.20% of shelf OR between -1.00% and 0% below shelf without reclaim.
          3. SWEEP_FAILED_BREAKDOWN: Price < 0.990 * shelf OR (< 4H swing low AND Depth Ratio < 0.35).
          4. SWEEP_AND_RECLAIM_CONFIRMED: 24H wick <= 1.002 * shelf, current > shelf, Spot CVD >= 1.05, Depth Ratio >= 0.50.
        """
        if not lower:
            return LSCEState(
                status="UNTESTED",
                cluster_tested="None",
                sweep_depth_pct=0.0,
                reclaim_level=round(m.price, 2),
                spot_absorption="Neutral",
                action_verdict="No active lower liquidation pool. Standing aside."
            )

        l_price = lower.price_level
        cur_price = m.price
        dist_pct = (cur_price - l_price) / cur_price * 100
        reclaim_gates = (
            f"Reclaim requires: price > ${l_price:,.0f} + Spot CVD >= 1.05 "
            f"(now {m.spot_cvd_ratio:.2f}) + Depth >= 0.50 (now {m.bids_asks_depth_ratio:.2f})."
        )

        # Sweep and Reclaim: Capitulation wick touched/pierced the cluster, and price bounced above it with absorption proof
        if m.capitulation_wick_low <= l_price * 1.002 and cur_price > l_price and m.spot_cvd_ratio >= 1.05 and m.bids_asks_depth_ratio >= 0.50:
            return LSCEState(
                status="SWEEP_AND_RECLAIM_CONFIRMED",
                cluster_tested=f"Lower Longs (${l_price:,.0f})",
                sweep_depth_pct=round(dist_pct, 2),
                reclaim_level=round(l_price, 2),
                spot_absorption=f"Strong (CVD {m.spot_cvd_ratio:.2f}, Depth {m.bids_asks_depth_ratio:.2f})",
                action_verdict=f"Lower liquidation shelf (${l_price:,.0f}) swept and reclaimed with positive spot absorption. Authorized 0.75x entry."
            )

        # Active Sweep in Progress: Current price is within ±0.20% of shelf OR probing down to -1.00% below shelf
        if abs(cur_price - l_price) / cur_price <= 0.0020 or (cur_price < l_price and cur_price >= l_price * 0.990):
            phase_verb = (
                f"actively piercing below (${cur_price:,.2f}, {dist_pct:+.2f}%)"
                if cur_price < l_price
                else f"testing within ±0.20% sweep zone (${cur_price:,.2f}, {dist_pct:+.2f}%)"
            )
            return LSCEState(
                status="SWEEP_IN_PROGRESS",
                cluster_tested=f"Lower Longs (${l_price:,.0f})",
                sweep_depth_pct=round(dist_pct, 2),
                reclaim_level=round(l_price, 2),
                spot_absorption=f"Testing (CVD {m.spot_cvd_ratio:.2f}, Depth {m.bids_asks_depth_ratio:.2f})",
                action_verdict=f"Price is {phase_verb} of the ${l_price:,.0f} modeled shelf. Do NOT front-run active liquidations. {reclaim_gates}"
            )

        # Sweep Failed Breakdown: Price fell significantly below cluster and bids collapsed
        if cur_price < l_price * 0.990 or (cur_price < m.swing_low_4h and m.bids_asks_depth_ratio < 0.35):
            return LSCEState(
                status="SWEEP_FAILED_BREAKDOWN",
                cluster_tested=f"Lower Longs (${l_price:,.0f})",
                sweep_depth_pct=round(dist_pct, 2),
                reclaim_level=round(m.swing_low_4h, 2),
                spot_absorption=f"Collapsed (Depth {m.bids_asks_depth_ratio:.2f})",
                action_verdict=f"Modeled shelf at ${l_price:,.0f} failed to hold (depth {m.bids_asks_depth_ratio:.2f}). Potential cascade in progress. Hold 100% USDT cash."
            )

        # Untested: Price is comfortably (>0.20%) above the lower cluster
        return LSCEState(
            status="UNTESTED",
            cluster_tested=f"Lower Longs (${l_price:,.0f})",
            sweep_depth_pct=round(dist_pct, 2),
            reclaim_level=round(l_price, 2),
            spot_absorption="Pending",
            action_verdict=f"Lower modeled pool (${l_price:,.0f}) is {dist_pct:+.2f}% away and untested. Maintain cash reserve."
        )

    def _eval_spot_expansion(self, m: MarketMetrics) -> dict:
        """Regime 1: Spot-Led Expansion"""
        matched = []
        if m.price > m.daily_vwap and m.price > m.weekly_vwap:
            matched.append("Price holding above Daily and Weekly VWAP")
        if m.spot_cvd_ratio >= 1.05 and (m.spot_cvd_slope_7d > 0 or m.spot_cvd_slope_14d > 0):
            matched.append(f"Spot CVD leading (Ratio {m.spot_cvd_ratio:.2f}, Slope +{m.spot_cvd_slope_7d:.0f})")
        if m.funding_rate <= 0.012 and m.oi_change_24h_pct <= 3.5:
            matched.append(f"Funding and OI controlled (Funding {m.funding_rate*100:.3f}%, OI 24h {m.oi_change_24h_pct:+.1f}%)")
        if m.spot_vol_ratio >= 1.0:
            matched.append(f"Spot volume confirmed ({m.spot_vol_ratio:.2f}x 20D MA)")

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
        if m.price_change_24h_pct > 0.8 and m.spot_cvd_ratio < 1.12:
            matched.append(f"Price rising (+{m.price_change_24h_pct:.2f}%) but Spot CVD lagging ({m.spot_cvd_ratio:.2f})")
        if m.oi_change_24h_pct >= 4.0 or m.perp_cvd_trend == "surging" or m.oi_change_3d_pct >= 10.0:
            matched.append(f"Futures leverage expanding (OI +{m.oi_change_24h_pct:.2f}% 24h, Perp CVD {m.perp_cvd_trend})")
        if m.funding_rate >= 0.015 or m.futures_basis_annualized >= 12.0:
            matched.append(f"Funding elevated ({m.funding_rate*100:.3f}%) or basis wide ({m.futures_basis_annualized:.1f}%)")
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

    def _eval_range_magnet(self, m: MarketMetrics, dom_magnet: str, dom_title: str, lsce: LSCEState) -> dict:
        """Regime 3: Range / Liquidation Magnet (Core Operating Zone)"""
        matched = []
        range_width_pct = (m.swing_high_4h - m.swing_low_4h) / m.price * 100
        if range_width_pct <= 4.5 or m.atr_compression_pct >= 30.0:
            matched.append(f"Defined range ({range_width_pct:.2f}% width) & ATR compressed {m.atr_compression_pct:.1f}%")
        if 0.90 <= m.spot_cvd_ratio <= 1.25:
            matched.append(f"Spot CVD neutral/balanced (Ratio {m.spot_cvd_ratio:.2f})")
        if (m.ls_ratio_available and m.long_short_account_ratio >= 1.6) or m.funding_rate >= 0.008 or m.funding_rate <= -0.004:
            if m.ls_ratio_available:
                matched.append(f"Positioning crowded (L/S {m.long_short_account_ratio:.2f}, funding {m.funding_rate*100:.3f}%)")
            else:
                matched.append(f"Funding positioning skewed (funding {m.funding_rate*100:.3f}%; L/S feed unavailable)")
        matched.append("Clear liquidation clusters active above and below price")

        mid_channel = (m.swing_low_4h + m.swing_high_4h) / 2.0

        # Action and Sizing are strictly determined by the LSCE state to eliminate internal contradictions:
        if lsce.status == "SWEEP_AND_RECLAIM_CONFIRMED":
            sizing = 0.75
            action = f"Trade the Magnet: Buy Spot ({sizing:.2f}x)"
            rotation = "USDT -> BTC"
            entry_inst = "Confirmed sweep & reclaim: 50% market spot / 50% limit at reclaimed range floor."
            playbook = f"Core Operating Zone — Trade the Magnet ({sizing:.2f}x)"
        elif lsce.status == "SWEEP_IN_PROGRESS":
            sizing = 0.0
            action = "Wait / Active Sweep in Progress (0.0x)"
            rotation = "Remain USDT"
            entry_inst = "Active liquidation sweep underway. Do NOT front-run. Wait for 1H close reclaim above cluster."
            playbook = "Active Sweep Protection: Stand Aside in Cash (0.0x)"
        elif m.price >= m.swing_high_4h * 0.990:
            sizing = 0.0
            action = "Range Resistance: Trim to Cash (0.0x)"
            rotation = "BTC -> USDT"
            entry_inst = "Price testing range ceiling and lower magnet dominates. Harvest profit to USDT cash."
            playbook = "Range Resistance: Harvest to Cash (0.0x)"
        else:
            sizing = 0.0
            action = "Wait for Sweep Reclaim: Cash (0.0x)"
            rotation = "Remain USDT"
            entry_inst = "Price oscillating mid-range without confirmed sweep reclaim. Maintain dry powder."
            playbook = "Range Wait: Stand Aside for Reclaim (0.0x)"

        return {
            "regime_id": "RANGE_LIQUIDATION_MAGNET",
            "name": "Range / Liquidation Magnet",
            "diagnosis": "Positioning imbalance and forced liquidations dominate",
            "playbook": playbook,
            "suitability": "Core Operating Zone (High Edge)",
            "priority": 3,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": sizing,
            "action": action,
            "rotation": rotation,
            "entry_instruction": entry_inst,
            "stop_rule": "Structural: 1H close < 4H swing low | Inviolable: Below 200D SMA & 25x shelf -0.7%"
        }

    def _eval_cascade(self, m: MarketMetrics) -> dict:
        """Regime 4: Cascade / Forced Deleveraging"""
        matched = []
        if m.price_change_1h_pct <= -2.8 or m.price_change_24h_pct <= -6.0:
            matched.append(f"Sharp price drop ({m.price_change_1h_pct:.2f}% 1h / {m.price_change_24h_pct:.2f}% 24h)")
        if m.oi_change_1h_pct <= -3.5 or m.oi_change_4h_pct <= -7.0:
            matched.append(f"OI crashing ({m.oi_change_1h_pct:.2f}% 1h / {m.oi_change_4h_pct:.2f}% 4h)")
        if m.funding_rate <= -0.005:
            matched.append(f"Funding plunged deeply negative ({m.funding_rate*100:.3f}%)")
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
        if m.price < m.daily_vwap and m.price < m.ema_20d and m.price < m.ema_50d:
            matched.append("Price below Daily VWAP, 20D EMA, and 50D EMA")
        if m.spot_cvd_slope_7d < 0 or m.spot_cvd_ratio <= 0.88:
            matched.append(f"Spot CVD persistently negative (Slope < 0 / Ratio {m.spot_cvd_ratio:.2f})")
        if m.spot_vol_ratio < 0.95:
            matched.append(f"Spot volume depressed ({m.spot_vol_ratio:.2f}x 20D MA)")
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

    def _eval_transition_mixed(self, m: MarketMetrics, candidates: List[dict], conflict_reason: str = None) -> dict:
        """Default Fallback: Transition / Mixed (when signals are conflicted or no clean regime majority)"""
        top_cand = max(candidates, key=lambda x: x["matches_count"])
        matched = []
        if conflict_reason:
            matched.append(conflict_reason)
            matched.append(
                f"Sub-VWAP Gate Triggered: Spot (${m.price:,.2f}) trails Daily VWAP (${m.daily_vwap:,.2f}) "
                f"& Weekly VWAP (${m.weekly_vwap:,.2f})"
            )
            matched.append(
                f"Derivatives & Depth Gate Triggered: Basis {m.futures_basis_annualized:+.2f}% annualized, "
                f"Book Depth Ratio {m.bids_asks_depth_ratio:.2f} (<0.35 threshold)"
            )
            matched.append(f"Candidate ({top_cand['name']}) demoted pending spot reclaim or LSCE confirmation")
        else:
            matched.append(f"Top candidate ({top_cand['name']}) scored only {top_cand['matches_count']}/4 (<3 required)")
            matched.append(f"Sub-VWAP / Trend status: Spot ${m.price:,.2f} vs Daily VWAP ${m.daily_vwap:,.2f}")
            matched.append(f"Order Flow & Basis: Spot CVD {m.spot_cvd_ratio:.2f} | Futures Basis {m.futures_basis_annualized:+.2f}%")
            matched.append("Capital preservation default: hold 100% USDT cash until >=3/4 regime consensus emerges")

        return {
            "regime_id": "TRANSITION_MIXED",
            "name": "Transition / Mixed",
            "diagnosis": "Signals mixed or transitioning between regimes (Downside Fragility)",
            "playbook": "Stand Aside / Cash (0.0x)",
            "suitability": "Neutral / Stand Aside",
            "priority": 5,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": 0.0,
            "action": "Stand Aside / Cash (0.0x)",
            "rotation": "Remain USDT",
            "entry_instruction": "Hold 100% USDT cash reserve. Do not buy into unconfirmed sweep. Wait for daily VWAP reclaim or post-sweep proof.",
            "stop_rule": "Structural: 1H close < 4H swing low | Inviolable: Below 200D SMA & 25x shelf -0.7%"
        }

    def _evaluate_dominant_magnet(
        self,
        m: MarketMetrics,
        upper: Optional[LiquidationCluster],
        lower: Optional[LiquidationCluster]
    ) -> Tuple[str, str, str, dict, float, float, float, float, List[Dict[str, Any]]]:
        """
        Evaluates Upper vs Lower Liquidation Magnet using the 6 Override Factors & Dual Imbalance Accounting:
          1. Immediate Imbalance: Nearest 100x Long vs Nearest 50-100x Short
          2. Total Ladder Imbalance: Modeled 10x-100x Longs vs 10x-100x Shorts anchored to tracked OI & 4H extrema
        Also builds one canonical 6-tier liquidation_ladder list shared by index.html, text.html, and the AI prompt.
        """
        u_vol = upper.estimated_vol_usd / 1e6 if upper else 0.0
        l_vol = lower.estimated_vol_usd / 1e6 if lower else 0.0

        # Scale modeled outer 25x & 10x bands proportionally from tracked venue OI notional & directional L/S skew
        oi_notional_m = max(10.0, (m.open_interest * m.price) / 1e6)
        ls = m.long_short_account_ratio if (m.ls_ratio_available and m.long_short_account_ratio > 0) else 1.0
        long_share = ls / (1.0 + ls)
        l_crowd_w = max(0.50, long_share / 0.50)
        u_crowd_w = max(0.50, (1.0 - long_share) / 0.50)

        u_25_vol = round(max(1.0, oi_notional_m * 0.032 * u_crowd_w), 1)
        u_10_vol = round(max(1.0, oi_notional_m * 0.024 * u_crowd_w), 1)
        l_25_vol = round(max(1.0, oi_notional_m * 0.040 * l_crowd_w), 1)
        l_10_vol = round(max(1.0, oi_notional_m * 0.028 * l_crowd_w), 1)

        tot_u_vol = round(u_10_vol + u_25_vol + u_vol, 1)
        tot_l_vol = round(l_10_vol + l_25_vol + l_vol, 1)

        imm_ratio = l_vol / max(u_vol, 0.1)
        tot_ratio = tot_l_vol / max(tot_u_vol, 0.1)

        atr_safe = max(m.atr, 1.0)
        cur_p = max(m.price, 1.0)
        s10_p = round(m.swing_high_4h * 1.025, 2)
        s25_p = round(m.swing_high_4h * 1.012, 2)
        u_near_p = round(upper.price_level, 2) if upper else round(m.swing_high_4h * 1.005, 2)
        l_near_p = round(lower.price_level, 2) if lower else round(m.swing_low_4h * 0.995, 2)
        l25_p = round(m.swing_low_4h * 0.988, 2)
        l10_p = round(m.swing_low_4h * 0.975, 2)

        def _row(tier: str, lev: str, side: str, lvl: float, vol_m: float, dist_pct_override: Optional[float] = None, dist_atr_override: Optional[float] = None, is_nearest: bool = False) -> Dict[str, Any]:
            signed_pct = ((lvl - cur_p) / cur_p) * 100.0
            if dist_pct_override is not None:
                mag_pct = dist_pct_override
                signed_pct = mag_pct if side == "upper" else -mag_pct
            if dist_atr_override is not None:
                signed_atr = dist_atr_override if side == "upper" else -dist_atr_override
            else:
                signed_atr = (lvl - cur_p) / atr_safe
            return {
                "tier": tier,
                "leverage": lev,
                "side": side,
                "price": lvl,
                "distance_pct": round(signed_pct, 2),
                "distance_atr": round(signed_atr, 2),
                "estimated_vol_m": round(vol_m, 1),
                "modeled": True,
                "is_nearest": is_nearest,
            }

        ladder = [
            _row("10x Shorts", "10x", "upper", s10_p, u_10_vol),
            _row("25x Shorts", "25x", "upper", s25_p, u_25_vol),
            _row(
                "50-100x Shorts",
                "50-100x",
                "upper",
                u_near_p,
                u_vol,
                dist_pct_override=upper.distance_pct if upper else None,
                dist_atr_override=upper.distance_atr if upper else None,
                is_nearest=True,
            ),
            _row(
                "100x Longs",
                "100x",
                "lower",
                l_near_p,
                l_vol,
                dist_pct_override=lower.distance_pct if lower else None,
                dist_atr_override=lower.distance_atr if lower else None,
                is_nearest=True,
            ),
            _row("25x Longs", "25x", "lower", l25_p, l_25_vol),
            _row("10x Longs", "10x", "lower", l10_p, l_10_vol),
        ]

        if not upper and not lower:
            return "Neutral / None", "NEUTRAL: No clear clusters", "No liquidation clusters detected.", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio, ladder
        if not upper:
            desc = f"LOWER (${lower.price_level:,.0f}, -{lower.distance_pct:.2f}%)"
            return "Lower Long Sweep Magnet", desc, f"Only lower modeled cluster active (${lower.estimated_vol_usd/1e6:.1f}M).", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio, ladder
        if not lower:
            desc = f"UPPER (${upper.price_level:,.0f}, +{upper.distance_pct:.2f}%)"
            return "Upper Short Squeeze Magnet", desc, f"Only upper modeled cluster active (${upper.estimated_vol_usd/1e6:.1f}M).", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio, ladder

        u_dist_raw = upper.distance_pct
        l_dist_raw = lower.distance_pct
        u_dist = max(0.04, u_dist_raw)
        l_dist = max(0.04, l_dist_raw)

        imm_disp = f"~{round(imm_ratio):.0f}x" if imm_ratio >= 10 else f"{imm_ratio:.1f}x"
        f1_text = (
            f"Immediate Tier (Modeled): LOWER is {imm_disp} larger (~${l_vol:.1f}M vs ~${u_vol:.1f}M) | "
            f"Total Ladder (10x-100x Modeled): LOWER is {tot_ratio:.2f}x (~${tot_l_vol:.1f}M vs ~${tot_u_vol:.1f}M)"
        )
        f2_text = f"Spot CVD ratio {m.spot_cvd_ratio:.2f} vs Perp trend {m.perp_cvd_trend}"
        if m.ls_ratio_available:
            f3_text = f"Funding {m.funding_rate*100:+.4f}%, Retail L/S {m.long_short_account_ratio:.2f} ({long_share*100:.1f}% long)"
        else:
            f3_text = f"Funding {m.funding_rate*100:+.4f}%, Retail L/S ratio unavailable on fallback feed"
        f4_text = (
            "Range compression with downside fragility (sub-VWAP)"
            if m.price < m.daily_vwap
            else "Range structure above Daily VWAP"
        )
        f5_text = f"LOWER is -{l_dist_raw:.2f}% away vs UPPER +{u_dist_raw:.2f}% away"
        f6_text = f"ATR compressed {m.atr_compression_pct:.1f}% (${m.atr:,.0f} 1H ATR)"

        pull_upper = (u_vol / 1e6) / (u_dist ** 1.15)
        pull_lower = (l_vol / 1e6) / (l_dist ** 1.15)

        if m.ls_ratio_available and m.long_short_account_ratio >= 1.6:
            pull_lower *= 1.85
        if m.spot_cvd_ratio >= 1.15:
            pull_upper *= 1.40
        if imm_ratio >= 3.0:
            pull_lower *= 1.50

        factors_dict = {
            "factor_1_size": f1_text,
            "factor_2_spot_leadership": f2_text,
            "factor_3_crowding_fuel": f3_text,
            "factor_4_regime_structure": f4_text,
            "factor_5_asymmetry": f5_text,
            "factor_6_atr_volatility": f6_text,
        }

        if pull_lower >= pull_upper:
            dominant_name = "Lower Long Sweep Magnet"
            crowd_note = f"longs {long_share*100:.1f}% crowded" if m.ls_ratio_available else "modeled lower OI density"
            reason_short = f"LOWER (Immediate {imm_disp} / Ladder {tot_ratio:.2f}x; {crowd_note})"
            reason_full = f"Modeled lower cluster dominates immediately (~${l_vol:.1f}M vs ~${u_vol:.1f}M) and across the total ladder (~${tot_l_vol:.1f}M vs ~${tot_u_vol:.1f}M)."
        else:
            dominant_name = "Upper Short Squeeze Magnet"
            reason_short = "UPPER (Proximity + Spot Reclaim bias)"
            reason_full = "Modeled upper cluster chosen as path of least resistance."

        return dominant_name, reason_short, reason_full, factors_dict, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio, ladder

    def _calculate_stop(self, regime_id: str, m: MarketMetrics) -> Tuple[float, float, float, float, float, str]:
        """
        Calculates Dual Stop Levels:
          1. Structural Invalidation Level: 4H swing low (exit on 1H candle close)
          2. Inviolable Disaster Stop: Placed safely BELOW 200D SMA and 25x Long Pool with 0.7% buffer
        """
        current_price = m.price
        struct_invalidation = m.swing_low_4h
        shelf_25x = m.swing_low_4h * 0.988
        shelf_10x = m.swing_low_4h * 0.975

        # Inviolable Disaster Hard Stop: sits below 200D SMA, 25x Long Pool, and 3D base floor (-0.7% buffer)
        deep_shelf = min(m.ma_200d, shelf_25x, m.base_floor)
        disaster_stop_price = round(deep_shelf * (1.0 - 0.007), 2)
        disaster_dist_pct = round(abs(current_price - disaster_stop_price) / current_price * 100, 2)

        if disaster_stop_price > shelf_10x:
            stop_note = (
                f"Anchored -0.7% below 200D SMA (${m.ma_200d:,.0f}) & 25x shelf (${shelf_25x:,.0f}). "
                f"Note: sits above modeled 10x tail-risk shelf (${shelf_10x:,.0f}) to stay inside the 4.5% max stop budget."
            )
        else:
            stop_note = (
                f"Anchored -0.7% below 200D SMA (${m.ma_200d:,.0f}), 25x shelf (${shelf_25x:,.0f}), "
                f"and 10x shelf (${shelf_10x:,.0f})."
            )

        stop_price = disaster_stop_price
        stop_dist_pct = disaster_dist_pct

        return stop_price, stop_dist_pct, disaster_stop_price, disaster_dist_pct, struct_invalidation, stop_note

    def _get_plain_english_breakdown(
        self,
        regime_id: str,
        m: Optional[MarketMetrics],
        stop_price: float,
        stop_dist_pct: float,
        sizing: float,
        dominant_magnet: str,
        lsce: Optional[LSCEState] = None,
        lower_cluster: Optional[LiquidationCluster] = None,
    ) -> Tuple[str, List[str], str, str]:
        """Translates quantitative findings into plain English strictly bound to current scan numbers."""
        lsce_status = lsce.status if lsce else "UNTESTED"

        if regime_id == "SPOT_LED_EXPANSION" and m is not None:
            verdict = (
                f"Real cash buyers are pushing Bitcoin above Daily VWAP (${m.daily_vwap:,.2f}) and "
                f"Weekly VWAP (${m.weekly_vwap:,.2f}) on {m.spot_vol_ratio:.2f}x 20D volume and {m.spot_cvd_ratio:.2f} Spot CVD."
            )
            why_points = [
                f"True Spot Accumulation: 24h volume is {m.spot_vol_ratio:.2f}x 20D MA with Spot CVD at {m.spot_cvd_ratio:.2f}.",
                f"Controlled Leverage: 8h funding is {m.funding_rate*100:+.4f}% and 24h OI change is {m.oi_change_24h_pct:+.2f}%.",
                f"Structural Strength: Spot (${m.price:,.2f}) holds above Daily VWAP (${m.daily_vwap:,.2f}) & Weekly VWAP (${m.weekly_vwap:,.2f}).",
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? Real spot demand leads with controlled derivatives risk; scaled spot allocation is warranted."
            why_stop = f"Your Safety Net: Placed at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away). If structural floor (${m.swing_low_4h:,.0f}) fails, exit immediately."

        elif regime_id == "RANGE_LIQUIDATION_MAGNET" and m is not None:
            range_w = (m.swing_high_4h - m.swing_low_4h) / max(m.price, 1.0) * 100.0
            lower_str = f"${lower_cluster.price_level:,.0f} (-{lower_cluster.distance_pct:.2f}%)" if lower_cluster else f"${m.swing_low_4h:,.0f}"
            verdict = (
                f"Bitcoin (${m.price:,.2f}) is trading in a {range_w:.2f}% range between ${m.swing_low_4h:,.0f} and "
                f"${m.swing_high_4h:,.0f}. LSCE Status: {lsce_status}."
            )
            why_points = [
                f"Defined Consolidation Range: 4H channel width is {range_w:.2f}% with 1H ATR compressed {m.atr_compression_pct:.1f}%.",
                f"Liquidation Sweep State ({lsce_status}): Lower modeled shelf ({lower_str}) is monitored for Spot CVD >= 1.05 & Depth >= 0.50 (now {m.bids_asks_depth_ratio:.2f}).",
                f"Positioning Balance: Spot CVD is {m.spot_cvd_ratio:.2f} with {m.funding_rate*100:+.4f}% 8h funding.",
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? Allocation unlocks only after post-sweep reclaim proof; while sweep is unconfirmed, we hold 100% cash."
            why_stop = f"Your Safety Net: Inviolable Disaster Stop at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away), below 200D SMA (${m.ma_200d:,.0f}) and 25x shelf (${m.swing_low_4h * 0.988:,.0f})."

        elif regime_id == "TRANSITION_MIXED" and m is not None:
            ls = m.long_short_account_ratio
            long_pct = (ls / (1.0 + ls) * 100.0) if (1.0 + ls) > 0 else 50.0
            cvd_state = "positive" if m.spot_cvd_ratio >= 1.0 else "soft/negative"
            basis_state = "negative (backwardation)" if m.futures_basis_annualized < 0 else "flat/positive"
            oi_clause = (
                f"and 24h OI changed {m.oi_change_24h_pct:+.2f}%"
                if m.oi_history_available
                else "while 24h OI history is unavailable on fallback feed"
            )
            ls_clause = (
                f"{long_pct:.1f}% of tracked retail accounts are net long (L/S {ls:.2f})"
                if m.ls_ratio_available
                else "retail L/S ratio unavailable on fallback feed"
            )
            lower_str = f"${lower_cluster.price_level:,.0f} (-{lower_cluster.distance_pct:.2f}%)" if lower_cluster else f"${m.swing_low_4h:,.0f}"
            verdict = (
                f"Market signals conflict: Spot CVD is {m.spot_cvd_ratio:.2f} ({cvd_state}), yet Spot (${m.price:,.2f}) trades "
                f"below Daily VWAP (${m.daily_vwap:,.2f}) with {m.futures_basis_annualized:+.2f}% futures basis and thin book depth ({m.bids_asks_depth_ratio:.2f})."
            )
            why_points = [
                f"Conflicted Order Flow: Spot CVD is {m.spot_cvd_ratio:.2f}, yet price (${m.price:,.2f}) sits below Daily VWAP (${m.daily_vwap:,.2f}), showing overhead supply.",
                f"Derivatives Posture: Annualized basis is {basis_state} at {m.futures_basis_annualized:+.2f}% {oi_clause}, with depth ratio at {m.bids_asks_depth_ratio:.2f}.",
                f"Downside Fragility: {ls_clause} above modeled lower pool at {lower_str}. Holding 100% USDT cash avoids buying into an unabsorbed sweep.",
            ]
            why_sizing = "Why 0% Sizing (100% Cash)? Cash is an active protective position when sub-VWAP weakness, backwardation, and thin depth overlap."
            why_stop = f"Safety Protocol: Currently 100% in USDT cash. If holding existing spot, structural invalidation triggers on a 1H close below ${m.swing_low_4h:,.2f}."

        elif regime_id == "CASCADE_FORCED_DELEVERAGING" and m is not None:
            verdict = (
                f"Emergency state: Spot dropped {m.price_change_24h_pct:+.2f}% (24h) / {m.price_change_1h_pct:+.2f}% (1h) "
                f"with OI sliding {m.oi_change_24h_pct:+.2f}% (24h). Never buy an active liquidation waterfall."
            )
            why_points = [
                f"Forced Unwind Speed: 1H move {m.price_change_1h_pct:+.2f}% with OI delta {m.oi_change_1h_pct:+.2f}% (1h) / {m.oi_change_4h_pct:+.2f}% (4h).",
                f"Thin Liquidity: Order book bid/ask depth ratio is {m.bids_asks_depth_ratio:.2f} with {m.futures_basis_annualized:+.2f}% basis.",
                f"Capital Preservation Mandate: Hold 100% USDT cash until OI stabilizes and price reclaims ${m.swing_low_4h:,.0f}.",
            ]
            why_sizing = "Why 0% Sizing? Buying during an active liquidation waterfall has fatal negative expectancy. We wait for selling exhaustion."
            why_stop = "Safety Net: 100% Cash. No new spot position is open."

        elif m is not None:
            verdict = (
                f"Bitcoin (${m.price:,.2f}) sits below Daily VWAP (${m.daily_vwap:,.2f}), 20D EMA (${m.ema_20d:,.0f}), "
                f"and 50D EMA (${m.ema_50d:,.0f}) with Spot CVD at {m.spot_cvd_ratio:.2f} — seller distribution dominates."
            )
            why_points = [
                f"Sub-VWAP Trend: Price (${m.price:,.2f}) remains trapped below Daily VWAP (${m.daily_vwap:,.2f}) and 20D/50D EMAs.",
                f"Weak Spot Conviction: 24h volume ratio is {m.spot_vol_ratio:.2f}x 20D MA with Spot CVD at {m.spot_cvd_ratio:.2f}.",
                f"Cash Priority: Preserving 100% USDT reserve while funding is {m.funding_rate*100:+.4f}% and basis is {m.futures_basis_annualized:+.2f}%.",
            ]
            why_sizing = "Why 0% Sizing? Capital preservation is paramount in bear distribution regimes."
            why_stop = f"Safety Net: Structural invalidation only on 1D reclaim above 50D EMA (${m.ema_50d:,.0f}) with rising Spot CVD."

        else:
            verdict = "Telemetry incomplete or unavailable. System automatically defaults to 100% USDT cash protection."
            why_points = [
                "Missing Exchange Data: Required spot or derivatives telemetry failed verification.",
                "Zero Synthetic Fallback Policy: The engine refuses to invent placeholder prices or ratios.",
                "Capital Preservation Default: Wait for live REST/WebSocket recovery before deploying capital.",
            ]
            why_sizing = "Why 0% Sizing? Withholding risk deployment whenever telemetry cannot be verified."
            why_stop = "Safety Net: 100% Cash reserve."

        return verdict, why_points, why_sizing, why_stop

    def _create_data_incomplete_result(self, reason: str) -> RegimeResult:
        """Returns safe default when critical exchange data is unavailable."""
        verdict, why_pts, why_sizing, why_stop = self._get_plain_english_breakdown(
            "DATA_INCOMPLETE", None, 0.0, 0.0, 0.0, "N/A"
        )
        return RegimeResult(
            regime="Data Incomplete",
            regime_id="DATA_INCOMPLETE",
            name="Data Incomplete",
            diagnosis="Critical exchange data feeds offline or corrupted",
            playbook="100% Cash Reserve (0.0x)",
            suitability="Safe Default",
            sizing_factor=0.0,
            action="Hold 100% Cash",
            rotation="Remain USDT",
            entry_instruction="Do not trade. Wait for exchange API connections to recover.",
            stop_rule="N/A",
            stop_price=0.0,
            stop_distance_pct=0.0,
            nearest_upper_cluster=None,
            nearest_lower_cluster=None,
            dominant_magnet="N/A",
            dominant_magnet_reason=reason,
            risk_budget_ok=False,
            recommended_cash_deploy_pct=0.0,
            target_btc_allocation_pct=0.0,
            target_usdt_reserve_pct=100.0,
            matched_criteria=[],
            notes=reason,
            plain_english_verdict=verdict,
            why_points=why_pts,
            why_sizing_reason=why_sizing,
            why_stop_reason=why_stop
        )
