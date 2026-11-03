from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from db import connection, utc_now

SESSION_TTL = timedelta(days=7)


def create_session(database_path: str | Path, user_id: int) -> str:
    """Create a server-side session record and return the opaque client token."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + SESSION_TTL).isoformat(timespec="microseconds")
    with connection(database_path) as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_hash_token(token), user_id, utc_now(), expires_at),
        )
    return token


def resolve_session(database_path: str | Path, token: str) -> int | None:
    """Return the session's user id if the token is valid and unexpired."""
    with connection(database_path) as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (utc_now(),))
        row = conn.execute(
            "SELECT user_id FROM sessions WHERE token_hash = ?",
            (_hash_token(token),),
        ).fetchone()
        return int(row["user_id"]) if row is not None else None


def delete_session(database_path: str | Path, token: str) -> None:
    with connection(database_path) as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
