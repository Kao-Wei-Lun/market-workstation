# Market Workstation

Minimal backend foundation for the shared V1/V2 architecture:
- FastAPI API service
- PostgreSQL-backed SQLAlchemy models
- Alembic migrations
- Initial healthcheck endpoint

## Local startup

1. Create a local environment file:
   `cp .env.example .env`
2. Install project dependencies into the local Python 3.12 environment:
   `python -m pip install -e .`
3. Run the initial migration:
   `alembic upgrade head`
4. Run the API locally:
   `source .venv/bin/activate`
   `uvicorn apps.api.main:app --reload`

## Docker Compose startup

1. Create `.env` from `.env.example`.
2. Start the required services:
   `docker compose up --build db api`
3. Apply the migration from the API container:
   `docker compose run --rm api alembic upgrade head`

## Verification

- `pytest -q`
- `ruff check .`
- `mypy .`

## ETL development notes

- Connector modules live under `services/connectors/` and should stay provider-isolated.
- The ETL foundation lives under `services/core/etl/` with separate fetch, normalize, validate, and load steps.
- `services/core/ingest_jobs.py` records ingest lifecycle state in `ingest_jobs`.
- `series_points` is the initial persistence table for macro-style time series ingestion.
- The current TWSE connector includes one realistic stock daily path; US and macro connectors are provider-driven skeletons intended for mocked tests and future provider-specific expansion.

## Taiwan derivatives analysis

- TAIFEX institutional daily ingestion is implemented through `services/connectors/taifex.py`.
- Raw institutional rows normalize into `tw_derivatives_daily`, and derived analytics persist in `tw_derivatives_features`.
- The first feature layer computes `delta_1d`, `delta_5d`, `delta_20d`, `zscore_20d`, `regime_label`, `bias_score`, and `anomaly_flag`.
- `services/core/derivatives/summary.py` generates a basic daily institutional bias snapshot for reporting and later API/report integration.
