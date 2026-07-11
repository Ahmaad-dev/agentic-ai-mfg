"""
PT4 Persistence Layer — engine & session factory (AP2).

The database backend is selected purely via the `DATABASE_URL` connection string
(AP2.4). Local development defaults to a SQLite file; the Azure SQL target is
enabled simply by providing an `mssql+pyodbc://...` URL — typically injected from
Key Vault as an environment variable in production (12-factor style).

Env vars:
    DATABASE_URL   Full SQLAlchemy connection string. If unset, a local SQLite
                   file (demo/db/pt4.sqlite3) is used.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from .models import Base

load_dotenv()

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_database_url() -> str:
    """
    Resolve the DB connection string.

    Priority:
    1. DATABASE_URL env var (Azure SQL in prod, injected from Key Vault).
    2. Local SQLite fallback (demo/db/pt4.sqlite3).
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    db_path = Path(__file__).parent / "pt4.sqlite3"
    return f"sqlite:///{db_path.as_posix()}"


def get_engine() -> Engine:
    """Return a lazily-created singleton SQLAlchemy engine."""
    global _engine
    if _engine is None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True, future=True)
    return _engine


def get_sessionmaker() -> sessionmaker:
    """Return a lazily-created singleton session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, expire_on_commit=False, future=True
        )
    return _SessionLocal


def init_db() -> None:
    """
    Create all tables directly from the ORM metadata.

    Convenience for local/tests; production uses Alembic migrations.
    """
    Base.metadata.create_all(bind=get_engine())
