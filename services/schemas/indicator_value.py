from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class IndicatorValueBase(BaseModel):
    instrument_id: int
    trade_date: date
    indicator_name: str
    component: str
    parameter_signature: str
    value: Decimal


class IndicatorValueCreate(IndicatorValueBase):
    pass


class IndicatorValueRead(IndicatorValueBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
