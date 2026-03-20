# Market Workstation

V1 local daily-data research system for market ETL, indicators, Taiwan derivatives analysis, watchlists, backtesting, and daily reports. The current repository includes:
- FastAPI API service
- PostgreSQL-backed SQLAlchemy models and Alembic migrations
- Scheduler and analysis worker foundations
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
4. Load sample daily market data:
   `TRADE_DATE=2026-03-20 make sample-etl`
5. Compute indicators:
   `TRADE_DATE=2026-03-20 make indicator-update`
6. Generate daily reports:
   `TRADE_DATE=2026-03-20 make generate-reports`

## Running services locally

- API:
  `make run-api`
- Scheduler worker:
  `make run-scheduler`
- Analysis worker:
  `make run-analysis`

## Management CLI

All bootstrap commands are available through `scripts/manage.py`:
- `python scripts/manage.py migrate`
- `python scripts/manage.py seed`
- `python scripts/manage.py sample-etl --trade-date 2026-03-20`
- `python scripts/manage.py indicator-update --trade-date 2026-03-20`
- `python scripts/manage.py generate-reports --trade-date 2026-03-20`

## Docker Compose notes

- `docker-compose.yml` is set up for local development with `db`, `api`, `scheduler`, and `analysis`.
- Compose now falls back to sane local defaults when `.env` is missing or incomplete.
- Source code is mounted into the containers so API and worker code changes are reflected without rebuilding the image for every edit.
- The API service exposes `http://localhost:8000/healthz` and has a compose healthcheck.

## Sample verification

After running the quickstart commands:
- Open `http://localhost:8000/health`
- Open `http://localhost:8000/healthz`
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
- `make sample-etl`
- `make indicator-update`
- `make generate-reports`
- `make run-api`
- `make run-scheduler`
- `make run-analysis`
- `make test`
- `make lint`
- `make typecheck`
- `make dev-up`
- `make dev-down`

## Feature notes

- Connector modules live under `services/connectors/` and stay provider-isolated.
- The ETL foundation lives under `services/core/etl/` with separate fetch, normalize, validate, and load stages.
- Technical indicators currently include `SMA`, `EMA`, `MACD`, `RSI`, and `Bollinger Bands`.
- Taiwan derivatives analysis persists raw daily rows to `tw_derivatives_daily` and derived analytics to `tw_derivatives_features`.
- Daily reports persist to `reports_daily`, and query APIs are exposed under `/reports`.
- Scheduler and analysis workers share a registered-job runtime and persist heartbeat state to `worker_health`.

## Verification

- `pytest -q`
- `ruff check .`
- `mypy .`
