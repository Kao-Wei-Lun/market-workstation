from __future__ import annotations

from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
from typing import Any

import httpx

from services.connectors.base import ConnectorRequest, ProviderConnectorConfig, SeriesConnector
from services.schemas.etl import NormalizedDataBatch, NormalizedTwDerivativesDailyRecord


class TaifexInstitutionalDailyConnector(SeriesConnector):
    source_route = "taifex_open_data"
    futures_url = "https://www.taifex.com.tw/enl/eng3/futContractsDate"
    options_url = "https://www.taifex.com.tw/enl/eng3/optContractsDate"

    def __init__(self, config: ProviderConnectorConfig | None = None) -> None:
        config = config or ProviderConnectorConfig(
            provider_name=self.source_route,
            base_url=self.futures_url,
        )
        super().__init__(config)

    def fetch(self, request: ConnectorRequest):
        if request.trade_date is None:
            msg = "TAIFEX connector requires trade_date"
            raise ValueError(msg)

        params = {"queryDate": request.trade_date.strftime("%Y/%m/%d")}
        futures_html = self._get_text(self.futures_url, params)
        options_html = self._get_text(self.options_url, params)
        payload = {
            "rows": [
                *self._extract_rows_from_html(futures_html, market="futures"),
                *self._extract_rows_from_html(options_html, market="options"),
            ]
        }
        return self._build_fetch_result(payload)

    def normalize(self, payload: dict[str, Any], request: ConnectorRequest) -> NormalizedDataBatch:
        rows = payload.get("data") or payload.get("rows") or []
        normalized_rows = [self._normalize_row(row, request) for row in rows]
        return NormalizedDataBatch(tw_derivatives_daily=normalized_rows)

    def _normalize_row(
        self,
        row: dict[str, Any],
        request: ConnectorRequest,
    ) -> NormalizedTwDerivativesDailyRecord:
        trade_date = request.trade_date or self._parse_date(self._get_value(row, "日期", "date"))
        product_code = str(self._get_value(row, "商品代號", "product_code", "commodity_id"))
        product_name = self._optional_str(self._get_value(row, "商品名稱", "product_name", default=None))
        institution = str(self._get_value(row, "身份別", "institution"))
        market = str(self._get_value(row, "市場別", "market", default="futures"))
        contract_period = self._optional_str(
            self._get_value(row, "契約", "contract_period", "contract_month", default=None)
        )
        call_put = self._optional_str(self._get_value(row, "買賣權別", "call_put", default=None))
        long_oi = self._parse_int(self._get_value(row, "多方未平倉口數", "long_open_interest"))
        short_oi = self._parse_int(self._get_value(row, "空方未平倉口數", "short_open_interest"))
        net_oi_raw = self._get_value(row, "淨未平倉口數", "net_open_interest", default=None)
        long_amount = self._parse_optional_decimal(
            self._get_value(row, "多方契約金額", "long_amount", default=None)
        )
        short_amount = self._parse_optional_decimal(
            self._get_value(row, "空方契約金額", "short_amount", default=None)
        )
        net_amount_raw = self._get_value(row, "淨契約金額", "net_amount", default=None)
        market_normalized = market.lower()
        return NormalizedTwDerivativesDailyRecord(
            trade_date=trade_date,
            market=market_normalized,
            product_code=product_code,
            product_name=product_name,
            contract_period=contract_period,
            institution=institution,
            call_put=call_put,
            long_open_interest=long_oi,
            short_open_interest=short_oi,
            net_open_interest=(
                self._parse_int(net_oi_raw) if net_oi_raw is not None else long_oi - short_oi
            ),
            long_amount=long_amount,
            short_amount=short_amount,
            net_amount=(
                self._parse_optional_decimal(net_amount_raw)
                if net_amount_raw is not None
                else self._calculate_net_amount(long_amount, short_amount)
            ),
            source_route=request.source_route or self.source_route,
            is_options=market_normalized == "options",
        )

    @staticmethod
    def _get_value(row: dict[str, Any], *keys: str, default: Any = ...):
        for key in keys:
            if key in row and row[key] not in {"", None}:
                return row[key]
        if default is not ...:
            return default
        msg = f"missing required TAIFEX field from {keys}"
        raise ValueError(msg)

    @staticmethod
    def _parse_date(value: str) -> date:
        normalized = value.replace("/", "-")
        return date.fromisoformat(normalized)

    @staticmethod
    def _parse_int(value: Any) -> int:
        return int(str(value).replace(",", ""))

    @staticmethod
    def _parse_optional_decimal(value: Any) -> Decimal | None:
        if value in {None, "", "--"}:
            return None
        return Decimal(str(value).replace(",", ""))

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        if value in {None, ""}:
            return None
        return str(value)

    @staticmethod
    def _calculate_net_amount(long_amount: Decimal | None, short_amount: Decimal | None) -> Decimal | None:
        if long_amount is None or short_amount is None:
            return None
        return long_amount - short_amount

    def _get_text(self, url: str, params: dict[str, str]) -> str:
        with httpx.Client(timeout=self.config.timeout_seconds) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.text

    def _extract_rows_from_html(self, html: str, *, market: str) -> list[dict[str, Any]]:
        parser = _SimpleHtmlTableParser()
        parser.feed(html)
        rows: list[dict[str, Any]] = []
        for table in parser.tables:
            parsed = self._extract_rows_from_table(table, market=market)
            if parsed:
                rows.extend(parsed)
        return rows

    def _extract_rows_from_table(self, table: list[list[str]], *, market: str) -> list[dict[str, Any]]:
        normalized_table = [[cell.strip() for cell in row] for row in table if any(cell.strip() for cell in row)]
        if not normalized_table:
            return []

        header_index = self._find_header_row_index(normalized_table)
        if header_index is None:
            return []

        headers = normalized_table[header_index]
        if len(headers) < 15:
            return []
        contract_index = self._find_header_index(headers, "contract code", "商品代號")
        item_index = self._find_header_index(headers, "item", "身份別")
        if contract_index is None or item_index is None:
            return []

        extracted_rows: list[dict[str, Any]] = []
        last_contract_code = ""
        for row in normalized_table[header_index + 1 :]:
            if len(row) < max(contract_index, item_index) + 1 or len(row) < 6:
                continue
            contract_code = row[contract_index].strip() or last_contract_code
            last_contract_code = contract_code or last_contract_code
            institution_label = row[item_index].strip()
            institution = self._normalize_institution(institution_label)
            if not contract_code or institution is None:
                continue

            metrics = row[-6:]
            extracted_rows.append(
                {
                    "date": None,
                    "market": market,
                    "product_code": contract_code,
                    "product_name": contract_code,
                    "contract_period": None,
                    "institution": institution,
                    "call_put": None,
                    "long_open_interest": self._parse_int(metrics[0]),
                    "long_amount": self._parse_optional_decimal(metrics[1]),
                    "short_open_interest": self._parse_int(metrics[2]),
                    "short_amount": self._parse_optional_decimal(metrics[3]),
                    "net_open_interest": self._parse_int(metrics[4]),
                    "net_amount": self._parse_optional_decimal(metrics[5]),
                }
            )
        return extracted_rows

    @staticmethod
    def _find_header_row_index(rows: list[list[str]]) -> int | None:
        for index, row in enumerate(rows):
            lower_cells = " ".join(cell.lower() for cell in row[:4])
            if "contract code" in lower_cells and "item" in lower_cells:
                return index
            if "商品代號" in lower_cells and "身份別" in lower_cells:
                return index
        return None

    @staticmethod
    def _find_header_index(headers: list[str], *patterns: str) -> int | None:
        lowered = [header.lower() for header in headers]
        for index, header in enumerate(lowered):
            if any(pattern.lower() in header for pattern in patterns):
                return index
        return None

    @staticmethod
    def _normalize_institution(value: str) -> str | None:
        mapping = {
            "dealers": "dealers",
            "investment trust": "investment_trust",
            "fini": "foreign_investors",
        }
        return mapping.get(value.lower())


class _SimpleHtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag == "table":
            self._current_table = []
            return
        if self._current_table is None:
            return
        if tag == "tr":
            self._current_row = []
            return
        if tag in {"td", "th"}:
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._current_cell is not None and self._current_row is not None:
            self._current_row.append(" ".join(part.strip() for part in self._current_cell if part.strip()))
            self._current_cell = None
            return
        if tag == "tr" and self._current_table is not None and self._current_row is not None:
            if self._current_row:
                self._current_table.append(self._current_row)
            self._current_row = None
            return
        if tag == "table" and self._current_table is not None:
            if self._current_table:
                self.tables.append(self._current_table)
            self._current_table = None
