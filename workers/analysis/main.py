from __future__ import annotations

import argparse
import logging
import time
from datetime import date

from config.settings import get_settings
from services.db.session import SessionLocal
from workers.shared.jobs import list_registered_jobs
from workers.shared.runtime import record_worker_idle_heartbeat, run_registered_job


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Analysis worker")
    parser.add_argument("--run-job", type=str, help="Run a single analysis job immediately.")
    parser.add_argument("--trade-date", type=date.fromisoformat, help="Override trade date in YYYY-MM-DD.")
    parser.add_argument("--list-jobs", action="store_true", help="List analysis jobs.")
    parser.add_argument("--heartbeat-once", action="store_true", help="Write one idle heartbeat and exit.")
    parser.add_argument("--loop-heartbeat", action="store_true", help="Run idle heartbeat loop.")
    parser.add_argument("--worker-name", type=str, default="analysis", help="Worker name for heartbeat records.")
    args = parser.parse_args(argv)

    if args.list_jobs:
        for job in list_registered_jobs(worker_role="analysis"):
            print(job.name)
        return 0

    if args.run_job:
        run_registered_job(
            session_factory=SessionLocal,
            worker_name=args.worker_name,
            worker_role="analysis",
            job_name=args.run_job,
            trade_date=args.trade_date or date.today(),
        )
        return 0

    if args.heartbeat_once:
        record_worker_idle_heartbeat(
            session_factory=SessionLocal,
            worker_name=args.worker_name,
            worker_role="analysis",
        )
        return 0

    if args.loop_heartbeat:
        _run_idle_loop(worker_name=args.worker_name)
        return 0

    parser.print_help()
    return 1


def _run_idle_loop(worker_name: str) -> None:
    interval_seconds = get_settings().worker_heartbeat_interval_seconds
    while True:
        record_worker_idle_heartbeat(
            session_factory=SessionLocal,
            worker_name=worker_name,
            worker_role="analysis",
        )
        time.sleep(interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
