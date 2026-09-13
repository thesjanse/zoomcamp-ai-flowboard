"""Database wiring for the application.

A single SQLAlchemy ``engine`` is created from ``config.DATABASE_URL`` so the
data layer is database-agnostic (SQLite today, Postgres later — just change
the URL).  ``Base.metadata.create_all()`` creates the schema on startup; no
migration tooling is used yet.
"""

from __future__ import annotations

import datetime

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.types import DateTime, TypeDecorator

from . import config


class Base(DeclarativeBase):
    pass


class TZDateTime(TypeDecorator[datetime.datetime]):
    """Store datetimes as naive UTC; return timezone-aware UTC datetimes.

    SQLite has no timezone support, so we persist a normalized naive UTC
    timestamp and re-attach ``timezone.utc`` when a row is read.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime.datetime | None, dialect) -> datetime.datetime | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value: datetime.datetime | None, dialect) -> datetime.datetime | None:
        if value is None:
            return None
        return value.replace(tzinfo=datetime.timezone.utc)


_engine: Engine | None = None


def get_engine() -> Engine:
    """Return the process-wide engine, created lazily from ``DATABASE_URL``."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            config.DATABASE_URL,
            connect_args={"check_same_thread": False}
            if config.DATABASE_URL.startswith("sqlite")
            else {},
        )
    return _engine


def new_session(engine: Engine | None = None) -> Session:
    return Session(bind=engine or get_engine())


def init_db(engine: Engine | None = None) -> None:
    Base.metadata.create_all(bind=engine or get_engine())