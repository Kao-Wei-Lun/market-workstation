from __future__ import annotations

from sqlalchemy.orm import Session

from services.core.worker_health import record_worker_heartbeat
from services.models.worker_health import WorkerHealth


def test_worker_health_heartbeat_upserts(worker_session: Session) -> None:
    first = record_worker_heartbeat(
        worker_session,
        worker_name="scheduler-test",
        worker_role="scheduler",
        status="idle",
    )
    worker_session.commit()

    second = record_worker_heartbeat(
        worker_session,
        worker_name="scheduler-test",
        worker_role="scheduler",
        status="running",
        last_job_name="daily_market_etl",
        last_job_status="running",
        last_error=None,
    )
    worker_session.commit()

    records = worker_session.query(WorkerHealth).all()

    assert first.id == second.id
    assert len(records) == 1
    assert records[0].status == "running"
    assert records[0].last_job_name == "daily_market_etl"
