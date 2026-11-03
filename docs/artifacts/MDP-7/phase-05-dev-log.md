# Phase 05: Development Log

Run: 2026-11-03 interactive HITL re-run (multi-user scope). Closes all 7 gaps from
`phase-03-design-review.md`.

## Delivered

### New modules
- `db.py` — shared SQLite connection helper (`PRAGMA foreign_keys = ON`), UTC
  timestamps, and schema initialization for `users`, `sessions`, and `tasks`
  (with `user_id` FK and `idx_tasks_user` index). Drops a legacy single-user
  `tasks` table on first start per the approved disposable-data decision.
- `user_store.py` — user creation (unique username via `IntegrityError` mapping),
  lookup by username/id; only password hashes are stored.
- `session_store.py` — server-side sessions: opaque `secrets.token_urlsafe(32)`
  tokens, SHA-256-hashed at rest, 7-day expiry with lazy purge, create/resolve/delete.
- `auth.py` — auth blueprint: `GET/POST /register`, `GET/POST /login`,
  `POST /logout`, `login_required` guard with `next` redirect (local paths only),
  session rotation on login, generic login-failure message, structured auth events.
- `logging_config.py` — JSON log formatter (`ts`, `level`, `event`, `user_id`,
  `detail`) and `log_event` helper; never logs passwords, hashes, or tokens.

### Reworked modules
- `app.py` — registers the auth blueprint; all task routes guarded by
  `login_required` and scoped to `g.user`; `task.create/update/delete` and
  `http.error` structured events; session cookie hardened (`HttpOnly`,
  `SameSite=Lax`).
- `task_store.py` — every CRUD/filter query scoped by `user_id`; schema ownership
  moved to `db.py`.
- Templates — new `base.html` (signed-in user bar, logout, flash messages),
  `login.html`, `register.html`; `index.html` now extends the base layout. Styles
  extended for auth panels and error notices.

### Tests
- `tests/conftest.py` — temp-DB app fixture plus `register_and_login` helper,
  `auth_client`, and `user_id` fixtures.
- `tests/test_auth.py` (new, 13 tests) — registration happy path and hash storage,
  invalid username/password, duplicate username, generic login failure, anonymous
  redirect for all task routes, logout, unsafe `next` rejection, per-user task
  isolation (view/update/delete all 404, data unchanged), session rotation
  invalidating the old token.
- `tests/test_tasks.py` (reworked, 19 tests) — previous CRUD/validation/filter
  coverage as an authenticated user, plus unknown-id 404s, 200-character title
  boundary, no-match filter empty state, and CSRF flows that register/sign in with
  real tokens.

### Doc sync (Gap 7)
- `task-manager-app/README.md` — multi-user features, auth usage, route table,
  migration note, logging reference.
- `docs/api.md` — full route/request/response contract, auth model, error handling,
  and data model; parity with implementation to be gate-checked in Phase 07.

## Validation Performed During Development

- `python -m pytest -q` from `task-manager-app/`: **32 passed in 5.91s**
  (< 60 s performance gate).
- Schema rebuild path exercised implicitly by fresh test databases; legacy-table
  drop verified by code inspection.
- Formal verification (full suite re-run, HTTP smoke checks, doc parity) is
  deferred to Phase 07 per the pipeline flow.

## Known Limits

- Legacy single-user task data is intentionally discarded on upgrade (approved in
  Phase 03).
- No rate limiting on login attempts; acceptable for the local MVP, flagged for
  Phase 06 review.
- Session expiry is absolute (7 days); no sliding renewal.
