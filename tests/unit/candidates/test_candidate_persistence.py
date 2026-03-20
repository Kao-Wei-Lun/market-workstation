from __future__ import annotations

from datetime import date
from typing import cast

from sqlalchemy.orm import Session

from services.core.candidates.service import (
    generate_and_persist_candidate_run,
    get_candidate_run,
    get_latest_candidate_run_for_date,
    list_candidate_items,
)


def test_candidate_run_persistence_round_trip(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    candidate_date = cast(date, reporting_seed["report_date"])

    run, items = generate_and_persist_candidate_run(reporting_session, candidate_date=candidate_date, top_n=10)

    assert run.total_candidates == 2
    assert len(items) == 2
    assert items[0].rank == 1
    assert get_candidate_run(reporting_session, run.id) is not None
    assert get_latest_candidate_run_for_date(reporting_session, candidate_date) is not None
    assert [item.symbol for item in list_candidate_items(reporting_session, run.id)] == ["2330", "2303"]
