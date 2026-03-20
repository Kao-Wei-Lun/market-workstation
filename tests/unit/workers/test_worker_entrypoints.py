from __future__ import annotations

from workers.analysis import main as analysis_main
from workers.scheduler import main as scheduler_main


def test_scheduler_entrypoint_runs_single_job(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run_registered_job(**kwargs):
        captured.update(kwargs)
        return None

    monkeypatch.setattr(scheduler_main, "run_registered_job", fake_run_registered_job)

    exit_code = scheduler_main.main(["--run-job", "daily_market_etl", "--trade-date", "2024-01-05"])

    assert exit_code == 0
    assert captured["job_name"] == "daily_market_etl"


def test_scheduler_entrypoint_starts_foreground_scheduler(monkeypatch) -> None:
    state = {"heartbeat_called": False, "scheduler_started": False}

    class _FakeScheduler:
        def start(self) -> None:
            state["scheduler_started"] = True

    def fake_record_worker_idle_heartbeat(**kwargs) -> None:
        state["heartbeat_called"] = True

    monkeypatch.setattr(scheduler_main, "record_worker_idle_heartbeat", fake_record_worker_idle_heartbeat)
    monkeypatch.setattr(scheduler_main, "build_scheduler", lambda worker_name: _FakeScheduler())

    exit_code = scheduler_main.main(["--start", "--worker-name", "scheduler-test"])

    assert exit_code == 0
    assert state["heartbeat_called"] is True
    assert state["scheduler_started"] is True


def test_analysis_entrypoint_writes_single_heartbeat(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_record_worker_idle_heartbeat(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(analysis_main, "record_worker_idle_heartbeat", fake_record_worker_idle_heartbeat)

    exit_code = analysis_main.main(["--heartbeat-once", "--worker-name", "analysis-test"])

    assert exit_code == 0
    assert captured["worker_name"] == "analysis-test"
    assert captured["worker_role"] == "analysis"


def test_analysis_entrypoint_lists_analysis_jobs(capsys) -> None:
    exit_code = analysis_main.main(["--list-jobs"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "indicator_update" in output
    assert "daily_report_generation" in output
