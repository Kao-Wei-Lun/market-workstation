from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import func

from services.core.bootstrap import (
    DEFAULT_DEMO_TRADE_DATE,
    DEFAULT_V1_UNIVERSE_PRESET,
    generate_demo_data,
    load_instrument_universe,
    run_sample_daily_market_etl,
    seed_sample_reference_data,
)
from services.core.market_data import (
    clear_demo_workspace_data,
    refresh_real_workspace,
    run_real_taifex_backfill,
    run_real_twse_backfill,
)
from services.core.smoke import run_smoke_test
from services.db.session import SessionLocal
from services.models.backtest_run import BacktestRun
from services.models.candidate_run import CandidateRun
from services.models.report_daily import ReportDaily
from services.models.tw_derivatives_daily import TwDerivativesDaily
from workers.shared.jobs import run_daily_report_generation_job, run_indicator_update_job
from config.universe import describe_universe_preset, list_available_universe_presets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local development management CLI")
    subparsers = parser.add_subparsers(dest="command")

    migrate_parser = subparsers.add_parser("migrate", help="Run Alembic migrations.")
    migrate_parser.add_argument("--revision", default="head")

    subparsers.add_parser("seed", help="Seed sample reference data.")

    subparsers.add_parser("list-universes", help="List available universe presets.")

    universe_parser = subparsers.add_parser("load-universe", help="Load a broader instrument universe preset.")
    universe_parser.add_argument("--preset", default=DEFAULT_V1_UNIVERSE_PRESET)
    universe_parser.add_argument(
        "--scope",
        action="append",
        default=[],
        help="Limit loading to one or more scope keys declared by the preset.",
    )
    universe_parser.add_argument(
        "--skip-watchlists",
        action="store_true",
        help="Load instruments and tags without preset watchlists.",
    )

    demo_data_parser = subparsers.add_parser("demo-data", help="Generate frontend-visible local demo data.")
    demo_data_parser.add_argument("--trade-date", type=date.fromisoformat, default=DEFAULT_DEMO_TRADE_DATE)

    sample_etl_parser = subparsers.add_parser("sample-etl", help="Run sample ETL data load.")
    sample_etl_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    real_tw_parser = subparsers.add_parser("real-twse-backfill", help="Load real TWSE daily data for symbols/date range.")
    real_tw_parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    real_tw_parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    real_tw_parser.add_argument("--symbol", action="append", default=[], help="Limit to one or more TWSE symbols.")

    real_taifex_parser = subparsers.add_parser("real-taifex-backfill", help="Load real TAIFEX daily data for date range.")
    real_taifex_parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    real_taifex_parser.add_argument("--end-date", type=date.fromisoformat, required=True)

    subparsers.add_parser("clear-demo-data", help="Remove demo/sample source data and generated demo artifacts.")

    real_workspace_parser = subparsers.add_parser(
        "real-workspace",
        help="Clear demo data, backfill supported real sources, and regenerate derived daily outputs.",
    )
    real_workspace_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)
    real_workspace_parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    real_workspace_parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    real_workspace_parser.add_argument("--tw-symbol", action="append", default=[], help="Limit real TWSE backfill.")
    real_workspace_parser.add_argument("--us-symbol", action="append", default=[], help="Limit real US EOD backfill.")
    real_workspace_parser.add_argument(
        "--macro-series",
        action="append",
        default=[],
        help="Limit real macro backfill to one or more series keys.",
    )

    indicator_parser = subparsers.add_parser("indicator-update", help="Run indicator update job.")
    indicator_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    reports_parser = subparsers.add_parser("generate-reports", help="Run daily report generation job.")
    reports_parser.add_argument("--trade-date", type=date.fromisoformat, required=True)

    smoke_parser = subparsers.add_parser("smoke-test", help="Run local startup smoke checks.")
    smoke_parser.add_argument("--api-base-url", default="http://localhost:8000")

    verify_parser = subparsers.add_parser("verify-v1", help="Run local V1 release-readiness checks.")
    verify_parser.add_argument("--api-base-url", default="http://localhost:8000")
    verify_parser.add_argument("--trade-date", type=date.fromisoformat, default=DEFAULT_DEMO_TRADE_DATE)

    args = parser.parse_args(argv)

    if args.command == "migrate":
        _run_migrations(args.revision)
        print(f"Applied migrations up to {args.revision}.")
        return 0

    if args.command == "seed":
        with SessionLocal() as session:
            seed_result = seed_sample_reference_data(session)
        print(
            "Seeded sample reference data: "
            f"instruments_created={seed_result.instruments_created}, "
            f"watchlists_created={seed_result.watchlists_created}, "
            f"tags_created={seed_result.tags_created}"
        )
        return 0

    if args.command == "list-universes":
        for preset_name in list_available_universe_presets():
            description = describe_universe_preset(preset_name)
            scope_keys = description["scope_keys"]
            scope_text = ",".join(scope_keys if isinstance(scope_keys, list) else []) or "all"
            print(
                f"{preset_name}: instruments={description['instrument_count']}, "
                f"watchlists={description['watchlist_count']}, scopes={scope_text}"
            )
        return 0

    if args.command == "load-universe":
        with SessionLocal() as session:
            universe_result = load_instrument_universe(
                session,
                preset_name=args.preset,
                include_watchlists=not args.skip_watchlists,
                scope_keys=tuple(args.scope),
            )
        print(
            "Loaded instrument universe: "
            f"preset={universe_result.preset_name}, "
            f"requested_scopes={','.join(universe_result.requested_scope_keys) or 'all'}, "
            f"scopes_declared={universe_result.scopes_declared}, "
            f"instruments_created={universe_result.instruments_created}, "
            f"instruments_updated={universe_result.instruments_updated}, "
            f"tags_created={universe_result.tags_created}, "
            f"watchlists_created={universe_result.watchlists_created}, "
            f"watchlist_items_added={universe_result.watchlist_items_added}, "
            f"total_instruments={universe_result.total_instruments}"
        )
        return 0

    if args.command == "demo-data":
        with SessionLocal() as session:
            demo_result = generate_demo_data(session, trade_date=args.trade_date)
        print(
            "Generated demo data: "
            f"trade_date={demo_result.trade_date.isoformat()}, "
            f"daily_bars_loaded={demo_result.daily_bars_loaded}, "
            f"indicator_values_persisted={demo_result.indicator_values_persisted}, "
            f"tw_derivatives_features_persisted={demo_result.tw_derivatives_features_persisted}, "
            f"candidate_items_created={demo_result.candidate_items_created}, "
            f"backtest_trades_created={demo_result.backtest_trades_created}, "
            f"reports_persisted={demo_result.reports_persisted}"
        )
        return 0

    if args.command == "sample-etl":
        with SessionLocal() as session:
            etl_result = run_sample_daily_market_etl(session, trade_date=args.trade_date)
        print(
            "Loaded sample market data: "
            f"instruments_processed={etl_result.instruments_processed}, "
            f"daily_bars_loaded={etl_result.daily_bars_loaded}"
        )
        return 0

    if args.command == "real-twse-backfill":
        with SessionLocal() as session:
            tw_result = run_real_twse_backfill(
                session,
                symbols=tuple(args.symbol),
                start_date=args.start_date,
                end_date=args.end_date,
            )
        print(
            "Loaded real TWSE daily data: "
            f"symbols_requested={','.join(tw_result.symbols_requested) or 'all'}, "
            f"instruments_processed={tw_result.instruments_processed}, "
            f"trading_days_processed={tw_result.trading_days_processed}, "
            f"daily_bars_loaded={tw_result.daily_bars_loaded}"
        )
        return 0

    if args.command == "real-taifex-backfill":
        with SessionLocal() as session:
            taifex_result = run_real_taifex_backfill(
                session,
                start_date=args.start_date,
                end_date=args.end_date,
            )
        print(
            "Loaded real TAIFEX data: "
            f"trading_days_processed={taifex_result.trading_days_processed}, "
            f"tw_derivatives_daily_loaded={taifex_result.tw_derivatives_daily_loaded}, "
            f"tw_derivatives_features_persisted={taifex_result.tw_derivatives_features_persisted}"
        )
        return 0

    if args.command == "clear-demo-data":
        with SessionLocal() as session:
            cleanup_result = clear_demo_workspace_data(session)
        print(
            "Cleared demo workspace data: "
            f"daily_bars_deleted={cleanup_result.daily_bars_deleted}, "
            f"indicator_values_deleted={cleanup_result.indicator_values_deleted}, "
            f"series_points_deleted={cleanup_result.series_points_deleted}, "
            f"tw_derivatives_daily_deleted={cleanup_result.tw_derivatives_daily_deleted}, "
            f"tw_derivatives_features_deleted={cleanup_result.tw_derivatives_features_deleted}, "
            f"tw_institutional_spot_deleted={cleanup_result.tw_institutional_spot_deleted}, "
            f"candidate_runs_deleted={cleanup_result.candidate_runs_deleted}, "
            f"candidate_items_deleted={cleanup_result.candidate_items_deleted}, "
            f"report_rows_deleted={cleanup_result.report_rows_deleted}, "
            f"backtest_runs_deleted={cleanup_result.backtest_runs_deleted}, "
            f"backtest_trades_deleted={cleanup_result.backtest_trades_deleted}"
        )
        return 0

    if args.command == "real-workspace":
        with SessionLocal() as session:
            refresh_result = refresh_real_workspace(
                session,
                trade_date=args.trade_date,
                start_date=args.start_date,
                end_date=args.end_date,
                tw_symbols=tuple(args.tw_symbol),
                us_symbols=tuple(args.us_symbol),
                macro_series_keys=tuple(args.macro_series),
            )
        print(
            "Refreshed real workspace: "
            f"trade_date={refresh_result.trade_date.isoformat()}, "
            f"tw_daily_bars_loaded={refresh_result.tw_daily_bars_loaded}, "
            f"taifex_daily_loaded={refresh_result.taifex_daily_loaded}, "
            f"taifex_features_persisted={refresh_result.taifex_features_persisted}, "
            f"us_daily_bars_loaded={refresh_result.us_daily_bars_loaded}, "
            f"macro_series_points_loaded={refresh_result.macro_series_points_loaded}, "
            f"indicator_values_persisted={refresh_result.indicator_values_persisted}, "
            f"candidate_items_created={refresh_result.candidate_items_created}, "
            f"reports_persisted={refresh_result.reports_persisted}, "
            f"skipped_sources={','.join(refresh_result.skipped_sources) or 'none'}"
        )
        return 0

    if args.command == "indicator-update":
        with SessionLocal() as session:
            indicator_result = run_indicator_update_job(session, args.trade_date)
        print(f"Indicator update complete: {indicator_result.metrics}")
        return 0

    if args.command == "generate-reports":
        with SessionLocal() as session:
            report_result = run_daily_report_generation_job(session, args.trade_date)
        print(f"Daily reports generated: {report_result.metrics}")
        return 0

    if args.command == "smoke-test":
        with SessionLocal() as session:
            smoke_result = run_smoke_test(session, api_base_url=args.api_base_url)
        print(
            "Smoke test result: "
            f"database_connectivity_ok={smoke_result.database_connectivity_ok}, "
            f"api_health_ok={smoke_result.api_health_ok}, "
            f"schema_reachable={smoke_result.schema_reachable}, "
            f"sample_data_ok={smoke_result.sample_data_ok}, "
            f"checked_symbols={','.join(smoke_result.checked_symbols)}"
        )
        return 0 if smoke_result.passed else 1

    if args.command == "verify-v1":
        with SessionLocal() as session:
            demo_result = generate_demo_data(session, trade_date=args.trade_date)
            smoke_result = run_smoke_test(session, api_base_url=args.api_base_url)
            candidate_runs = session.query(func.count(CandidateRun.id)).scalar() or 0
            backtest_runs = session.query(func.count(BacktestRun.id)).scalar() or 0
            reports = session.query(func.count(ReportDaily.id)).scalar() or 0
            derivatives_rows = session.query(func.count(TwDerivativesDaily.id)).scalar() or 0
        passed = bool(
            smoke_result.passed
            and candidate_runs > 0
            and backtest_runs > 0
            and reports > 0
            and derivatives_rows > 0
        )
        print(
            "V1 verify result: "
            f"passed={passed}, "
            f"trade_date={demo_result.trade_date.isoformat()}, "
            f"smoke_test_passed={smoke_result.passed}, "
            f"candidate_runs={candidate_runs}, "
            f"backtest_runs={backtest_runs}, "
            f"reports={reports}, "
            f"tw_derivatives_daily={derivatives_rows}"
        )
        return 0 if passed else 1

    parser.print_help()
    return 1


def _run_migrations(revision: str) -> None:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, revision)


if __name__ == "__main__":
    raise SystemExit(main())
