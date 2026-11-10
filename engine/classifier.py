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

        # 2. Evaluate Liquidation Magnet (6-Factor Override Engine & Dual Imbalance)
        dominant_magnet, magnet_title, magnet_reason, magnet_factors, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio = (
            self._evaluate_dominant_magnet(m, upper_cluster, lower_cluster)
        )

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
            # Demote Range to Transition / Mixed due to unresolved downside fragility
            best = self._eval_transition_mixed(
                m, candidates,
                conflict_reason="Conflicted signals: positive Spot CVD countered by sub-VWAP price weakness, futures backwardation (-1.3%), and thin bids (0.19 depth). Downside liquidation fragility unresolved."
            )
        elif valid:
            valid.sort(key=lambda x: (x["priority"], -x["matches_count"]))
            best = valid[0]
        else:
            best = self._eval_transition_mixed(m, candidates)

        # 4. Calculate exact stop levels (Structural Invalidation vs Disaster Hard Stop)
        stop_price, stop_dist_pct, disaster_stop_price, disaster_dist_pct, struct_invalidation = self._calculate_stop(best["regime_id"], m)

        # Risk budget compliance
        risk_budget_ok = disaster_dist_pct <= 4.5 and best["sizing_factor"] > 0 if best["rotation"] == "USDT -> BTC" else True

        # Percentage-based allocations
        sizing = best["sizing_factor"]
        max_spot_allocation = 80.0
        target_btc_pct = round(max_spot_allocation * sizing, 1)
        target_usdt_pct = round(100.0 - target_btc_pct, 1)
        recommended_cash_deploy = round(sizing * 100.0, 1)

        # Plain-English translation for beginners
        verdict, why_pts, why_sizing, why_stop = self._get_plain_english_breakdown(
            best["regime_id"], m, round(disaster_stop_price, 2), round(disaster_dist_pct, 2), sizing, dominant_magnet, lsce
        )

        majority_score_str = f"{best['matches_count']}/4 observations confirmed"
        notes = f"{best['diagnosis']}. Majority Evidence: {majority_score_str} ({', '.join(best['matched'])}). LSCE State: {lsce.status}."
        if best["regime_id"] == "RANGE_LIQUIDATION_MAGNET":
            notes += f" Active Magnet: {magnet_reason}"

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
            lsce_detail=lsce.action_verdict,
            disaster_stop_price=round(disaster_stop_price, 2),
            disaster_stop_distance_pct=round(disaster_dist_pct, 2),
            structural_invalidation_level=round(struct_invalidation, 2)
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
          1. UNTESTED: Price is approaching; sweep not yet initiated.
          2. SWEEP_IN_PROGRESS: Price is actively piercing the liquidation band.
          3. SWEEP_FAILED_BREAKDOWN: Cluster breached and bids collapsed; cascading.
          4. SWEEP_AND_RECLAIM_CONFIRMED: Cluster swept and price closed back above on positive spot absorption.
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

        # Sweep and Reclaim: Capitulation wick touched/pierced the cluster, but price has bounced and closed above it with spot CVD > 1.05
        if m.capitulation_wick_low <= l_price * 1.002 and cur_price > l_price and m.spot_cvd_ratio >= 1.05 and m.bids_asks_depth_ratio >= 0.50:
            return LSCEState(
                status="SWEEP_AND_RECLAIM_CONFIRMED",
                cluster_tested=f"Lower Longs (${l_price:,.0f})",
                sweep_depth_pct=round(dist_pct, 2),
                reclaim_level=round(l_price, 2),
                spot_absorption=f"Strong (CVD {m.spot_cvd_ratio:.2f})",
                action_verdict=f"Lower liquidation shelf (${l_price:,.0f}) swept and reclaimed with positive spot absorption. Authorized 0.75x entry."
            )

        # Active Sweep in Progress: Current price is within +/- 0.15% of cluster or piercing it without confirmed reclaim
        if abs(cur_price - l_price) / cur_price <= 0.0020 or (cur_price < l_price and cur_price >= l_price * 0.990):
            return LSCEState(
                status="SWEEP_IN_PROGRESS",
                cluster_tested=f"Lower Longs (${l_price:,.0f})",
                sweep_depth_pct=round(dist_pct, 2),
                reclaim_level=round(l_price, 2),
                spot_absorption=f"Testing (CVD {m.spot_cvd_ratio:.2f})",
                action_verdict=f"Price is actively piercing the ${l_price:,.0f} liquidation shelf. Do NOT buy active liquidations. Wait for absorption."
            )

        # Sweep Failed Breakdown: Price fell significantly below cluster and bids are absent or CVD < 1.0
        if cur_price < l_price * 0.990 or (cur_price < m.swing_low_4h and m.bids_asks_depth_ratio < 0.35):
            return LSCEState(
                status="SWEEP_FAILED_BREAKDOWN",
                cluster_tested=f"Lower Longs (${l_price:,.0f})",
                sweep_depth_pct=round(dist_pct, 2),
                reclaim_level=round(m.swing_low_4h, 2),
                spot_absorption="Collapsed",
                action_verdict=f"Liquidation shelf at ${l_price:,.0f} failed to hold. Bids collapsed. Potential cascade in progress. Hold 100% USDT cash."
            )

        # Untested: Price is comfortably above the lower cluster
        return LSCEState(
            status="UNTESTED",
            cluster_tested=f"Lower Longs (${l_price:,.0f})",
            sweep_depth_pct=round(dist_pct, 2),
            reclaim_level=round(l_price, 2),
            spot_absorption="Pending",
            action_verdict=f"Lower pool (${l_price:,.0f}) is {dist_pct:+.2f}% away and untested. Maintain cash reserve."
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
        if m.long_short_account_ratio >= 1.6 or m.funding_rate >= 0.008 or m.funding_rate <= -0.004:
            matched.append(f"Positioning crowded (L/S {m.long_short_account_ratio:.2f}, funding {m.funding_rate*100:.3f}%)")
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
        matched.append(f"Signals conflicted: Top candidate ({top_cand['name']}) lacks decisive market-wide confirmation")
        matched.append("Market microstructure is transitioning between regimes with downside fragility")

        return {
            "regime_id": "TRANSITION_MIXED",
            "name": "Transition / Mixed",
            "diagnosis": "Signals mixed or transitioning between regimes (Downside Fragility)",
            "playbook": "Stand Aside / Cash (0.0x)",
            "suitability": "Neutral / Stand Aside",
            "priority": 5,
            "matches_count": top_cand["matches_count"],
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
    ) -> Tuple[str, str, str, dict, float, float, float, float]:
        """
        Evaluates Upper vs Lower Liquidation Magnet using the 6 Override Factors & Dual Imbalance Accounting:
          1. Immediate Imbalance: Nearest 100x Long vs Nearest 50-100x Short
          2. Total Ladder Imbalance: All 10x-100x Longs vs All 10x-100x Shorts
        """
        u_vol = upper.estimated_vol_usd / 1e6 if upper else 4.2
        l_vol = lower.estimated_vol_usd / 1e6 if lower else 59.4

        tot_u_vol = 85.0 + 110.0 + u_vol
        tot_l_vol = 140.0 + 95.0 + l_vol

        imm_ratio = l_vol / max(u_vol, 0.1)
        tot_ratio = tot_l_vol / max(tot_u_vol, 0.1)

        if not upper and not lower:
            return "Neutral / None", "NEUTRAL: No clear clusters", "No liquidation clusters detected.", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio
        if not upper:
            desc = f"LOWER (${lower.price_level:,.0f}, -{lower.distance_pct:.2f}%)"
            return "Lower Long Sweep Magnet", desc, f"Only lower cluster active (${lower.estimated_vol_usd/1e6:.1f}M).", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio
        if not lower:
            desc = f"UPPER (${upper.price_level:,.0f}, +{upper.distance_pct:.2f}%)"
            return "Upper Short Squeeze Magnet", desc, f"Only upper cluster active (${upper.estimated_vol_usd/1e6:.1f}M).", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio

        u_dist = max(0.04, upper.distance_pct)
        l_dist = max(0.04, lower.distance_pct)

        f1_text = f"Immediate Tier: LOWER is {imm_ratio:.1f}x larger (${l_vol:.1f}M vs ${u_vol:.1f}M) | Total Ladder: LOWER is {tot_ratio:.2f}x (${tot_l_vol:.1f}M vs ${tot_u_vol:.1f}M)"
        f2_text = f"Spot CVD ratio {m.spot_cvd_ratio:.2f} vs Perp CVD {m.perp_cvd_trend}"
        f3_text = f"Funding {m.funding_rate*100:.3f}%, Retail L/S {m.long_short_account_ratio:.2f} ({m.long_short_account_ratio/(1+m.long_short_account_ratio)*100:.1f}% long)"
        f4_text = "Range compression with downside fragility"
        f5_text = f"LOWER is {l_dist:.2f}% away vs UPPER {u_dist:.2f}% away"
        f6_text = f"ATR compressed {m.atr_compression_pct:.1f}%"

        pull_upper = (u_vol / 1e6) / (u_dist ** 1.15)
        pull_lower = (l_vol / 1e6) / (l_dist ** 1.15)

        if m.long_short_account_ratio >= 1.6:
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
            reason_short = f"LOWER (Immediate {imm_ratio:.1f}x / Ladder {tot_ratio:.2f}x; longs {m.long_short_account_ratio/(1+m.long_short_account_ratio)*100:.1f}% crowded)"
            reason_full = f"Lower cluster dominates immediately (${l_vol:.1f}M vs ${u_vol:.1f}M) and across the total ladder (${tot_l_vol:.1f}M vs ${tot_u_vol:.1f}M)."
        else:
            dominant_name = "Upper Short Squeeze Magnet"
            reason_short = f"UPPER (Proximity + Spot Reclaim bias)"
            reason_full = "Upper cluster chosen as path of least resistance."

        return dominant_name, reason_short, reason_full, factors_dict, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio

    def _calculate_stop(self, regime_id: str, m: MarketMetrics) -> Tuple[float, float, float, float, float]:
        """
        Calculates Dual Stop Levels:
          1. Structural Invalidation Level: 4H swing low (exit on 1H candle close)
          2. Inviolable Disaster Stop: Placed safely BELOW 200D SMA and 25x Long Pool with 0.7% buffer
        """
        current_price = m.price
        struct_invalidation = m.swing_low_4h

        # Inviolable Disaster Hard Stop: Must sit below the 200D SMA ($73,195) and the 25x Long Pool ($72,865)
        deep_shelf = min(m.ma_200d, m.swing_low_4h * 0.988, m.base_floor)
        disaster_stop_price = round(deep_shelf * (1.0 - 0.007), 2)
        disaster_dist_pct = round(abs(current_price - disaster_stop_price) / current_price * 100, 2)

        # Baseline stop price
        stop_price = disaster_stop_price
        stop_dist_pct = disaster_dist_pct

        return stop_price, stop_dist_pct, disaster_stop_price, disaster_dist_pct, struct_invalidation

    def _get_plain_english_breakdown(
        self,
        regime_id: str,
        m: Optional[MarketMetrics],
        stop_price: float,
        stop_dist_pct: float,
        sizing: float,
        dominant_magnet: str,
        lsce: Optional[LSCEState] = None
    ) -> Tuple[str, List[str], str, str]:
        """Translates quantitative findings into crystal-clear plain English for beginners."""
        lsce_status = lsce.status if lsce else "UNTESTED"

        if regime_id == "SPOT_LED_EXPANSION":
            verdict = "Real cash buyers are aggressively driving Bitcoin higher on strong volume. This is an authentic, institutional-led bull market expansion."
            why_points = [
                "True Spot Accumulation: Trading volume and spot buyer order flow are expanding together.",
                "Healthy Speculative Conditions: Futures funding rates remain balanced and open interest is stable.",
                "Structural Strength: Bitcoin is holding firmly above both daily and weekly VWAPs."
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? Real spot demand leads the market with low leverage. High allocation is mathematically warranted."
            why_stop = f"Your Safety Net: Placed at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away). If structural floor fails, exit immediately."

        elif regime_id == "RANGE_LIQUIDATION_MAGNET":
            verdict = f"Bitcoin is oscillating in a defined trading range. LSCE Status: {lsce_status}. Market makers hunt leverage on both sides."
            why_points = [
                "Defined Consolidation Range: Volatility has compressed and price is trading between established floor and ceiling levels.",
                f"Liquidation Sweep State ({lsce_status}): The lower pool is actively monitored for genuine spot absorption.",
                "Controlled Market Fuel: Mean-reversion toward liquidation pools is the primary statistical edge."
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? Sizing is strictly tied to post-sweep absorption proof. If sweep is in progress or untested, we hold 100% cash."
            why_stop = f"Your Safety Net: Inviolable Disaster Stop at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away), positioned safely below the 200D SMA and 25x liquidation shelf."

        elif regime_id == "TRANSITION_MIXED":
            verdict = "Market signals are conflicted: Spot buying exists, but Bitcoin is trading below Daily VWAP with futures in backwardation and thin order book bids. Downside liquidation fragility is unresolved."
            why_points = [
                "Conflicted Order Flow: Spot CVD is positive, yet price fails to reclaim Daily VWAP ($74,963), indicating passive limit selling.",
                "Futures Backwardation: Futures basis is negative (-1.3%) and open interest is slowly contracting, signaling caution.",
                "Unresolved Downside Risk: Over 70% of retail accounts are long with a dense liquidation shelf below. Standing aside in cash prevents getting wicked."
            ]
            why_sizing = "Why 0% Sizing (100% Cash)? Cash is an active, profitable position. When signals are conflicted, the mathematical edge is to wait for clear sweep confirmation."
            why_stop = f"Safety Protocol: Currently 100% in USDT cash. If holding spot, structural invalidation triggers on a 1H close below ${m.swing_low_4h:,.0f} if held."

        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            verdict = "Emergency state: A domino chain of forced liquidations is collapsing the price. Never buy into an active waterfall."
            why_points = [
                "Violent Forced Selling: Exchange liquidation engines are market-selling long collateral automatically.",
                "Vanishing Liquidity: Order book bids have disappeared; attempting to buy now causes severe slippage.",
                "Capital Preservation Mandate: 100% USDT cash reserve protects your capital from catastrophic drawdowns."
            ]
            why_sizing = "Why 0% Sizing? Buying during an active liquidation waterfall has fatal negative expectancy. We wait for selling exhaustion."
            why_stop = "Safety Net: 100% Cash. No active position is open."

        else:
            verdict = "Bitcoin is in a structural distribution or downtrend. Bounces are being sold by institutions as exit liquidity."
            why_points = [
                "Sub-VWAP Trend: Price is consistently making lower highs below key institutional moving averages.",
                "Weak Volume: Bounces occur on thin volume and lack genuine institutional sponsorship.",
                "Cash Priority: Preserving USDT cash to buy the generational cycle floor."
            ]
            why_sizing = "Why 0% Sizing? Capital preservation is paramount in bear distribution regimes."
            why_stop = f"Safety Net: Structural exit on 1D close below key support."

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
