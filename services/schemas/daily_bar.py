from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DailyBarBase(BaseModel):
    instrument_id: int
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    turnover_value: Decimal | None = None
    transactions_count: int | None = None
    change: Decimal | None = None
    change_percent: Decimal | None = None


class DailyBarCreate(DailyBarBase):
    pass


class DailyBarRead(DailyBarBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
