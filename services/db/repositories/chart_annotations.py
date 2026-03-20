from __future__ import annotations

from sqlalchemy.orm import Session

from services.models.chart_annotation import ChartAnnotation
from services.schemas.charts import ChartAnnotationCreate


class ChartAnnotationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_instrument(
        self,
        instrument_id: int,
        *,
        view_kind: str,
    ) -> list[ChartAnnotation]:
        return (
            self.session.query(ChartAnnotation)
            .filter(
                ChartAnnotation.instrument_id == instrument_id,
                ChartAnnotation.view_kind == view_kind,
            )
            .order_by(ChartAnnotation.created_at.asc(), ChartAnnotation.id.asc())
            .all()
        )

    def create(
        self,
        *,
        instrument_id: int,
        symbol_snapshot: str,
        payload: ChartAnnotationCreate,
    ) -> ChartAnnotation:
        annotation = ChartAnnotation(
            instrument_id=instrument_id,
            symbol_snapshot=symbol_snapshot,
            view_kind=payload.view_kind,
            annotation_type=payload.annotation_type,
            timeframe=payload.timeframe,
            label=payload.label,
            payload_json=payload.payload_json,
        )
        self.session.add(annotation)
        self.session.flush()
        return annotation

    def get(self, annotation_id: int) -> ChartAnnotation | None:
        return self.session.query(ChartAnnotation).filter(ChartAnnotation.id == annotation_id).one_or_none()

    def delete(self, annotation: ChartAnnotation) -> None:
        self.session.delete(annotation)
        self.session.flush()

    def clear_for_instrument(self, instrument_id: int, *, view_kind: str) -> int:
        deleted = (
            self.session.query(ChartAnnotation)
            .filter(
                ChartAnnotation.instrument_id == instrument_id,
                ChartAnnotation.view_kind == view_kind,
            )
            .delete(synchronize_session=False)
        )
        self.session.flush()
        return int(deleted)
