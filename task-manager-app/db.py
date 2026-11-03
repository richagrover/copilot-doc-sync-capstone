from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


@contextmanager
def connection(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    with closing(sqlite3.connect(str(database_path), timeout=5)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        with conn:
            yield conn


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def initialize_database(database_path: str | Path) -> None:
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    with connection(database_path) as conn:
        _drop_legacy_single_user_schema(conn)
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT NOT NULL UNIQUE
                              CHECK(length(trim(username)) BETWEEN 3 AND 50),
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS sessions (
                token_hash  TEXT PRIMARY KEY,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                created_at  TEXT NOT NULL,
                expires_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title       TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 200),
                description TEXT NOT NULL DEFAULT '',
                status      TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'done')),
                priority    TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')),
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_user ON tasks(user_id, status, priority);
            """
        )


def _drop_legacy_single_user_schema(conn: sqlite3.Connection) -> None:
    """Drop a pre-multi-user tasks table (no user_id column); local data is disposable."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
    if columns and "user_id" not in columns:
        conn.execute("DROP TABLE tasks")
