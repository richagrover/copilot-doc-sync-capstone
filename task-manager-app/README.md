# Task Manager

A multi-user task manager built with Flask and SQLite. Users register with a local
username/password, sign in to a server-side session, and manage their own isolated
task list. Tasks have a status and priority and can be filtered by either or both.

## Features

- Local account registration and sign-in (passwords stored as salted hashes)
- Server-side sessions: opaque tokens stored hashed in SQLite, 7-day expiry, rotation on login
- Per-user task isolation — users can only see and modify their own tasks
- Task CRUD with status (`todo`, `in_progress`, `done`) and priority (`low`, `medium`, `high`)
- Combinable status/priority filters
- CSRF protection on all state-changing requests
- Structured JSON logging of auth events, task mutations, and HTTP errors

## Requirements

- Python 3.10 or newer

## Setup

From this directory, create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

```powershell
python -m flask --app app run --host 127.0.0.1
```

The development server binds to loopback and debug mode is disabled by default. The
SQLite database is created at `instance/tasks.db`. Open `http://127.0.0.1:5000/`,
register an account, and sign in.

Set `TASK_MANAGER_SECRET_KEY` to a private, stable value if sessions must remain
valid across app restarts. Do not commit that value.

> Upgrading from the single-user version: the legacy `tasks` table (without
> `user_id`) is dropped and recreated on first start; previous local task data is
> not preserved.

## Routes

| Method & path | Auth | Purpose |
| --- | --- | --- |
| `GET /register` | — | Registration form |
| `POST /register` | CSRF | Create account (username 3–50 chars, password ≥ 8) |
| `GET /login` | — | Sign-in form |
| `POST /login` | CSRF | Verify credentials, start session |
| `POST /logout` | session + CSRF | End session |
| `GET /` | session | Own task list; optional `status`/`priority` filters |
| `POST /tasks` | session + CSRF | Create task |
| `POST /tasks/<id>` | session + CSRF | Update own task |
| `POST /tasks/<id>/delete` | session + CSRF | Delete own task |

Full request/response details: see [docs/api.md](../docs/api.md).

## Test

```powershell
python -m pytest -q
```

Tests use isolated temporary SQLite databases and cover auth, per-user isolation,
task CRUD, validation, filtering, and CSRF behavior.

## Logging

Structured JSON events are written to stderr, e.g.:

```json
{"ts": "2026-11-03T12:00:00.000+00:00", "level": "INFO", "event": "task.create", "user_id": 1, "detail": "task_id=7"}
```

Events: `auth.register`, `auth.login.success`, `auth.login.failure`, `auth.logout`,
`task.create`, `task.update`, `task.delete`, `http.error`. Passwords, password
hashes, and session tokens are never logged.
