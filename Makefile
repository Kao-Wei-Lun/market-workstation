.PHONY: test lint typecheck format dev-up dev-down backup-commit

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy .

dev-up:
	docker compose up -d

dev-down:
	docker compose down

backup-commit:
	bash scripts/auto_commit.sh
