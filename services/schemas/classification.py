from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class InstrumentTagCreate(BaseModel):
    tag: str


class InstrumentTagRead(BaseModel):
    id: int
    instrument_id: int
    tag: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistCreate(BaseModel):
    name: str
    description: str | None = None


class WatchlistRead(BaseModel):
    id: int
    name: str
    description: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistItemRead(BaseModel):
    id: int
    watchlist_id: int
    instrument_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GroupMemberChange(BaseModel):
    instrument_id: int
    symbol: str
    close_change_pct: Decimal


class GroupSummaryRead(BaseModel):
    member_count: int
    average_close_change_pct: Decimal
    top_gainers: list[GroupMemberChange]
    top_losers: list[GroupMemberChange]
    percentage_above_sma: Decimal
