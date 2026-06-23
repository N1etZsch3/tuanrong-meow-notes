from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

engine: Engine | None = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def get_engine() -> Engine:
    global engine
    if engine is None:
        engine = create_engine(get_settings().required_database_url, pool_pre_ping=True)
    return engine


def configure_session() -> None:
    session_options = getattr(SessionLocal, "kw", {})
    if session_options.get("bind") is None and hasattr(SessionLocal, "configure"):
        SessionLocal.configure(bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    configure_session()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
