# Phase 04: Implementation Manifest

## Scope

Close the 7 gaps from `phase-03-design-review.md`: convert the single-user task
manager in `task-manager-app/` into the approved multi-user application with local
authentication, server-side sessions, per-user task isolation, structured logging,
and synced README/API documentation.

## Planned Files

| Path | Action | Purpose |
| --- | --- | --- |
| `task-manager-app/db.py` | add | Shared SQLite connection helper, UTC timestamps, schema initialization (users, sessions, tasks) with single-user-schema rebuild |
| `task-manager-app/user_store.py` | add | User persistence: create (unique username), lookup by name/id |
| `task-manager-app/session_store.py` | add | Server-side sessions: opaque tokens hashed at rest, 7-day expiry, create/resolve/delete |
| `task-manager-app/auth.py` | add | Auth blueprint: register, login (session rotation), logout, `login_required`, safe `next` redirect |
| `task-manager-app/logging_config.py` | add | JSON log formatter and `log_event` helper (no secrets logged) |
| `task-manager-app/app.py` | rework | Register auth blueprint, guard task routes, scope tasks to `g.user`, log mutations and HTTP errors |
| `task-manager-app/task_store.py` | rework | All CRUD/filter queries scoped by `user_id`; schema moved to `db.py` |
| `task-manager-app/templates/base.html` | add | Shared layout: nav with signed-in user, logout form, flash messages |
| `task-manager-app/templates/login.html` | add | Sign-in form (CSRF) |
| `task-manager-app/templates/register.html` | add | Registration form (CSRF) |
| `task-manager-app/templates/index.html` | rework | Extend base layout; unchanged task UI |
| `task-manager-app/tests/conftest.py` | rework | Temp-DB app fixture plus registered + signed-in `auth_client` fixture |
| `task-manager-app/tests/test_auth.py` | add | Registration, login/logout, guard redirects, isolation, session rotation |
| `task-manager-app/tests/test_tasks.py` | rework | Existing CRUD/validation/filter/CSRF coverage as an authenticated user; 404 and boundary cases |
| `task-manager-app/README.md` | rework | Auth usage, route list, setup/run/test (doc-sync) |
| `docs/api.md` | add | Full API/route documentation (doc-sync target, parity-checked in Phase 07) |

## Implementation Sequence

1. Persistence foundation: `db.py` schema (users, sessions, tasks + index), stores.
2. Auth blueprint with hashing, server-side session records, rotation, guard.
3. Route rework: user scoping, structured logging, error logging.
4. Templates: base/login/register; index extends base.
5. Tests: auth fixtures, new auth suite, authenticated task suite.
6. Doc sync: README + `docs/api.md` route parity.

## Test Plan

- Auth: register happy path; duplicate username; short password; login success,
  wrong password (generic message), unknown user; logout; redirect-to-login for
  anonymous access; safe `next` handling; session rotation invalidates old token.
- Isolation: user A receives 404 for user B's task on view/update/delete; B's data unchanged.
- Tasks (authenticated): create with defaults; update fields + `updated_at`; delete;
  empty/201-char titles rejected; unsupported status/priority rejected; 200-char
  title accepted; unknown id 404; combined filters; invalid filter 400.
- CSRF: mutations without/with invalid token rejected (auth + task routes); valid token accepted.
- Suite runtime < 60 s (performance gate).

## Run Commands

- Install: `python -m pip install -r requirements.txt`
- Test: `python -m pytest -q`
- Run locally: `python -m flask --app app run --host 127.0.0.1`

Schema note: on startup, a legacy single-user `tasks` table (no `user_id` column) is
dropped and recreated per the approved disposable-data decision in Phase 03.
