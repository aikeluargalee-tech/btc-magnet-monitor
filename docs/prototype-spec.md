# BTC Magnet — Minimal Prototype Specification

### Goal
Single-screen, mobile-friendly web app. Free. No accounts.

### Features
1. Price display (BTC/USD + 24h change)
2. Simplified magnet visual (1–2 main bands)
3. Status card (default “wait” or high-conviction note)
4. Share Magnet Card button
5. Auto-refresh

### Data sources
- Price: Binance / CoinGecko public API
- Magnet / OI / funding: public CoinGlass-style or exchange endpoints
- Regime: simple internal calculation

### Technical approach
- Mobile-first single HTML page
- Free hosting (Vercel / Netlify / Cloudflare Pages)
- Client-side share image generation

### Out of scope for v1
Native apps, accounts, payments, alerts, extra screens.