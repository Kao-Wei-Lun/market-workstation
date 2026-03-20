from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from services.connectors.base import ConnectorRequest, DailyBarConnector
from services.schemas.etl import NormalizedDailyBarRecord, NormalizedDataBatch


class TwseIndexDailyConnector(DailyBarConnector):
    source_route = "twse_index_openapi"
    base_url = "https://www.twse.com.tw/en/indicesReport/MI_5MINS_HIST"

    def fetch(self, request: ConnectorRequest):
        if request.trade_date is None:
            msg = "TWSE index connector requires trade_date"
            raise ValueError(msg)

        params = {"response": "json", "date": request.trade_date.strftime("%Y%m%d")}
        payload = self._get_json(self.base_url, params)
        return self._build_fetch_result(payload)

    def normalize(self, payload: dict[str, Any], request: ConnectorRequest) -> NormalizedDataBatch:
        if request.trade_date is None:
            msg = "TWSE index normalization requires trade_date"
            raise ValueError(msg)

        fields = [str(item) for item in payload.get("fields") or []]
        rows = payload.get("data") or []
        if not rows:
            return NormalizedDataBatch()

        indices = {
            "date": self._find_field_index(fields, "date", "日期"),
            "open": self._find_field_index(fields, "open index", "open", "開盤"),
            "high": self._find_field_index(fields, "highest index", "high index", "high", "最高"),
            "low": self._find_field_index(fields, "lowest index", "low index", "low", "最低"),
            "close": self._find_field_index(fields, "closing index", "close index", "close", "收盤"),
            "volume": self._find_field_index(fields, "volume", "成交股數", "成交量"),
            "turnover": self._find_field_index(fields, "value", "成交金額"),
        }
        required = ("date", "open", "high", "low", "close")
        if any(indices[key] is None for key in required):
            msg = "TWSE index payload does not contain required OHLC fields"
            raise ValueError(msg)

        normalized_rows = [
            self._normalize_row(row, request=request, field_indices=indices)
            for row in rows
            if self._parse_date(str(row[indices["date"]])) == request.trade_date
        ]
        return NormalizedDataBatch(daily_bars=normalized_rows)

    def _normalize_row(
        self,
        row: list[str],
        *,
        request: ConnectorRequest,
        field_indices: dict[str, int | None],
    ) -> NormalizedDailyBarRecord:
        symbol = request.symbol or "^TWII"
        trade_date = self._parse_date(str(row[self._require_index(field_indices, "date")]))
        return NormalizedDailyBarRecord(
            instrument_id=request.instrument_id,
            symbol=symbol,
            market="TW",
            currency="TWD",
            source_route=request.source_route or self.source_route,
            trade_date=trade_date,
            open=self._parse_required_decimal(row[self._require_index(field_indices, "open")], "open"),
            high=self._parse_required_decimal(row[self._require_index(field_indices, "high")], "high"),
            low=self._parse_required_decimal(row[self._require_index(field_indices, "low")], "low"),
            close=self._parse_required_decimal(row[self._require_index(field_indices, "close")], "close"),
            volume=self._parse_int_from_index(row, field_indices["volume"]) or 0,
            turnover_value=self._parse_decimal_from_index(row, field_indices["turnover"]),
            change=self._optional_decimal(self._extract_change_value(row)),
            change_percent=None,
        )

    @staticmethod
    def _find_field_index(fields: list[str], *patterns: str) -> int | None:
        lowered = [field.lower() for field in fields]
        for index, field in enumerate(lowered):
            if any(pattern.lower() in field for pattern in patterns):
                return index
        return None

    @staticmethod
    def _require_index(indices: dict[str, int | None], key: str) -> int:
        index = indices[key]
        if index is None:
            msg = f"missing required field index: {key}"
            raise ValueError(msg)
        return index

    @staticmethod
    def _parse_date(value: str) -> date:
        normalized = value.strip()
        if "/" in normalized:
            year, month, day = normalized.split("/")
            if len(year) == 3:
                return date(int(year) + 1911, int(month), int(day))
            return date(int(year), int(month), int(day))
        return date.fromisoformat(normalized)

    @staticmethod
    def _parse_required_decimal(value: str, field_name: str) -> Decimal:
        parsed = TwseIndexDailyConnector._optional_decimal(value)
        if parsed is None:
            msg = f"TWSE index field {field_name} is required"
            raise ValueError(msg)
        return parsed

    @staticmethod
    def _optional_decimal(value: Any) -> Decimal | None:
        cleaned = str(value).replace(",", "").replace("X", "").strip()
        if cleaned in {"", "--", "None"}:
            return None
        return Decimal(cleaned)

    @staticmethod
    def _parse_decimal_from_index(row: list[str], index: int | None) -> Decimal | None:
        if index is None or index >= len(row):
            return None
        return TwseIndexDailyConnector._optional_decimal(row[index])

    @staticmethod
    def _parse_int_from_index(row: list[str], index: int | None) -> int | None:
        parsed = TwseIndexDailyConnector._parse_decimal_from_index(row, index)
        return int(parsed) if parsed is not None else None

    @staticmethod
    def _extract_change_value(row: list[str]) -> str | None:
        if len(row) < 2:
            return None
        for value in reversed(row):
            cleaned = str(value).replace(",", "").replace("X", "").strip()
            if cleaned.startswith(("+", "-")):
                return cleaned
        return None
