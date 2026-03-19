from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from config.settings import get_settings
from services.connectors.base import ConnectorRequest, ProviderConnectorConfig, SeriesConnector
from services.schemas.etl import NormalizedDataBatch, NormalizedSeriesPointRecord


class MacroSeriesConnector(SeriesConnector):
    source_route = "macro_series_provider"

    def __init__(self, config: ProviderConnectorConfig | None = None) -> None:
        if config is None:
            settings = get_settings()
            config = ProviderConnectorConfig(
                provider_name=settings.macro_provider,
                base_url=settings.macro_base_url,
                api_key=settings.macro_api_key,
            )
        super().__init__(config)

    def fetch(self, request: ConnectorRequest):
        if request.series_key is None:
            msg = "Macro connector requires series_key"
            raise ValueError(msg)
        if self.config.base_url is None:
            msg = "Macro base_url is required for live fetches"
            raise ValueError(msg)

        params = {
            "series": request.series_key,
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
        series_key = request.series_key or payload.get("series_key")
        if series_key is None:
            msg = "Macro normalization requires series_key"
            raise ValueError(msg)

        observations = payload.get("data") or payload.get("observations") or []
        normalized = [
            NormalizedSeriesPointRecord(
                instrument_id=request.instrument_id,
                series_key=series_key,
                source_route=request.source_route or self.source_route,
                trade_date=date.fromisoformat(str(item["date"])),
                value=Decimal(str(item["value"])),
            )
            for item in observations
        ]
        return NormalizedDataBatch(series_points=normalized)
