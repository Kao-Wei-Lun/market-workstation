from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from services.connectors.base import ConnectorRequest, DailyBarConnector
from services.schemas.etl import NormalizedDailyBarRecord, NormalizedDataBatch


class StaticDailyBarConnector(DailyBarConnector):
    source_route = "local_seed"

    def __init__(
        self,
        *,
        payload: dict[str, Any],
        market: str,
        currency: str,
    ) -> None:
        super().__init__()
        self._payload = payload
        self._market = market
        self._currency = currency

    def fetch(self, request: ConnectorRequest):
        return self._build_fetch_result(self._payload)

    def normalize(self, payload: dict[str, Any], request: ConnectorRequest) -> NormalizedDataBatch:
        if request.symbol is None:
            msg = "static daily bar connector requires symbol"
            raise ValueError(msg)

        rows = [
            NormalizedDailyBarRecord(
                instrument_id=request.instrument_id,
                symbol=request.symbol,
                market=self._market,
                currency=self._currency,
                source_route=request.source_route or self.source_route,
                trade_date=date.fromisoformat(str(item["trade_date"])),
                open=Decimal(str(item["open"])),
                high=Decimal(str(item["high"])),
                low=Decimal(str(item["low"])),
                close=Decimal(str(item["close"])),
                volume=int(item["volume"]),
                turnover_value=Decimal(str(item["turnover_value"])) if item.get("turnover_value") is not None else None,
                transactions_count=int(item["transactions_count"])
                if item.get("transactions_count") is not None
                else None,
                change=Decimal(str(item["change"])) if item.get("change") is not None else None,
                change_percent=Decimal(str(item["change_percent"]))
                if item.get("change_percent") is not None
                else None,
            )
            for item in payload.get("data", [])
        ]
        return NormalizedDataBatch(daily_bars=rows)
