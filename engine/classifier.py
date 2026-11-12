from typing import List, Tuple, Optional, Dict, Any
from engine.models import MarketMetrics, LiquidationCluster, RegimeResult, LSCEState


class RegimeClassifier:
    """
    Bidirectional 5-Regime + DIBSE (Dual-Inventory Bidirectional Swing Engine) Classifier:
      1. Spot-Led Expansion
      2. Leveraged / Fragile Upside  -> Loop B (BTC -> USDT) Harvest into Perp Squeeze
      3. Range / Liquidation Magnet  -> Symmetric Loop A (Lower Sweep) / Loop B (Upper Sweep)
      4. Cascade / Forced Deleveraging -> Wait Waterfall Exhaustion (Zero Forced Stop-Outs)
      5. Distribution / Bear Continuation -> Loop B on Weak Bounce, Protect USDT Sleeve
      Default: Transition / Mixed -> Hold Both Sleeves (10% USDT + 10% BTC)

    Strict DIBSE Rules Enforced:
      - Permanent Dual-Inventory Sandbox: 10% USDT Sleeve + 10% BTC Sleeve (20% Active | 80% Core Untouched).
      - Bidirectional Loops: Loop A (USDT -> BTC -> USDT, P_exit > P_buy) & Loop B (BTC -> USDT -> BTC, P_rebuy < P_sell).
      - Zero Leverage, Zero Forced Stop-Losses, Zero Upside Stop-Buys, Zero MA/EMA/RSI/MACD/ATR.
      - Closed 4H bars (klines[:-1]) for all structural levels & liquidation cluster modeling.
    """

    def classify(self, m: Optional[MarketMetrics], clusters: List[LiquidationCluster]) -> RegimeResult:
        if m is None or not clusters:
            return self._create_data_incomplete_result("Market metrics or liquidation clusters unavailable.")

        upper_cluster = next((c for c in clusters if c.side == "upper"), None)
        lower_cluster = next((c for c in clusters if c.side == "lower"), None)

        # 1. Symmetric Bidirectional Sweep Confirmation Engine (LSCE Lower + Upper)
        lsce = self._eval_lsce(m, lower_cluster, upper_cluster)

        # 2. Evaluate Dominant Liquidation Magnet & Unified 10x-100x Modeled Ladder (zero ATR)
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

        # 3. Evaluate the 5 observable regimes (Majority-based: >= 3 of 4 matches, zero MA/EMA/ATR)
        candidates = [
            self._eval_cascade(m),
            self._eval_leveraged_upside(m),
            self._eval_distribution_bear(m, lsce),
            self._eval_range_magnet(m, lsce),
            self._eval_spot_expansion(m, lsce),
        ]

        valid = [c for c in candidates if c["matches_count"] >= 3]

        # Conflicted sub-VWAP gate: only demotes Range if NEITHER lower reclaim NOR upper squeeze rejection is active
        has_edge_trigger = lsce.status in ("SWEEP_AND_RECLAIM_CONFIRMED", "UPPER_SWEEP_REJECTION_CONFIRMED")
        is_conflicted = (
            m.price < m.daily_vwap
            and m.price < m.weekly_vwap
            and m.futures_basis_annualized < 0.0
            and m.bids_asks_depth_ratio < 0.35
            and not has_edge_trigger
        )

        if is_conflicted and any(c["regime_id"] == "RANGE_LIQUIDATION_MAGNET" for c in valid):
            cvd_desc = (
                f"positive Spot CVD ({m.spot_cvd_ratio:.2f})"
                if m.spot_cvd_ratio >= 1.0
                else f"weak Spot CVD ({m.spot_cvd_ratio:.2f})"
            )
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

        # 4. Compute bidirectional DIBSE action zones (zero forced stop-losses)
        loop_a_zone, loop_b_zone = self._calc_dibse_zones(m, lower_cluster, upper_cluster)
        dibse_signal = best.get("dibse_signal", "HOLD BOTH SLEEVES")
        sizing = best["sizing_factor"]
        rotation = best["rotation"]

        # Portfolio sandbox percentages (10% USDT Sleeve + 10% BTC Sleeve = 20% active; 80% core untouched)
        if dibse_signal == "LOOP A: USDT -> BTC":
            active_btc_pct = round(10.0 + 10.0 * sizing, 1)
            active_usdt_pct = round(10.0 * (1.0 - sizing), 1)
            deploy_pct = round(sizing * 100.0, 1)
        elif dibse_signal == "LOOP B: BTC -> USDT":
            active_btc_pct = round(10.0 * (1.0 - sizing), 1)
            active_usdt_pct = round(10.0 + 10.0 * sizing, 1)
            deploy_pct = round(sizing * 100.0, 1)
        else:
            active_btc_pct = 10.0
            active_usdt_pct = 10.0
            deploy_pct = 0.0

        verdict, why_pts, why_sizing, why_stop = self._get_plain_english_breakdown(
            best["regime_id"],
            m,
            sizing,
            dibse_signal,
            lsce,
            lower_cluster,
            upper_cluster,
            loop_a_zone,
            loop_b_zone,
        )

        if best["regime_id"] == "TRANSITION_MIXED":
            majority_score_str = f"Conflict Override ({len(best['matched'])}/4 conflict gates triggered)"
        else:
            majority_score_str = f"{best['matches_count']}/4 observations confirmed"
        notes = f"{best['diagnosis']}. Rule Score: {majority_score_str} ({', '.join(best['matched'])}). LSCE State: {lsce.status}."
        if best["regime_id"] == "RANGE_LIQUIDATION_MAGNET":
            notes += f" Active Magnet: {magnet_reason}"

        # Reconcile sweep headline vs macro DIBSE state
        lsce_action_detail = lsce.action_verdict
        if dibse_signal == "HOLD BOTH SLEEVES" and lsce.status == "SWEEP_AND_RECLAIM_CONFIRMED":
            l_price_val = lower_cluster.price_level if lower_cluster else 0.0
            lsce_action_detail = (
                f"Lower shelf (${l_price_val:,.0f}) swept, but Loop A USDT deployment is paused by macro "
                f"regime ({best['name']}). Keep 10% USDT + 10% BTC sleeves balanced."
            )

        return RegimeResult(
            regime=best["name"],
            regime_id=best["regime_id"],
            name=best["name"],
            diagnosis=best["diagnosis"],
            playbook=best["playbook"],
            suitability=best["suitability"],
            sizing_factor=sizing,
            action=best["action"],
            rotation=rotation,
            entry_instruction=best["entry_instruction"],
            stop_rule="ZERO STOP-LOSSES (DIBSE Asymmetric Self-Healing Inventory)",
            stop_price=0.0,
            stop_distance_pct=0.0,
            nearest_upper_cluster=upper_cluster,
            nearest_lower_cluster=lower_cluster,
            dominant_magnet=dominant_magnet,
            dominant_magnet_reason=magnet_title,
            magnet_factors=magnet_factors,
            risk_budget_ok=True,
            recommended_cash_deploy_pct=deploy_pct,
            target_btc_allocation_pct=active_btc_pct,
            target_usdt_reserve_pct=active_usdt_pct,
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
            lsce_side=lsce.side,
            lsce_detail=lsce_action_detail,
            disaster_stop_price=0.0,
            disaster_stop_distance_pct=0.0,
            structural_invalidation_level=round(m.swing_low_4h, 2),
            liquidation_ladder=liquidation_ladder,
            stop_placement_note=(
                "Zero Stop-Losses: Underwater Loop A waits for > P_buy; bypassed Loop B waits for < P_sell."
            ),
            dibse_signal=dibse_signal,
            dibse_action_headline=best.get("dibse_headline", dibse_signal),
            loop_a_zone=loop_a_zone,
            loop_b_zone=loop_b_zone,
        )

    def _eval_lsce(
        self,
        m: MarketMetrics,
        lower: Optional[LiquidationCluster],
        upper: Optional[LiquidationCluster],
    ) -> LSCEState:
        """
        Symmetric Bidirectional Liquidation Sweep Confirmation Engine (LSCE):
          Lower (Loop A Support Washout):
            - SWEEP_AND_RECLAIM_CONFIRMED: wick <= 1.002*lower, lower < price <= 1.015*lower, CVD >= 1.05, depth >= 0.50
            - SWEEP_IN_PROGRESS: within +-0.20% of lower OR -1.00%..0% below lower without reclaim
            - SWEEP_FAILED_BREAKDOWN: price < 0.990*lower OR (< closed 4H low AND depth < 0.35)
          Upper (Loop B Squeeze & Resistance Rejection):
            - UPPER_SWEEP_REJECTION_CONFIRMED: 24h wick >= 0.998*upper_ref, 0.985*upper_ref <= price < upper_ref, exhaustion signs
            - UPPER_SWEEP_IN_PROGRESS: testing within +-0.20% of upper_shelf or probing above up to +1.00%
        """
        cur_price = m.price
        wick_high = m.euphoria_wick_high if m.euphoria_wick_high > 0 else cur_price
        l_price = lower.price_level if lower else m.swing_low_4h
        u_price = upper.price_level if upper else m.swing_high_4h

        # 1. Loop A Lower Washout Reclaim Confirmed (only near reclaimed lower shelf, never chasing high resistance)
        if lower and m.capitulation_wick_low <= l_price * 1.002 and (l_price < cur_price <= l_price * 1.015) and m.spot_cvd_ratio >= 1.05 and m.bids_asks_depth_ratio >= 0.50:
            dist_pct = (cur_price - l_price) / max(cur_price, 1.0) * 100
            return LSCEState(
                status="SWEEP_AND_RECLAIM_CONFIRMED",
                side="LOWER",
                cluster_tested=f"Lower Longs (${l_price:,.0f})",
                sweep_depth_pct=round(dist_pct, 2),
                reclaim_level=round(l_price, 2),
                spot_absorption=f"Strong Bid Absorption (CVD {m.spot_cvd_ratio:.2f}, Depth {m.bids_asks_depth_ratio:.2f})",
                action_verdict=f"Lower long shelf (${l_price:,.0f}) swept and reclaimed with spot buying. Loop A (USDT -> BTC) zone confirmed.",
            )

        # 2. Loop B Upper Squeeze Sweep & Rejection Confirmed (only rejecting near swept ceiling, never selling the bottom)
        u_ref = u_price if (upper and wick_high >= u_price * 0.998) else m.swing_high_4h
        upper_exhaustion = (m.spot_cvd_ratio < 1.08) or (m.bids_asks_depth_ratio < 0.75) or (m.funding_rate >= 0.010)
        if upper and u_ref > 0 and wick_high >= u_ref * 0.998 and (u_ref * 0.985 <= cur_price < u_ref) and upper_exhaustion:
            dist_pct = (wick_high - u_ref) / max(cur_price, 1.0) * 100
            return LSCEState(
                status="UPPER_SWEEP_REJECTION_CONFIRMED",
                side="UPPER",
                cluster_tested=f"Upper Shorts (${u_ref:,.0f})",
                sweep_depth_pct=round(dist_pct, 2),
                reclaim_level=round(u_ref, 2),
                spot_absorption=f"Upper Rejection (CVD {m.spot_cvd_ratio:.2f}, Depth {m.bids_asks_depth_ratio:.2f})",
                action_verdict=f"Upper short liquidity (${u_ref:,.0f}) swept (wick ${wick_high:,.0f}) and rejected without spot follow-through. Loop B (BTC -> USDT) active.",
            )

        # 3. Active Lower Sweep in Progress (wait before Loop A deploy)
        if lower:
            dist_l = (cur_price - l_price) / max(cur_price, 1.0) * 100
            if abs(cur_price - l_price) / max(cur_price, 1.0) <= 0.0020 or (l_price * 0.990 <= cur_price < l_price):
                verb = f"piercing below (${cur_price:,.2f}, {dist_l:+.2f}%)" if cur_price < l_price else f"testing +-0.20% sweep zone (${cur_price:,.2f})"
                return LSCEState(
                    status="SWEEP_IN_PROGRESS",
                    side="LOWER",
                    cluster_tested=f"Lower Longs (${l_price:,.0f})",
                    sweep_depth_pct=round(dist_l, 2),
                    reclaim_level=round(l_price, 2),
                    spot_absorption=f"Testing (CVD {m.spot_cvd_ratio:.2f}, Depth {m.bids_asks_depth_ratio:.2f})",
                    action_verdict=(
                        f"Price is {verb} of ${l_price:,.0f} lower shelf. Wait for reclaim (price > ${l_price:,.0f} + "
                        f"CVD >= 1.05 + Depth >= 0.50) before firing Loop A."
                    ),
                )

            if cur_price < l_price * 0.990 or (cur_price < m.swing_low_4h and m.bids_asks_depth_ratio < 0.35):
                return LSCEState(
                    status="SWEEP_FAILED_BREAKDOWN",
                    side="LOWER",
                    cluster_tested=f"Lower Longs (${l_price:,.0f})",
                    sweep_depth_pct=round(dist_l, 2),
                    reclaim_level=round(m.swing_low_4h, 2),
                    spot_absorption=f"Thin Bids (Depth {m.bids_asks_depth_ratio:.2f})",
                    action_verdict=(
                        f"Lower shelf (${l_price:,.0f}) broke below range floor. Hold 10% USDT Sleeve dry for lower "
                        f"stabilization; zero stop-loss on 10% BTC inventory."
                    ),
                )

        # 4. Active Upper Squeeze Sweep in Progress
        if upper:
            dist_u = (cur_price - u_price) / max(cur_price, 1.0) * 100
            if abs(u_price - cur_price) / max(cur_price, 1.0) <= 0.0020 or (u_price < cur_price <= u_price * 1.010):
                return LSCEState(
                    status="UPPER_SWEEP_IN_PROGRESS",
                    side="UPPER",
                    cluster_tested=f"Upper Shorts (${u_price:,.0f})",
                    sweep_depth_pct=round(dist_u, 2),
                    reclaim_level=round(u_price, 2),
                    spot_absorption=f"Testing Ceiling (CVD {m.spot_cvd_ratio:.2f}, Depth {m.bids_asks_depth_ratio:.2f})",
                    action_verdict=(
                        f"Price is testing/sweeping upper short pool (${u_price:,.0f}). Prepare Loop B (BTC -> USDT) "
                        f"sell into squeeze exhaustion or rejection < ${u_price:,.0f}."
                    ),
                )

        # 5. Untested Mid-Channel
        dist_l_pct = (cur_price - l_price) / max(cur_price, 1.0) * 100
        dist_u_pct = (u_price - cur_price) / max(cur_price, 1.0) * 100
        return LSCEState(
            status="UNTESTED",
            side="NONE",
            cluster_tested=f"Lower ${l_price:,.0f} | Upper ${u_price:,.0f}",
            sweep_depth_pct=round(dist_l_pct, 2),
            reclaim_level=round(l_price, 2),
            spot_absorption="Balanced / Mid-Range",
            action_verdict=(
                f"Spot sits +{dist_l_pct:.2f}% above lower pool (${l_price:,.0f}) and -{dist_u_pct:.2f}% below "
                f"upper pool (${u_price:,.0f}). Hold both sleeves for range edge sweep."
            ),
        )

    def _eval_spot_expansion(self, m: MarketMetrics, lsce: LSCEState) -> dict:
        """Regime 1: Spot-Led Expansion (Zero upside stop-buys under DIBSE)."""
        matched = []
        if m.price > m.daily_vwap and m.price > m.weekly_vwap:
            matched.append("Price holding above Daily and Weekly VWAP")
        if m.spot_cvd_ratio >= 1.05 and (m.spot_cvd_slope_7d > 0 or m.spot_cvd_slope_14d > 0):
            matched.append(f"Spot CVD leading (Ratio {m.spot_cvd_ratio:.2f}, Slope +{m.spot_cvd_slope_7d:.0f})")
        if m.funding_rate <= 0.012 and m.oi_change_24h_pct <= 3.5:
            matched.append(f"Funding and OI controlled (Funding {m.funding_rate*100:.3f}%, OI 24h {m.oi_change_24h_pct:+.1f}%)")
        if m.spot_vol_ratio >= 1.0:
            matched.append(f"Spot volume confirmed ({m.spot_vol_ratio:.2f}x 20D MA)")

        # Under DIBSE Rule 4: never chase green breakouts above range ceiling.
        if lsce.status == "UPPER_SWEEP_REJECTION_CONFIRMED":
            sizing = 0.50
            dibse_sig = "LOOP B: BTC -> USDT"
            rotation = "BTC -> USDT"
            action = "Loop B: Harvest 50% of 10% BTC Sleeve into Upper Sweep"
            playbook = "Spot Expansion Exhaustion -> Loop B Trim (0.50x BTC Sleeve)"
            entry_inst = "Sell 50% of 10% BTC Sleeve into upper sweep rejection; rebuy strictly < P_sell on VWAP washout."
        elif lsce.status == "SWEEP_AND_RECLAIM_CONFIRMED" or m.price <= m.daily_vwap * 1.004:
            sizing = 0.75
            dibse_sig = "LOOP A: USDT -> BTC"
            rotation = "USDT -> BTC"
            action = "Loop A: Deploy 75% of 10% USDT Sleeve on VWAP Pullback"
            playbook = "Spot-Led Pullback -> Loop A Accumulate (0.75x USDT Sleeve)"
            entry_inst = "Deploy 75% of 10% USDT Sleeve near Daily VWAP / lower sweep reclaim. Take profit > P_buy."
        else:
            sizing = 0.0
            dibse_sig = "HOLD BOTH SLEEVES"
            rotation = "Hold Both Sleeves"
            action = "Hold Both Sleeves (Zero Upside Stop-Buy)"
            playbook = "Ride 10% BTC Sleeve; Keep 10% USDT Dry for Washout"
            entry_inst = "Price extended above Daily VWAP. Never chase breakouts; let 10% BTC Sleeve ride or harvest upper sweep."

        return {
            "regime_id": "SPOT_LED_EXPANSION",
            "name": "Spot-Led Expansion",
            "diagnosis": "Genuine spot demand supporting upside",
            "playbook": playbook,
            "suitability": "Trend Environment (Zero Chase Rule)",
            "priority": 4,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": sizing,
            "action": action,
            "rotation": rotation,
            "dibse_signal": dibse_sig,
            "dibse_headline": action,
            "entry_instruction": entry_inst,
        }

    def _eval_leveraged_upside(self, m: MarketMetrics) -> dict:
        """Regime 2: Leveraged / Fragile Upside -> Triggers DIBSE Loop B (BTC -> USDT)."""
        matched = []
        if m.price_change_24h_pct > 0.8 and m.spot_cvd_ratio < 1.12:
            matched.append(f"Price rising (+{m.price_change_24h_pct:.2f}%) while Spot CVD lags ({m.spot_cvd_ratio:.2f})")
        if m.oi_change_24h_pct >= 4.0 or m.perp_cvd_trend == "surging" or m.oi_change_3d_pct >= 10.0:
            matched.append(f"Futures leverage expanding (OI +{m.oi_change_24h_pct:.2f}% 24h, Perp CVD {m.perp_cvd_trend})")
        if m.funding_rate >= 0.015 or m.futures_basis_annualized >= 12.0:
            matched.append(f"Funding elevated ({m.funding_rate*100:.3f}%) or basis wide ({m.futures_basis_annualized:.1f}%)")
        if m.spot_vol_ratio < 1.0:
            matched.append(f"Spot volume failing to confirm ({m.spot_vol_ratio:.2f}x 20D MA)")

        return {
            "regime_id": "LEVERAGED_FRAGILE_UPSIDE",
            "name": "Leveraged / Fragile Upside",
            "diagnosis": "Upside driven mainly by futures leverage / crowding",
            "playbook": "Loop B: Rotate 10% BTC Sleeve -> USDT",
            "suitability": "Loop B Distribution Harvest Zone",
            "priority": 2,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": 1.0,
            "action": "Loop B: Sell 10% BTC Sleeve into Squeeze",
            "rotation": "BTC -> USDT",
            "dibse_signal": "LOOP B: BTC -> USDT",
            "dibse_headline": "LOOP B: Sell 10% BTC Sleeve -> USDT",
            "entry_instruction": (
                "Sell up to 100% of 10% BTC Sleeve into perp-driven squeeze. Rebuy strictly < P_sell at lower pool; "
                "if rally continues, HOLDING SPOT USDT INVENTORY (WAIT FOR < P_SELL)."
            ),
        }

    def _eval_range_magnet(self, m: MarketMetrics, lsce: LSCEState) -> dict:
        """Regime 3: Range / Liquidation Magnet -> Bidirectional Loop A & Loop B Core Habitat."""
        matched = []
        range_width_pct = (m.swing_high_4h - m.swing_low_4h) / max(m.price, 1.0) * 100
        in_range = m.swing_low_4h * 0.985 <= m.price <= m.swing_high_4h * 1.015
        if range_width_pct <= 4.5 and in_range:
            matched.append(f"Closed 4H range channel ({range_width_pct:.2f}% width: ${m.swing_low_4h:,.0f}-${m.swing_high_4h:,.0f})")
        if 0.90 <= m.spot_cvd_ratio <= 1.25:
            matched.append(f"Spot CVD balanced inside range (Ratio {m.spot_cvd_ratio:.2f})")
        if (m.ls_ratio_available and m.long_short_account_ratio >= 1.6) or m.funding_rate >= 0.008 or m.funding_rate <= -0.004:
            if m.ls_ratio_available:
                matched.append(f"Positioning skewed (L/S {m.long_short_account_ratio:.2f}, funding {m.funding_rate*100:.3f}%)")
            else:
                matched.append(f"Funding skewed ({m.funding_rate*100:.3f}%; L/S feed DATA UNAVAILABLE)")
        matched.append("Symmetrical modeled liquidation pools active above and below spot")

        if lsce.status == "SWEEP_AND_RECLAIM_CONFIRMED":
            sizing = 0.75
            dibse_sig = "LOOP A: USDT -> BTC"
            rotation = "USDT -> BTC"
            action = "Loop A: Buy Spot (75% of 10% USDT Sleeve)"
            playbook = "Range Washout Reclaim -> Loop A Entry"
            entry_inst = (
                "Deploy 75% of 10% USDT Sleeve on confirmed lower sweep reclaim. Sell target > P_buy toward closed 4H ceiling; "
                "if lower later, HOLDING SPOT BTC INVENTORY (WAIT FOR > P_BUY)."
            )
        elif lsce.status == "UPPER_SWEEP_REJECTION_CONFIRMED" or m.price >= m.swing_high_4h * 0.992:
            sizing = 0.75
            dibse_sig = "LOOP B: BTC -> USDT"
            rotation = "BTC -> USDT"
            action = "Loop B: Sell Spot (75% of 10% BTC Sleeve)"
            playbook = "Range Ceiling / Upper Squeeze -> Loop B Harvest"
            entry_inst = (
                "Rotate 75% of 10% BTC Sleeve into USDT at resistance/upper sweep rejection. Rebuy strictly < P_sell at lower pool; "
                "if higher later, HOLDING SPOT USDT INVENTORY (WAIT FOR < P_SELL)."
            )
        elif lsce.status == "SWEEP_IN_PROGRESS":
            sizing = 0.0
            dibse_sig = "HOLD BOTH SLEEVES"
            rotation = "Hold Both Sleeves"
            action = "Hold Both Sleeves (Lower Sweep In Progress)"
            playbook = "Wait for Lower Washout Reclaim before Loop A"
            entry_inst = "Active lower sweep underway. Do NOT front-run Loop A until spot reclaims above lower shelf with Spot CVD >= 1.05."
        else:
            sizing = 0.0
            dibse_sig = "HOLD BOTH SLEEVES"
            rotation = "Hold Both Sleeves"
            action = "Hold Both Sleeves (Wait Range Edge)"
            playbook = "Dual-Sleeve Standby: 10% USDT + 10% BTC"
            entry_inst = "Price mid-channel. Keep 10% USDT Sleeve ready for Loop A lower sweep and 10% BTC Sleeve ready for Loop B upper squeeze."

        return {
            "regime_id": "RANGE_LIQUIDATION_MAGNET",
            "name": "Range / Liquidation Magnet",
            "diagnosis": "Defined 4H channel with liquidation clusters on both edges",
            "playbook": playbook,
            "suitability": "Core Bidirectional DIBSE Habitat",
            "priority": 3,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": sizing,
            "action": action,
            "rotation": rotation,
            "dibse_signal": dibse_sig,
            "dibse_headline": action,
            "entry_instruction": entry_inst,
        }

    def _eval_cascade(self, m: MarketMetrics) -> dict:
        """Regime 4: Cascade / Forced Deleveraging -> Pause Loop A; Zero Stop-Outs."""
        matched = []
        if m.price_change_1h_pct <= -2.8 or m.price_change_24h_pct <= -6.0:
            matched.append(f"Sharp price plunge ({m.price_change_1h_pct:.2f}% 1h / {m.price_change_24h_pct:.2f}% 24h)")
        if m.oi_change_1h_pct <= -3.5 or m.oi_change_4h_pct <= -7.0:
            matched.append(f"OI unwinding sharply ({m.oi_change_1h_pct:.2f}% 1h / {m.oi_change_4h_pct:.2f}% 4h)")
        if m.funding_rate <= -0.005:
            matched.append(f"Funding deeply negative ({m.funding_rate*100:.3f}%)")
        if m.futures_basis_annualized < 1.0:
            matched.append(f"Basis collapsed / backwardation ({m.futures_basis_annualized:+.2f}%)")

        return {
            "regime_id": "CASCADE_FORCED_DELEVERAGING",
            "name": "Cascade / Forced Deleveraging",
            "diagnosis": "Forced derivatives unwind in progress",
            "playbook": "Pause Loop A Entries; Hold Existing Inventory",
            "suitability": "Waterfall Protection Mode (Zero Panic Selling)",
            "priority": 1,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": 0.0,
            "action": "Hold Both Sleeves (Wait Exhaustion)",
            "rotation": "Hold Both Sleeves",
            "dibse_signal": "HOLD BOTH SLEEVES",
            "dibse_headline": "Hold Both Sleeves (Pause Loop A Until OI Settles)",
            "entry_instruction": (
                "Keep 10% USDT Sleeve dry until cascade OI unwinds & local support reclaims. "
                "Zero forced stop-loss on 10% BTC Sleeve (HOLDING SPOT BTC INVENTORY if underwater)."
            ),
        }

    def _eval_distribution_bear(self, m: MarketMetrics, lsce: LSCEState) -> dict:
        """Regime 5: Distribution / Bear Continuation -> Zero EMA; Loop B on Weak Bounces."""
        matched = []
        if m.price < m.daily_vwap and m.price < m.weekly_vwap and m.price < m.swing_high_4h * 0.99:
            matched.append("Price trapped below Daily VWAP, Weekly VWAP, and closed 4H ceiling")
        if m.spot_cvd_slope_7d < 0 or m.spot_cvd_ratio <= 0.88:
            matched.append(f"Spot CVD persistently negative (7D {m.spot_cvd_slope_7d:+.0f} / Ratio {m.spot_cvd_ratio:.2f})")
        if m.spot_vol_ratio < 0.95:
            matched.append(f"Spot volume depressed ({m.spot_vol_ratio:.2f}x 20D baseline)")
        if m.funding_rate >= 0.002 or m.futures_basis_annualized < 4.0:
            matched.append(f"Funding {m.funding_rate*100:+.4f}% / compressed basis ({m.futures_basis_annualized:+.2f}%)")

        if lsce.status == "UPPER_SWEEP_REJECTION_CONFIRMED" or m.price >= m.daily_vwap * 0.998:
            sizing = 0.50
            dibse_sig = "LOOP B: BTC -> USDT"
            rotation = "BTC -> USDT"
            action = "Loop B: Trim 50% of 10% BTC Sleeve into Weak Bounce"
            playbook = "Distribution Bounce -> Loop B Trim (0.50x BTC Sleeve)"
            entry_inst = "Sell 50% of 10% BTC Sleeve into VWAP/resistance rejection; rebuy lower < P_sell at deep washout."
        else:
            sizing = 0.0
            dibse_sig = "HOLD BOTH SLEEVES"
            rotation = "Hold Both Sleeves"
            action = "Hold Both Sleeves (Protect 10% USDT Sleeve)"
            playbook = "Guard 10% USDT Sleeve; Hold BTC Inventory (No Stop-Loss)"
            entry_inst = "Distribution trend below VWAPs. Hold 10% USDT Sleeve until confirmed support sweep reclaim; never stop out BTC sleeve."

        return {
            "regime_id": "DISTRIBUTION_BEAR_CONTINUATION",
            "name": "Distribution / Bear Continuation",
            "diagnosis": "Weak spot demand / active overhead distribution",
            "playbook": playbook,
            "suitability": "Loop B Bounce Harvest / Loop A Patient",
            "priority": 2,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": sizing,
            "action": action,
            "rotation": rotation,
            "dibse_signal": dibse_sig,
            "dibse_headline": action,
            "entry_instruction": entry_inst,
        }

    def _eval_transition_mixed(self, m: MarketMetrics, candidates: List[dict], conflict_reason: str = None) -> dict:
        """Default Fallback: Transition / Mixed -> Hold Dual Inventory Sleeves."""
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
            matched.append(f"Candidate ({top_cand['name']}) awaiting Loop A reclaim or Loop B upper rejection")
        else:
            matched.append(f"Top candidate ({top_cand['name']}) scored only {top_cand['matches_count']}/4 (<3 required)")
            matched.append(f"Sub-VWAP / VWAP benchmark: Spot ${m.price:,.2f} vs Daily VWAP ${m.daily_vwap:,.2f}")
            matched.append(f"Order Flow & Basis: Spot CVD {m.spot_cvd_ratio:.2f} | Futures Basis {m.futures_basis_annualized:+.2f}%")
            matched.append("Dual-sleeve discipline: hold 10% USDT + 10% BTC until clean range-edge sweep confirms")

        return {
            "regime_id": "TRANSITION_MIXED",
            "name": "Transition / Mixed",
            "diagnosis": "Signals mixed or transitioning (Awaiting Loop A/B Edge)",
            "playbook": "Hold Both Sleeves (10% USDT + 10% BTC)",
            "suitability": "Neutral Dual-Sleeve Standby",
            "priority": 5,
            "matches_count": len(matched),
            "matched": matched,
            "sizing_factor": 0.0,
            "action": "Hold Both Sleeves (Wait Edge)",
            "rotation": "Hold Both Sleeves",
            "dibse_signal": "HOLD BOTH SLEEVES",
            "dibse_headline": "Hold Both Sleeves (10% USDT + 10% BTC)",
            "entry_instruction": (
                "Hold balanced 10% USDT + 10% BTC sleeves (80% Core untouched). Execute Loop A only on confirmed "
                "lower sweep reclaim or Loop B on upper squeeze rejection."
            ),
        }

    def _evaluate_dominant_magnet(
        self,
        m: MarketMetrics,
        upper: Optional[LiquidationCluster],
        lower: Optional[LiquidationCluster],
    ) -> Tuple[str, str, str, dict, float, float, float, float, List[Dict[str, Any]]]:
        """Evaluates Upper vs Lower Liquidation Magnet and builds canonical 6-tier ladder (zero ATR)."""
        u_vol = upper.estimated_vol_usd / 1e6 if upper else 0.0
        l_vol = lower.estimated_vol_usd / 1e6 if lower else 0.0

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

        cur_p = max(m.price, 1.0)
        s10_p = round(m.swing_high_4h * 1.025, 2)
        s25_p = round(m.swing_high_4h * 1.012, 2)
        u_near_p = round(upper.price_level, 2) if upper else round(m.swing_high_4h * 1.005, 2)
        l_near_p = round(lower.price_level, 2) if lower else round(m.swing_low_4h * 0.995, 2)
        l25_p = round(m.swing_low_4h * 0.988, 2)
        l10_p = round(m.swing_low_4h * 0.975, 2)

        def _row(
            tier: str,
            lev: str,
            side: str,
            lvl: float,
            vol_m: float,
            dist_pct_override: Optional[float] = None,
            is_nearest: bool = False,
        ) -> Dict[str, Any]:
            signed_pct = ((lvl - cur_p) / cur_p) * 100.0
            if dist_pct_override is not None:
                signed_pct = float(dist_pct_override) if side == "upper" else -float(dist_pct_override)
            return {
                "tier": tier,
                "leverage": lev,
                "side": side,
                "price": lvl,
                "distance_pct": round(signed_pct, 2),
                "distance_atr": None,
                "estimated_vol_m": round(vol_m, 1),
                "modeled": True,
                "is_nearest": is_nearest,
            }

        ladder = [
            _row("10x Shorts", "10x", "upper", s10_p, u_10_vol),
            _row("25x Shorts", "25x", "upper", s25_p, u_25_vol),
            _row("50-100x Shorts", "50-100x", "upper", u_near_p, u_vol, dist_pct_override=upper.distance_pct if upper else None, is_nearest=True),
            _row("100x Longs", "100x", "lower", l_near_p, l_vol, dist_pct_override=lower.distance_pct if lower else None, is_nearest=True),
            _row("25x Longs", "25x", "lower", l25_p, l_25_vol),
            _row("10x Longs", "10x", "lower", l10_p, l_10_vol),
        ]

        if not upper and not lower:
            return "Neutral / None", "NEUTRAL: No clear clusters", "No liquidation clusters detected.", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio, ladder
        if not upper:
            desc = f"LOWER (${lower.price_level:,.0f}, -{lower.distance_pct:.2f}%)"
            return "Lower Long Sweep Magnet", desc, f"Only lower modeled cluster active (~${lower.estimated_vol_usd/1e6:.1f}M).", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio, ladder
        if not lower:
            desc = f"UPPER (${upper.price_level:,.0f}, +{upper.distance_pct:.2f}%)"
            return "Upper Short Squeeze Magnet", desc, f"Only upper modeled cluster active (~${upper.estimated_vol_usd/1e6:.1f}M).", {}, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio, ladder

        u_dist_raw = upper.distance_pct
        l_dist_raw = lower.distance_pct
        u_dist = max(0.04, u_dist_raw)
        l_dist = max(0.04, l_dist_raw)
        range_w_pct = ((m.swing_high_4h - m.swing_low_4h) / cur_p) * 100.0
        wick_high = m.euphoria_wick_high if m.euphoria_wick_high > 0 else m.swing_high_4h
        wick_span_pct = ((wick_high - m.capitulation_wick_low) / cur_p) * 100.0

        imm_disp = f"~{round(imm_ratio):.0f}x" if imm_ratio >= 10 else f"{imm_ratio:.1f}x"
        f1_text = (
            f"Immediate Tier (Modeled): LOWER is {imm_disp} larger (~${l_vol:.1f}M vs ~${u_vol:.1f}M) | "
            f"Total Ladder (10x-100x Modeled): LOWER is {tot_ratio:.2f}x (~${tot_l_vol:.1f}M vs ~${tot_u_vol:.1f}M)"
        )
        f2_text = f"Spot CVD ratio {m.spot_cvd_ratio:.2f} vs Perp trend {m.perp_cvd_trend}"
        if m.ls_ratio_available:
            f3_text = f"Funding {m.funding_rate*100:+.4f}%, Retail L/S {m.long_short_account_ratio:.2f} ({long_share*100:.1f}% long)"
        else:
            f3_text = f"Funding {m.funding_rate*100:+.4f}%, Retail L/S ratio: DATA UNAVAILABLE"
        f4_text = (
            "Sub-VWAP structure (Loop B overhead supply active)"
            if m.price < m.daily_vwap
            else "Above Daily VWAP (Supportive spot floor)"
        )
        f5_text = f"LOWER is -{l_dist_raw:.2f}% away vs UPPER +{u_dist_raw:.2f}% away"
        f6_text = f"Closed 4H Range {range_w_pct:.2f}% | 24h Closed Wick Span {wick_span_pct:.2f}% | Depth {m.bids_asks_depth_ratio:.2f}"

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
            "factor_6_range_compression": f6_text,
        }

        if pull_lower >= pull_upper:
            dominant_name = "Lower Long Sweep Magnet"
            crowd_note = f"longs {long_share*100:.1f}% crowded" if m.ls_ratio_available else "modeled lower OI density"
            reason_short = f"LOWER (Immediate {imm_disp} / Ladder {tot_ratio:.2f}x; {crowd_note})"
            reason_full = f"Modeled lower cluster dominates (~${l_vol:.1f}M vs ~${u_vol:.1f}M) and across 10x-100x (~${tot_l_vol:.1f}M vs ~${tot_u_vol:.1f}M)."
        else:
            dominant_name = "Upper Short Squeeze Magnet"
            reason_short = "UPPER (Short Squeeze Resistance Target)"
            reason_full = "Modeled upper cluster chosen as primary upper magnet / Loop B trim target."

        return dominant_name, reason_short, reason_full, factors_dict, imm_ratio, tot_u_vol, tot_l_vol, tot_ratio, ladder

    def _calc_dibse_zones(
        self,
        m: MarketMetrics,
        lower: Optional[LiquidationCluster],
        upper: Optional[LiquidationCluster],
    ) -> Tuple[str, str]:
        """Builds empirical Loop A (buy washout -> exit > P_buy) and Loop B (sell rally -> rebuy < P_sell) play zones."""
        l_entry = lower.price_level if lower else m.swing_low_4h
        u_entry = upper.price_level if upper else m.swing_high_4h
        loop_a = f"Washout Zone ${min(l_entry, m.swing_low_4h):,.0f}-${max(l_entry, m.swing_low_4h):,.0f} -> Profit Exit > P_buy near ${max(m.daily_vwap, m.swing_high_4h):,.0f}"
        loop_b = f"Squeeze/Resistance ${min(u_entry, m.swing_high_4h):,.0f}-${max(u_entry, m.swing_high_4h):,.0f} -> Rebuy Target < P_sell near ${min(m.daily_vwap, m.swing_low_4h):,.0f}"
        return loop_a, loop_b

    def _get_plain_english_breakdown(
        self,
        regime_id: str,
        m: Optional[MarketMetrics],
        sizing: float,
        dibse_signal: str,
        lsce: Optional[LSCEState] = None,
        lower_cluster: Optional[LiquidationCluster] = None,
        upper_cluster: Optional[LiquidationCluster] = None,
        loop_a_zone: str = "",
        loop_b_zone: str = "",
    ) -> Tuple[str, List[str], str, str]:
        """Translates live telemetry into Bidirectional DIBSE Plain English strictly bound to scan values."""
        if m is None:
            return (
                "Telemetry incomplete or DATA UNAVAILABLE. Holding 10% USDT + 10% BTC sleeves passively (80% Core untouched).",
                [
                    "Missing Exchange Data: Required spot or derivatives telemetry failed verification.",
                    "Zero Synthetic Fallback Policy: The engine refuses to invent placeholder prices or ratios.",
                    "DIBSE Safe Standby: Await verified primary REST/WS recovery before rotating either sleeve.",
                ],
                "0% Sleeve Rotation: Holding existing 10% USDT + 10% BTC inventory calmly.",
                "Zero Stop-Losses: Underwater Loop A waits > P_buy; bypassed Loop B waits < P_sell.",
            )

        ls = m.long_short_account_ratio
        long_pct = (ls / (1.0 + ls) * 100.0) if (1.0 + ls) > 0 else 50.0
        lsce_status = lsce.status if lsce else "UNTESTED"
        lower_str = f"${lower_cluster.price_level:,.0f} (-{lower_cluster.distance_pct:.2f}%)" if lower_cluster else f"${m.swing_low_4h:,.0f}"
        upper_str = f"${upper_cluster.price_level:,.0f} (+{upper_cluster.distance_pct:.2f}%)" if upper_cluster else f"${m.swing_high_4h:,.0f}"

        if dibse_signal == "LOOP A: USDT -> BTC":
            verdict = (
                f"LOOP A TRIGGERED (USDT -> BTC): Spot (${m.price:,.2f}) confirmed washout absorption near {lower_str} "
                f"(Spot CVD {m.spot_cvd_ratio:.2f}, Depth {m.bids_asks_depth_ratio:.2f}). Deploy {sizing*100:.0f}% of your 10% USDT Sleeve."
            )
            why_sizing = (
                f"Deploy {sizing*100:.0f}% of 10% USDT Sleeve (= {sizing*10:.1f}% total equity; 80% core untouched). "
                f"Sell back to USDT only when price > P_buy ({loop_a_zone})."
            )
        elif dibse_signal == "LOOP B: BTC -> USDT":
            verdict = (
                f"LOOP B TRIGGERED (BTC -> USDT): Spot (${m.price:,.2f}) stretched into upper resistance/squeeze near {upper_str} "
                f"(Spot CVD {m.spot_cvd_ratio:.2f}, Basis {m.futures_basis_annualized:+.2f}%). Rotate {sizing*100:.0f}% of your 10% BTC Sleeve into USDT."
            )
            why_sizing = (
                f"Rotate {sizing*100:.0f}% of 10% BTC Sleeve (= {sizing*10:.1f}% total equity; 80% core untouched). "
                f"Rebuy BTC only when price < P_sell ({loop_b_zone})."
            )
        elif regime_id == "CASCADE_FORCED_DELEVERAGING":
            verdict = (
                f"Waterfall state: Spot dropped {m.price_change_24h_pct:+.2f}% (24h) / {m.price_change_1h_pct:+.2f}% (1h) with "
                f"OI {m.oi_change_24h_pct:+.2f}% (24h). Pause Loop A USDT buys until selling exhausts; zero forced stop-outs on existing BTC sleeve."
            )
            why_sizing = "Hold 10% USDT + 10% BTC Sleeves: Keep 10% USDT ready for post-cascade Loop A floor reclaim without panic-selling BTC."
        elif regime_id == "TRANSITION_MIXED":
            verdict = (
                f"Mixed Transition: Spot CVD is {m.spot_cvd_ratio:.2f}, Spot (${m.price:,.2f}) sits vs Daily VWAP "
                f"(${m.daily_vwap:,.2f}) with {m.futures_basis_annualized:+.2f}% basis & {m.bids_asks_depth_ratio:.2f} depth. Hold both sleeves for clean Loop A/B edge."
            )
            why_sizing = "Hold Both Sleeves (10% USDT + 10% BTC): Neither Loop A lower reclaim nor Loop B upper rejection has fired yet."
        else:
            verdict = (
                f"Mid-Range Standby (${m.price:,.2f} inside closed 4H band ${m.swing_low_4h:,.0f}-${m.swing_high_4h:,.0f}, LSCE {lsce_status}). "
                f"Watch {lower_str} for Loop A buy washout or {upper_str} for Loop B sell rally."
            )
            why_sizing = "Hold Both Sleeves (10% USDT + 10% BTC, 80% Core Untouched): Wait for verified sweep at either range extreme."

        oi_clause = f"24h OI {m.oi_change_24h_pct:+.2f}%" if m.oi_history_available else "OI history DATA UNAVAILABLE"
        ls_clause = f"{long_pct:.1f}% net long (L/S {ls:.2f})" if m.ls_ratio_available else "L/S ratio DATA UNAVAILABLE"

        why_points = [
            f"Closed 4H Structure & VWAP: Spot ${m.price:,.2f} vs Daily VWAP ${m.daily_vwap:,.2f} inside 4H band ${m.swing_low_4h:,.0f}-${m.swing_high_4h:,.0f}.",
            f"Spot vs Perp Flow: Spot CVD is {m.spot_cvd_ratio:.2f} ({m.spot_vol_ratio:.2f}x 20D vol), Depth {m.bids_asks_depth_ratio:.2f}, {oi_clause}, Basis {m.futures_basis_annualized:+.2f}%.",
            f"Bidirectional Pools ({lsce_status}): {ls_clause}; Loop A watch {lower_str} | Loop B watch {upper_str}.",
        ]
        why_stop = (
            "ZERO STOP-LOSSES (DIBSE Self-Healing): If Loop A drops below P_buy -> HOLDING SPOT BTC INVENTORY (WAIT FOR > P_BUY). "
            "If Loop B rallies above P_sell -> HOLDING SPOT USDT INVENTORY (WAIT FOR < P_SELL)."
        )
        return verdict, why_points, why_sizing, why_stop

    def _create_data_incomplete_result(self, reason: str) -> RegimeResult:
        """Returns safe default when critical exchange data is unavailable (explicit DATA UNAVAILABLE)."""
        verdict, why_pts, why_sizing, why_stop = self._get_plain_english_breakdown("DATA_INCOMPLETE", None, 0.0, "HOLD BOTH SLEEVES")
        return RegimeResult(
            regime="Data Incomplete",
            regime_id="DATA_INCOMPLETE",
            name="DATA UNAVAILABLE",
            diagnosis="Critical exchange data feeds offline or unverified",
            playbook="Hold Both Sleeves Passively (No Rotation)",
            suitability="Safe Standby",
            sizing_factor=0.0,
            action="DATA UNAVAILABLE — Hold Sleeves",
            rotation="Hold Both Sleeves",
            entry_instruction="Do not rotate either sleeve until verified primary API feeds recover.",
            stop_rule="ZERO STOP-LOSSES (DIBSE Asymmetric Self-Healing Inventory)",
            stop_price=0.0,
            stop_distance_pct=0.0,
            nearest_upper_cluster=None,
            nearest_lower_cluster=None,
            dominant_magnet="DATA UNAVAILABLE",
            dominant_magnet_reason=reason,
            risk_budget_ok=False,
            recommended_cash_deploy_pct=0.0,
            target_btc_allocation_pct=10.0,
            target_usdt_reserve_pct=10.0,
            matched_criteria=[],
            notes=reason,
            plain_english_verdict=verdict,
            why_points=why_pts,
            why_sizing_reason=why_sizing,
            why_stop_reason=why_stop,
            data_quality="DATA UNAVAILABLE",
            dibse_signal="HOLD BOTH SLEEVES",
            dibse_action_headline="DATA UNAVAILABLE — Hold Both Sleeves",
            loop_a_zone="DATA UNAVAILABLE",
            loop_b_zone="DATA UNAVAILABLE",
        )
