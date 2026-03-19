from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Literal

from sqlalchemy.orm import Session

from services.connectors.base import ConnectorRequest
from services.connectors.twse import TwseDailyMarketDataConnector
from services.connectors.us_eod import UsEodConnector
from services.core.derivatives.etl import run_taifex_derivatives_ingestion
from services.core.derivatives.features import compute_tw_derivatives_features
from services.core.indicators.base import IndicatorCalculator
from services.core.indicators.bollinger import BollingerBandsIndicator
from services.core.indicators.ema import EMAIndicator
from services.core.indicators.macd import MACDIndicator
from services.core.indicators.rsi import RSIIndicator
from services.core.indicators.service import compute_and_persist_indicators
from services.core.indicators.sma import SMAIndicator
from services.core.reports.generators import (
    generate_group_summary_snapshot_report,
    generate_market_summary_report,
    generate_next_day_watch_candidates_report,
    generate_taiwan_derivatives_summary_report,
    generate_watchlist_summary_report,
)
from services.core.reports.service import persist_generated_report
from services.core.etl.pipeline import run_ingestion_pipeline
from services.db.repositories.tw_derivatives import TwDerivativesFeatureRepository
from services.models.daily_bar import DailyBar
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.watchlist import Watchlist
WorkerRole = Literal["scheduler", "analysis"]
JobHandler = Callable[[Session, date], "JobExecutionResult"]


@dataclass(frozen=True)
class JobExecutionResult:
    job_name: str
    metrics: dict[str, int]


@dataclass(frozen=True)
class RegisteredJob:
    name: str
    worker_role: WorkerRole
    description: str
    cron: str
    handler: JobHandler


def get_registered_jobs() -> dict[str, RegisteredJob]:
    return {
        definition.name: definition
        for definition in [
            RegisteredJob(
                name="daily_market_etl",
                worker_role="scheduler",
                description="Run daily market ETL for active instruments.",
                cron="0 18 * * 1-5",
                handler=run_daily_market_etl_job,
            ),
            RegisteredJob(
                name="indicator_update",
                worker_role="analysis",
                description="Compute and persist default technical indicators.",
                cron="30 18 * * 1-5",
                handler=run_indicator_update_job,
            ),
            RegisteredJob(
                name="taiwan_derivatives_pipeline",
                worker_role="analysis",
                description="Run TAIFEX ingestion and feature recomputation.",
                cron="40 18 * * 1-5",
                handler=run_taiwan_derivatives_pipeline_job,
            ),
            RegisteredJob(
                name="daily_report_generation",
                worker_role="analysis",
                description="Generate and persist daily reports.",
                cron="0 19 * * 1-5",
                handler=run_daily_report_generation_job,
            ),
        ]
    }


def list_registered_jobs(worker_role: WorkerRole | None = None) -> list[RegisteredJob]:
    jobs = list(get_registered_jobs().values())
    if worker_role is not None:
        jobs = [job for job in jobs if job.worker_role == worker_role]
    return sorted(jobs, key=lambda item: item.name)


def get_registered_job(job_name: str) -> RegisteredJob:
    try:
        return get_registered_jobs()[job_name]
    except KeyError as exc:
        msg = f"unknown job: {job_name}"
        raise ValueError(msg) from exc


def run_daily_market_etl_job(session: Session, trade_date: date) -> JobExecutionResult:
    connectors = {
        "twse_openapi": TwseDailyMarketDataConnector(),
        "us_eod_provider": UsEodConnector(),
    }
    instruments = (
        session.query(Instrument)
        .filter(Instrument.is_active.is_(True), Instrument.source_route.in_(tuple(connectors.keys())))
        .order_by(Instrument.id.asc())
        .all()
    )

    instruments_processed = 0
    bars_loaded = 0
    for instrument in instruments:
        try:
            request = ConnectorRequest(
                symbol=instrument.symbol,
                trade_date=trade_date,
                start_date=trade_date if instrument.source_route == "us_eod_provider" else None,
                end_date=trade_date if instrument.source_route == "us_eod_provider" else None,
                instrument_id=instrument.id,
                source_route=instrument.source_route,
            )
            load_result = run_ingestion_pipeline(
                session,
                connector=connectors[instrument.source_route],
                request=request,
                job_type="daily_market_sync",
            )
            session.commit()
        except Exception:
            session.commit()
            raise
        instruments_processed += 1
        bars_loaded += load_result.daily_bars_loaded

    return JobExecutionResult(
        job_name="daily_market_etl",
        metrics={
            "instruments_processed": instruments_processed,
            "daily_bars_loaded": bars_loaded,
        },
    )


def run_indicator_update_job(session: Session, trade_date: date) -> JobExecutionResult:
    instrument_ids = [
        instrument_id
        for (instrument_id,) in (
            session.query(DailyBar.instrument_id)
            .filter(DailyBar.trade_date <= trade_date)
            .distinct()
            .order_by(DailyBar.instrument_id.asc())
            .all()
        )
    ]

    calculators: list[IndicatorCalculator] = [
        SMAIndicator(20),
        EMAIndicator(20),
        MACDIndicator(),
        RSIIndicator(14),
        BollingerBandsIndicator(20, 2),
    ]
    indicators_persisted = 0
    instruments_processed = 0
    for instrument_id in instrument_ids:
        indicators_persisted += compute_and_persist_indicators(
            session,
            instrument_id=instrument_id,
            calculators=calculators,
        )
        instruments_processed += 1

    session.commit()
    return JobExecutionResult(
        job_name="indicator_update",
        metrics={
            "instruments_processed": instruments_processed,
            "indicator_values_persisted": indicators_persisted,
        },
    )


def run_taiwan_derivatives_pipeline_job(session: Session, trade_date: date) -> JobExecutionResult:
    try:
        load_result = run_taifex_derivatives_ingestion(
            session,
            request=ConnectorRequest(trade_date=trade_date, source_route="taifex_open_data"),
        )
        session.commit()
    except Exception:
        session.commit()
        raise

    records = (
        session.query(TwDerivativesDaily)
        .filter(TwDerivativesDaily.trade_date <= trade_date)
        .order_by(TwDerivativesDaily.trade_date.asc(), TwDerivativesDaily.id.asc())
        .all()
    )
    features = compute_tw_derivatives_features(records)
    features_persisted = TwDerivativesFeatureRepository(session).replace_many(features)
    session.commit()
    return JobExecutionResult(
        job_name="taiwan_derivatives_pipeline",
        metrics={
            "tw_derivatives_daily_loaded": load_result.tw_derivatives_daily_loaded,
            "tw_derivatives_features_persisted": features_persisted,
        },
    )


def run_daily_report_generation_job(session: Session, trade_date: date) -> JobExecutionResult:
    reports_persisted = 0

    reports_persisted += _persist_report(generate_market_summary_report(session, report_date=trade_date), session)
    reports_persisted += _persist_report(
        generate_taiwan_derivatives_summary_report(session, report_date=trade_date),
        session,
    )
    reports_persisted += _persist_report(
        generate_next_day_watch_candidates_report(session, report_date=trade_date),
        session,
    )

    for watchlist in session.query(Watchlist).order_by(Watchlist.id.asc()).all():
        reports_persisted += _persist_report(
            generate_watchlist_summary_report(session, report_date=trade_date, watchlist_id=watchlist.id),
            session,
        )

    tags = [
        tag
        for (tag,) in session.query(InstrumentTag.tag).distinct().order_by(InstrumentTag.tag.asc()).all()
    ]
    for tag in tags:
        reports_persisted += _persist_report(
            generate_group_summary_snapshot_report(session, report_date=trade_date, tag=tag),
            session,
        )

    return JobExecutionResult(
        job_name="daily_report_generation",
        metrics={"reports_persisted": reports_persisted},
    )


def _persist_report(generated_report, session: Session) -> int:
    persist_generated_report(session, generated_report)
    return 1
