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


@dataclass(frozen=True)
class _RealTwResult:
    symbols_requested: tuple[str, ...]
    instruments_processed: int
    trading_days_processed: int
    daily_bars_loaded: int


@dataclass(frozen=True)
class _RealTaifexResult:
    trading_days_processed: int
    tw_derivatives_daily_loaded: int
    tw_derivatives_features_persisted: int


@dataclass(frozen=True)
class _DemoDataResult:
    trade_date: object
    daily_bars_loaded: int
    indicator_values_persisted: int
    tw_derivatives_features_persisted: int
    candidate_items_created: int
    backtest_trades_created: int
    reports_persisted: int


@dataclass(frozen=True)
class _VerifySmokeResult:
    database_connectivity_ok: bool
    api_health_ok: bool
    schema_reachable: bool
    sample_data_ok: bool
    checked_symbols: list[str]
    passed: bool


@dataclass(frozen=True)
class _UniverseLoadResult:
    preset_name: str
    description: str
    requested_scope_keys: tuple[str, ...]
    scopes_declared: int
    instruments_created: int
    instruments_updated: int
    tags_created: int
    watchlists_created: int
    watchlist_items_added: int
    total_instruments: int
    available_presets: tuple[str, ...]


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


def test_manage_load_universe_dispatches_to_universe_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(manage, "SessionLocal", lambda: _session_context())
    monkeypatch.setattr(
        manage,
        "load_instrument_universe",
        lambda session, preset_name, include_watchlists, scope_keys: _UniverseLoadResult(
            preset_name=preset_name,
            description="demo",
            requested_scope_keys=scope_keys,
            scopes_declared=1,
            instruments_created=20,
            instruments_updated=5,
            tags_created=40,
            watchlists_created=2,
            watchlist_items_added=9,
            total_instruments=25,
            available_presets=("sample_reference", "v1_market_expanded"),
        ),
    )

    exit_code = manage.main(["load-universe", "--preset", "v1_market_expanded"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "preset=v1_market_expanded" in output
    assert "instruments_created=20" in output


def test_manage_load_universe_accepts_scope_filters(monkeypatch, capsys) -> None:
    monkeypatch.setattr(manage, "SessionLocal", lambda: _session_context())
    monkeypatch.setattr(
        manage,
        "load_instrument_universe",
        lambda session, preset_name, include_watchlists, scope_keys: _UniverseLoadResult(
            preset_name=preset_name,
            description="demo",
            requested_scope_keys=scope_keys,
            scopes_declared=1,
            instruments_created=6,
            instruments_updated=0,
            tags_created=12,
            watchlists_created=1,
            watchlist_items_added=6,
            total_instruments=6,
            available_presets=("sample_reference", "v1_market_expanded"),
        ),
    )

    exit_code = manage.main(["load-universe", "--preset", "v1_market_expanded", "--scope", "macro_series_core"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "requested_scopes=macro_series_core" in output


def test_manage_list_universes_prints_available_presets(monkeypatch, capsys) -> None:
    monkeypatch.setattr(manage, "list_available_universe_presets", lambda: ["sample_reference", "v1_market_expanded"])
    monkeypatch.setattr(
        manage,
        "describe_universe_preset",
        lambda preset_name: {
            "preset_name": preset_name,
            "instrument_count": 3 if preset_name == "sample_reference" else 10,
            "watchlist_count": 1 if preset_name == "sample_reference" else 4,
            "scope_keys": [] if preset_name == "sample_reference" else ["tw_equities_full", "macro_series_core"],
        },
    )

    exit_code = manage.main(["list-universes"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "sample_reference" in output
    assert "v1_market_expanded" in output


def test_manage_demo_data_dispatches_to_demo_service(monkeypatch, capsys) -> None:
    from datetime import date

    monkeypatch.setattr(manage, "SessionLocal", lambda: _session_context())
    monkeypatch.setattr(
        manage,
        "generate_demo_data",
        lambda session, trade_date: _DemoDataResult(
            trade_date=date(2026, 3, 20),
            daily_bars_loaded=90,
            indicator_values_persisted=120,
            tw_derivatives_features_persisted=63,
            candidate_items_created=2,
            backtest_trades_created=3,
            reports_persisted=7,
        ),
    )

    exit_code = manage.main(["demo-data", "--trade-date", "2026-03-20"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "daily_bars_loaded=90" in output
    assert "candidate_items_created=2" in output


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


def test_manage_real_twse_backfill_dispatches_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(manage, "SessionLocal", lambda: _session_context())
    monkeypatch.setattr(
        manage,
        "run_real_twse_backfill",
        lambda session, symbols, start_date, end_date: _RealTwResult(
            symbols_requested=symbols,
            instruments_processed=1,
            trading_days_processed=5,
            daily_bars_loaded=5,
        ),
    )

    exit_code = manage.main(
        ["real-twse-backfill", "--start-date", "2026-03-10", "--end-date", "2026-03-14", "--symbol", "2330"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "symbols_requested=2330" in output
    assert "daily_bars_loaded=5" in output


def test_manage_real_taifex_backfill_dispatches_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(manage, "SessionLocal", lambda: _session_context())
    monkeypatch.setattr(
        manage,
        "run_real_taifex_backfill",
        lambda session, start_date, end_date: _RealTaifexResult(
            trading_days_processed=5,
            tw_derivatives_daily_loaded=15,
            tw_derivatives_features_persisted=15,
        ),
    )

    exit_code = manage.main(["real-taifex-backfill", "--start-date", "2026-03-10", "--end-date", "2026-03-14"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "tw_derivatives_daily_loaded=15" in output


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


def test_manage_verify_v1_runs_demo_and_smoke_checks(monkeypatch, capsys) -> None:
    from datetime import date

    monkeypatch.setattr(manage, "SessionLocal", lambda: _verify_session_context())
    monkeypatch.setattr(
        manage,
        "generate_demo_data",
        lambda session, trade_date: _DemoDataResult(
            trade_date=date(2026, 3, 20),
            daily_bars_loaded=60,
            indicator_values_persisted=120,
            tw_derivatives_features_persisted=10,
            candidate_items_created=5,
            backtest_trades_created=4,
            reports_persisted=3,
        ),
    )
    monkeypatch.setattr(
        manage,
        "run_smoke_test",
        lambda session, api_base_url: _VerifySmokeResult(
            database_connectivity_ok=True,
            api_health_ok=True,
            schema_reachable=True,
            sample_data_ok=True,
            checked_symbols=["2330"],
            passed=True,
        ),
    )

    exit_code = manage.main(["verify-v1", "--api-base-url", "http://localhost:8000", "--trade-date", "2026-03-20"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "passed=True" in output
    assert "candidate_runs=1" in output


class _session_context:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeCountQuery:
    def __init__(self, count: int) -> None:
        self.count = count

    def scalar(self) -> int:
        return self.count


class _verify_session_context:
    def __enter__(self):
        return _FakeVerifySession()

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeVerifySession:
    def query(self, _expression):
        return _FakeCountQuery(1)
