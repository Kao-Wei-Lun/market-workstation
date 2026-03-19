from datetime import date
from decimal import Decimal

from services.connectors.base import ConnectorRequest
from services.connectors.macro import MacroSeriesConnector
from services.connectors.twse import TwseDailyMarketDataConnector
from services.connectors.us_eod import UsEodConnector


def test_twse_connector_normalizes_daily_bar_payload() -> None:
    connector = TwseDailyMarketDataConnector()
    request = ConnectorRequest(symbol="2330", trade_date=date(2024, 1, 2), instrument_id=1)
    payload = {
        "data": [
            [
                "113/01/02",
                "12,345,678",
                "6,543,210,000",
                "520.00",
                "525.00",
                "518.00",
                "523.00",
                "+3.00",
                "18,765",
            ]
        ]
    }

    batch = connector.normalize(payload, request)

    assert len(batch.daily_bars) == 1
    record = batch.daily_bars[0]
    assert record.trade_date == date(2024, 1, 2)
    assert record.close == Decimal("523.00")
    assert record.volume == 12345678
    assert record.turnover_value == Decimal("6543210000")


def test_us_eod_connector_normalizes_provider_payload() -> None:
    connector = UsEodConnector()
    request = ConnectorRequest(symbol="AAPL", instrument_id=2)
    payload = {
        "data": [
            {
                "date": "2024-01-02",
                "open": "185.64",
                "high": "188.44",
                "low": "183.89",
                "close": "185.14",
                "volume": 82488700,
                "change": "-0.50",
                "change_percent": "-0.27",
            }
        ]
    }

    batch = connector.normalize(payload, request)

    assert len(batch.daily_bars) == 1
    assert batch.daily_bars[0].symbol == "AAPL"
    assert batch.daily_bars[0].market == "US"


def test_macro_connector_normalizes_series_payload() -> None:
    connector = MacroSeriesConnector()
    request = ConnectorRequest(series_key="VIXCLS")
    payload = {"observations": [{"date": "2024-01-02", "value": "14.30"}]}

    batch = connector.normalize(payload, request)

    assert len(batch.series_points) == 1
    assert batch.series_points[0].series_key == "VIXCLS"
    assert batch.series_points[0].value == Decimal("14.30")
