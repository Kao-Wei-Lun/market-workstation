.PHONY: setup migrate seed list-universes load-universe demo-data sample-etl clear-demo-data real-workspace real-twse-backfill real-taifex-backfill indicator-update generate-reports smoke-test verify-v1 release-check run-api run-scheduler run-analysis run-frontend frontend-install frontend-build frontend-test test lint typecheck format dev-up dev-down backup-commit

PYTHON := .venv/bin/python
PIP_INSTALL := . .venv/bin/activate && python -m pip install -e .

setup:
	test -d .venv || python3 -m venv .venv
	bash -lc '$(PIP_INSTALL)'

migrate:
	$(PYTHON) scripts/manage.py migrate

seed:
	$(PYTHON) scripts/manage.py seed

list-universes:
	$(PYTHON) scripts/manage.py list-universes

load-universe:
	$(PYTHON) scripts/manage.py load-universe --preset $${PRESET:-v1_market_expanded} $${SCOPE:+--scope $$SCOPE}

demo-data:
	$(PYTHON) scripts/manage.py demo-data --trade-date $${TRADE_DATE:-2026-03-20}

sample-etl:
	$(PYTHON) scripts/manage.py sample-etl --trade-date $${TRADE_DATE:?set TRADE_DATE=YYYY-MM-DD}

clear-demo-data:
	$(PYTHON) scripts/manage.py clear-demo-data

real-workspace:
	$(PYTHON) scripts/manage.py real-workspace --trade-date $${TRADE_DATE:?set TRADE_DATE=YYYY-MM-DD} --start-date $${START_DATE:?set START_DATE=YYYY-MM-DD} --end-date $${END_DATE:?set END_DATE=YYYY-MM-DD} $${TW_SYMBOL:+--tw-symbol $$TW_SYMBOL} $${US_SYMBOL:+--us-symbol $$US_SYMBOL} $${MACRO_SERIES:+--macro-series $$MACRO_SERIES}

real-twse-backfill:
	$(PYTHON) scripts/manage.py real-twse-backfill --start-date $${START_DATE:?set START_DATE=YYYY-MM-DD} --end-date $${END_DATE:?set END_DATE=YYYY-MM-DD} $${SYMBOL:+--symbol $$SYMBOL}

real-taifex-backfill:
	$(PYTHON) scripts/manage.py real-taifex-backfill --start-date $${START_DATE:?set START_DATE=YYYY-MM-DD} --end-date $${END_DATE:?set END_DATE=YYYY-MM-DD}

indicator-update:
	$(PYTHON) scripts/manage.py indicator-update --trade-date $${TRADE_DATE:?set TRADE_DATE=YYYY-MM-DD}

generate-reports:
	$(PYTHON) scripts/manage.py generate-reports --trade-date $${TRADE_DATE:?set TRADE_DATE=YYYY-MM-DD}

smoke-test:
	$(PYTHON) scripts/manage.py smoke-test --api-base-url $${API_BASE_URL:-http://localhost:8000}

verify-v1:
	$(PYTHON) scripts/manage.py verify-v1 --api-base-url $${API_BASE_URL:-http://localhost:8000} --trade-date $${TRADE_DATE:-2026-03-20}

run-api:
	$(PYTHON) -m uvicorn apps.api.main:app --reload

run-scheduler:
	$(PYTHON) -m workers.scheduler.main --start

run-analysis:
	$(PYTHON) -m workers.analysis.main --loop-heartbeat

frontend-install:
	cd frontend && npm install

run-frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

frontend-build:
	cd frontend && npm run build

frontend-test:
	cd frontend && npm run test

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy .

release-check: demo-data smoke-test test lint typecheck frontend-test frontend-build verify-v1

dev-up:
	docker compose up --build -d db api scheduler analysis frontend

dev-down:
	docker compose down

backup-commit:
	bash scripts/auto_commit.sh
