from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session, sessionmaker

from services.models.ingest_job import IngestJob
from services.models.worker_health import WorkerHealth
from workers.shared import runtime
from workers.shared.jobs import JobExecutionResult, list_registered_jobs


@dataclass(frozen=True)
class _FakeJobDefinition:
    name: str
    worker_role: str
    description: str
    cron: str
    handler: object


def test_registered_jobs_cover_required_worker_tasks() -> None:
    assert [job.name for job in list_registered_jobs()] == [
        "daily_market_etl",
        "daily_report_generation",
        "indicator_update",
        "taiwan_derivatives_pipeline",
    ]


def test_run_registered_job_tracks_lifecycle_and_heartbeat(
    monkeypatch,
    worker_session_factory: sessionmaker[Session],
) -> None:
    def fake_handler(session: Session, trade_date: date) -> JobExecutionResult:
        assert trade_date == date(2024, 1, 5)
        return JobExecutionResult(job_name="fake_job", metrics={"processed": 3})

    monkeypatch.setattr(
        runtime,
        "get_registered_job",
        lambda job_name: _FakeJobDefinition(
            name=job_name,
            worker_role="analysis",
            description="fake",
            cron="* * * * *",
            handler=fake_handler,
        ),
    )

    result = runtime.run_registered_job(
        session_factory=worker_session_factory,
        worker_name="analysis-test",
        worker_role="analysis",
        job_name="fake_job",
        trade_date=date(2024, 1, 5),
    )

    with worker_session_factory() as session:
        ingest_jobs = session.query(IngestJob).all()
        health = session.query(WorkerHealth).filter(WorkerHealth.worker_name == "analysis-test").one()

    assert result.metrics == {"processed": 3}
    assert len(ingest_jobs) == 1
    assert ingest_jobs[0].status == "success"
    assert health.status == "idle"
    assert health.last_job_name == "fake_job"
    assert health.last_job_status == "success"
