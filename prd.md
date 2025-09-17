# Crypto Analytics & Sentiment Platform — Product Requirements (PRD)

## 1. Overview
A full‑stack product that aggregates cryptocurrency market data and augments it with text sentiment analysis. Users browse top coins with rich metrics, analyze texts or articles, and interact via a simple chat bot. The system consists of a FastAPI backend and a Flutter app (Android, iOS, desktop, web).

## 2. Goals & Non‑Goals
- Goals
  - Provide a fast, paginated crypto market list with prices, market cap, volume, and 24h change.
  - Support sentiment analysis for English and Persian (with translation fallback).
  - Store analyzed articles and scores for later review.
  - Deliver a modern, responsive Flutter app experience with offline demo mode.
- Non‑Goals
  - Portfolio tracking and trading execution.
  - Advanced NLP beyond rule‑based sentiment.
  - User authentication/authorization (v1).

## 3. Target Users & Personas
- Retail crypto enthusiasts: Want quick market view and lightweight insights.
- Content researchers: Test sentiment on news/articles quickly.
- Learners/developers: Explore simple AI + fintech app stack.

## 4. Primary Use Cases
1) Browse cryptocurrencies with pagination and see key metrics at a glance.
2) Tap a coin to view details (rank, price, 24h change, market cap, last updated).
3) Analyze arbitrary text (or articles) for sentiment and store results.
4) Use chat to get quick, friendly guidance.
5) Configure backend URL and turn Demo Mode on/off.

## 5. Features & Requirements
### 5.1 Crypto Browsing
- Fetch coins from CoinGecko (markets endpoint) with rate‑limit handling.
- Pagination: page and per_page parameters; show total_pages estimate.
- Display for each coin: rank, name, symbol, price, market cap, 24h change, volume, last updated, and icon image.
- Infinite scroll and manual pagination controls.

### 5.2 Sentiment Analysis
- Rule‑based English and Persian analyzers; auto‑detect language and translate non‑EN (best‑effort) to English.
- Endpoint returns label and scores (positive, negative, neutral).
- Persist each analysis result; allow article ingestion and listing.

### 5.3 Articles
- POST ingest single article with title/content; store and analyze.
- GET articles in reverse chronological order.

### 5.4 Chat Bot
- Simple, rule‑based responses for greeting, question, help, thanks, goodbye, and pointers to endpoints.

### 5.5 App Settings
- Backend URL configurable in Settings (auto 10.0.2.2 for Android emulator).
- Demo Mode toggles local sample data; persisted via Hive.
- Connectivity test action.

## 6. Platforms & Tech
- Backend: FastAPI, SQLModel (SQLite), requests, httpx, python‑dotenv, optional googletrans.
- Frontend: Flutter (Material 3), Provider, http, Hive, fl_chart.
- DevOps: Docker for backend; optional Nginx to serve Flutter web build; GitHub Actions for tests.

## 7. APIs (v1)
- Health: GET `/` → metadata and endpoints list.
- Crypto:
  - GET `/cryptos?page={n}&per_page={m}` → CryptoResponse { coins[], total_pages, last_updated, has_next, has_prev }
  - GET `/cryptos/top/{limit}` → CryptoResponse with top N coins
  - Coin fields: rank, id, symbol, name, price_usd, market_cap_usd, change_24h_pct, total_volume_usd, last_updated, image_url
- Sentiment:
  - POST `/analyze` { text } → { text, lang, label, scores, model }
  - POST `/ingest` { title, content } → Article
  - GET `/articles` → Article[]
- Chat: POST `/chat` { message } → { response }

## 8. Data Model (simplified)
- Article: id, title, content, created_at
- Analysis: id, text, label, positive, negative, neutral, created_at
- CryptoCoin (response): rank, symbol, id, name, price_usd, market_cap_usd, change_24h_pct, total_volume_usd, last_updated, image_url

## 9. UX Flows (happy paths)
1) Launch app → Home → Crypto List → Scroll/Next/Prev → Tap coin → Details dialog.
2) Settings → Turn off Demo Mode → Set backend URL → Connectivity test → Back → Crypto list loads live data.
3) Article page (future) → Paste title/content → Analyze → Saved and visible in Articles list.
4) Sentiment quick test → Enter text → Submit → See label/scores.

## 10. Error Handling & Edge Cases
- Backend:
  - Rate limit 429 retry with exponential backoff.
  - Timeouts → 500 with user‑readable messages.
  - Validation errors → 400 with details (page/per_page bounds, limit bounds).
- App:
  - Show error states (SnackBar/toast) with retry button.
  - Default placeholders when fields are null (e.g., price N/A, image fallback).

## 11. Non‑Functional Requirements
- Performance: First crypto list page < 1.5s on broadband; pagination under 1s cached.
- Reliability: Endpoint uptime via local server; simple in‑memory cache with TTL (60s default).
- Security: No auth in v1; CORS configurable; avoid leaking secrets.
- Internationalization: English UI; support Persian/English text input for sentiment.
- Observability: Structured logging; CI runs unit tests on PRs.

## 12. Configuration
- Env (`.env`): DATABASE_URL, CORS_ORIGINS, CRYPTO_CACHE_TTL, CoinGecko params.
- Flutter: Persisted `backendBaseUrl` and `demoMode` via Hive; platform‑aware defaults.

## 13. Release Plan (Milestones)
- v0.1 (MVP): Crypto list (pagination + icons), sentiment analyze, articles ingest/list, Settings (demo/backend), Docker backend, tests + CI.
- v0.2: Charts (price, dominance), improved error states, screenshots/docs polish.
- v0.3: Caching strategy improvements, optional Postgres, basic analytics.

## 14. Success Metrics
- Time‑to‑first‑data (TTFD) for `/cryptos` < 1.5s.
- Crash‑free sessions > 99% on app.
- 95th percentile `/cryptos` latency < 800ms (with cache warm).

## 15. Risks & Mitigations
- CoinGecko rate limits → backoff, caching, adjustable delays.
- Translation availability → on‑demand import; can disable gracefully.
- Localhost networking (emulator) → platform‑aware URLs and connectivity test.

## 16. Out of Scope (v1)
- Login, roles, and ACL.
- Historical price charts with persistence.
- Push notifications.

## 17. Open Questions
- Should we add a coin details screen with sparkline/price history?
- Persist article sentiment linkage to article id?
- Add web deploy pipeline for Flutter (static hosting)?

## 18. Acceptance Criteria (v0.1)
- Backend runs via `uvicorn` and serves `/cryptos`, `/cryptos/top/{n}`, `/analyze`, `/ingest`, `/articles`, `/chat`.
- Flutter app loads crypto list from backend, shows icons and ranks; infinite scroll; settings persist; connectivity test works.
- Unit tests pass in CI.
