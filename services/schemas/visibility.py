from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from services.schemas.ingest_job import IngestJobRead
from services.schemas.output import DashboardMetaRead, DashboardSummaryCardRead


class UniversePresetSummaryRead(BaseModel):
    preset_name: str
    description: str
    available_presets: list[str] = Field(default_factory=list)
    configured_instrument_count: int
    configured_watchlist_count: int
    scopes_declared: int


class UniverseScopeCoverageRead(BaseModel):
    key: str
    label: str
    group_label: str
    market: str
    asset_type: str
    source_route: str
    coverage: str
    description: str
    stale_after_days: int
    configured_instrument_count: int
    loaded_instrument_count: int
    instruments_with_data_count: int
    missing_data_count: int
    stale_data_count: int
    latest_data_date: date | None = None
    status: Literal["ready", "partial", "missing", "stale"] = "missing"
    configured_watchlist_count: int
    loaded_watchlist_count: int
    sample_symbols: list[str] = Field(default_factory=list)
    sample_missing_symbols: list[str] = Field(default_factory=list)
    sample_stale_symbols: list[str] = Field(default_factory=list)


class InstrumentCategoryCountRead(BaseModel):
    category_type: Literal["market", "asset_type", "source_route"]
    key: str
    label: str
    instrument_count: int
    instruments_with_data_count: int = 0
    missing_data_count: int = 0
    stale_data_count: int = 0
    latest_data_date: date | None = None


class UniverseCompletenessSummaryRead(BaseModel):
    reference_latest_date: date | None = None
    configured_instrument_count: int
    loaded_instrument_count: int
    instruments_with_data_count: int
    missing_data_count: int
    stale_data_count: int
    scopes_declared: int
    bootstrapped_scope_count: int
    ready_scope_count: int
    attention_scope_count: int


class UniverseCoverageDataRead(BaseModel):
    preset: UniversePresetSummaryRead
    completeness: UniverseCompletenessSummaryRead
    scopes: list[UniverseScopeCoverageRead] = Field(default_factory=list)
    market_counts: list[InstrumentCategoryCountRead] = Field(default_factory=list)
    asset_type_counts: list[InstrumentCategoryCountRead] = Field(default_factory=list)
    source_route_counts: list[InstrumentCategoryCountRead] = Field(default_factory=list)


class UniverseCoverageRead(BaseModel):
    meta: DashboardMetaRead
    summary_cards: list[DashboardSummaryCardRead] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    data: UniverseCoverageDataRead


class DatasetFreshnessRead(BaseModel):
    dataset_key: str
    label: str
    latest_date: date | None = None
    record_count: int
    status: Literal["ready", "missing"] = "missing"


class JobStatusCountRead(BaseModel):
    status: str
    count: int


class WorkerStatusRead(BaseModel):
    worker_name: str
    worker_role: str
    status: str
    heartbeat_at: datetime
    stale: bool
    last_job_name: str | None = None
    last_job_status: str | None = None
    last_error: str | None = None


class SystemStatusDataRead(BaseModel):
    datasets: list[DatasetFreshnessRead] = Field(default_factory=list)
    recent_jobs: list[IngestJobRead] = Field(default_factory=list)
    job_status_counts: list[JobStatusCountRead] = Field(default_factory=list)
    workers: list[WorkerStatusRead] = Field(default_factory=list)


class SystemStatusRead(BaseModel):
    meta: DashboardMetaRead
    summary_cards: list[DashboardSummaryCardRead] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)
    data: SystemStatusDataRead
