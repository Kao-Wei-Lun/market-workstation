from __future__ import annotations

from sqlalchemy.orm import Session

from services.models.backtest_run import BacktestRun
from services.models.backtest_trade import BacktestTrade
from services.models.strategy import Strategy


class StrategyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        instrument_id: int,
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
            .order_by(BacktestTrade.entry_date.asc())
            .all()
        )
