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


def test_taifex_connector_extracts_rows_from_html_tables() -> None:
    connector = TaifexInstitutionalDailyConnector()
    html = """
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Contract Code</th>
          <th>Item</th>
          <th>Ignore 1</th>
          <th>Ignore 2</th>
          <th>Ignore 3</th>
          <th>Ignore 4</th>
          <th>Ignore 5</th>
          <th>Ignore 6</th>
          <th>Long OI</th>
          <th>Long Amount</th>
          <th>Short OI</th>
          <th>Short Amount</th>
          <th>Net OI</th>
          <th>Net Amount</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>2024/01/02</td>
          <td>TX</td>
          <td>FINI</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>12,000</td>
          <td>120,000</td>
          <td>10,500</td>
          <td>100,000</td>
          <td>1,500</td>
          <td>20,000</td>
        </tr>
        <tr>
          <td>2024/01/02</td>
          <td>TXO</td>
          <td>Dealers</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>8,000</td>
          <td>70,000</td>
          <td>5,000</td>
          <td>30,000</td>
          <td>3,000</td>
          <td>40,000</td>
        </tr>
      </tbody>
    </table>
    """

    rows = connector._extract_rows_from_html(html, market="futures")

    assert len(rows) == 2
    assert rows[0]["product_code"] == "TX"
    assert rows[0]["institution"] == "foreign_investors"
    assert rows[0]["net_open_interest"] == 1500
    assert rows[1]["product_code"] == "TXO"
    assert rows[1]["institution"] == "dealers"


def test_taifex_connector_returns_empty_rows_when_html_has_no_tables() -> None:
    connector = TaifexInstitutionalDailyConnector()

    rows = connector._extract_rows_from_html("<html><body>No data</body></html>", market="options")

    assert rows == []
