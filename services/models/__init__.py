"""ORM model registry."""

from services.models.daily_bar import DailyBar
from services.models.ingest_job import IngestJob
from services.models.instrument import Instrument


def import_models() -> None:
    """Import model modules so SQLAlchemy metadata is fully populated."""


__all__ = ["DailyBar", "IngestJob", "Instrument", "import_models"]
