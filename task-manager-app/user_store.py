from __future__ import annotations

import sqlite3
from pathlib import Path

from db import connection, utc_now

USERNAME_MIN = 3
USERNAME_MAX = 50
PASSWORD_MIN = 8


def create_user(database_path: str | Path, *, username: str, password_hash: str) -> int | None:
    """Insert a user; returns the new id, or None if the username is taken."""
    try:
        with connection(database_path) as conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                (username, password_hash, utc_now()),
            )
            return int(cursor.lastrowid)
    except sqlite3.IntegrityError:
        return None


def find_by_username(database_path: str | Path, username: str) -> dict[str, int | str] | None:
    with connection(database_path) as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row is not None else None


def get_user(database_path: str | Path, user_id: int) -> dict[str, int | str] | None:
    with connection(database_path) as conn:
        row = conn.execute(
            "SELECT id, username, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row is not None else None
