from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from config.settings import get_settings
from config.universe import load_universe_preset
from sqlalchemy.orm import Session

from services.connectors.base import ConnectorRequest
from services.connectors.macro import MacroSeriesConnector
from services.connectors.taifex import TaifexInstitutionalDailyConnector
from services.connectors.twse import TwseDailyMarketDataConnector
from services.connectors.us_eod import UsEodConnector
from services.core.candidates.service import generate_and_persist_candidate_run
from services.core.derivatives.etl import run_taifex_derivatives_ingestion
from services.core.derivatives.features import compute_tw_derivatives_features
from services.core.etl.pipeline import run_ingestion_pipeline
from services.db.repositories.tw_derivatives import TwDerivativesFeatureRepository
from services.models.backtest_run import BacktestRun
from services.models.backtest_trade import BacktestTrade
from services.models.candidate_item import CandidateItem
from services.models.candidate_run import CandidateRun
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.report_daily import ReportDaily
from services.models.series_point import SeriesPoint
from services.models.strategy import Strategy
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.tw_institutional_spot_daily import TwInstitutionalSpotDaily
from workers.shared.jobs import run_daily_report_generation_job, run_indicator_update_job

DEMO_SOURCE_ROUTES = ("demo_seed", "local_seed")
DEMO_SAMPLE_SYMBOLS = tuple(item.symbol for item in load_universe_preset("sample_reference").instruments)
DEMO_BACKTEST_NAME = "Demo Time Exit Trend"
DEMO_BACKTEST_DESCRIPTION = "Deterministic local demo backtest"

@dataclass(frozen=True)
class RealTwMarketLoadResult:
    symbols_requested: tuple[str, ...]
    instruments_processed: int
    trading_days_processed: int
    daily_bars_loaded: int


@dataclass(frozen=True)
class RealTaifexLoadResult:
    trading_days_processed: int
    tw_derivatives_daily_loaded: int
    tw_derivatives_features_persisted: int


@dataclass(frozen=True)
class RealUsMarketLoadResult:
    symbols_requested: tuple[str, ...]
    instruments_processed: int
    daily_bars_loaded: int


@dataclass(frozen=True)
class RealMacroLoadResult:
    series_requested: tuple[str, ...]
    instruments_processed: int
    series_points_loaded: int


@dataclass(frozen=True)
class DemoCleanupResult:
    daily_bars_deleted: int
    indicator_values_deleted: int
    series_points_deleted: int
    tw_derivatives_daily_deleted: int
    tw_derivatives_features_deleted: int
    tw_institutional_spot_deleted: int
    candidate_runs_deleted: int
    candidate_items_deleted: int
    report_rows_deleted: int
    backtest_runs_deleted: int
    backtest_trades_deleted: int
    strategies_deleted: int


@dataclass(frozen=True)
class RealWorkspaceRefreshResult:
    trade_date: date
    cleanup: DemoCleanupResult
    tw_daily_bars_loaded: int
    taifex_daily_loaded: int
    taifex_features_persisted: int
    us_daily_bars_loaded: int
    macro_series_points_loaded: int
    indicator_values_persisted: int
    candidate_items_created: int
    reports_persisted: int
    skipped_sources: tuple[str, ...]


def run_real_twse_backfill(
    session: Session,
    *,
    symbols: tuple[str, ...] = (),
    start_date: date,
    end_date: date,
    connector: TwseDailyMarketDataConnector | None = None,
) -> RealTwMarketLoadResult:
    connector_instance = connector or TwseDailyMarketDataConnector()
    instruments = _select_twse_instruments(session, symbols=symbols)
    trading_dates = _build_trading_dates_between(start_date, end_date)

    bars_loaded = 0
    for instrument in instruments:
        for trade_date in trading_dates:
            load_result = run_ingestion_pipeline(
                session,
                connector=connector_instance,
                request=ConnectorRequest(
                    symbol=instrument.symbol,
                    trade_date=trade_date,
                    instrument_id=instrument.id,
                    source_route=instrument.source_route,
                ),
                job_type="manual_real_tw_market_backfill",
            )
            session.commit()
            bars_loaded += load_result.daily_bars_loaded

    return RealTwMarketLoadResult(
        symbols_requested=symbols,
        instruments_processed=len(instruments),
        trading_days_processed=len(trading_dates),
        daily_bars_loaded=bars_loaded,
    )


def run_real_taifex_backfill(
    session: Session,
    *,
    start_date: date,
    end_date: date,
    connector: TaifexInstitutionalDailyConnector | None = None,
) -> RealTaifexLoadResult:
    connector = connector or TaifexInstitutionalDailyConnector()
    trading_dates = _build_trading_dates_between(start_date, end_date)

    daily_loaded = 0
    for trade_date in trading_dates:
        load_result = run_taifex_derivatives_ingestion(
            session,
            request=ConnectorRequest(trade_date=trade_date, source_route=connector.source_route),
            connector=connector,
        )
        session.commit()
        daily_loaded += load_result.tw_derivatives_daily_loaded

    all_records = (
        session.query(TwDerivativesDaily)
        .filter(TwDerivativesDaily.trade_date <= end_date)
        .order_by(TwDerivativesDaily.trade_date.asc(), TwDerivativesDaily.id.asc())
        .all()
    )
    features = compute_tw_derivatives_features(all_records)
    features_persisted = TwDerivativesFeatureRepository(session).replace_many(features)
    session.commit()

    return RealTaifexLoadResult(
        trading_days_processed=len(trading_dates),
        tw_derivatives_daily_loaded=daily_loaded,
        tw_derivatives_features_persisted=features_persisted,
    )


def run_real_us_backfill(
    session: Session,
    *,
    symbols: tuple[str, ...] = (),
    start_date: date,
    end_date: date,
    connector: UsEodConnector | None = None,
) -> RealUsMarketLoadResult:
    connector_instance = connector or UsEodConnector()
    if connector_instance.config.base_url is None or connector_instance.config.provider_name == "demo":
        msg = "US real provider is not configured"
        raise ValueError(msg)

    instruments = _select_instruments_by_source_route(session, source_route=UsEodConnector.source_route, symbols=symbols)
    bars_loaded = 0
    for instrument in instruments:
        load_result = run_ingestion_pipeline(
            session,
            connector=connector_instance,
            request=ConnectorRequest(
                symbol=instrument.symbol,
                start_date=start_date,
                end_date=end_date,
                instrument_id=instrument.id,
                source_route=instrument.source_route,
            ),
            job_type="manual_real_us_market_backfill",
        )
        session.commit()
        bars_loaded += load_result.daily_bars_loaded

    return RealUsMarketLoadResult(
        symbols_requested=symbols,
        instruments_processed=len(instruments),
        daily_bars_loaded=bars_loaded,
    )


def run_real_macro_backfill(
    session: Session,
    *,
    series_keys: tuple[str, ...] = (),
    start_date: date,
    end_date: date,
    connector: MacroSeriesConnector | None = None,
) -> RealMacroLoadResult:
    connector_instance = connector or MacroSeriesConnector()
    if connector_instance.config.base_url is None or connector_instance.config.provider_name == "demo":
        msg = "Macro real provider is not configured"
        raise ValueError(msg)

    instruments = _select_instruments_by_source_route(
        session,
        source_route=MacroSeriesConnector.source_route,
        symbols=series_keys,
    )
    points_loaded = 0
    for instrument in instruments:
        load_result = run_ingestion_pipeline(
            session,
            connector=connector_instance,
            request=ConnectorRequest(
                series_key=instrument.symbol,
                start_date=start_date,
                end_date=end_date,
                instrument_id=instrument.id,
                source_route=instrument.source_route,
            ),
            job_type="manual_real_macro_backfill",
        )
        session.commit()
        points_loaded += load_result.series_points_loaded

    return RealMacroLoadResult(
        series_requested=series_keys,
        instruments_processed=len(instruments),
        series_points_loaded=points_loaded,
    )


def clear_demo_workspace_data(session: Session) -> DemoCleanupResult:
    sample_instrument_ids = [
        instrument_id
        for (instrument_id,) in (
            session.query(Instrument.id).filter(Instrument.symbol.in_(DEMO_SAMPLE_SYMBOLS)).all()
        )
    ]
    demo_run_ids = [
        run_id
        for (run_id,) in (
            session.query(BacktestRun.id)
            .join(Strategy, Strategy.id == BacktestRun.strategy_id)
            .filter(
                Strategy.name == DEMO_BACKTEST_NAME,
                Strategy.description == DEMO_BACKTEST_DESCRIPTION,
            )
            .all()
        )
    ]
    strategy_ids = [
        strategy_id
        for (strategy_id,) in (
            session.query(Strategy.id)
            .filter(
                Strategy.name == DEMO_BACKTEST_NAME,
                Strategy.description == DEMO_BACKTEST_DESCRIPTION,
            )
            .all()
        )
    ]

    indicator_values_deleted = 0
    daily_bars_deleted = 0
    if sample_instrument_ids:
        indicator_values_deleted = (
            session.query(IndicatorValue)
            .filter(IndicatorValue.instrument_id.in_(sample_instrument_ids))
            .delete(synchronize_session=False)
        )
        daily_bars_deleted = (
            session.query(DailyBar)
            .filter(DailyBar.instrument_id.in_(sample_instrument_ids))
            .delete(synchronize_session=False)
        )

    series_points_deleted = (
        session.query(SeriesPoint)
        .filter(SeriesPoint.source_route.in_(DEMO_SOURCE_ROUTES))
        .delete(synchronize_session=False)
    )
    tw_derivatives_features_deleted = session.query(TwDerivativesFeature).delete(synchronize_session=False)
    tw_derivatives_daily_deleted = (
        session.query(TwDerivativesDaily)
        .filter(TwDerivativesDaily.source_route.in_(DEMO_SOURCE_ROUTES))
        .delete(synchronize_session=False)
    )
    tw_institutional_spot_deleted = (
        session.query(TwInstitutionalSpotDaily)
        .filter(TwInstitutionalSpotDaily.source_route.in_(DEMO_SOURCE_ROUTES))
        .delete(synchronize_session=False)
    )
    candidate_items_deleted = session.query(CandidateItem).delete(synchronize_session=False)
    candidate_runs_deleted = session.query(CandidateRun).delete(synchronize_session=False)
    report_rows_deleted = session.query(ReportDaily).delete(synchronize_session=False)

    backtest_trades_deleted = 0
    backtest_runs_deleted = 0
    strategies_deleted = 0
    if demo_run_ids:
        backtest_trades_deleted = (
            session.query(BacktestTrade)
            .filter(BacktestTrade.run_id.in_(demo_run_ids))
            .delete(synchronize_session=False)
        )
        backtest_runs_deleted = (
            session.query(BacktestRun)
            .filter(BacktestRun.id.in_(demo_run_ids))
            .delete(synchronize_session=False)
        )
    if strategy_ids:
        strategies_deleted = (
            session.query(Strategy)
            .filter(Strategy.id.in_(strategy_ids))
            .delete(synchronize_session=False)
        )

    session.commit()
    return DemoCleanupResult(
        daily_bars_deleted=daily_bars_deleted,
        indicator_values_deleted=indicator_values_deleted,
        series_points_deleted=series_points_deleted,
        tw_derivatives_daily_deleted=tw_derivatives_daily_deleted,
        tw_derivatives_features_deleted=tw_derivatives_features_deleted,
        tw_institutional_spot_deleted=tw_institutional_spot_deleted,
        candidate_runs_deleted=candidate_runs_deleted,
        candidate_items_deleted=candidate_items_deleted,
        report_rows_deleted=report_rows_deleted,
        backtest_runs_deleted=backtest_runs_deleted,
        backtest_trades_deleted=backtest_trades_deleted,
        strategies_deleted=strategies_deleted,
    )


def refresh_real_workspace(
    session: Session,
    *,
    trade_date: date,
    start_date: date,
    end_date: date,
    tw_symbols: tuple[str, ...] = (),
    us_symbols: tuple[str, ...] = (),
    macro_series_keys: tuple[str, ...] = (),
) -> RealWorkspaceRefreshResult:
    cleanup = clear_demo_workspace_data(session)
    settings = get_settings()
    skipped_sources: list[str] = []

    tw_result = run_real_twse_backfill(
        session,
        symbols=tw_symbols,
        start_date=start_date,
        end_date=end_date,
    )
    taifex_result = run_real_taifex_backfill(
        session,
        start_date=start_date,
        end_date=end_date,
    )

    us_daily_bars_loaded = 0
    if settings.us_eod_base_url and settings.us_eod_provider != "demo":
        us_result = run_real_us_backfill(
            session,
            symbols=us_symbols,
            start_date=start_date,
            end_date=end_date,
        )
        us_daily_bars_loaded = us_result.daily_bars_loaded
    else:
        skipped_sources.append(UsEodConnector.source_route)

    macro_series_points_loaded = 0
    if settings.macro_base_url and settings.macro_provider != "demo":
        macro_result = run_real_macro_backfill(
            session,
            series_keys=macro_series_keys,
            start_date=start_date,
            end_date=end_date,
        )
        macro_series_points_loaded = macro_result.series_points_loaded
    else:
        skipped_sources.append(MacroSeriesConnector.source_route)

    indicator_result = run_indicator_update_job(session, trade_date)
    _candidate_run, candidate_items = generate_and_persist_candidate_run(session, candidate_date=trade_date, top_n=20)
    report_result = run_daily_report_generation_job(session, trade_date)

    return RealWorkspaceRefreshResult(
        trade_date=trade_date,
        cleanup=cleanup,
        tw_daily_bars_loaded=tw_result.daily_bars_loaded,
        taifex_daily_loaded=taifex_result.tw_derivatives_daily_loaded,
        taifex_features_persisted=taifex_result.tw_derivatives_features_persisted,
        us_daily_bars_loaded=us_daily_bars_loaded,
        macro_series_points_loaded=macro_series_points_loaded,
        indicator_values_persisted=indicator_result.metrics["indicator_values_persisted"],
        candidate_items_created=len(candidate_items),
        reports_persisted=report_result.metrics["reports_persisted"],
        skipped_sources=tuple(skipped_sources),
    )


def has_any_daily_bars(
    session: Session,
    *,
    instrument_id: int,
    start_date: date,
    end_date: date,
) -> bool:
    return (
        session.query(DailyBar.id)
        .filter(
            DailyBar.instrument_id == instrument_id,
            DailyBar.trade_date >= start_date,
            DailyBar.trade_date <= end_date,
        )
        .limit(1)
        .scalar()
        is not None
    )


def _select_twse_instruments(session: Session, *, symbols: tuple[str, ...]) -> list[Instrument]:
    return _select_instruments_by_source_route(session, source_route=TwseDailyMarketDataConnector.source_route, symbols=symbols)


def _select_instruments_by_source_route(
    session: Session,
    *,
    source_route: str,
    symbols: tuple[str, ...],
) -> list[Instrument]:
    query = (
        session.query(Instrument)
        .filter(
            Instrument.is_active.is_(True),
            Instrument.source_route == source_route,
        )
        .order_by(Instrument.symbol.asc())
    )
    if symbols:
        query = query.filter(Instrument.symbol.in_(symbols))
    return query.all()


def _build_trading_dates_between(start_date: date, end_date: date) -> list[date]:
    if end_date < start_date:
        msg = "end_date must be on or after start_date"
        raise ValueError(msg)

    days: list[date] = []
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() < 5:
            days.append(current_date)
        current_date += timedelta(days=1)
    return days
