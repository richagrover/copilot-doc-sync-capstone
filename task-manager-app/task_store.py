from __future__ import annotations

from pathlib import Path

from db import connection, utc_now

STATUSES = ("todo", "in_progress", "done")
PRIORITIES = ("low", "medium", "high")


def create_task(
    database_path: str | Path,
    user_id: int,
    *,
    title: str,
    description: str,
    status: str,
    priority: str,
) -> int:
    now = utc_now()
    with connection(database_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (user_id, title, description, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, description, status, priority, now, now),
        )
        return int(cursor.lastrowid)


def get_task(
    database_path: str | Path, user_id: int, task_id: int
) -> dict[str, int | str] | None:
    with connection(database_path) as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        ).fetchone()
        return dict(row) if row is not None else None


def list_tasks(
    database_path: str | Path,
    user_id: int,
    *,
    status: str | None = None,
    priority: str | None = None,
) -> list[dict[str, int | str]]:
    conditions = ["user_id = ?"]
    values: list[int | str] = [user_id]
    if status is not None:
        conditions.append("status = ?")
        values.append(status)
    if priority is not None:
        conditions.append("priority = ?")
        values.append(priority)

    query = (
        "SELECT * FROM tasks WHERE "
        + " AND ".join(conditions)
        + " ORDER BY created_at DESC, id DESC"
    )

    with connection(database_path) as conn:
        rows = conn.execute(query, values).fetchall()
        return [dict(row) for row in rows]


def update_task(
    database_path: str | Path,
    user_id: int,
    task_id: int,
    *,
    title: str,
    description: str,
    status: str,
    priority: str,
) -> bool:
    with connection(database_path) as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, status = ?, priority = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (title, description, status, priority, utc_now(), task_id, user_id),
        )
        return cursor.rowcount == 1


def delete_task(database_path: str | Path, user_id: int, task_id: int) -> bool:
    with connection(database_path) as conn:
        cursor = conn.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        )
        return cursor.rowcount == 1
