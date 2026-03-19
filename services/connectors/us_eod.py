from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from config.settings import get_settings
from services.connectors.base import ConnectorRequest, DailyBarConnector, ProviderConnectorConfig
from services.schemas.etl import NormalizedDailyBarRecord, NormalizedDataBatch


class UsEodConnector(DailyBarConnector):
    source_route = "us_eod_provider"

    def __init__(self, config: ProviderConnectorConfig | None = None) -> None:
        if config is None:
            settings = get_settings()
            config = ProviderConnectorConfig(
                provider_name=settings.us_eod_provider,
                base_url=settings.us_eod_base_url,
                api_key=settings.us_eod_api_key,
            )
        super().__init__(config)

    def fetch(self, request: ConnectorRequest):
        if request.symbol is None:
            msg = "US EOD connector requires symbol"
            raise ValueError(msg)
        if self.config.base_url is None:
            msg = "US EOD base_url is required for live fetches"
            raise ValueError(msg)

        params = {
            "symbol": request.symbol,
            "provider": self.config.provider_name,
        }
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        if request.start_date is not None:
            params["start_date"] = request.start_date.isoformat()
        if request.end_date is not None:
            params["end_date"] = request.end_date.isoformat()
        params.update(self.config.extra_params)
        payload = self._get_json(self.config.base_url, params)
        return self._build_fetch_result(payload)

    def normalize(self, payload: dict[str, Any], request: ConnectorRequest) -> NormalizedDataBatch:
        symbol = request.symbol or payload.get("symbol")
        if symbol is None:
            msg = "US EOD normalization requires a symbol"
            raise ValueError(msg)

        records = payload.get("data") or payload.get("bars") or []
        normalized = [
            NormalizedDailyBarRecord(
                instrument_id=request.instrument_id,
                symbol=symbol,
                market="US",
                currency=str(item.get("currency", "USD")),
                source_route=request.source_route or self.source_route,
                trade_date=self._parse_date(str(item["date"])),
                open=Decimal(str(item["open"])),
                high=Decimal(str(item["high"])),
                low=Decimal(str(item["low"])),
                close=Decimal(str(item["close"])),
                volume=int(item["volume"]),
                turnover_value=self._optional_decimal(item.get("turnover_value")),
                transactions_count=self._optional_int(item.get("transactions_count")),
                change=self._optional_decimal(item.get("change")),
                change_percent=self._optional_decimal(item.get("change_percent")),
            )
            for item in records
        ]
        return NormalizedDataBatch(daily_bars=normalized)

    @staticmethod
    def _parse_date(value: str) -> date:
        return date.fromisoformat(value)

    @staticmethod
    def _optional_decimal(value: Any) -> Decimal | None:
        return Decimal(str(value)) if value is not None else None

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        return int(value) if value is not None else None
