from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InstrumentBase(BaseModel):
    symbol: str
    name: str
    market: str
    asset_type: str
    currency: str
    timezone: str
    source_route: str
    is_active: bool = True


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentRead(InstrumentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
