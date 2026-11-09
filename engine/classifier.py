from typing import List, Tuple, Optional
from engine.models import MarketMetrics, LiquidationCluster, RegimeResult

class RegimeClassifier:
    """Classifies current BTC market state into Configs A through J strictly matching the Regime Radar."""

    def classify(self, m: MarketMetrics, clusters: List[LiquidationCluster]) -> RegimeResult:
        upper_cluster = next((c for c in clusters if c.side == "upper"), None)
        lower_cluster = next((c for c in clusters if c.side == "lower"), None)

        # Determine dominant magnet based on the 6 override factors
        dominant_magnet, magnet_title, magnet_reason, magnet_factors = self._evaluate_dominant_magnet(m, upper_cluster, lower_cluster)

        # Score all configs
        candidates = [
            self._eval_config_e(m),
            self._eval_config_g(m),
            self._eval_config_j(m),
            self._eval_config_c(m),
            self._eval_config_f(m),
            self._eval_config_b(m),
            self._eval_config_d(m),
            self._eval_config_h(m),
            self._eval_config_i(m),
            self._eval_config_a(m),
        ]

        # Filter candidates that scored >= 50, sort by priority and score
        valid = [c for c in candidates if c["score"] >= 45]
        
        if valid:
            valid.sort(key=lambda x: (x["priority"], -x["score"]))
            best = valid[0]
        else:
            candidates.sort(key=lambda x: -x["score"])
            best = candidates[0]

        # Calculate exact stop price and stop distance %
        stop_price, stop_dist_pct = self._calculate_stop(best["config_id"], m)

        # Risk budget check: standard swing trade risk limit is <= 3.5% stop distance
        risk_budget_ok = stop_dist_pct <= 3.5

        # Allocations based on sizing factor
        sizing = best["sizing_factor"]
        max_spot_allocation = 80.0  # Max ceiling 80% BTC, 20% USDT reserve
        current_recommended_allocation = round(max_spot_allocation * sizing, 1)

        # Combine diagnosis notes with explicit 1-2 sentence decisive magnet rationale
        notes = f"{best['diagnosis']}. Magnet Analysis: {magnet_reason} Matched {len(best['matched'])} facts: {', '.join(best['matched'])}."

        return RegimeResult(
            config=best["config_id"],
            name=best["name"],
            diagnosis=best["diagnosis"],
            regime_type=best["regime_type"],
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
            max_spot_allocation_pct=max_spot_allocation,
            current_recommended_allocation_pct=current_recommended_allocation,
            matched_criteria=best["matched"],
            notes=notes
        )

    def _evaluate_dominant_magnet(
        self,
        m: MarketMetrics,
        upper: Optional[LiquidationCluster],
        lower: Optional[LiquidationCluster]
    ) -> Tuple[str, str, str, dict]:
        """
        Systematically evaluates Upper vs Lower Liquidation Magnet using the 6 Override Factors:
          1. Cluster Size / Magnitude Disparity
          2. Spot vs Derivatives Leadership (Spot CVD)
          3. Crowding and Fuel (Funding Rate + Retail L/S + OI Flow)
          4. Regime & Higher-Timeframe Structure (Range/Base vs Trend)
          5. Asymmetry (Distance & Density comparison)
          6. Volatility Regime (ATR Compression)
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
            f1_text = f"LOWER is {size_ratio_l_to_u:.1f}x larger (${l_vol/1e6:.1f}M vs ${u_vol/1e6:.1f}M); massive liquidity pool advantage"
        elif size_ratio_l_to_u <= 0.33:
            f1_text = f"UPPER is {1.0/size_ratio_l_to_u:.1f}x larger (${u_vol/1e6:.1f}M vs ${l_vol/1e6:.1f}M); strong liquidity pool advantage"
        else:
            f1_text = f"Balanced magnitudes (${u_vol/1e6:.1f}M UPPER vs ${l_vol/1e6:.1f}M LOWER; ratio {size_ratio_l_to_u:.1f}x)"

        # Factor 2: Spot vs Derivatives Leadership
        spot_override_upper = False
        spot_override_lower = False
        if m.spot_cvd_ratio >= 1.25:
            f2_text = f"Spot CVD strongly positive ({m.spot_cvd_ratio:.2f}); genuine spot demand supports upside pull"
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
        if m.price < m.ma_200d and m.price < m.daily_vwap:
            f4_text = "Price below VWAP & 200D MA; structural weight favors lower base retests"
        elif m.price > m.daily_vwap and m.price > m.weekly_vwap:
            f4_text = "Price above Daily & Weekly VWAP; structural momentum favors upper continuation"
        else:
            f4_text = "Range / base compression; positioning magnets dominate immediate travel"

        # Factor 5: Asymmetry
        dist_ratio = l_dist / u_dist
        if 0.6 <= dist_ratio <= 1.6:
            f5_text = f"Distances roughly comparable ({u_dist:.2f}% UPPER vs {l_dist:.2f}% LOWER); size and crowding decide priority"
        elif dist_ratio > 1.6:
            f5_text = f"UPPER is closer ({u_dist:.2f}% vs {l_dist:.2f}%); proximity favors UPPER unless size disparity is extreme"
        else:
            f5_text = f"LOWER is closer ({l_dist:.2f}% vs {u_dist:.2f}%); proximity favors LOWER"

        # Factor 6: Volatility Regime (ATR)
        if m.atr_compression_pct >= 35.0:
            f6_text = f"ATR compressed {m.atr_compression_pct:.1f}%; low volatility amplifies magnetic pull of nearest dense pool"
        else:
            f6_text = f"ATR normal ({m.atr:,.0f} USD); price has sufficient room for wider expansion"

        # --- Compute Gravitational Pull Score ---
        # Base gravitational pull: Volume / (Distance % ^ 1.15)
        pull_upper = (u_vol / 1e6) / (u_dist ** 1.15)
        pull_lower = (l_vol / 1e6) / (l_dist ** 1.15)

        # Multipliers
        # Crowding boost (trapped liquidity attracts price)
        if crowd_lower:
            pull_lower *= 1.85
        if crowd_upper:
            pull_upper *= 1.85

        # Spot leadership confirmation
        if spot_override_upper:
            pull_upper *= 1.60
            pull_lower *= 0.70
        elif spot_override_lower:
            pull_lower *= 1.60
            pull_upper *= 0.70

        # Size override: if one cluster is > 5x larger, give extra inertia boost
        if size_ratio_l_to_u >= 5.0:
            pull_lower *= min(2.5, (size_ratio_l_to_u / 5.0) ** 0.5)
        elif size_ratio_l_to_u <= 0.2:
            pull_upper *= min(2.5, ((1.0 / size_ratio_l_to_u) / 5.0) ** 0.5)

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
                reason_short = f"LOWER (Size {size_ratio_l_to_u:.1f}x larger outweighs +{l_dist - u_dist:.2f}% distance; longs crowded)"
                reason_full = f"Lower cluster chosen: massive liquidity pool (${l_vol/1e6:.1f}M vs ${u_vol/1e6:.1f}M, {size_ratio_l_to_u:.1f}x) overrides the minor proximity of upper cluster, amplified by crowded long positioning."
            elif l_dist <= u_dist:
                reason_short = f"LOWER (Nearest -{l_dist:.2f}% + larger volume ${l_vol/1e6:.1f}M; spot neutral)"
                reason_full = f"Lower cluster chosen: nearest distance (-{l_dist:.2f}%) combined with superior volume density (${l_vol/1e6:.1f}M)."
            else:
                reason_short = f"LOWER (Downside gravity score {pull_lower:.0f} vs {pull_upper:.0f}; crowding fuel below)"
                reason_full = f"Lower cluster chosen based on aggregate gravitational pull ({pull_lower:.0f} vs {pull_upper:.0f}) and trapped long leverage."
        else:
            dominant_name = "Upper Short Squeeze Magnet"
            if size_ratio_l_to_u <= 0.4 and l_dist < u_dist:
                reason_short = f"UPPER (Size {1.0/size_ratio_l_to_u:.1f}x larger outweighs +{u_dist - l_dist:.2f}% distance; upside fuel)"
                reason_full = f"Upper cluster chosen: superior liquidation volume (${u_vol/1e6:.1f}M vs ${l_vol/1e6:.1f}M) outweighs minor lower proximity."
            elif u_dist <= l_dist and spot_override_upper:
                reason_short = f"UPPER (Nearest +{u_dist:.2f}% + Spot CVD confirming upside + compressed ATR)"
                reason_full = f"Upper cluster chosen: nearest proximity (+{u_dist:.2f}%) reinforced by positive spot CVD leadership."
            else:
                reason_short = f"UPPER (Nearest +{u_dist:.2f}% vs -{l_dist:.2f}%; compressed ATR favors path of least resistance)"
                reason_full = f"Upper cluster chosen as path of least resistance in compressed ATR regime."

        return dominant_name, reason_short, reason_full, factors_dict

    def _calculate_stop(self, config_id: str, m: MarketMetrics) -> Tuple[float, float]:
        """Calculates stop price and distance % based on the exact Config protocol."""
        current_price = m.price
        stop_price = current_price * 0.97  # fallback 3%

        if config_id == "Config A":
            stop_price = m.swing_low_4h * (1.0 - 0.006)
        elif config_id == "Config B":
            stop_price = m.swing_low_4h
        elif config_id == "Config C":
            stop_price = m.capitulation_wick_low * (1.0 - 0.005)
        elif config_id == "Config D":
            stop_price = m.swing_low_4h
        elif config_id == "Config E":
            stop_price = m.capitulation_wick_low * (1.0 - 0.01)
        elif config_id == "Config F":
            stop_price = m.base_floor * (1.0 - 0.005)
        elif config_id == "Config G":
            stop_price = m.swing_low_4h * (1.0 - 0.004)
        elif config_id == "Config H":
            stop_price = current_price  # Breakeven
        elif config_id == "Config I":
            stop_price = m.ema_50d * 1.01  # Invalidation is above 50D EMA
        elif config_id == "Config J":
            stop_price = m.capitulation_wick_low * (1.0 - 0.006)

        stop_dist_pct = abs(current_price - stop_price) / current_price * 100
        return stop_price, stop_dist_pct

    # --- Evaluators for Configs A through J ---

    def _eval_config_e(self, m: MarketMetrics) -> dict:
        """Config E: Liquidation Cascade (Forced Waterfall Deleveraging)."""
        score = 0
        matched = []
        if m.price_change_1h_pct <= -3.5 or m.price_change_24h_pct <= -7.0:
            score += 35
            matched.append(f"Price waterfall drop ({m.price_change_1h_pct:.2f}% 1h)")
        if m.oi_change_1h_pct <= -4.0 or m.oi_change_4h_pct <= -8.0:
            score += 30
            matched.append(f"OI crashing ({m.oi_change_1h_pct:.2f}% 1h / {m.oi_change_4h_pct:.2f}% 4h)")
        if m.funding_rate <= -0.005:
            score += 20
            matched.append(f"Funding plunged negative ({m.funding_rate*100:.3f}%)")
        if m.futures_basis_annualized < 1.0:
            score += 15
            matched.append("Basis backwardation / collapse")

        return {
            "config_id": "Config E",
            "name": "Liquidation Cascade",
            "diagnosis": "Forced Waterfall Deleveraging",
            "regime_type": "Waterfall Deleveraging",
            "suitability": "Core Operating Zone (Wait for Phase 3)",
            "priority": 1,
            "score": score,
            "sizing_factor": 0.0,
            "action": "Wait for Phase 3",
            "rotation": "Remain USDT",
            "entry_instruction": "Wait for Phase 3: 5m liqs < $2M, OI stabilizing flat, 15m hammer wick. Deploy 0.50x ladder (30%/40%/30%).",
            "stop_rule": "Capitulation wick low - 1.0%",
            "matched": matched
        }

    def _eval_config_g(self, m: MarketMetrics) -> dict:
        """Config G: Short Squeeze (Mechanical Liquidation Run)."""
        score = 0
        matched = []
        if m.price_change_1h_pct >= 2.0 and m.price > m.daily_vwap:
            score += 30
            matched.append(f"Explosive price pump (+{m.price_change_1h_pct:.2f}% 1h)")
        if m.oi_change_1h_pct <= -2.5 and m.price_change_1h_pct > 1.0:
            score += 30
            matched.append(f"OI collapsing as price rises ({m.oi_change_1h_pct:.2f}% 1h)")
        if m.funding_rate <= -0.005:
            score += 20
            matched.append(f"Funding deeply negative ({m.funding_rate*100:.3f}%)")
        if m.perp_cvd_trend == "surging" and m.spot_cvd_ratio < 1.20:
            score += 20
            matched.append("Perp CVD surging with spot CVD lagging")

        return {
            "config_id": "Config G",
            "name": "Short Squeeze",
            "diagnosis": "Mechanical Liquidation Run",
            "regime_type": "Short Squeeze",
            "suitability": "Core Operating Zone",
            "priority": 1,
            "score": score,
            "sizing_factor": 0.0,
            "action": "Harvest Gains",
            "rotation": "BTC -> USDT",
            "entry_instruction": "Sizing 0.0x (Never buy at squeeze peak). Scale out 50% spot profit directly into the pump.",
            "stop_rule": "Pre-squeeze 1H low - 0.4%",
            "matched": matched
        }

    def _eval_config_j(self, m: MarketMetrics) -> dict:
        """Config J: Bear Trap (Capitulation Absorption)."""
        score = 0
        matched = []
        if m.price > m.capitulation_wick_low and m.price >= m.daily_vwap * 0.995:
            score += 25
            matched.append("Price swept lows & VWAP/support reclaimed")
        if m.funding_rate <= -0.008:
            score += 30
            matched.append(f"Funding deeply negative ({m.funding_rate*100:.3f}%)")
        if m.oi_change_4h_pct >= 2.0 or m.long_short_account_ratio < 1.1:
            score += 25
            matched.append(f"OI expanding into lows / shorts crowding (L/S {m.long_short_account_ratio:.2f})")
        if m.spot_cvd_ratio >= 1.0:
            score += 20
            matched.append("Spot CVD refusing to drop (holding green/flat)")

        return {
            "config_id": "Config J",
            "name": "Bear Trap",
            "diagnosis": "Capitulation Absorption",
            "regime_type": "Absorption Base",
            "suitability": "Core Operating Zone",
            "priority": 2,
            "score": score,
            "sizing_factor": 1.0,
            "action": "Reclaim Buy (1.0x)",
            "rotation": "USDT -> BTC",
            "entry_instruction": "Maximum +EV setup. 4H close decisively back above broken support. Sizing 0.90x-1.0x.",
            "stop_rule": "Capitulation wick low - 0.6%",
            "matched": matched
        }

    def _eval_config_c(self, m: MarketMetrics) -> dict:
        """Config C: Bullish Absorption (Institutional Base Defense)."""
        score = 0
        matched = []
        if abs(m.price - m.ma_200d) / m.ma_200d <= 0.035 or abs(m.price - m.base_floor) / m.base_floor <= 0.02:
            score += 25
            matched.append("Price testing major range low / 200D MA")
        if m.spot_cvd_ratio >= 1.20:
            score += 30
            matched.append(f"Spot CVD surging positive (Ratio {m.spot_cvd_ratio:.2f})")
        if m.perp_cvd_trend in ["declining", "lower_lows"]:
            score += 20
            matched.append(f"Perp CVD printing lower lows ({m.perp_cvd_trend})")
        if m.oi_change_24h_pct <= 1.5:
            score += 15
            matched.append(f"OI flat or dropping ({m.oi_change_24h_pct:.2f}% 24h)")
        if m.bids_asks_depth_ratio >= 1.25:
            score += 10
            matched.append(f"Bids/Asks depth ratio favorable ({m.bids_asks_depth_ratio:.2f})")

        return {
            "config_id": "Config C",
            "name": "Bullish Absorption",
            "diagnosis": "Institutional Base Defense",
            "regime_type": "Absorption Base",
            "suitability": "Core Operating Zone",
            "priority": 2,
            "score": score,
            "sizing_factor": 0.75,
            "action": "Build Spot (0.75x)",
            "rotation": "USDT -> BTC",
            "entry_instruction": "Build Spot (0.75x). 50% on 1H range reclaim / 50% limit at support low.",
            "stop_rule": "Sweep wick low - 0.5%",
            "matched": matched
        }

    def _eval_config_f(self, m: MarketMetrics) -> dict:
        """Config F: Re-Accumulation (Post-Cascade Clean Base)."""
        score = 0
        matched = []
        if m.atr_compression_pct >= 30.0:
            score += 25
            matched.append(f"ATR compressed {m.atr_compression_pct:.1f}% from peak")
        range_width_pct = (m.swing_high_4h - m.swing_low_4h) / m.price * 100
        if range_width_pct <= 3.5:
            score += 25
            matched.append(f"Tight base range ({range_width_pct:.2f}% width)")
        if -2.0 <= m.oi_change_24h_pct <= 2.5:
            score += 20
            matched.append(f"OI flat / reset baseline ({m.oi_change_24h_pct:.2f}% 24h)")
        if 0.000 <= m.funding_rate <= 0.006:
            score += 15
            matched.append(f"Funding reset near zero ({m.funding_rate*100:.3f}%)")
        if m.spot_cvd_ratio >= 0.95:
            score += 15
            matched.append("Spot CVD stabilizing green/flat")

        return {
            "config_id": "Config F",
            "name": "Re-Accumulation",
            "diagnosis": "Post-Cascade Clean Base",
            "regime_type": "Clean Base",
            "suitability": "Core Operating Zone",
            "priority": 2,
            "score": score,
            "sizing_factor": 0.75,
            "action": "Re-Accumulate (0.75x)",
            "rotation": "USDT -> BTC",
            "entry_instruction": "Re-Accumulate (0.75x). 50% on 4H close above Base POC / 50% limit at base floor.",
            "stop_rule": "Base consolidation floor - 0.5%",
            "matched": matched
        }

    def _eval_config_b(self, m: MarketMetrics) -> dict:
        """Config B: Leveraged Bull (Fragile Overextension / Trap)."""
        score = 0
        matched = []
        if m.price_change_24h_pct >= 3.5:
            score += 25
            matched.append(f"Rapid vertical price expansion (+{m.price_change_24h_pct:.2f}% 24h)")
        if m.spot_cvd_ratio < 1.10 and m.perp_cvd_trend == "surging":
            score += 30
            matched.append("Perp CVD surging upward while Spot CVD lags/declines")
        if m.oi_change_24h_pct >= 6.0 or m.oi_change_3d_pct >= 14.0:
            score += 25
            matched.append(f"OI surging (+{m.oi_change_24h_pct:.2f}% 24h / +{m.oi_change_3d_pct:.2f}% 3D)")
        if m.funding_rate >= 0.020:
            score += 20
            matched.append(f"Funding elevated ({m.funding_rate*100:.3f}% / >20% ann.)")

        return {
            "config_id": "Config B",
            "name": "Leveraged Bull",
            "diagnosis": "Fragile Overextension / Trap",
            "regime_type": "Fragile Trap",
            "suitability": "Core Operating Zone",
            "priority": 3,
            "score": score,
            "sizing_factor": 0.0,
            "action": "Trim / Stand Aside (0.0x)",
            "rotation": "BTC -> USDT",
            "entry_instruction": "Strictly zero new buying. Harvest 33% profit directly into perp pump. Trail stop on 67%.",
            "stop_rule": "Trail tight stop at 4H swing low",
            "matched": matched
        }

    def _eval_config_d(self, m: MarketMetrics) -> dict:
        """Config D: Masked Fragility (Stealth Distribution Top)."""
        score = 0
        matched = []
        if m.spot_cvd_ratio <= 0.88:
            score += 30
            matched.append(f"Spot CVD strongly negative/falling ({m.spot_cvd_ratio:.2f})")
        if m.perp_cvd_trend in ["positive", "surging"]:
            score += 25
            matched.append("Perp CVD sustaining artificial price float")
        if m.oi_change_24h_pct > 2.0 and m.funding_rate >= 0.012:
            score += 25
            matched.append(f"OI expanding with positive funding ({m.funding_rate*100:.3f}%)")
        if m.price < m.daily_vwap:
            score += 20
            matched.append("Daily VWAP tested and broken below")

        return {
            "config_id": "Config D",
            "name": "Masked Fragility",
            "diagnosis": "Stealth Distribution Top",
            "regime_type": "Distribution Top",
            "suitability": "Secondary / Confirmatory",
            "priority": 3,
            "score": score,
            "sizing_factor": 0.0,
            "action": "Defensive Cash (100%)",
            "rotation": "BTC -> USDT",
            "entry_instruction": "Sizing 0.0x (Target: 75%-100% USDT Cash). Market sell 50% on 1H close below VWAP.",
            "stop_rule": "Hard trailing stop on 50% at 24h low",
            "matched": matched
        }

    def _eval_config_h(self, m: MarketMetrics) -> dict:
        """Config H: Distribution Top (Topping Exhaustion Failure)."""
        score = 0
        matched = []
        if abs(m.price - m.swing_high_4h) / m.price <= 0.015 and m.price < m.daily_vwap:
            score += 30
            matched.append("Double top / marginal high rejected below VWAP")
        if m.spot_cvd_ratio < 0.95 and m.spot_cvd_slope_7d < 0:
            score += 30
            matched.append("Bearish Spot CVD divergence (Price high, CVD lower)")
        if m.funding_rate >= 0.018:
            score += 20
            matched.append(f"Funding elevated ({m.funding_rate*100:.3f}%)")
        if m.futures_basis_annualized > 10.0:
            score += 20
            matched.append(f"Basis contango abnormally wide ({m.futures_basis_annualized:.1f}%)")

        return {
            "config_id": "Config H",
            "name": "Distribution Top",
            "diagnosis": "Topping Exhaustion Failure",
            "regime_type": "Distribution Top",
            "suitability": "Secondary / Confirmatory",
            "priority": 3,
            "score": score,
            "sizing_factor": 0.0,
            "action": "Defensive Cash (100%)",
            "rotation": "BTC -> USDT",
            "entry_instruction": "Sizing 0.0x (Cash: 85%-100% USDT). Market sell 70% spot on 4H rejection.",
            "stop_rule": "Move stop to Breakeven on remaining 30%",
            "matched": matched
        }

    def _eval_config_i(self, m: MarketMetrics) -> dict:
        """Config I: Bear Trend (Bearish Trend Continuation)."""
        score = 0
        matched = []
        if m.price < m.ema_20d and m.price < m.ema_50d and m.price < m.daily_vwap:
            score += 35
            matched.append("Price below 20D EMA, 50D EMA, and Daily VWAP")
        if m.spot_cvd_slope_7d < 0 and m.spot_cvd_slope_14d < 0:
            score += 30
            matched.append("Spot CVD persistent downward slope (7D and 14D negative)")
        if m.funding_rate >= 0.003:
            score += 15
            matched.append(f"Funding positive with trapped longs paying ({m.funding_rate*100:.3f}%)")
        if m.futures_basis_annualized < 4.0:
            score += 20
            matched.append(f"Basis compressed below 4% ann. ({m.futures_basis_annualized:.1f}%)")

        return {
            "config_id": "Config I",
            "name": "Bear Trend",
            "diagnosis": "Bearish Trend Continuation",
            "regime_type": "Bear Trend",
            "suitability": "Restricted / Cash Zone",
            "priority": 3,
            "score": score,
            "sizing_factor": 0.0,
            "action": "Strict Cash (100%)",
            "rotation": "Remain USDT",
            "entry_instruction": "Strict Cash (100% USDT). Treat every relief bounce as exit liquidity. Active magnet hunting forbidden.",
            "stop_rule": "Invalidation: 1D close > 50D EMA with positive Spot CVD",
            "matched": matched
        }

    def _eval_config_a(self, m: MarketMetrics) -> dict:
        """Config A: Healthy Bull (Genuine Spot-Led Expansion)."""
        score = 0
        matched = []
        if m.price > m.daily_vwap and m.price > m.weekly_vwap:
            score += 25
            matched.append("Price rising above Daily & Weekly VWAP")
        if m.spot_vol_ratio >= 1.25:
            score += 25
            matched.append(f"Spot volume expanding ({m.spot_vol_ratio:.2f}x 20D MA)")
        if m.spot_cvd_ratio >= 1.20:
            score += 25
            matched.append(f"Spot CVD positive (Ratio {m.spot_cvd_ratio:.2f})")
        if -1.0 <= m.oi_change_24h_pct <= 5.0:
            score += 15
            matched.append(f"OI moderate ({m.oi_change_24h_pct:.2f}% 24h)")
        if 0.002 <= m.funding_rate <= 0.012:
            score += 10
            matched.append(f"Funding controlled ({m.funding_rate*100:.3f}%)")

        return {
            "config_id": "Config A",
            "name": "Healthy Bull",
            "diagnosis": "Genuine Spot-Led Expansion",
            "regime_type": "Bullish Expansion",
            "suitability": "Core Operating Zone",
            "priority": 4,
            "score": score,
            "sizing_factor": 1.0,
            "action": "Full Spot Long (1.0x)",
            "rotation": "USDT -> BTC",
            "entry_instruction": "Full Spot Long (1.0x). Entry: 60% breakout confirmation / 40% VWAP retest. Max equity: 50%.",
            "stop_rule": "4H swing low - 0.6%",
            "matched": matched
        }
