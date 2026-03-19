from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TwDerivativesFeatureBase(BaseModel):
    daily_record_id: int
    trade_date: date
    market: str
    product_code: str
    contract_period: str | None = None
    institution: str
    call_put: str | None = None
    delta_1d: Decimal | None = None
    delta_5d: Decimal | None = None
    delta_20d: Decimal | None = None
    zscore_20d: Decimal | None = None
    regime_label: str
    bias_score: Decimal
    anomaly_flag: bool


class TwDerivativesFeatureCreate(TwDerivativesFeatureBase):
    pass


class TwDerivativesFeatureRead(TwDerivativesFeatureBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
