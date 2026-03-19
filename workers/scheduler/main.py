from __future__ import annotations

import argparse
import logging
from datetime import date

from services.db.session import SessionLocal
from workers.scheduler.scheduler import build_scheduler
from workers.shared.jobs import list_registered_jobs
from workers.shared.runtime import record_worker_idle_heartbeat, run_registered_job


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    parser = argparse.ArgumentParser(description="Scheduler worker")
    parser.add_argument("--start", action="store_true", help="Start the APScheduler loop.")
    parser.add_argument("--run-job", type=str, help="Run a single registered job immediately.")
    parser.add_argument("--trade-date", type=date.fromisoformat, help="Override trade date in YYYY-MM-DD.")
    parser.add_argument("--list-jobs", action="store_true", help="List available registered jobs.")
    parser.add_argument("--worker-name", type=str, default="scheduler", help="Worker name for heartbeat records.")
    args = parser.parse_args(argv)

    if args.list_jobs:
        for job in list_registered_jobs():
            print(job.name)
        return 0

    if args.run_job:
        run_registered_job(
            session_factory=SessionLocal,
            worker_name=args.worker_name,
            worker_role="scheduler",
            job_name=args.run_job,
            trade_date=args.trade_date or date.today(),
        )
        return 0

    if args.start:
        record_worker_idle_heartbeat(
            session_factory=SessionLocal,
            worker_name=args.worker_name,
            worker_role="scheduler",
        )
        scheduler = build_scheduler(worker_name=args.worker_name)
        scheduler.start()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
