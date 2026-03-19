from datetime import date
from decimal import Decimal

from services.connectors.base import ConnectorRequest
from services.connectors.taifex import TaifexInstitutionalDailyConnector


def test_taifex_connector_normalizes_institutional_row() -> None:
    connector = TaifexInstitutionalDailyConnector()
    payload = {
        "data": [
            {
                "日期": "2024/01/02",
                "市場別": "futures",
                "商品代號": "TX",
                "商品名稱": "臺股期貨",
                "契約": "202401",
                "身份別": "foreign_investors",
                "多方未平倉口數": "12,000",
                "空方未平倉口數": "10,500",
                "多方契約金額": "120,000",
                "空方契約金額": "100,000",
            }
        ]
    }

    batch = connector.normalize(payload, ConnectorRequest(trade_date=date(2024, 1, 2)))

    assert len(batch.tw_derivatives_daily) == 1
    record = batch.tw_derivatives_daily[0]
    assert record.trade_date == date(2024, 1, 2)
    assert record.product_code == "TX"
    assert record.net_open_interest == 1500
    assert record.net_amount == Decimal("20000")
