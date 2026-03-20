from __future__ import annotations

from dataclasses import dataclass

from scripts import manage


@dataclass(frozen=True)
class _SeedResult:
    instruments_created: int
    watchlists_created: int
    tags_created: int


@dataclass(frozen=True)
class _JobResult:
    job_name: str
    metrics: dict[str, int]


def test_manage_migrate_dispatches_to_alembic(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_migrations(revision: str) -> None:
        captured["revision"] = revision

    monkeypatch.setattr(manage, "_run_migrations", fake_run_migrations)

    exit_code = manage.main(["migrate", "--revision", "head"])

    assert exit_code == 0
    assert captured["revision"] == "head"


def test_manage_seed_dispatches_to_seed_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(manage, "SessionLocal", lambda: _session_context())
    monkeypatch.setattr(
        manage,
        "seed_sample_reference_data",
        lambda session: _SeedResult(instruments_created=3, watchlists_created=1, tags_created=5),
    )

    exit_code = manage.main(["seed"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "instruments_created=3" in output


def test_manage_indicator_update_dispatches_job(monkeypatch, capsys) -> None:
    monkeypatch.setattr(manage, "SessionLocal", lambda: _session_context())
    monkeypatch.setattr(
        manage,
        "run_indicator_update_job",
        lambda session, trade_date: _JobResult(
            job_name="indicator_update",
            metrics={"indicator_values_persisted": 10},
        ),
    )

    exit_code = manage.main(["indicator-update", "--trade-date", "2024-01-05"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "indicator_values_persisted" in output


def test_manage_smoke_test_dispatches_service(monkeypatch, capsys) -> None:
    class _SmokeResult:
        database_connectivity_ok = True
        api_health_ok = True
        schema_reachable = True
        sample_data_ok = True
        checked_symbols = ["2330", "AAPL"]
        passed = True

    monkeypatch.setattr(manage, "SessionLocal", lambda: _session_context())
    monkeypatch.setattr(manage, "run_smoke_test", lambda session, api_base_url: _SmokeResult())

    exit_code = manage.main(["smoke-test", "--api-base-url", "http://localhost:8000"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "database_connectivity_ok=True" in output


class _session_context:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb) -> None:
        return None
