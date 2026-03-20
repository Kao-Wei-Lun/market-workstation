# Market Workstation

V1 local daily-data research system for market ETL, indicators, Taiwan derivatives analysis, watchlists, backtesting, and daily reports. The current repository includes:
- FastAPI API service
- PostgreSQL-backed SQLAlchemy models and Alembic migrations
- Scheduler and analysis worker foundations
- Vue 3 + Vite frontend dashboard foundation
- Sample bootstrap and local management CLI for first-run development

## Prerequisites

- Python 3.12
- PostgreSQL 16 if running without Docker
- Docker and Docker Compose for the recommended local stack

## Environment setup

1. Create a local environment file:
   `cp .env.example .env`
2. For host-side commands such as `make migrate` and `make seed`, keep `POSTGRES_HOST=localhost` in `.env`.
3. Docker Compose overrides the in-container DB host to `db`, so the same `.env` still works for containers.
4. Leave provider API keys empty for the sample local workflow unless you are wiring a real source.

## Local Python setup

1. Create the virtual environment:
   `python3 -m venv .venv`
2. Install the project:
   `make setup`

## Quickstart

1. Start the local development services:
   `make dev-up`
2. Run database migrations:
   `make migrate`
3. Seed sample instruments, watchlist membership, and tags:
   `make seed`
4. Generate deterministic frontend-visible demo data:
   `make demo-data`
5. Run the startup smoke test:
   `make smoke-test`
6. Start the frontend:
   `make run-frontend`

## Running services locally

- API:
  `make run-api`
- Scheduler worker:
  `make run-scheduler`
- Analysis worker:
  `make run-analysis`
- Frontend:
  `make run-frontend`

## Management CLI

All bootstrap commands are available through `scripts/manage.py`:
- `python scripts/manage.py migrate`
- `python scripts/manage.py seed`
- `python scripts/manage.py demo-data --trade-date 2026-03-20`
- `python scripts/manage.py sample-etl --trade-date 2026-03-20`
- `python scripts/manage.py indicator-update --trade-date 2026-03-20`
- `python scripts/manage.py generate-reports --trade-date 2026-03-20`
- `python scripts/manage.py smoke-test --api-base-url http://localhost:8000`

## Docker Compose notes

- `docker-compose.yml` is set up for local development with `db`, `api`, `scheduler`, and `analysis`.
- The compose stack also includes an optional `frontend` service on `http://localhost:5173`.
- Compose now falls back to sane local defaults when `.env` is missing or incomplete.
- Source code is mounted into the containers so API and worker code changes are reflected without rebuilding the image for every edit.
- The API service exposes `http://localhost:8000/healthz` and has a compose healthcheck.

## Sample verification

After running the quickstart commands:
- Open `http://localhost:8000/health`
- Open `http://localhost:8000/healthz`
- Open `http://localhost:5173`
- Run `make smoke-test`
- Query a report list:
  `curl "http://localhost:8000/reports?report_date=2026-03-20"`
- Run the worker job list:
  `python -m workers.scheduler.main --list-jobs`
  `python -m workers.analysis.main --list-jobs`
- Verify the scheduler stays up:
  `docker compose ps`
  `docker compose logs scheduler --tail=100`

## Make targets

- `make setup`
- `make migrate`
- `make seed`
- `make demo-data`
- `make sample-etl`
- `make indicator-update`
- `make generate-reports`
- `make smoke-test`
- `make run-api`
- `make run-scheduler`
- `make run-analysis`
- `make frontend-install`
- `make run-frontend`
- `make frontend-build`
- `make frontend-test`
- `make test`
- `make lint`
- `make typecheck`
- `make dev-up`
- `make dev-down`

## Feature notes

- Connector modules live under `services/connectors/` and stay provider-isolated.
- The ETL foundation lives under `services/core/etl/` with separate fetch, normalize, validate, and load stages.
- Technical indicators currently include `SMA`, `EMA`, `MACD`, `RSI`, `Bollinger Bands`, `ADX/DMI`, `ATR`, `Stochastic`, `OBV`, `Ichimoku`, `Supertrend`, `Keltner Channel`, `CCI`, `ROC`, `MFI`, `Williams %R`, `Donchian Channel`, and `Parabolic SAR`.
- Taiwan derivatives analysis persists raw daily rows to `tw_derivatives_daily` and derived analytics to `tw_derivatives_features`.
- Daily reports persist to `reports_daily`, and query APIs are exposed under `/reports`.
- Daily reporting now includes a richer persisted `daily_report_bundle` with structured sections for market summary, watchlist highlights, group scanner highlights, derivatives context, next-day candidates, top movers, and technical breadth.
- Next-day watch candidate runs persist to `candidate_runs` and `candidate_items`, with generation and query APIs exposed under `/candidates`.
- Scheduler and analysis workers share a registered-job runtime and persist heartbeat state to `worker_health`.
- Auto-classification rules can tag instruments from market, asset type, symbol, name, and existing-tag rules, and the group scanner can scan either a tag group or a watchlist.
- Backtesting now supports composite rule trees, parameterized rule operands, optional universe filters, multi-position daily execution controls, parameter search, and walk-forward evaluation APIs.

## Seed vs Demo Data

- `make seed` only creates reference data such as instruments, watchlists, and tags.
- `make demo-data` builds on `seed` and generates deterministic frontend-visible datasets for local development:
  - daily bars
  - indicator values
  - Taiwan derivatives rows and features
  - a candidate run with items
  - a backtest run with trades
  - persisted daily reports and a report bundle
- `make demo-data` is designed to be repeatable for the same `TRADE_DATE` without growing duplicate demo backtests or candidate runs.

## Frontend Demo Flow

- For a visibly usable local frontend, this is the shortest path:
  `make migrate`
  `make seed`
  `make demo-data`
  `make run-frontend`
- After running demo data generation, these endpoints should return non-empty payloads:
  `curl http://localhost:8000/backtests/runs`
  `curl http://localhost:8000/candidates/runs`
  `curl http://localhost:8000/reports/latest`
  `curl http://localhost:8000/derivatives/summary/latest`

## Next-Day Candidates

- Generate a persisted candidate run:
  `curl -X POST http://localhost:8000/candidates/runs -H "Content-Type: application/json" -d '{"candidate_date":"2026-03-20","top_n":10}'`
- Get the latest run for a date:
  `curl http://localhost:8000/candidates/runs/by-date/2026-03-20`
- List candidate items for a run:
  `curl http://localhost:8000/candidates/runs/<run_id>/items`
- The daily next-day candidates report reuses the same scoring service as the candidate run API.

## Daily Report Bundle

- Retrieve the richer daily report bundle:
  `curl http://localhost:8000/reports/2026-03-20/bundle`
- Retrieve one bundle section:
  `curl http://localhost:8000/reports/2026-03-20/bundle/sections/technical_breadth_summary`
- The bundle includes structured sections and markdown-friendly content for market review and next-day planning.

## Advanced Backtesting

- Run a parameterized daily backtest:
  `curl -X POST http://localhost:8000/backtests/runs -H "Content-Type: application/json" -d '{"name":"SMA template","parameters":{"entry_threshold":"10","exit_threshold":"11"},"definition":{"instrument_id":1,"initial_cash":"100000","position_size":"0.5","max_concurrent_positions":2,"entry_rule":{"left":{"kind":"price","field":"close"},"operator":"gt","right":{"kind":"parameter","parameter_name":"entry_threshold"}},"exit_rule":{"left":{"kind":"price","field":"close"},"operator":"lt","right":{"kind":"parameter","parameter_name":"exit_threshold"}}}}'`
- Run a parameter search:
  `curl -X POST http://localhost:8000/backtests/searches -H "Content-Type: application/json" -d '{"name":"SMA grid","definition":{"instrument_id":1,"entry_rule":{"left":{"kind":"price","field":"close"},"operator":"gt","right":{"kind":"parameter","parameter_name":"entry_threshold"}},"exit_rule":{"left":{"kind":"price","field":"close"},"operator":"lt","right":{"kind":"parameter","parameter_name":"exit_threshold"}}},"parameter_space":{"entry_threshold":["10","11"],"exit_threshold":["11","12"]}}'`
- Run walk-forward evaluation:
  `curl -X POST http://localhost:8000/backtests/walk-forward -H "Content-Type: application/json" -d '{"name":"SMA walk forward","definition":{"instrument_id":1,"entry_rule":{"left":{"kind":"price","field":"close"},"operator":"gt","right":{"kind":"parameter","parameter_name":"entry_threshold"}},"exit_rule":{"left":{"kind":"price","field":"close"},"operator":"lt","right":{"kind":"parameter","parameter_name":"exit_threshold"}}},"parameter_space":{"entry_threshold":["10","11"],"exit_threshold":["11","12"]},"train_window_days":60,"test_window_days":20}'`
- Retrieve search results:
  `curl http://localhost:8000/backtests/searches/<search_run_id>/results`
- Retrieve walk-forward windows:
  `curl http://localhost:8000/backtests/walk-forward/<walk_forward_run_id>/windows`

## API Output And Export

- Dashboard overview:
  `curl "http://localhost:8000/api/dashboard/overview?trade_date=2026-03-20&watchlist_id=1&tag=semiconductor"`
- Watchlist dashboard payload:
  `curl "http://localhost:8000/api/dashboard/watchlists/1?trade_date=2026-03-20"`
- Group dashboard payload:
  `curl "http://localhost:8000/api/dashboard/groups/semiconductor?trade_date=2026-03-20"`
- Latest candidates dashboard payload:
  `curl "http://localhost:8000/api/dashboard/candidates/latest?candidate_date=2026-03-20&limit=10&offset=0"`
- Latest derivatives dashboard payload:
  `curl "http://localhost:8000/api/dashboard/derivatives/latest?trade_date=2026-03-20"`
- Latest backtests dashboard payload:
  `curl "http://localhost:8000/api/dashboard/backtests/latest?limit=5"`
- Latest reports dashboard payload:
  `curl "http://localhost:8000/api/dashboard/reports/latest?report_date=2026-03-20&limit=10&offset=0"`
- Latest derivatives bias summary:
  `curl http://localhost:8000/derivatives/summary/latest`
- List latest reports:
  `curl http://localhost:8000/reports/latest`
- Export a report bundle as CSV:
  `curl "http://localhost:8000/reports/2026-03-20/bundle/export?export_format=csv"`
- List candidate runs or filter candidate items:
  `curl "http://localhost:8000/candidates/runs?candidate_date=2026-03-20"`
  `curl "http://localhost:8000/candidates/items?candidate_date=2026-03-20&symbol=2330"`
- Export a candidate run:
  `curl "http://localhost:8000/candidates/runs/<run_id>/export?export_format=csv"`
- Query scanner summaries and export them:
  `curl "http://localhost:8000/scanner/summary?trade_date=2026-03-20&tag=semiconductor"`
  `curl "http://localhost:8000/scanner/export?trade_date=2026-03-20&watchlist_id=1&export_format=csv"`
- List backtest runs or export trades:
  `curl http://localhost:8000/backtests/runs`
  `curl "http://localhost:8000/backtests/runs/<run_id>/export?export_format=csv"`

Dashboard-oriented APIs now return a consistent top-level structure with `meta`, `summary_cards`, `highlights`, `ranked_lists`, and typed `data` payloads, which is intended to reduce frontend-side reshaping work.

## Frontend Dashboard

- The frontend lives under `frontend/` and uses Vue 3, Vite, TypeScript, Vue Router, Pinia, and Axios.
- Overview, Watchlists, Groups, Candidates, Reports, Backtests, and Derivatives now use the existing backend APIs for local single-user review.
- The frontend reads aggregate dashboard payloads from `/api/dashboard/...` and also fetches page-specific detail data from `/watchlists`, `/candidates`, `/reports`, `/backtests`, and `/derivatives`.
- The current frontend pass adds practical UI helpers across the pages:
  - filter bars for page scope and quick search
  - sortable data tables for runs, items, and report lists
  - lightweight bar charts for rankings and breadth-style summaries
  - detail panels and metric grids for selected run/report/derivatives context
- Configure the browser-side API target with `VITE_API_BASE_URL` in `.env` or `frontend/.env.example`.
- Typical local setting:
  `VITE_API_BASE_URL=http://localhost:8000`
- For local development:
  `make frontend-install`
  `make run-frontend`
- For Docker Compose development:
  `make dev-up`
  Then open `http://localhost:5173`.
- The frontend expects the backend API to be reachable before loading detail views; if you change the API host or port, restart the Vite dev server after updating `VITE_API_BASE_URL`.
- The API now allows local frontend origins by default through CORS:
  `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:4173`, and `http://127.0.0.1:4173`
- Override allowed browser origins with `CORS_ALLOWED_ORIGINS` in `.env` if your frontend runs on a different host or port.
- If the frontend shows an API error that mentions a network or CORS problem, verify:
  `curl http://localhost:8000/health`
  and confirm `VITE_API_BASE_URL` points at that API origin.

## Verification

- `pytest -q`
- `ruff check .`
- `mypy .`
