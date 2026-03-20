from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CandidateGenerateRequest(BaseModel):
    candidate_date: date
    top_n: int = 20


class CandidateSummaryRead(BaseModel):
    overall_derivatives_regime: str
    overall_derivatives_bias_score: Decimal
    instruments_considered: int
    eligible_candidates: int


class CandidateItemRead(BaseModel):
    id: int
    run_id: int
    instrument_id: int
    candidate_date: date
    symbol: str
    score: Decimal
    rank: int
    candidate_reasons: list[str] = Field(alias="candidate_reasons_json")
    supporting_metrics: dict[str, Any] = Field(alias="supporting_metrics_json")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class CandidateRunRead(BaseModel):
    id: int
    candidate_date: date
    status: str
    total_candidates: int
    generation_config_json: dict[str, Any]
    summary_json: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CandidateRunWithItemsRead(BaseModel):
    run: CandidateRunRead
    items: list[CandidateItemRead]
