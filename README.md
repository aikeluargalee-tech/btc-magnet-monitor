# 🧲 BTC Magnet
> **Observable Positioning Mechanics & Liquidation Regime Diagnostic Engine**  
> *Engineered for Spot Swing Traders • Zero Leverage • Pre-Defined Inviolable Risk*

---

## 1. Overview & Purpose

**BTC Magnet** is an automated crypto market microstructure engine. Instead of predicting future prices using subjective chart patterns or narrative guesswork, BTC Magnet tracks **observable positioning mechanics**:

1. **Real Demand vs. Leveraged Positioning:** Dissecting whether moves are driven by real spot capital (Spot CVD, spot volume) or fragile leverage (Perp CVD, surging Open Interest, extreme funding).
2. **Liquidation Magnet Proximity:** Calculating dense pools of forced stop-losses and liquidations that act as mechanical price magnets.
3. **Regime Radar (Configs A through J):** Classifying market state into 10 distinct, quantifiable setups.
4. **Spot-Only Bidirectional Rotation:** Rotating capital between **BTC** and **USDT** based on the diagnosed regime, without needing margin, futures, or shorting.
5. **Inviolable Risk Control:** Every trade setup is evaluated against fixed risk budgets. If the structural stop distance exceeds the allowed budget, the trade is automatically rejected or downsized.

---

## 2. Quantitative Regime Radar (Configs A through J)

| Config | Diagnosis | Microstructure Facts | Actionable Protocol | Rotation |
| :--- | :--- | :--- | :--- | :--- |
| **Config A** | **Healthy Bull** (Spot Expansion) | Price > VWAP, Spot Vol > 1.35x 20D MA, Spot CVD positive, OI moderate, Funding controlled | Full Spot Long (1.0x). Stop: 4H swing low -0.6% | `USDT -> BTC` |
| **Config B** | **Leveraged Bull** (Fragile Trap) | Vertical price (>2.5x ATR), Spot CVD flat, Perp CVD surging, OI surging (>+7%), Funding elevated | Trim / Stand Aside (0.0x). Harvest 33% profit into pump | `BTC -> USDT` |
| **Config C** | **Bullish Absorption** (Base Defense) | Price testing 200D MA/base, Spot CVD surging, Perp CVD printing lower lows, Depth ratio >1.3 | Build Spot (0.75x). Stop: Sweep wick low -0.5% | `USDT -> BTC` |
| **Config D** | **Masked Fragility** (Distribution) | Price churning, Spot CVD negative, Perp CVD floating price, OI up with funding, VWAP breaking | Defensive Cash (100%). Sell 50% on 1H close < VWAP | `BTC -> USDT` |
| **Config E** | **Liquidation Cascade** (Waterfall) | Rapid drop >4%-8%, OI crashing <=-5% 1h, Funding negative, Basis backwardation | Wait for Phase 3 (0.0x). Do NOT catch knife | `Remain USDT` |
| **Config F** | **Re-Accumulation** (Clean Base) | ATR compressed >30%, tight range <2.5% width, OI flat, Funding near zero, Spot CVD flat | Re-Accumulate (0.75x). Stop: Base floor -0.5% | `USDT -> BTC` |
| **Config G** | **Short Squeeze** (Liquidation Run) | Explosive pump, Funding was negative, OI collapsing (short covering), Spot CVD lagging | Harvest Gains (0.0x). Scale out 50% spot profit | `BTC -> USDT` |
| **Config H** | **Distribution Top** (Failure) | Double top/wicks, Bearish Spot CVD divergence, Funding elevated, Basis wide contango | Defensive Cash (100%). Sell 70% spot on 4H rejection | `BTC -> USDT` |
| **Config I** | **Bear Trend** (Continuation) | Price < 20D/50D EMA & VWAP, Spot CVD downward slope, Funding positive, Basis <3% | Strict Cash (100%). Treat every relief bounce as exit | `Remain USDT` |
| **Config J** | **Bear Trap** (Capitulation) | Panic breakdown, Funding deeply negative, Shorts crowding (OI up), Spot CVD refusing to drop | Reclaim Buy (1.0x). 4H close back above support | `USDT -> BTC` |

---

## 3. Architecture & Deployment

```
   ┌────────────────────────────────────────────────────────┐
   │       GitHub Actions (Cron Trigger: Every 30m)         │
   │                                                        │
   │  1. Ingest Binance Spot & Futures Microstructure Data  │
   │  2. Compute VWAP, CVD, OI Changes, Basis, ATR          │
   │  3. Calculate Liquidation Clusters (Upper/Lower Magnets│
   │  4. Classify Config A-J & Apply Inviolable Risk Rules  │
   │  5. Export artifacts to `dist/`                        │
   └───────────────────────────┬────────────────────────────┘
                               │ Deploy Artifacts
                               ▼
   ┌────────────────────────────────────────────────────────┐
   │           GitHub Pages (Free High-Speed CDN)           │
   │     https://<your-username>.github.io/btc-magnet/      │
   ├───────────────────────────┬────────────────────────────┤
   │ • index.html              │ • regime.json              │
   │   (Live Mobile Web HUD)   │   (Free REST API Endpoint) │
   └─────────────┬─────────────┴─────────────┬──────────────┘
                 ▼                           ▼
        [Phone Home Screen]         [Native Mobile App]
        Instant PWA Dashboard       Polls JSON + AdMob & Alerts
```

---

## 4. Setup & Local Execution

### 1. Run Locally
```bash
# Clone the repository
git clone https://github.com/<your-username>/btc-magnet.git
cd btc-magnet

# Install dependencies
pip install -r requirements.txt

# Run the diagnostic engine
python main.py
```

### 2. Enable GitHub Pages Deployment
1. Push this repository to GitHub.
2. In your repository on GitHub, navigate to:
   **Settings $\rightarrow$ Pages**
3. Under **Build and deployment**:
   * **Source**: Select `GitHub Actions`
4. The workflow in `.github/workflows/radar.yml` will now automatically run every **30 minutes**, execute the scanner, and publish the live dashboard and API feed to:
   `https://<your-username>.github.io/btc-magnet/`

---

## 5. Machine-Readable API Endpoint (`regime.json`)

The GitHub Pages deployment generates a live JSON feed at:
`https://<your-username>.github.io/btc-magnet/regime.json`

Example response:
```json
{
  "timestamp": "2026-11-09T14:30:15.123456+00:00",
  "symbol": "BTCUSDT",
  "regime": {
    "config": "Config F",
    "name": "Re-Accumulation",
    "diagnosis": "Post-Cascade Clean Base",
    "sizing_factor": 0.75,
    "action": "Re-Accumulate (0.75x)",
    "rotation": "USDT -> BTC",
    "entry_instruction": "50% on 4H close above Base POC / 50% limit at base floor.",
    "stop_price": 73142.45,
    "stop_distance_pct": 1.61,
    "nearest_upper_cluster": {
      "price_level": 74880.0,
      "distance_pct": 0.73,
      "distance_atr": 0.87,
      "estimated_vol_usd": 64800000.0
    },
    "nearest_lower_cluster": {
      "price_level": 74240.0,
      "distance_pct": 0.13,
      "distance_atr": 0.16,
      "estimated_vol_usd": 360000000.0
    },
    "dominant_magnet": "Lower Long Sweep Magnet",
    "risk_budget_ok": true
  }
}
```

This REST endpoint will power the native mobile app with Google AdMob in Phase 3.
