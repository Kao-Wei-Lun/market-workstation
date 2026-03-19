from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TwDerivativesDailyBase(BaseModel):
    trade_date: date
    market: str
    product_code: str
    product_name: str | None = None
    contract_period: str | None = None
    institution: str
    call_put: str | None = None
    long_open_interest: int
    short_open_interest: int
    net_open_interest: int
    long_amount: Decimal | None = None
    short_amount: Decimal | None = None
    net_amount: Decimal | None = None
    source_route: str
    is_options: bool = False


class TwDerivativesDailyCreate(TwDerivativesDailyBase):
    pass


class TwDerivativesDailyRead(TwDerivativesDailyBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
