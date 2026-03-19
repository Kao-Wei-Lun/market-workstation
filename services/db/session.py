from collections.abc import AsyncGenerator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from config.settings import get_settings


def create_db_engine(database_uri: str | None = None) -> Engine:
    settings = get_settings()
    return create_engine(
        database_uri or settings.sqlalchemy_database_uri,
        pool_pre_ping=True,
    )


def create_session_factory(bind: Engine | None = None) -> sessionmaker[Session]:
    return sessionmaker(bind=bind or engine, autoflush=False, autocommit=False, class_=Session)


engine = create_db_engine()
SessionLocal = create_session_factory(engine)


async def get_db_session() -> AsyncGenerator[Session, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
