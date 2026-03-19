# Market Workstation

Minimal backend foundation for the shared V1/V2 architecture:
- FastAPI API service
- PostgreSQL-backed SQLAlchemy models
- Alembic migrations
- Initial healthcheck endpoint

## Local startup

1. Create a local environment file:
   `cp .env.example .env`
2. Run the API locally:
   `source .venv/bin/activate`
   `uvicorn apps.api.main:app --reload`
3. Run the initial migration:
   `alembic upgrade head`

## Docker Compose startup

1. Create `.env` from `.env.example`.
2. Start the required services:
   `docker compose up --build db api`
3. Apply the migration from the API container:
   `docker compose run --rm api alembic upgrade head`
