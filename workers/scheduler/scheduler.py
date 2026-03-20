from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings
from services.db.session import SessionLocal
from workers.shared.jobs import list_registered_jobs
from workers.shared.runtime import run_registered_job


def build_scheduler(
    *,
    session_factory: sessionmaker[Session] = SessionLocal,
    worker_name: str = "scheduler",
) -> BlockingScheduler:
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.scheduler_timezone)
    for job in list_registered_jobs():
        scheduler.add_job(
            run_scheduled_job,
            trigger=CronTrigger.from_crontab(
                _cron_expression_for_job(job.name),
                timezone=settings.scheduler_timezone,
            ),
            kwargs={
                "session_factory": session_factory,
                "worker_name": worker_name,
                "worker_role": "scheduler",
                "job_name": job.name,
            },
            id=job.name,
            replace_existing=True,
        )
    return scheduler


def run_scheduled_job(
    *,
    session_factory: sessionmaker[Session],
    worker_name: str,
    worker_role: str,
    job_name: str,
) -> None:
    settings = get_settings()
    trade_date = datetime.now(tz=ZoneInfo(settings.scheduler_timezone)).date()
    run_registered_job(
        session_factory=session_factory,
        worker_name=worker_name,
        worker_role=worker_role,
        job_name=job_name,
        trade_date=trade_date,
    )


def _cron_expression_for_job(job_name: str) -> str:
    settings = get_settings()
    mapping = {
        "daily_market_etl": settings.scheduler_daily_market_etl_cron,
        "indicator_update": settings.scheduler_indicator_update_cron,
        "taiwan_derivatives_pipeline": settings.scheduler_taiwan_derivatives_pipeline_cron,
        "daily_report_generation": settings.scheduler_daily_report_generation_cron,
    }
    return mapping[job_name]
