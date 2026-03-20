from __future__ import annotations

from datetime import date
from typing import cast

from sqlalchemy.orm import Session

from services.core.candidates.service import build_candidate_generation


def test_candidate_generation_scores_and_ranks_candidates(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    candidate_date = cast(date, reporting_seed["report_date"])

    result = build_candidate_generation(reporting_session, candidate_date=candidate_date, top_n=10)

    assert result.summary["overall_derivatives_regime"] == "neutral"
    assert result.summary["eligible_candidates"] == 2
    assert [item.symbol for item in result.items] == ["2330", "2303"]
    assert result.items[0].rank == 1
    assert result.items[0].score > result.items[1].score
    assert "watchlist_member" in result.items[0].candidate_reasons
    assert "close_above_sma20" in result.items[0].candidate_reasons
    assert result.items[0].supporting_metrics["technical_score"] == "3.000000"


def test_candidate_generation_respects_top_n(
    reporting_session: Session,
    reporting_seed: dict[str, object],
) -> None:
    candidate_date = cast(date, reporting_seed["report_date"])

    result = build_candidate_generation(reporting_session, candidate_date=candidate_date, top_n=1)

    assert len(result.items) == 1
    assert result.items[0].symbol == "2330"
