from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

import httpx

from services.schemas.etl import NormalizedDataBatch


JsonMapping = dict[str, Any]


@dataclass(frozen=True)
class ProviderConnectorConfig:
    provider_name: str
    base_url: str | None = None
    api_key: str | None = None
    timeout_seconds: float = 10.0
    extra_params: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ConnectorRequest:
    symbol: str | None = None
    series_key: str | None = None
    trade_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    instrument_id: int | None = None
    source_route: str | None = None


@dataclass(frozen=True)
class FetchResult:
    source_route: str
    payload: JsonMapping
    requested_at: datetime


class BaseConnector(ABC):
    source_route: str

    def __init__(self, config: ProviderConnectorConfig | None = None) -> None:
        self.config = config or ProviderConnectorConfig(provider_name=self.source_route)

    def _get_json(self, url: str, params: dict[str, str]) -> JsonMapping:
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    @abstractmethod
    def fetch(self, request: ConnectorRequest) -> FetchResult:
        raise NotImplementedError

    @abstractmethod
    def normalize(self, payload: JsonMapping, request: ConnectorRequest) -> NormalizedDataBatch:
        raise NotImplementedError

    def _build_fetch_result(self, payload: JsonMapping) -> FetchResult:
        return FetchResult(
            source_route=self.source_route,
            payload=payload,
            requested_at=datetime.now(tz=timezone.utc),
        )


class DailyBarConnector(BaseConnector, ABC):
    pass


class SeriesConnector(BaseConnector, ABC):
    pass
