.PHONY: setup migrate seed sample-etl indicator-update generate-reports run-api run-scheduler run-analysis test lint typecheck format dev-up dev-down backup-commit

PYTHON := .venv/bin/python
PIP_INSTALL := . .venv/bin/activate && python -m pip install -e .

setup:
	test -d .venv || python3 -m venv .venv
	bash -lc '$(PIP_INSTALL)'

migrate:
	$(PYTHON) scripts/manage.py migrate

seed:
	$(PYTHON) scripts/manage.py seed

sample-etl:
	$(PYTHON) scripts/manage.py sample-etl --trade-date $${TRADE_DATE:?set TRADE_DATE=YYYY-MM-DD}

indicator-update:
	$(PYTHON) scripts/manage.py indicator-update --trade-date $${TRADE_DATE:?set TRADE_DATE=YYYY-MM-DD}

generate-reports:
	$(PYTHON) scripts/manage.py generate-reports --trade-date $${TRADE_DATE:?set TRADE_DATE=YYYY-MM-DD}

run-api:
	$(PYTHON) -m uvicorn apps.api.main:app --reload

run-scheduler:
	$(PYTHON) -m workers.scheduler.main --start

run-analysis:
	$(PYTHON) -m workers.analysis.main --loop-heartbeat

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

typecheck:
	$(PYTHON) -m mypy .

dev-up:
	docker compose up --build -d db api scheduler analysis

dev-down:
	docker compose down

backup-commit:
	bash scripts/auto_commit.sh
