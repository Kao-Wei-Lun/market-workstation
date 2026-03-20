"""ORM model registry."""

from services.models.auto_classification_rule import AutoClassificationRule
from services.models.backtest_run import BacktestRun
from services.models.backtest_search_result import BacktestSearchResult
from services.models.backtest_search_run import BacktestSearchRun
from services.models.backtest_trade import BacktestTrade
from services.models.backtest_walk_forward_run import BacktestWalkForwardRun
from services.models.backtest_walk_forward_window import BacktestWalkForwardWindow
from services.models.candidate_item import CandidateItem
from services.models.candidate_run import CandidateRun
from services.models.chart_annotation import ChartAnnotation
from services.models.daily_bar import DailyBar
from services.models.indicator_value import IndicatorValue
from services.models.ingest_job import IngestJob
from services.models.instrument import Instrument
from services.models.instrument_tag import InstrumentTag
from services.models.report_daily import ReportDaily
from services.models.series_point import SeriesPoint
from services.models.strategy import Strategy
from services.models.tw_derivatives_daily import TwDerivativesDaily
from services.models.tw_derivatives_feature import TwDerivativesFeature
from services.models.tw_institutional_spot_daily import TwInstitutionalSpotDaily
from services.models.watchlist import Watchlist
from services.models.watchlist_item import WatchlistItem
from services.models.worker_health import WorkerHealth


def import_models() -> None:
    """Import model modules so SQLAlchemy metadata is fully populated."""


__all__ = [
    "AutoClassificationRule",
    "BacktestRun",
    "BacktestSearchResult",
    "BacktestSearchRun",
    "BacktestTrade",
    "BacktestWalkForwardRun",
    "BacktestWalkForwardWindow",
    "CandidateItem",
    "CandidateRun",
    "ChartAnnotation",
    "DailyBar",
    "IndicatorValue",
    "IngestJob",
    "Instrument",
    "InstrumentTag",
    "ReportDaily",
    "SeriesPoint",
    "Strategy",
    "TwDerivativesDaily",
    "TwDerivativesFeature",
    "TwInstitutionalSpotDaily",
    "Watchlist",
    "WatchlistItem",
    "WorkerHealth",
    "import_models",
]
