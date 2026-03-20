from __future__ import annotations

from sqlalchemy.orm import Session

from services.models.backtest_run import BacktestRun
from services.models.backtest_search_result import BacktestSearchResult
from services.models.backtest_search_run import BacktestSearchRun
from services.models.backtest_trade import BacktestTrade
from services.models.backtest_walk_forward_run import BacktestWalkForwardRun
from services.models.backtest_walk_forward_window import BacktestWalkForwardWindow
from services.models.strategy import Strategy


class StrategyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        instrument_id: int | None,
        name: str,
        description: str | None,
        definition_json: dict,
    ) -> Strategy:
        strategy = Strategy(
            instrument_id=instrument_id,
            name=name,
            description=description,
            definition_json=definition_json,
        )
        self.session.add(strategy)
        self.session.flush()
        return strategy


class BacktestRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run: BacktestRun) -> BacktestRun:
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, run_id: int) -> BacktestRun | None:
        return self.session.query(BacktestRun).filter(BacktestRun.id == run_id).one_or_none()


class BacktestTradeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(self, trades: list[BacktestTrade]) -> int:
        if not trades:
            return 0
        self.session.add_all(trades)
        self.session.flush()
        return len(trades)

    def list_for_run(self, run_id: int) -> list[BacktestTrade]:
        return (
            self.session.query(BacktestTrade)
            .filter(BacktestTrade.run_id == run_id)
            .order_by(BacktestTrade.entry_date.asc(), BacktestTrade.instrument_id.asc())
            .all()
        )


class BacktestSearchRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run: BacktestSearchRun) -> BacktestSearchRun:
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, run_id: int) -> BacktestSearchRun | None:
        return self.session.query(BacktestSearchRun).filter(BacktestSearchRun.id == run_id).one_or_none()


class BacktestSearchResultRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(self, results: list[BacktestSearchResult]) -> int:
        if not results:
            return 0
        self.session.add_all(results)
        self.session.flush()
        return len(results)

    def list_for_search_run(self, run_id: int) -> list[BacktestSearchResult]:
        return (
            self.session.query(BacktestSearchResult)
            .filter(BacktestSearchResult.search_run_id == run_id)
            .order_by(BacktestSearchResult.rank.asc())
            .all()
        )


class BacktestWalkForwardRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, run: BacktestWalkForwardRun) -> BacktestWalkForwardRun:
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, run_id: int) -> BacktestWalkForwardRun | None:
        return self.session.query(BacktestWalkForwardRun).filter(BacktestWalkForwardRun.id == run_id).one_or_none()


class BacktestWalkForwardWindowRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_many(self, windows: list[BacktestWalkForwardWindow]) -> int:
        if not windows:
            return 0
        self.session.add_all(windows)
        self.session.flush()
        return len(windows)

    def list_for_walk_forward_run(self, run_id: int) -> list[BacktestWalkForwardWindow]:
        return (
            self.session.query(BacktestWalkForwardWindow)
            .filter(BacktestWalkForwardWindow.walk_forward_run_id == run_id)
            .order_by(BacktestWalkForwardWindow.window_index.asc())
            .all()
        )
