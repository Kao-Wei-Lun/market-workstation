from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from services.connectors.base import ConnectorRequest
from services.connectors.taifex import TaifexInstitutionalDailyConnector
from services.connectors.twse import TwseDailyMarketDataConnector
from services.core.derivatives.etl import run_taifex_derivatives_ingestion
from services.core.derivatives.features import compute_tw_derivatives_features
from services.core.etl.pipeline import run_ingestion_pipeline
from services.db.repositories.tw_derivatives import TwDerivativesFeatureRepository
from services.models.daily_bar import DailyBar
from services.models.instrument import Instrument
from services.models.tw_derivatives_daily import TwDerivativesDaily


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
    query = (
        session.query(Instrument)
        .filter(
            Instrument.is_active.is_(True),
            Instrument.source_route == TwseDailyMarketDataConnector.source_route,
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
