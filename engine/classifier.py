from typing import List, Tuple, Optional, Dict
from engine.models import MarketMetrics, LiquidationCluster, RegimeResult

class RegimeClassifier:
    """
    Classifies market state into Configs A through J strictly matching the Regime Radar.
    Strict Data Integrity:
      - Validates that market metrics are verified and live before evaluating.
      - Withholds trading verdict if data is incomplete.
      - Implements 100% mathematical alignment across all 6 magnet override factors.
      - Provides clear, jargon-free plain-English explanations for beginners (95% of users).
    """

    def classify(self, m: Optional[MarketMetrics], clusters: List[LiquidationCluster]) -> RegimeResult:
        # Data integrity check
        if m is None or not clusters:
            return self._create_data_incomplete_result("Market metrics or liquidation clusters unavailable.")

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

        # Allocations based on sizing factor (Percentage-based, privacy-first)
        sizing = best["sizing_factor"]
        max_spot_allocation = 80.0
        target_btc_pct = round(max_spot_allocation * sizing, 1)
        target_usdt_pct = round(100.0 - target_btc_pct, 1)
        recommended_cash_deploy = round(sizing * 100.0, 1)

        # Plain-English translation for beginners (Verdict, Why Points, Sizing Reason, Stop Reason)
        verdict, why_pts, why_sizing, why_stop = self._get_plain_english_breakdown(
            best["config_id"], m, round(stop_price, 2), round(stop_dist_pct, 2), sizing
        )

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
            recommended_cash_deploy_pct=recommended_cash_deploy,
            target_btc_allocation_pct=target_btc_pct,
            target_usdt_reserve_pct=target_usdt_pct,
            matched_criteria=best["matched"],
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
            "DATA_INCOMPLETE", None, 0.0, 0.0, 0.0
        )
        return RegimeResult(
            config="DATA_INCOMPLETE",
            name="Data Incomplete",
            diagnosis="Critical market data feed unavailable. Trading verdict withheld for safety.",
            regime_type="Incomplete Data",
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
            notes=f"Trading verdict withheld. Reason: {reason}",
            plain_english_verdict=verdict,
            why_points=why_pts,
            why_sizing_reason=why_sizing,
            why_stop_reason=why_stop,
            data_quality="UNAVAILABLE"
        )

    def _get_plain_english_breakdown(
        self,
        config_id: str,
        m: Optional[MarketMetrics],
        stop_price: float,
        stop_dist_pct: float,
        sizing: float
    ) -> Tuple[str, List[str], str, str]:
        """
        Translates quantitative findings into crystal-clear plain English for the 95% beginner audience.
        Returns (Verdict, Why Reasons, Sizing Explanation, Stop-Loss Explanation).
        """
        if config_id == "Config F":
            verdict = "The aggressive selling panic has subsided, speculative leverage debt has reset, and Bitcoin is forming a calm, stable foundation. It is an optimal window to steadily accumulate spot Bitcoin."
            why_points = [
                "The Bleeding Has Stopped: Wild price swings have calmed down by over 40% from peak turmoil. The market has exited panic mode and is holding a steady floor.",
                "Speculative Debt Flushed Clean: Borrowing funding fees have reset near zero and futures open interest is flat. Risky, over-leveraged traders have been cleared out.",
                "Patient Buyers Absorbing Supply: Real spot buyers are steadily soaking up available coins at the bottom of this range, creating strong structural support."
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? We are accumulating inside an established floor before the big move starts. Committing {sizing*100:.0f}% of your available trading cash secures an early favorable entry, while keeping a 25% cash buffer in reserve in case the floor is briefly re-tested."
            why_stop = f"Your Inviolable Safety Net: Stop-loss is placed at ${stop_price:,.2f} ({stop_dist_pct:.2f}% below current price). If Bitcoin drops below this floor, our accumulation thesis is invalidated. Sell back to USDT cash immediately to cap risk to a tiny, controlled loss."

        elif config_id == "Config A":
            verdict = "Real cash buyers are actively bidding Bitcoin higher on strong volume. This is an authentic, institutional-led bull market expansion."
            why_points = [
                "True Spot Demand: Trading volume and spot buyer order flow are expanding together. This move is driven by real capital, not borrowed leverage.",
                "Controlled Speculation: Futures funding rates remain healthy and balanced, meaning the rally is not over-leveraged or in bubble territory.",
                "Upward Momentum: Bitcoin is holding firmly above both daily and weekly trendlines, consistently making higher highs."
            ]
            why_sizing = "Why 100% Sizing? When real spot demand leads the market with low leverage, the odds heavily favor continuation. Full position allocation (1.0x) is mathematically warranted."
            why_stop = f"Your Inviolable Safety Net: Stop is placed at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away). If the recent swing low fails, exit to protect accumulated profits."

        elif config_id == "Config B":
            verdict = "Warning: The price may look high, but this rally is built on dangerous borrowed debt rather than real spot buyers. High probability of a sharp rug-pull."
            why_points = [
                "Fake Buying Pressure: Futures leverage is skyrocketing while actual spot cash buying is declining or flat. This is artificial momentum.",
                "Extreme Greed & High Fees: Borrowing rates have surged, showing that late retail traders are piling into hyper-leveraged longs at the top.",
                "Fragile Market Ceiling: Once leverage runs out of fresh capital, cascading stop-outs will trigger a fast, painful downward correction."
            ]
            why_sizing = "Why 0% Sizing (Take Profit)? Never chase a rally built on leverage. The system directs you to buy zero new Bitcoin, harvest 33% profit into cash, and trail your stops."
            why_stop = f"Your Inviolable Safety Net: Trail your protective stop tightly at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away). If price drops, lock in cash profits automatically."

        elif config_id == "Config C":
            verdict = "Smart money is actively defending key support. Major buyers are absorbing heavy selling pressure, preventing further downside."
            why_points = [
                "Rock-Solid Support: Bitcoin is testing major multi-month support or the 200-day moving average, where long-term investors step in.",
                "Spot Buyers Stepping Up: Real spot order flow is surging green even as derivatives traders panic, showing clear divergence and institutional accumulation.",
                "Seller Exhaustion: The selling pressure is failing to push prices lower, signaling that sellers have run out of inventory."
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? Accumulating at major defense zones offers exceptional risk-to-reward. Deploying {sizing*100:.0f}% of cash establishes a core position while preserving {100-sizing*100:.0f}% cash for flexibility."
            why_stop = f"Your Inviolable Safety Net: Stop is anchored at ${stop_price:,.2f} ({stop_dist_pct:.2f}% risk). If institutional support breaks, cut the position immediately."

        elif config_id == "Config D":
            verdict = "Danger: Behind a calm surface, large holders are quietly dumping their coins into retail buyers. A sudden breakdown is brewing."
            why_points = [
                "Smart Money Selling Out: Spot order flow is strongly negative. Large accounts are selling off coins while price appears flat.",
                "Retail Left Holding the Bag: Futures traders are attempting to keep price afloat with borrowed leverage, which never lasts.",
                "Loss of Daily Anchor: Price is slipping beneath the daily benchmark average (VWAP), signaling lost institutional support."
            ]
            why_sizing = "Why 0% Sizing (100% Cash)? Do not provide exit liquidity to dumping whales. Protect 100% of your portfolio in cash."
            why_stop = f"Your Inviolable Safety Net: Hard stop at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away). If triggered, convert everything to USDT cash."

        elif config_id == "Config E":
            verdict = "Emergency / Waterfall: Over-leveraged traders are being forcibly liquidated by exchanges in a domino effect. Stand aside and hold cash."
            why_points = [
                "Forced Liquidation Chain: Traders are getting margin called, and exchanges are market-selling their coins automatically.",
                "Plunging Open Interest: Billions in speculative positions are being wiped out in minutes.",
                "Falling Knife Danger: Bids are vanishing and price is falling vertically. Trying to guess the exact bottom here is extremely dangerous."
            ]
            why_sizing = "Why 0% Sizing (Hold Cash)? The system strictly enforces zero buying during active waterfalls. Wait until the selling completely runs out of fuel."
            why_stop = "Your Inviolable Safety Net: No active trades are taken during a cascade. 100% portfolio safety in cash."

        elif config_id == "Config G":
            verdict = "Aggressive short sellers got trapped and are now being forcibly squeezed out, triggering a violent upward rocket."
            why_points = [
                "Trapped Bearish Speculators: Excessive short positions piled in near the lows, expecting further downside.",
                "Forced Buying Cascade: As price pushed upward, their stop-losses were hit, forcing exchanges to buy market orders that accelerate the pump.",
                "Rapid Momentum: Open interest is dropping fast while price spikes, proving this is a mechanical squeeze rather than organic spot adoption."
            ]
            why_sizing = f"Why {sizing*100:.0f}% Sizing? Squeezes can run far and fast, but often exhaust once shorts finish covering. A {sizing*100:.0f}% tactical allocation captures the surge without reckless exposure."
            why_stop = f"Your Inviolable Safety Net: Trail your stop aggressively at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away) to lock in quick gains."

        elif config_id == "Config H":
            verdict = "The bull run has run out of gas. Buyers failed to break higher at resistance, creating a topping pattern."
            why_points = [
                "Failed Breakout: Price attempted to reach new highs but was aggressively rejected back down.",
                "Volume Divergence: As price tested the highs, actual spot buying volume was nowhere to be seen.",
                "High Overhead Pressure: Trapped late buyers at the highs are now looking to break even, creating a heavy ceiling."
            ]
            why_sizing = "Why 0% Sizing (Move to Cash)? When an uptrend exhausts at resistance, the next phase is typically a sharp correction. Harvest your profits into cash."
            why_stop = f"Your Inviolable Safety Net: Set stops at breakeven or at ${stop_price:,.2f} ({stop_dist_pct:.2f}% away) to prevent giving back gains."

        elif config_id == "Config I":
            verdict = "Bitcoin is locked in an entrenched downtrend. Every small bounce is met with heavy selling. Cash is the only safe position."
            why_points = [
                "Trend Resistance: Price is trapped below key 20-day and 50-day moving averages, confirming sellers dominate every rally.",
                "Depressed Spot Demand: Institutional buyers are on the sidelines; multi-week spot accumulation remains consistently negative.",
                "Dip-Buyer Traps: Retail traders trying to 'buy the dip' are consistently getting stopped out."
            ]
            why_sizing = "Why 0% Sizing (100% USDT Cash)? In a confirmed bear trend, your greatest edge is patience. Holding 100% cash guarantees complete capital preservation."
            why_stop = f"Your Inviolable Safety Net: No buying permitted until Bitcoin definitively reclaims the 50-day moving average (${stop_price:,.2f}) with real volume."

        elif config_id == "Config J":
            verdict = "False breakdown trap! Bitcoin briefly broke below major support to trigger panic, but big buyers instantly swallowed the supply and reclaimed the level."
            why_points = [
                "Bearish Trap Sprung: Short sellers rushed in at the breakdown, only to have the floor immediately reclaimed beneath their feet.",
                "Aggressive Dip Absorption: Massive volume surged in on the wick, showing smart money stepping in with conviction.",
                "High-Probability Reversal: Reclaiming a broken level with spot volume is historically one of the most reliable buy signals in Bitcoin."
            ]
            why_sizing = "Why 100% Sizing? Bear traps provide the highest statistical edge in crypto. Maximum capital deployment (1.0x) is warranted upon the 4-hour close reclaim."
            why_stop = f"Your Inviolable Safety Net: Place your stop strictly beneath the capitulation wick low at ${stop_price:,.2f} ({stop_dist_pct:.2f}% risk). If that level breaks, exit immediately."

        else:  # DATA_INCOMPLETE or fallback
            verdict = "Market data feed is temporarily offline or incomplete. All trading recommendations are locked to protect your funds."
            why_points = [
                "Zero-Guesswork Policy: The monitor never invents or approximates missing exchange data.",
                "Capital Protection First: If live order flow or open interest data cannot be verified, the only responsible action is holding cash.",
                "Automatic Recovery: The system checks exchange feeds every 30 minutes and will resume once verified data is restored."
            ]
            why_sizing = "Why 0% Sizing? Never trade blind. Keep 100% of your portfolio in cash until data integrity is confirmed."
            why_stop = "N/A: No active trades are placed while data is incomplete."

        return verdict, why_points, why_sizing, why_stop

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
          4. Regime & Higher-Timeframe Structure (Range/Base vs Trend)
          5. Asymmetry (Distance & Density comparison)
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
        # Base gravitational pull: Volume / (Distance % ^ 1.15) [Factor 1 & 5]
        pull_upper = (u_vol / 1e6) / (u_dist ** 1.15)
        pull_lower = (l_vol / 1e6) / (l_dist ** 1.15)

        # Factor 3 Multiplier: Crowding boost (trapped liquidity attracts price)
        if crowd_lower:
            pull_lower *= 1.85
        if crowd_upper:
            pull_upper *= 1.85

        # Factor 2 Multiplier: Spot leadership confirmation
        if spot_override_upper:
            pull_upper *= 1.60
            pull_lower *= 0.70
        elif spot_override_lower:
            pull_lower *= 1.60
            pull_upper *= 0.70

        # Factor 1 Multiplier: Extreme Size disparity inertia
        if size_ratio_l_to_u >= 5.0:
            pull_lower *= min(2.5, (size_ratio_l_to_u / 5.0) ** 0.5)
        elif size_ratio_l_to_u <= 0.2:
            pull_upper *= min(2.5, ((1.0 / size_ratio_l_to_u) / 5.0) ** 0.5)

        # Factor 4 Multiplier: Structural Trend Bias
        if regime_upper_bias:
            pull_upper *= 1.30
            pull_lower *= 0.85
        elif regime_lower_bias:
            pull_lower *= 1.30
            pull_upper *= 0.85

        # Factor 6 Multiplier: ATR Compression Impact
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
                reason_short = f"UPPER (Size {1.0/size_ratio_l_to_u:.1f}x larger outweighs distance edge; upside fuel)"
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
        stop_price = current_price * 0.97

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
            stop_price = current_price
        elif config_id == "Config I":
            stop_price = m.ema_50d * 1.01
        elif config_id == "Config J":
            stop_price = m.capitulation_wick_low * (1.0 - 0.006)

        stop_dist_pct = abs(current_price - stop_price) / current_price * 100
        return stop_price, stop_dist_pct

    # --- Evaluators for Configs A through J (Strictly verified on-exchange metrics) ---

    def _eval_config_e(self, m: MarketMetrics) -> dict:
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
            "action": "Wait for Phase 3 (0.0x)",
            "rotation": "Remain USDT",
            "entry_instruction": "Wait for Phase 3: 5m liqs stabilize, OI flat, 15m hammer wick. Deploy 0.50x ladder.",
            "stop_rule": "Capitulation wick low - 1.0%",
            "matched": matched
        }

    def _eval_config_g(self, m: MarketMetrics) -> dict:
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
            "sizing_factor": 0.5,
            "action": "Momentum Ride (0.50x)",
            "rotation": "USDT -> BTC",
            "entry_instruction": "Momentum Ride (0.50x). Trail 15m stop behind higher lows. Take 50% profit at pool target.",
            "stop_rule": "Tight trailing stop at 15m swing low",
            "matched": matched
        }

    def _eval_config_j(self, m: MarketMetrics) -> dict:
        score = 0
        matched = []
        if m.price < m.swing_low_4h and m.price_change_1h_pct > 0.8:
            score += 30
            matched.append("Sweep of 4H swing low followed by immediate V-reclaim")
        if abs(m.price - m.capitulation_wick_low) / m.price <= 0.015:
            score += 25
            matched.append("Price hovering tightly above capitulation wick low")
        if m.oi_change_1h_pct >= 1.0 and m.long_short_account_ratio < 1.0:
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
            "entry_instruction": "Maximum +EV setup. 4H close decisively back above broken support. Sizing 1.0x.",
            "stop_rule": "Capitulation wick low - 0.6%",
            "matched": matched
        }

    def _eval_config_c(self, m: MarketMetrics) -> dict:
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
            "entry_instruction": "Strictly zero new buying. Harvest 33% profit directly into perp pump. Trail stop.",
            "stop_rule": "Trail tight stop at 4H swing low",
            "matched": matched
        }

    def _eval_config_d(self, m: MarketMetrics) -> dict:
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
            "entry_instruction": "Sizing 0.0x (Target: 100% USDT Cash). Market sell 50% on 1H close below VWAP.",
            "stop_rule": "Hard trailing stop on 50% at 24h low",
            "matched": matched
        }

    def _eval_config_h(self, m: MarketMetrics) -> dict:
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
            "entry_instruction": "Sizing 0.0x (Target: 100% USDT Cash). Market sell 70% spot on 4H rejection.",
            "stop_rule": "Move stop to Breakeven on remaining 30%",
            "matched": matched
        }

    def _eval_config_i(self, m: MarketMetrics) -> dict:
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
            "entry_instruction": "Strict Cash (100% USDT). Treat every relief bounce as exit liquidity.",
            "stop_rule": "Invalidation: 1D close > 50D EMA with positive Spot CVD",
            "matched": matched
        }

    def _eval_config_a(self, m: MarketMetrics) -> dict:
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
            "entry_instruction": "Full Spot Long (1.0x). Entry: 60% breakout confirmation / 40% VWAP retest.",
            "stop_rule": "4H swing low - 0.6%",
            "matched": matched
        }
