from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import cast

from config.universe import describe_universe_preset, list_available_universe_presets, load_universe_preset
from services.core.bootstrap import DEFAULT_V1_UNIVERSE_PRESET
from services.db.repositories.ingest_jobs import IngestJobRepository
from services.db.repositories.worker_health import WorkerHealthRepository
from services.models.candidate_run import CandidateRun
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.report_daily import ReportDaily
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.watchlist import Watchlist
from services.schemas.ingest_job import IngestJobRead
from services.schemas.output import DashboardMetaRead, DashboardSummaryCardRead
from services.schemas.visibility import (
    DatasetFreshnessRead,
    InstrumentCategoryCountRead,
    JobStatusCountRead,
    SystemStatusDataRead,
    SystemStatusRead,
    UniverseCoverageDataRead,
    UniverseCoverageRead,
    UniversePresetSummaryRead,
    UniverseScopeCoverageRead,
    WorkerStatusRead,
)


def build_universe_coverage(
    session: Session,
    *,
    preset_name: str = DEFAULT_V1_UNIVERSE_PRESET,
) -> UniverseCoverageRead:
    preset = load_universe_preset(preset_name)
    preset_description = describe_universe_preset(preset_name)
    loaded_watchlist_names = {
        name for (name,) in session.query(Watchlist.name).all()
    }
    loaded_symbols = {
        symbol for (symbol,) in session.query(Instrument.symbol).filter(Instrument.is_active.is_(True)).all()
    }

    scopes: list[UniverseScopeCoverageRead] = []
    for scope in preset.scopes:
        configured_symbols = sorted(
            instrument.symbol
            for instrument in preset.instruments
            if scope.key in instrument.scope_keys
        )
        configured_watchlists = sorted(
            watchlist.name
            for watchlist in preset.watchlists
            if scope.key in watchlist.scope_keys
        )
        scopes.append(
            UniverseScopeCoverageRead(
                key=scope.key,
                label=scope.label,
                market=scope.market,
                asset_type=scope.asset_type,
                source_route=scope.source_route,
                coverage=scope.coverage,
                description=scope.description,
                configured_instrument_count=len(configured_symbols),
                loaded_instrument_count=sum(1 for symbol in configured_symbols if symbol in loaded_symbols),
                configured_watchlist_count=len(configured_watchlists),
                loaded_watchlist_count=sum(1 for name in configured_watchlists if name in loaded_watchlist_names),
                sample_symbols=configured_symbols[:5],
            )
        )

    configured_instrument_count = cast(int, preset_description["instrument_count"])
    configured_watchlist_count = cast(int, preset_description["watchlist_count"])
    total_loaded = (
        session.query(func.count(Instrument.id))
        .filter(Instrument.is_active.is_(True))
        .scalar()
        or 0
    )
    highlights = [
        f"目前啟用標的 {total_loaded} 筆。",
        f"Universe preset {preset_name} 宣告 {configured_instrument_count} 筆標的與 {configured_watchlist_count} 個觀察清單。",
    ]
    if scopes:
        strongest_scope = max(scopes, key=lambda item: item.loaded_instrument_count)
        highlights.append(
            f"已載入最多的是 {strongest_scope.label}，共 {strongest_scope.loaded_instrument_count} 筆。"
        )

    return UniverseCoverageRead(
        meta=_meta(is_empty=not bool(scopes), item_count=len(scopes)),
        summary_cards=[
            _card("loaded_instruments", "已載入標的", total_loaded),
            _card("configured_instruments", "Preset 標的", configured_instrument_count),
            _card("configured_watchlists", "Preset 觀察清單", configured_watchlist_count),
            _card("scopes", "Coverage 區段", len(scopes)),
        ],
        highlights=highlights,
        data=UniverseCoverageDataRead(
            preset=UniversePresetSummaryRead(
                preset_name=preset_name,
                description=str(preset_description["description"]),
                available_presets=list_available_universe_presets(),
                configured_instrument_count=configured_instrument_count,
                configured_watchlist_count=configured_watchlist_count,
                scopes_declared=len(scopes),
            ),
            scopes=scopes,
            market_counts=_build_category_counts(session, "market"),
            asset_type_counts=_build_category_counts(session, "asset_type"),
            source_route_counts=_build_category_counts(session, "source_route"),
        ),
    )


def build_system_status(
    session: Session,
    *,
    job_limit: int = 20,
    worker_stale_minutes: int = 30,
) -> SystemStatusRead:
    recent_jobs = IngestJobRepository(session).list_recent(limit=job_limit)
    job_status_counts = [
        JobStatusCountRead(status=status, count=count)
        for status, count in IngestJobRepository(session).count_by_status()
    ]
    workers = [
        WorkerStatusRead(
            worker_name=worker.worker_name,
            worker_role=worker.worker_role,
            status=worker.status,
            heartbeat_at=worker.heartbeat_at,
            stale=_is_stale_heartbeat(worker.heartbeat_at, worker_stale_minutes),
            last_job_name=worker.last_job_name,
            last_job_status=worker.last_job_status,
            last_error=worker.last_error,
        )
        for worker in WorkerHealthRepository(session).list_all()
    ]
    datasets = _build_dataset_freshness(session)
    failed_jobs = sum(item.count for item in job_status_counts if item.status == "failed")
    stale_workers = sum(1 for worker in workers if worker.stale)
    ready_datasets = sum(1 for dataset in datasets if dataset.status == "ready")

    highlights = [
        f"資料集就緒 {ready_datasets}/{len(datasets)}。",
        f"最近 {len(recent_jobs)} 筆 ingest job 已納入狀態檢視。",
    ]
    if workers:
        highlights.append(f"目前有 {len(workers)} 個 worker heartbeat，過舊 {stale_workers} 個。")
    else:
        highlights.append("目前尚未記錄任何 worker heartbeat。")

    return SystemStatusRead(
        meta=_meta(
            as_of_date=max((dataset.latest_date for dataset in datasets if dataset.latest_date is not None), default=None),
            is_empty=not bool(recent_jobs or workers or datasets),
            item_count=len(recent_jobs) + len(workers) + len(datasets),
            returned_count=len(recent_jobs),
            limit=job_limit,
        ),
        summary_cards=[
            _card("datasets_ready", "就緒資料集", f"{ready_datasets}/{len(datasets)}", tone="positive" if ready_datasets else "neutral"),
            _card("recent_jobs", "近期工作", len(recent_jobs)),
            _card("failed_jobs", "失敗工作", failed_jobs, tone="negative" if failed_jobs else "neutral"),
            _card("workers", "Worker 心跳", len(workers), tone="info"),
        ],
        highlights=highlights,
        data=SystemStatusDataRead(
            datasets=datasets,
            recent_jobs=[IngestJobRead.model_validate(job) for job in recent_jobs],
            job_status_counts=job_status_counts,
            workers=workers,
        ),
    )


def _build_category_counts(
    session: Session,
    category_type: str,
) -> list[InstrumentCategoryCountRead]:
    column = getattr(Instrument, category_type)
    return [
        InstrumentCategoryCountRead(
            category_type=category_type,  # type: ignore[arg-type]
            key=str(key),
            label=str(key),
            instrument_count=int(count),
        )
        for key, count in (
            session.query(column, func.count(Instrument.id))
            .filter(Instrument.is_active.is_(True))
            .group_by(column)
            .order_by(func.count(Instrument.id).desc(), column.asc())
            .all()
        )
    ]


def _build_dataset_freshness(session: Session) -> list[DatasetFreshnessRead]:
    return [
        _dataset_freshness(session, DailyBar.trade_date, DailyBar.id, DailyBar, "daily_bars", "日線行情"),
        _dataset_freshness(session, IndicatorValue.trade_date, IndicatorValue.id, IndicatorValue, "indicator_values", "技術指標"),
        _dataset_freshness(session, TwDerivativesDaily.trade_date, TwDerivativesDaily.id, TwDerivativesDaily, "tw_derivatives_daily", "台灣衍生性商品"),
        _dataset_freshness(session, CandidateRun.candidate_date, CandidateRun.id, CandidateRun, "candidate_runs", "候選清單"),
        _dataset_freshness(session, ReportDaily.report_date, ReportDaily.id, ReportDaily, "reports_daily", "每日報表"),
    ]


def _dataset_freshness(session: Session, date_column, id_column, model, dataset_key: str, label: str) -> DatasetFreshnessRead:
    latest_date, record_count = session.query(func.max(date_column), func.count(id_column)).select_from(model).one()
    return DatasetFreshnessRead(
        dataset_key=dataset_key,
        label=label,
        latest_date=latest_date,
        record_count=int(record_count or 0),
        status="ready" if latest_date is not None else "missing",
    )


def _card(key: str, label: str, value: int | str, tone: str = "info") -> DashboardSummaryCardRead:
    text = str(value)
    return DashboardSummaryCardRead(
        key=key,
        label=label,
        value=text,
        display_value=text,
        tone=tone,  # type: ignore[arg-type]
    )


def _meta(
    *,
    as_of_date=None,
    is_empty: bool,
    item_count: int = 0,
    returned_count: int = 0,
    limit: int | None = None,
) -> DashboardMetaRead:
    return DashboardMetaRead(
        generated_at=datetime.now(tz=UTC),
        as_of_date=as_of_date,
        is_empty=is_empty,
        item_count=item_count,
        returned_count=returned_count,
        limit=limit,
        offset=0,
    )


def _is_stale_heartbeat(heartbeat_at: datetime, stale_minutes: int) -> bool:
    if heartbeat_at.tzinfo is None:
        return heartbeat_at < datetime.now(tz=UTC).replace(tzinfo=None) - timedelta(minutes=stale_minutes)
    return heartbeat_at < datetime.now(tz=UTC) - timedelta(minutes=stale_minutes)
