# AGENTS.md

## Project Rules
- Read all files in `docs/` before making architectural changes.
- Follow the requirements in `docs/srs-v1.md` and `docs/srs-v2.md`.
- V1 and V2 must share the same underlying architecture.
- PostgreSQL is the only database.
- Use a worker-based architecture:
  - API service
  - scheduler worker
  - analysis worker
  - optional realtime worker
- All secrets must come from environment variables.
- Never hardcode API keys, passwords, or certificate paths.
- All schema changes must include migrations.
- All new features must include tests.
- All external data providers must be isolated under `services/connectors/`.
- Keep modules small and composable.

## Delivery Rules
After completing each task:
1. run tests if available
2. run lint if available
3. summarize changes
4. create a git commit using `bash scripts/auto_commit.sh "<message>"`

## Code Style
- Prefer Python 3.12
- Prefer FastAPI for API service
- Prefer SQLAlchemy + Alembic
- Prefer typed Python
- Keep functions focused and testable
