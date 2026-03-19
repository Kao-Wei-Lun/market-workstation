"""ORM model registry."""

from services.models.backtest_run import BacktestRun
from services.models.backtest_trade import BacktestTrade
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.ingest_job import IngestJob
from services.models.instrument import Instrument
from services.models.series_point import SeriesPoint
from services.models.strategy import Strategy
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature


def import_models() -> None:
    """Import model modules so SQLAlchemy metadata is fully populated."""


__all__ = [
    "BacktestRun",
    "BacktestTrade",
    "DailyBar",
    "IndicatorValue",
    "IngestJob",
    "Instrument",
    "SeriesPoint",
    "Strategy",
    "TwDerivativesDaily",
    "TwDerivativesFeature",
    "import_models",
]
