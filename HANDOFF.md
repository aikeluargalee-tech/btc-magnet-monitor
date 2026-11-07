# BTC Magnet — Handoff Package

**For:** Google Antigravity (or any external builder)  
**Date:** November 2026  
**Owner repo:** https://github.com/nexus-analysis/btc-magnet (private)

## 1. Product Intent (Blue Ocean)
A free, mechanics-first Bitcoin app that answers one question only:  
**“What is currently pulling Bitcoin, and is there a clear swing edge or not?”**

It defaults to **“No clear edge — wait.”** and only speaks when strict internal conditions align. Growth comes from a clean, shareable “Magnet Card”. No red-ocean signal spam.

## 2. Locked Product Definition
See `docs/one-pager.md` for the full locked one-pager.

Key surface rules:
- Single screen only
- Live price + simplified magnet visual + one plain-language status card + Share button
- Open interest, funding, and regime are **internal filters only** — never shown as separate widgets
- Free forever for the core experience

## 3. Speaking Rules (Internal)
See `docs/speaking-rules.md`.

The app must default to “No clear edge — wait.” and only change status when all (or nearly all) of these are true:
1. Clear liquidation magnet present
2. Open-interest confirmation
3. Funding not contradictory
4. Regime allows the magnet to matter
5. Basic structure / spot-flow alignment
6. Not already swept
7. Minimum conviction threshold

## 4. Status Text Templates
See `docs/status-templates.md` for the exact voice and sentence patterns. Keep language honest and short. No hype.

## 5. Visual Direction
Modern dark fintech with restrained retro character (amber/cyan accents, terminal labeling).  
Reference the approved Magnet Card style (price, magnet bands, clean chart, terminal readout).  
The current live prototype UX is **not** the desired final design — rebuild the interface properly.

## 6. Data Sources (Prototype)
- Price: Binance public API (`https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT`)
- Modeled liquidation magnets: `https://edgeornot.com/api/liqmap/btc` (free, no key)
- Future: expand to real OI, funding, and regime calculations

## 7. Current Prototype Status
- Live at: https://btc-magnet.netlify.app
- Code in `prototype/index.html`
- Has live price + basic magnet bands + share button
- UX is functional but not production-quality — rebuild recommended

## 8. What to Build Next
1. Clean, high-quality mobile-first interface matching the visual direction
2. Full internal rule engine (OI + funding + regime + structure)
3. Reliable shareable Magnet Card image generation
4. Optional: simple history log of status calls for transparency
5. Keep the repo private; deploy publicly on Netlify or equivalent

## 9. Files in This Repo
- `docs/one-pager.md`
- `docs/speaking-rules.md`
- `docs/status-templates.md`
- `docs/prototype-spec.md`
- `prototype/index.html` (current starter)
- `HANDOFF.md` (this file)

All product decisions are locked. The builder should implement, not re-decide the core concept.
