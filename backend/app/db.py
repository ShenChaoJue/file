from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.config import get_settings

class Base(DeclarativeBase): pass

def make_engine():
    settings = get_settings(); args = {"check_same_thread": False} if settings.resolved_database_url.startswith("sqlite") else {}
    return create_engine(settings.resolved_database_url, connect_args=args)
engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try: yield db
    finally: db.close()

def init_db() -> None:
    from app import models  # noqa
    Base.metadata.create_all(bind=engine)
