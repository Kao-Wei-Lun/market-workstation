from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from services.schemas.instrument import InstrumentRead


class ChartInstrumentRead(InstrumentRead):
    latest_data_date: date | None = None


class ChartCandleRead(BaseModel):
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    change_percent: Decimal | None = None


class ChartIndicatorPointRead(BaseModel):
    trade_date: date
    value: Decimal


class ChartIndicatorSeriesRead(BaseModel):
    indicator_name: str
    component: str
    parameter_signature: str
    points: list[ChartIndicatorPointRead] = Field(default_factory=list)


class ChartAnnotationBase(BaseModel):
    view_kind: Literal["instrument", "index", "market_flow"]
    annotation_type: Literal["trend_line", "horizontal_line"]
    timeframe: str = "1d"
    label: str | None = None
    payload_json: dict[str, Any] = Field(default_factory=dict)


class ChartAnnotationCreate(ChartAnnotationBase):
    symbol: str


class ChartAnnotationRead(ChartAnnotationBase):
    id: int
    instrument_id: int
    symbol_snapshot: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChartDataRead(BaseModel):
    instrument: ChartInstrumentRead
    candles: list[ChartCandleRead] = Field(default_factory=list)
    indicators: list[ChartIndicatorSeriesRead] = Field(default_factory=list)
    annotations: list[ChartAnnotationRead] = Field(default_factory=list)
    available_indicator_keys: list[str] = Field(default_factory=list)


class InstitutionalFlowPointRead(BaseModel):
    trade_date: date
    spot_net_amount: Decimal | None = None
    futures_net_open_interest: int
    futures_net_amount: Decimal | None = None
    options_net_open_interest: int
    options_net_amount: Decimal | None = None
    options_directional_bias: Decimal | None = None
    average_bias_score: Decimal | None = None
    bullish_count: int = 0
    bearish_count: int = 0
    anomaly_count: int = 0


class InstitutionalFlowChartRead(BaseModel):
    instrument: ChartInstrumentRead
    candles: list[ChartCandleRead] = Field(default_factory=list)
    flow_points: list[InstitutionalFlowPointRead] = Field(default_factory=list)
    spot_flow_available: bool = False
    summary_highlights: list[str] = Field(default_factory=list)


class MarketStructureSummaryRead(BaseModel):
    trade_date: date | None = None
    overall_regime: str = "neutral"
    spot_direction: str = "neutral"
    futures_direction: str = "neutral"
    options_direction: str = "neutral"
    divergence_hints: list[str] = Field(default_factory=list)
    anomaly_hints: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)


class MarketStructureChartRead(BaseModel):
    instrument: ChartInstrumentRead
    candles: list[ChartCandleRead] = Field(default_factory=list)
    flow_points: list[InstitutionalFlowPointRead] = Field(default_factory=list)
    available_series: list[str] = Field(default_factory=list)
    summary: MarketStructureSummaryRead
