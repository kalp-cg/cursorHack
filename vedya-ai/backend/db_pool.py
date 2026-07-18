"""Thread-safe Postgres connection pool for async FastAPI + sync psycopg2."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
from psycopg2 import pool
from fastapi import HTTPException

_pool: Optional[pool.ThreadedConnectionPool] = None


def init_pool(dsn: str | None = None, minconn: int = 1, maxconn: int = 8) -> None:
    global _pool
    url = dsn or os.getenv("DATABASE_URL", "postgresql://vedya:vedyapass@localhost:5433/vedyaai")
    if _pool is not None:
        return
    _pool = pool.ThreadedConnectionPool(minconn, maxconn, url)


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None


def pool_ready() -> bool:
    return _pool is not None


@contextmanager
def get_connection() -> Generator:
    if _pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        try:
            # Always return a clean connection to the pool
            if conn.closed == 0:
                conn.rollback()
        except Exception:
            pass
        _pool.putconn(conn)


def get_db():
    """FastAPI dependency — yields a connection checked out from the pool."""
    if _pool is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        try:
            if conn.closed == 0:
                conn.rollback()
        except Exception:
            pass
        _pool.putconn(conn)
