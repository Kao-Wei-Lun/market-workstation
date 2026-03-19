from __future__ import annotations

from sqlalchemy.orm import Session

from services.db.repositories.daily_bars import DailyBarRepository
from services.db.repositories.series_points import SeriesPointRepository
from services.schemas.etl import LoadResult, NormalizedDataBatch


def load_normalized_batch(
    session: Session,
    batch: NormalizedDataBatch,
    *,
    daily_bar_repository: DailyBarRepository | None = None,
    series_point_repository: SeriesPointRepository | None = None,
) -> LoadResult:
    daily_repo = daily_bar_repository or DailyBarRepository(session)
    series_repo = series_point_repository or SeriesPointRepository(session)
    daily_bars_loaded = daily_repo.upsert_many(batch.daily_bars)
    series_points_loaded = series_repo.upsert_many(batch.series_points)
    session.flush()
    return LoadResult(
        daily_bars_loaded=daily_bars_loaded,
        series_points_loaded=series_points_loaded,
    )
