from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from typing import Callable

from sqlalchemy import func
from sqlalchemy.orm import Session

from services.core.bootstrap import (
    DEFAULT_DEMO_TRADE_DATE,
    generate_demo_data,
    run_sample_daily_market_etl,
)
from services.core.candidates.service import generate_and_persist_candidate_run
from services.core.ingest_jobs import record_job_failure, record_job_start, record_job_success
from services.db.repositories.ingest_jobs import IngestJobRepository
from services.models.daily_bar import DailyBar
from services.models.ingest_job import IngestJob
from services.schemas.operations import (
    ManualTaskActionRead,
    ManualTaskCenterDataRead,
    ManualTaskCenterRead,
    ManualTaskHistoryItemRead,
    ManualTaskRunRead,
)
from services.schemas.output import DashboardMetaRead, DashboardSummaryCardRead
from workers.shared.jobs import run_daily_report_generation_job, run_indicator_update_job

MANUAL_TASK_SOURCE_ROUTE = "manual_task_api"
MANUAL_TASK_JOB_PREFIX = "manual_task:"


@dataclass(frozen=True)
class ManualTaskDefinition:
    action_key: str
    label: str
    description: str
    target_label: str
    target_route_name: str | None
    handler: Callable[[Session, date], dict[str, int]]


def list_manual_task_actions(session: Session) -> list[ManualTaskActionRead]:
    suggested_trade_date = _resolve_default_trade_date(session)
    return [
        ManualTaskActionRead(
            action_key=definition.action_key,
            label=definition.label,
            description=definition.description,
            target_label=definition.target_label,
            target_route_name=definition.target_route_name,
            requires_trade_date=True,
            suggested_trade_date=suggested_trade_date,
        )
        for definition in _manual_task_definitions().values()
    ]


def build_manual_task_center(session: Session, *, limit: int = 20) -> ManualTaskCenterRead:
    actions = list_manual_task_actions(session)
    recent_jobs = list_recent_manual_tasks(session, limit=limit)
    success_count = sum(1 for item in recent_jobs if item.status == "success")
    failed_count = sum(1 for item in recent_jobs if item.status == "failed")
    latest_success = next((item for item in recent_jobs if item.status == "success"), None)

    highlights = [
        f"目前可手動執行 {len(actions)} 種本機任務。",
        f"最近 {len(recent_jobs)} 筆手動任務已納入檢視，成功 {success_count} 筆。",
    ]
    if latest_success is not None:
        highlights.append(
            f"最近成功任務為「{latest_success.label}」，完成於 {latest_success.finished_at or latest_success.started_at or '未知時間'}。"
        )
    else:
        highlights.append("目前尚未記錄任何手動任務，可先從示範資料或報表生成開始。")

    return ManualTaskCenterRead(
        meta=DashboardMetaRead(
            generated_at=datetime.now(tz=UTC),
            as_of_date=_resolve_default_trade_date(session),
            is_empty=not bool(recent_jobs),
            item_count=len(actions) + len(recent_jobs),
            returned_count=len(recent_jobs),
            limit=limit,
            offset=0,
        ),
        summary_cards=[
            _card("available_actions", "可執行任務", len(actions)),
            _card("recent_tasks", "近期手動任務", len(recent_jobs)),
            _card("success_tasks", "成功任務", success_count, tone="positive" if success_count else "neutral"),
            _card("failed_tasks", "失敗任務", failed_count, tone="negative" if failed_count else "neutral"),
        ],
        highlights=highlights,
        data=ManualTaskCenterDataRead(
            available_actions=actions,
            recent_tasks=recent_jobs,
        ),
    )


def execute_manual_task(
    session: Session,
    *,
    action_key: str,
    trade_date: date | None = None,
) -> ManualTaskRunRead:
    definition = _get_manual_task_definition(action_key)
    resolved_trade_date = trade_date or _resolve_default_trade_date(session)
    job = record_job_start(
        session,
        source_route=MANUAL_TASK_SOURCE_ROUTE,
        job_type=f"{MANUAL_TASK_JOB_PREFIX}{action_key}",
        trade_date=resolved_trade_date,
    )
    session.commit()
    session.refresh(job)

    try:
        metrics = definition.handler(session, resolved_trade_date)
        record_job_success(session, job)
        session.commit()
        session.refresh(job)
        return ManualTaskRunRead(
            action_key=definition.action_key,
            label=definition.label,
            target_label=definition.target_label,
            target_route_name=definition.target_route_name,
            status="success",
            trade_date=resolved_trade_date,
            metrics=metrics,
            message=f"{definition.label}已完成。",
            history_item=_history_item_from_job(job),
        )
    except Exception as exc:
        record_job_failure(session, job, str(exc))
        session.commit()
        session.refresh(job)
        raise


def list_recent_manual_tasks(session: Session, *, limit: int = 20) -> list[ManualTaskHistoryItemRead]:
    jobs = IngestJobRepository(session).list_recent(
        limit=limit,
        source_route=MANUAL_TASK_SOURCE_ROUTE,
        job_type_prefix=MANUAL_TASK_JOB_PREFIX,
    )
    return [_history_item_from_job(job) for job in jobs]


def _manual_task_definitions() -> dict[str, ManualTaskDefinition]:
    return {
        definition.action_key: definition
        for definition in [
            ManualTaskDefinition(
                action_key="demo_data",
                label="產生示範資料",
                description="建立本機可見的示範資料、候選、報表、衍生性商品與回測內容。",
                target_label="總覽 / 候選 / 報表",
                target_route_name="overview",
                handler=_run_demo_data,
            ),
            ManualTaskDefinition(
                action_key="sample_market_etl",
                label="載入示範日線",
                description="載入本機示範日線資料，供指標、候選與報表後續使用。",
                target_label="資料新鮮度 / 系統狀態",
                target_route_name="operations",
                handler=_run_sample_market_etl,
            ),
            ManualTaskDefinition(
                action_key="indicator_update",
                label="更新技術指標",
                description="使用現有日線資料重新計算並寫入技術指標。",
                target_label="候選 / 系統狀態",
                target_route_name="candidates",
                handler=_run_indicator_update,
            ),
            ManualTaskDefinition(
                action_key="candidate_generation",
                label="產生候選清單",
                description="依現有指標、群組與衍生性商品脈絡產生隔日候選。",
                target_label="候選清單",
                target_route_name="candidates",
                handler=_run_candidate_generation,
            ),
            ManualTaskDefinition(
                action_key="report_generation",
                label="產生每日報表",
                description="產生並保存每日報表 bundle 與主要摘要內容。",
                target_label="每日報表",
                target_route_name="reports",
                handler=_run_report_generation,
            ),
        ]
    }


def _get_manual_task_definition(action_key: str) -> ManualTaskDefinition:
    try:
        return _manual_task_definitions()[action_key]
    except KeyError as exc:
        msg = f"unknown manual task: {action_key}"
        raise ValueError(msg) from exc


def _resolve_default_trade_date(session: Session) -> date:
    latest_trade_date = session.query(func.max(DailyBar.trade_date)).scalar()
    return latest_trade_date or DEFAULT_DEMO_TRADE_DATE


def _run_demo_data(session: Session, trade_date: date) -> dict[str, int]:
    result = asdict(generate_demo_data(session, trade_date=trade_date))
    return {key: value for key, value in result.items() if isinstance(value, int)}


def _run_sample_market_etl(session: Session, trade_date: date) -> dict[str, int]:
    result = asdict(run_sample_daily_market_etl(session, trade_date=trade_date))
    return {key: value for key, value in result.items() if isinstance(value, int)}


def _run_indicator_update(session: Session, trade_date: date) -> dict[str, int]:
    return run_indicator_update_job(session, trade_date).metrics


def _run_candidate_generation(session: Session, trade_date: date) -> dict[str, int]:
    run, items = generate_and_persist_candidate_run(session, candidate_date=trade_date, top_n=20)
    return {
        "candidate_runs_created": int(run.id > 0),
        "candidate_items_created": len(items),
    }


def _run_report_generation(session: Session, trade_date: date) -> dict[str, int]:
    return run_daily_report_generation_job(session, trade_date).metrics


def _history_item_from_job(job: IngestJob) -> ManualTaskHistoryItemRead:
    action_key = job.job_type.removeprefix(MANUAL_TASK_JOB_PREFIX)
    definition = _manual_task_definitions().get(action_key)
    return ManualTaskHistoryItemRead(
        id=job.id,
        action_key=action_key,
        label=definition.label if definition else action_key,
        description=definition.description if definition else job.job_type,
        target_label=definition.target_label if definition else job.source_route,
        status=job.status,
        trade_date=job.trade_date,
        started_at=job.started_at.isoformat() if job.started_at is not None else None,
        finished_at=job.finished_at.isoformat() if job.finished_at is not None else None,
        error_summary=job.failure_reason,
        source_route=job.source_route,
        job_type=job.job_type,
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
