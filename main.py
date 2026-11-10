import os
import sys
import json
import datetime

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from engine.fetcher import MarketDataFetcher
from engine.classifier import RegimeClassifier
from engine.risk_manager import RiskManager
from web.generator import WebGenerator

def run_radar():
    print("=" * 65)
    print(" 🧲 BTC MAGNET — QUANTITATIVE 5-REGIME & LIQUIDATION RADAR ")
    print("=" * 65)

    fetcher = MarketDataFetcher()
    classifier = RegimeClassifier()
    risk_manager = RiskManager()
    web_gen = WebGenerator(output_dir="dist")

    metrics = None
    clusters = []
    data_error = None

    print("[1/4] Ingesting verified market microstructure (Binance & Deribit)...")
    try:
        metrics, clusters = fetcher.fetch_metrics()
        print(f"      BTC Spot Price: ${metrics.price:,.2f}")
        print(f"      Daily VWAP: ${metrics.daily_vwap:,.2f} | 200D MA: ${metrics.ma_200d:,.2f}")
        print(f"      Funding Rate: {metrics.funding_rate*100:.4f}% | Basis: {metrics.futures_basis_annualized:.1f}%")
        print(f"      Open Interest: {metrics.open_interest:,.1f} BTC (24h: {metrics.oi_change_24h_pct:+.2f}%)")
        print(f"      Data Provenance: {metrics.spot_data_source} & {metrics.futures_data_source}")
    except Exception as e:
        print(f"WARNING: Data Integrity alert during market fetch: {e}")
        data_error = str(e)

    if data_error:
        print("[2/4] Critical data unavailable — engaging Data Incomplete Protocol...")
        regime = classifier._create_data_incomplete_result(data_error)
        risk = risk_manager.evaluate_risk(regime)
    else:
        print("[2/4] Evaluating Modeled Liquidity Pools & Clustering...")
        upper_c = next((c for c in clusters if c.side == "upper"), None)
        lower_c = next((c for c in clusters if c.side == "lower"), None)
        if upper_c:
            print(f"      UPPER SHORT POOL: ${upper_c.price_level:,.2f} (+{upper_c.distance_pct:.2f}% / +{upper_c.distance_atr:.2f} ATR) [Model: ${upper_c.estimated_vol_usd/1e6:.1f}M]")
        if lower_c:
            print(f"      LOWER LONG POOL:  ${lower_c.price_level:,.2f} (-{lower_c.distance_pct:.2f}% / -{lower_c.distance_atr:.2f} ATR) [Model: ${lower_c.estimated_vol_usd/1e6:.1f}M]")

        print("[3/4] Running Simplified 5-Regime Radar Diagnostic...")
        regime = classifier.classify(metrics, clusters)
        print(f"      REGIME: [{regime.name}] ({regime.diagnosis})")
        print(f"      MAJORITY EVIDENCE: {regime.majority_score}")
        print(f"      DOMINANT MAGNET: {regime.dominant_magnet_reason}")
        print(f"      ACTION PROTOCOL: {regime.action}")
        print(f"      SPOT ROTATION:   >>> {regime.rotation} <<<")
        print(f"      INVIOLABLE STOP: ${regime.stop_price:,.2f} ({regime.stop_distance_pct:.2f}% distance)")

        print("[4/4] Verifying Risk Budget & Sizing (Percentage Allocations)...")
        risk = risk_manager.evaluate_risk(regime)
        print(f"      RISK BUDGET: {'APPROVED' if risk['risk_budget_ok'] else 'REJECTED/DOWNSIZED'}")
        print(f"      INSTRUCTION: {risk['actionable_trade_instruction']}")

    # Build comprehensive output payload
    timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload = {
        "timestamp": timestamp_iso,
        "symbol": "BTCUSDT",
        "data_status": regime.data_quality,
        "regime": regime.to_dict(),
        "metrics": metrics.to_dict() if metrics else {},
        "risk": risk
    }

    # Save to data directory
    os.makedirs("data", exist_ok=True)
    with open("data/regime.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Generate GitHub Pages artifacts (dist/regime.json & dist/index.html)
    json_path, html_path = web_gen.generate(payload)
    print("=" * 65)
    print(f"✓ Generated API payload: {json_path}")
    print(f"✓ Generated Web Dashboard: {html_path}")
    print("=" * 65)

if __name__ == "__main__":
    run_radar()
