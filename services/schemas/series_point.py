from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SeriesPointBase(BaseModel):
    instrument_id: int | None = None
    series_key: str
    source_route: str
    trade_date: date
    value: Decimal


class SeriesPointCreate(SeriesPointBase):
    pass


class SeriesPointRead(SeriesPointBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
