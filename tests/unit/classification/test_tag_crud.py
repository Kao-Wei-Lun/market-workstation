from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from services.core.classification.tags import add_tag_to_instrument, list_tags_for_instrument, remove_tag_from_instrument
from services.db.base import Base
from services.models import import_models
from services.models.instrument import Instrument


def _build_session() -> Session:
    import_models()
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    return session_factory()


def test_tag_crud_round_trip() -> None:
    session = _build_session()
    instrument = Instrument(
        symbol="2330",
        name="TSMC",
        market="TW",
        asset_type="stock",
        currency="TWD",
        timezone="Asia/Taipei",
        source_route="twse_openapi",
    )
    session.add(instrument)
    session.flush()

    add_tag_to_instrument(session, instrument_id=instrument.id, tag="Semiconductor")
    tags = list_tags_for_instrument(session, instrument_id=instrument.id)
    removed = remove_tag_from_instrument(session, instrument_id=instrument.id, tag="semiconductor")

    assert [tag.tag for tag in tags] == ["semiconductor"]
    assert removed is True
    assert list_tags_for_instrument(session, instrument_id=instrument.id) == []
