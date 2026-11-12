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
    print(" 🧲 BTC MAGNET — DIBSE BIDIRECTIONAL SPOT SWING & RADAR ")
    print("=" * 65)

    fetcher = MarketDataFetcher()
    classifier = RegimeClassifier()
    risk_manager = RiskManager()
    web_gen = WebGenerator(output_dir="dist")

    metrics = None
    clusters = []
    data_error = None

    print("[1/4] Ingesting closed-bar empirical microstructure (Binance & Perps)...")
    try:
        metrics, clusters = fetcher.fetch_metrics()
        print(f"      BTC Spot Price:  ${metrics.price:,.2f}")
        print(f"      Daily VWAP:      ${metrics.daily_vwap:,.2f} | Weekly VWAP: ${metrics.weekly_vwap:,.2f}")
        print(f"      Closed 4H Range: ${metrics.swing_low_4h:,.2f} - ${metrics.swing_high_4h:,.2f}")
        print(f"      Funding Rate:    {metrics.funding_rate*100:.4f}% | Basis: {metrics.futures_basis_annualized:.2f}%")
        print(f"      Open Interest:   {metrics.open_interest:,.1f} BTC (24h: {metrics.oi_change_24h_pct:+.2f}%)")
        print(f"      Data Provenance: {metrics.spot_data_source} & {metrics.futures_data_source}")
    except Exception as e:
        print(f"WARNING: Data Integrity alert during market fetch: {e}")
        data_error = str(e)

    if data_error:
        print("[2/4] Critical data unavailable — engaging DATA UNAVAILABLE Standby...")
        regime = classifier._create_data_incomplete_result(data_error)
        risk = risk_manager.evaluate_risk(regime)
    else:
        print("[2/4] Evaluating Modeled Liquidity Pools (Upper & Lower)...")
        upper_c = next((c for c in clusters if c.side == "upper"), None)
        lower_c = next((c for c in clusters if c.side == "lower"), None)
        if upper_c:
            print(f"      UPPER SHORT POOL (Loop B): ${upper_c.price_level:,.2f} (+{upper_c.distance_pct:.2f}%) [Model: ~${upper_c.estimated_vol_usd/1e6:.1f}M]")
        if lower_c:
            print(f"      LOWER LONG POOL  (Loop A): ${lower_c.price_level:,.2f} (-{lower_c.distance_pct:.2f}%) [Model: ~${lower_c.estimated_vol_usd/1e6:.1f}M]")

        print("[3/4] Running Bidirectional DIBSE + 5-Regime Radar Diagnostic...")
        regime = classifier.classify(metrics, clusters)
        print(f"      REGIME:       [{regime.name}] ({regime.diagnosis})")
        print(f"      DIBSE SIGNAL: >>> {regime.dibse_signal} <<< ({regime.rotation})")
        print(f"      LSCE GATE:    {regime.lsce_status} ({regime.lsce_side})")
        print(f"      LOOP A ZONE:  {regime.loop_a_zone}")
        print(f"      LOOP B ZONE:  {regime.loop_b_zone}")
        print(f"      STOP POLICY:  {regime.stop_rule}")

        print("[4/4] Verifying DIBSE Dual-Sleeve Sandbox (10% USDT + 10% BTC)...")
        risk = risk_manager.evaluate_risk(regime)
        print(f"      SANDBOX:      {regime.sleeve_allocation}")
        print(f"      INSTRUCTION:  {risk['actionable_trade_instruction']}")

    timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    payload = {
        "timestamp": timestamp_iso,
        "symbol": "BTCUSDT",
        "data_status": regime.data_quality,
        "regime": regime.to_dict(),
        "metrics": metrics.to_dict() if metrics else {},
        "risk": risk
    }

    os.makedirs("data", exist_ok=True)
    with open("data/regime.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    json_path, html_path = web_gen.generate(payload)
    print("=" * 65)
    print(f"✓ Generated API payload: {json_path}")
    print(f"✓ Generated Web Dashboard: {html_path}")
    print("=" * 65)


if __name__ == "__main__":
    run_radar()
