from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from services.connectors.base import ConnectorRequest, ProviderConnectorConfig, SeriesConnector
from services.schemas.etl import NormalizedDataBatch, NormalizedTwDerivativesDailyRecord


class TaifexInstitutionalDailyConnector(SeriesConnector):
    source_route = "taifex_open_data"

    def __init__(self, config: ProviderConnectorConfig | None = None) -> None:
        config = config or ProviderConnectorConfig(
            provider_name=self.source_route,
            base_url="https://www.taifex.com.tw/cht/3/futContractsDate",
        )
        super().__init__(config)

    def fetch(self, request: ConnectorRequest):
        if request.trade_date is None:
            msg = "TAIFEX connector requires trade_date"
            raise ValueError(msg)
        if self.config.base_url is None:
            msg = "TAIFEX base_url is required"
            raise ValueError(msg)

        params = {"queryDate": request.trade_date.strftime("%Y/%m/%d")}
        payload = self._get_json(self.config.base_url, params)
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
