from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from services.models.candidate_item import CandidateItem
from services.models.candidate_run import CandidateRun


class CandidateRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        candidate_date: date,
        status: str,
        total_candidates: int,
        generation_config_json: dict[str, Any],
        summary_json: dict[str, Any],
    ) -> CandidateRun:
        run = CandidateRun(
            candidate_date=candidate_date,
            status=status,
            total_candidates=total_candidates,
            generation_config_json=generation_config_json,
            summary_json=summary_json,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, run_id: int) -> CandidateRun | None:
        return self.session.query(CandidateRun).filter(CandidateRun.id == run_id).one_or_none()

    def get_latest_by_date(self, candidate_date: date) -> CandidateRun | None:
        return (
            self.session.query(CandidateRun)
            .filter(CandidateRun.candidate_date == candidate_date)
            .order_by(CandidateRun.created_at.desc(), CandidateRun.id.desc())
            .first()
        )


class CandidateItemRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(self, items: list[CandidateItem]) -> int:
        if not items:
            return 0
        self.session.add_all(items)
        self.session.flush()
        return len(items)

    def list_for_run(self, run_id: int) -> list[CandidateItem]:
        return (
            self.session.query(CandidateItem)
            .filter(CandidateItem.run_id == run_id)
            .order_by(CandidateItem.rank.asc(), CandidateItem.id.asc())
            .all()
        )
