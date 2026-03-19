from __future__ import annotations

from sqlalchemy.orm import Session, sessionmaker

from workers.scheduler.scheduler import build_scheduler


def test_scheduler_registers_all_expected_jobs(
    worker_session_factory: sessionmaker[Session],
) -> None:
    scheduler = build_scheduler(session_factory=worker_session_factory, worker_name="scheduler-test")
    job_ids = sorted(job.id for job in scheduler.get_jobs())

    assert job_ids == [
        "daily_market_etl",
        "daily_report_generation",
        "indicator_update",
        "taiwan_derivatives_pipeline",
    ]
