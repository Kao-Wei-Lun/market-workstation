from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from services.connectors.base import ConnectorRequest, DailyBarConnector
from services.schemas.etl import NormalizedDailyBarRecord, NormalizedDataBatch


class TwseDailyMarketDataConnector(DailyBarConnector):
    source_route = "twse_openapi"
    base_url = "https://www.twse.com.tw/exchangeReport/STOCK_DAY"

    def fetch(self, request: ConnectorRequest):
        if request.symbol is None or request.trade_date is None:
            msg = "TWSE connector requires symbol and trade_date"
            raise ValueError(msg)

        month_anchor = request.trade_date.replace(day=1).strftime("%Y%m%d")
        params = {"response": "json", "date": month_anchor, "stockNo": request.symbol}
        payload = self._get_json(self.base_url, params)
        return self._build_fetch_result(payload)

    def normalize(self, payload: dict[str, Any], request: ConnectorRequest) -> NormalizedDataBatch:
        if request.symbol is None or request.trade_date is None:
            msg = "TWSE normalization requires symbol and trade_date"
            raise ValueError(msg)

        rows = payload.get("data", [])
        normalized_rows = [
            self._normalize_row(row=row, request=request)
            for row in rows
            if self._parse_twse_trade_date(row[0]) == request.trade_date
        ]
        return NormalizedDataBatch(daily_bars=normalized_rows)

    def _normalize_row(self, row: list[str], request: ConnectorRequest) -> NormalizedDailyBarRecord:
        if request.symbol is None:
            msg = "TWSE normalization requires symbol"
            raise ValueError(msg)

        return NormalizedDailyBarRecord(
            instrument_id=request.instrument_id,
            symbol=request.symbol,
            market="TW",
            currency="TWD",
            source_route=request.source_route or self.source_route,
            trade_date=self._parse_twse_trade_date(row[0]),
            open=self._parse_required_decimal(row[3], "open"),
            high=self._parse_required_decimal(row[4], "high"),
            low=self._parse_required_decimal(row[5], "low"),
            close=self._parse_required_decimal(row[6], "close"),
            volume=self._parse_required_int(row[1], "volume"),
            turnover_value=self._parse_decimal(row[2]),
            transactions_count=self._parse_int(row[8]),
            change=self._parse_change(row[7]),
            change_percent=None,
        )

    @staticmethod
    def _parse_twse_trade_date(value: str) -> date:
        roc_year, month, day = value.split("/")
        return date(int(roc_year) + 1911, int(month), int(day))

    @staticmethod
    def _parse_decimal(value: str) -> Decimal | None:
        cleaned = value.replace(",", "").strip()
        if cleaned in {"", "--", "X0.00"}:
            return None
        return Decimal(cleaned)

    @staticmethod
    def _parse_int(value: str) -> int | None:
        parsed = TwseDailyMarketDataConnector._parse_decimal(value)
        return int(parsed) if parsed is not None else None

    @staticmethod
    def _parse_required_decimal(value: str, field_name: str) -> Decimal:
        parsed = TwseDailyMarketDataConnector._parse_decimal(value)
        if parsed is None:
            msg = f"TWSE field {field_name} is required"
            raise ValueError(msg)
        return parsed

    @staticmethod
    def _parse_required_int(value: str, field_name: str) -> int:
        parsed = TwseDailyMarketDataConnector._parse_int(value)
        if parsed is None:
            msg = f"TWSE field {field_name} is required"
            raise ValueError(msg)
        return parsed

    @staticmethod
    def _parse_change(value: str) -> Decimal | None:
        cleaned = value.replace(",", "").replace("X", "").strip()
        if cleaned in {"", "--"}:
            return None
        return Decimal(cleaned)
