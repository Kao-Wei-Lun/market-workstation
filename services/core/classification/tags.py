from __future__ import annotations

from sqlalchemy.orm import Session

from services.models.instrument_tag import InstrumentTag


def add_tag_to_instrument(session: Session, *, instrument_id: int, tag: str) -> InstrumentTag:
    normalized_tag = tag.strip().lower()
    existing = (
        session.query(InstrumentTag)
        .filter(InstrumentTag.instrument_id == instrument_id, InstrumentTag.tag == normalized_tag)
        .one_or_none()
    )
    if existing is not None:
        return existing
    instrument_tag = InstrumentTag(instrument_id=instrument_id, tag=normalized_tag)
    session.add(instrument_tag)
    session.flush()
    return instrument_tag


def remove_tag_from_instrument(session: Session, *, instrument_id: int, tag: str) -> bool:
    normalized_tag = tag.strip().lower()
    existing = (
        session.query(InstrumentTag)
        .filter(InstrumentTag.instrument_id == instrument_id, InstrumentTag.tag == normalized_tag)
        .one_or_none()
    )
    if existing is None:
        return False
    session.delete(existing)
    session.flush()
    return True


def list_tags_for_instrument(session: Session, *, instrument_id: int) -> list[InstrumentTag]:
    return (
        session.query(InstrumentTag)
        .filter(InstrumentTag.instrument_id == instrument_id)
        .order_by(InstrumentTag.tag.asc())
        .all()
    )
