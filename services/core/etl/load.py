from __future__ import annotations

from sqlalchemy.orm import Session

from services.db.repositories.daily_bars import DailyBarRepository
from services.db.repositories.series_points import SeriesPointRepository
from services.db.repositories.tw_derivatives import TwDerivativesDailyRepository
from services.schemas.etl import LoadResult, NormalizedDataBatch


def load_normalized_batch(
    session: Session,
    batch: NormalizedDataBatch,
    *,
    daily_bar_repository: DailyBarRepository | None = None,
    series_point_repository: SeriesPointRepository | None = None,
    tw_derivatives_daily_repository: TwDerivativesDailyRepository | None = None,
) -> LoadResult:
    daily_repo = daily_bar_repository or DailyBarRepository(session)
    series_repo = series_point_repository or SeriesPointRepository(session)
    derivatives_repo = tw_derivatives_daily_repository or TwDerivativesDailyRepository(session)
    daily_bars_loaded = daily_repo.upsert_many(batch.daily_bars)
    series_points_loaded = series_repo.upsert_many(batch.series_points)
    tw_derivatives_daily_loaded = derivatives_repo.upsert_many(batch.tw_derivatives_daily)
    session.flush()
    return LoadResult(
        daily_bars_loaded=daily_bars_loaded,
        series_points_loaded=series_points_loaded,
        tw_derivatives_daily_loaded=tw_derivatives_daily_loaded,
    )
