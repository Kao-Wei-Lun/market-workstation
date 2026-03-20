from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Literal, cast

from config.universe import describe_universe_preset, list_available_universe_presets, load_universe_preset
from services.core.bootstrap import DEFAULT_V1_UNIVERSE_PRESET
from services.db.repositories.ingest_jobs import IngestJobRepository
from services.db.repositories.worker_health import WorkerHealthRepository
from services.models.candidate_run import CandidateRun
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.instrument import Instrument
from services.models.report_daily import ReportDaily
from services.models.series_point import SeriesPoint
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.watchlist import Watchlist
from services.schemas.ingest_job import IngestJobRead
from services.schemas.output import DashboardMetaRead, DashboardSummaryCardRead
from services.schemas.visibility import (
    DatasetFreshnessRead,
    UniverseCompletenessSummaryRead,
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
    scope_symbols = sorted({instrument.symbol for instrument in preset.instruments})
    instrument_rows = (
        session.query(Instrument.id, Instrument.symbol, Instrument.market, Instrument.asset_type, Instrument.source_route)
        .filter(Instrument.is_active.is_(True), Instrument.symbol.in_(scope_symbols))
        .all()
    )
    instrument_by_symbol = {
        symbol: {
            "id": instrument_id,
            "market": market,
            "asset_type": asset_type,
            "source_route": source_route,
        }
        for instrument_id, symbol, market, asset_type, source_route in instrument_rows
    }
    instrument_ids = [int(row["id"]) for row in instrument_by_symbol.values()]
    latest_data_dates = _build_instrument_latest_data_dates(
        session,
        instrument_ids=instrument_ids,
    )
    reference_latest_date = max((value for value in latest_data_dates.values() if value is not None), default=None)

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
        loaded_scope_symbols = [symbol for symbol in configured_symbols if symbol in instrument_by_symbol]
        instruments_with_data_symbols = [
            symbol for symbol in loaded_scope_symbols if latest_data_dates.get(int(instrument_by_symbol[symbol]["id"])) is not None
        ]
        missing_symbols = [
            symbol
            for symbol in configured_symbols
            if symbol not in instrument_by_symbol
            or latest_data_dates.get(int(instrument_by_symbol[symbol]["id"])) is None
        ]
        stale_symbols = [
            symbol
            for symbol in loaded_scope_symbols
            if _is_stale_data_date(
                latest_data_dates.get(int(instrument_by_symbol[symbol]["id"])),
                reference_latest_date,
                scope.stale_after_days,
            )
        ]
        scope_dates = [
            latest_data_dates.get(int(instrument_by_symbol[symbol]["id"]))
            for symbol in loaded_scope_symbols
        ]
        latest_scope_date = max((value for value in scope_dates if value is not None), default=None)
        scopes.append(
            UniverseScopeCoverageRead(
                key=scope.key,
                label=scope.label,
                group_label=scope.group_label,
                market=scope.market,
                asset_type=scope.asset_type,
                source_route=scope.source_route,
                coverage=scope.coverage,
                description=scope.description,
                stale_after_days=scope.stale_after_days,
                configured_instrument_count=len(configured_symbols),
                loaded_instrument_count=sum(1 for symbol in configured_symbols if symbol in loaded_symbols),
                instruments_with_data_count=len(instruments_with_data_symbols),
                missing_data_count=len(missing_symbols),
                stale_data_count=len(stale_symbols),
                latest_data_date=latest_scope_date,
                status=_scope_status(
                    configured_count=len(configured_symbols),
                    with_data_count=len(instruments_with_data_symbols),
                    missing_count=len(missing_symbols),
                    stale_count=len(stale_symbols),
                ),
                configured_watchlist_count=len(configured_watchlists),
                loaded_watchlist_count=sum(1 for name in configured_watchlists if name in loaded_watchlist_names),
                sample_symbols=configured_symbols[:5],
                sample_missing_symbols=missing_symbols[:5],
                sample_stale_symbols=stale_symbols[:5],
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
        attention_scopes = [scope for scope in scopes if scope.status in {"missing", "partial", "stale"}]
        if attention_scopes:
            highlights.append(f"目前有 {len(attention_scopes)} 個 coverage 區段需要補資料或補跑。")

    return UniverseCoverageRead(
        meta=_meta(is_empty=not bool(scopes), item_count=len(scopes)),
        summary_cards=[
            _card("loaded_instruments", "已載入標的", total_loaded),
            _card("configured_instruments", "Preset 標的", configured_instrument_count),
            _card("with_data", "已有資料標的", sum(scope.instruments_with_data_count for scope in scopes), tone="positive"),
            _card("attention_scopes", "需留意區段", sum(1 for scope in scopes if scope.status in {"missing", "partial", "stale"}), tone="negative" if any(scope.status in {"missing", "partial", "stale"} for scope in scopes) else "positive"),
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
            completeness=UniverseCompletenessSummaryRead(
                reference_latest_date=reference_latest_date,
                configured_instrument_count=configured_instrument_count,
                loaded_instrument_count=sum(scope.loaded_instrument_count for scope in scopes),
                instruments_with_data_count=sum(scope.instruments_with_data_count for scope in scopes),
                missing_data_count=sum(scope.missing_data_count for scope in scopes),
                stale_data_count=sum(scope.stale_data_count for scope in scopes),
                scopes_declared=len(scopes),
                bootstrapped_scope_count=sum(1 for scope in scopes if scope.loaded_instrument_count > 0),
                ready_scope_count=sum(1 for scope in scopes if scope.status == "ready"),
                attention_scope_count=sum(1 for scope in scopes if scope.status in {"missing", "partial", "stale"}),
            ),
            scopes=scopes,
            market_counts=_build_category_counts(session, "market", instrument_ids, latest_data_dates, reference_latest_date),
            asset_type_counts=_build_category_counts(session, "asset_type", instrument_ids, latest_data_dates, reference_latest_date),
            source_route_counts=_build_category_counts(session, "source_route", instrument_ids, latest_data_dates, reference_latest_date),
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
    instrument_ids: list[int],
    latest_data_dates: dict[int, date | None],
    reference_latest_date: date | None,
) -> list[InstrumentCategoryCountRead]:
    if not instrument_ids:
        return []
    column = getattr(Instrument, category_type)
    rows = (
        session.query(Instrument.id, column)
        .filter(Instrument.is_active.is_(True), Instrument.id.in_(instrument_ids))
        .order_by(column.asc(), Instrument.id.asc())
        .all()
    )
    grouped: dict[str, list[int]] = {}
    for instrument_id, key in rows:
        grouped.setdefault(str(key), []).append(int(instrument_id))

    counts: list[InstrumentCategoryCountRead] = []
    for key, instrument_ids in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        dates = [latest_data_dates.get(instrument_id) for instrument_id in instrument_ids]
        latest_date = max((value for value in dates if value is not None), default=None)
        with_data_count = sum(1 for value in dates if value is not None)
        missing_count = sum(1 for value in dates if value is None)
        stale_count = sum(
            1 for value in dates if _is_stale_data_date(value, reference_latest_date, stale_after_days=3)
        )
        counts.append(
            InstrumentCategoryCountRead(
                category_type=category_type,  # type: ignore[arg-type]
                key=key,
                label=key,
                instrument_count=len(instrument_ids),
                instruments_with_data_count=with_data_count,
                missing_data_count=missing_count,
                stale_data_count=stale_count,
                latest_data_date=latest_date,
            )
        )
    return counts


def _build_instrument_latest_data_dates(
    session: Session,
    *,
    instrument_ids: list[int],
) -> dict[int, date | None]:
    if not instrument_ids:
        return {}

    latest_dates: dict[int, date | None] = {instrument_id: None for instrument_id in instrument_ids}
    for instrument_id, latest_date in (
        session.query(DailyBar.instrument_id, func.max(DailyBar.trade_date))
        .filter(DailyBar.instrument_id.in_(instrument_ids))
        .group_by(DailyBar.instrument_id)
        .all()
    ):
        latest_dates[int(instrument_id)] = latest_date

    for instrument_id, latest_date in (
        session.query(SeriesPoint.instrument_id, func.max(SeriesPoint.trade_date))
        .filter(SeriesPoint.instrument_id.in_(instrument_ids))
        .group_by(SeriesPoint.instrument_id)
        .all()
    ):
        if instrument_id is None:
            continue
        existing = latest_dates.get(int(instrument_id))
        if existing is None or (latest_date is not None and latest_date > existing):
            latest_dates[int(instrument_id)] = latest_date
    return latest_dates


def _scope_status(
    *,
    configured_count: int,
    with_data_count: int,
    missing_count: int,
    stale_count: int,
) -> Literal["ready", "partial", "missing", "stale"]:
    if configured_count == 0 or with_data_count == 0:
        return "missing"
    if stale_count > 0:
        return "stale"
    if missing_count > 0:
        return "partial"
    return "ready"


def _is_stale_data_date(latest_date: date | None, reference_latest_date: date | None, stale_after_days: int) -> bool:
    if latest_date is None or reference_latest_date is None:
        return False
    return latest_date < reference_latest_date - timedelta(days=stale_after_days)


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
