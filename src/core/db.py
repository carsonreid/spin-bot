import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from src.core.config import settings


def _ensure_db_directory() -> None:
    db_dir = os.path.dirname(settings.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def init_db() -> None:
    _ensure_db_directory()
    with sqlite3.connect(settings.db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS booking_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT NOT NULL,
                studio_name TEXT,
                weekday INTEGER NOT NULL CHECK(weekday BETWEEN 0 AND 6),
                start_time TEXT NOT NULL,
                week_offset INTEGER NOT NULL DEFAULT 1,
                active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0, 1)),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    _ensure_db_directory()
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
