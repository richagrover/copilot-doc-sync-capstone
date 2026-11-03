# Phase 02: Architecture (HLD + LLD)

Baseline: Phase 01 requirements approved via interactive HITL on 2026-11-03 (multi-user scope).

---

## Part A — High-Level Design (HLD)

### A.1 System Overview

A multi-user, server-rendered task manager. Users register and sign in with local
username/password credentials; each user manages an isolated set of tasks with
status, priority, and filtering. The Jira-driven orchestrator synchronizes SDLC
documentation: phase artifacts plus the application README/API docs.

```text
+-------------------+        +---------------------------+
|  Browser (HTML)   | <----> |  Flask application        |
|  forms + cookies  |  HTTP  |                           |
+-------------------+        |  auth blueprint           |
                             |  tasks routes             |
          session id cookie  |  login_required guard     |
                             |  structured JSON logging  |
                             +------------+--------------+
                                          |
                             +------------v--------------+
                             |  SQLite (instance/)       |
                             |  users / tasks / sessions |
                             +---------------------------+

Orchestrator (separate concern): Jira REST fetch -> docs/artifacts/MDP-7/* +
README/API doc sync for task-manager-app.
```

### A.2 Technology Stack

| Concern | Choice | Rationale |
| --- | --- | --- |
| Web framework | Flask (app factory) | Confirmed in HITL; existing code reuses |
| Persistence | SQLite via stdlib `sqlite3` | Confirmed; no DB service needed |
| Password hashing | `werkzeug.security` (pbkdf2) | Ships with Flask; no new dependency |
| Sessions | Server-side session records in SQLite; browser holds only an opaque signed session id cookie | Satisfies the "server-side sessions" HITL answer without a new dependency |
| CSRF | Flask-WTF `CSRFProtect` | Already integrated; confirmed keep |
| Logging | stdlib `logging` + JSON formatter | Structured, machine-parseable, zero deps |
| Tests | pytest | Confirmed |

### A.3 Component Boundaries

1. **Auth component** — registration, login, logout, session lifecycle, `login_required` guard.
2. **Task component** — user-scoped CRUD, status/priority, filtering.
3. **Persistence layer** — `user_store`, `session_store`, `task_store` modules owning all SQL.
4. **Presentation** — Jinja templates (`base`, `login`, `register`, `index`), autoescaped, responsive CSS.
5. **Observability** — structured JSON logs for auth events, task mutations, and HTTP errors; never logs passwords, hashes, or session ids.
6. **SDLC sync (orchestrator-owned)** — live Jira fetch, phase artifacts, `pipeline-state.json`, and README/API doc regeneration when routes or behavior change. The app itself has no Jira coupling.

### A.4 Security Model

- All task pages and mutations require an authenticated session; anonymous requests redirect to `/login?next=...`.
- Per-user isolation enforced in SQL (`WHERE user_id = ?`); foreign-owned task ids return 404 (no existence disclosure).
- CSRF tokens on every state-changing form; parameterized SQL everywhere; Jinja autoescaping.
- Login failures return a single generic message; no username/password distinction.
- Loopback bind, debug off, secret key from `TASK_MANAGER_SECRET_KEY`.

### A.5 Performance

Targets: < 500 ms page responses with up to 1,000 tasks per user; test suite < 60 s.
Approach: indexed `tasks(user_id)` lookups, single-query list rendering, no N+1 patterns.

---

## Part B — Low-Level Design (LLD)

### B.1 Directory Layout

```text
task-manager-app/
  app.py                 # App factory; registers auth + task routes, logging, CSRF
  auth.py                # Auth blueprint: register/login/logout, login_required
  user_store.py          # users table: create/find, password hash verify
  session_store.py       # server-side session records: create/get/delete, expiry
  task_store.py          # tasks table: user-scoped CRUD + filters
  logging_config.py      # JSON log formatter and logger setup
  templates/
    base.html            # Shared layout, flash messages, nav (login state)
    login.html           # Sign-in form
    register.html        # Registration form
    index.html           # Task list, filters, create/edit forms
  static/styles.css
  tests/
    conftest.py          # App/client fixtures, temp DB, helper to register+login
    test_auth.py         # Registration, login, logout, guard, isolation tests
    test_tasks.py        # CRUD, validation, filter, CSRF tests (as authed user)
  requirements.txt
  README.md              # Synced: setup, run, auth usage, API routes
docs/
  api.md                 # Synced API/route documentation (doc-sync target)
```

### B.2 Data Model

```sql
CREATE TABLE users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE
                CHECK(length(trim(username)) BETWEEN 3 AND 50),
  password_hash TEXT NOT NULL,
  created_at    TEXT NOT NULL
);

CREATE TABLE sessions (
  token_hash  TEXT PRIMARY KEY,          -- SHA-256 of the opaque session id
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at  TEXT NOT NULL,
  expires_at  TEXT NOT NULL
);

CREATE TABLE tasks (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title       TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 200),
  description TEXT NOT NULL DEFAULT '',
  status      TEXT NOT NULL CHECK(status IN ('todo','in_progress','done')),
  priority    TEXT NOT NULL CHECK(priority IN ('low','medium','high')),
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);
CREATE INDEX idx_tasks_user ON tasks(user_id, status, priority);
```

Migration note: the existing `tasks` table lacks `user_id`; the dev phase recreates
the schema (local MVP data is disposable) rather than shipping a migration tool.

### B.3 Route Map

| Method & path | Auth | Behavior | Errors |
| --- | --- | --- | --- |
| `GET /register` | anon | Registration form | — |
| `POST /register` | anon + CSRF | Validate username (3–50, unique) and password (min 8); create user; log `auth.register`; redirect to login | 400 invalid, duplicate -> form error |
| `GET /login` | anon | Login form | — |
| `POST /login` | anon + CSRF | Verify credentials; create server-side session; set cookie; log `auth.login.success/failure` | 400 generic "invalid credentials" |
| `POST /logout` | authed + CSRF | Delete session record and cookie; log `auth.logout` | — |
| `GET /` | authed | Owner's task list; optional `status`/`priority` filters | 400 invalid filter |
| `POST /tasks` | authed + CSRF | Create task for current user | 400 validation |
| `POST /tasks/<id>` | authed + CSRF | Update if owned by current user | 400 validation, 404 not owned/absent |
| `POST /tasks/<id>/delete` | authed + CSRF | Delete if owned | 404 not owned/absent |

### B.4 Auth Flow Detail

1. `login_required` reads the session cookie, hashes the token, looks up `sessions`;
   expired/absent -> redirect `/login?next=<path>` (next restricted to local paths).
2. Successful login rotates the session (new token) to prevent fixation.
3. Passwords: `generate_password_hash` on register, `check_password_hash` on login.
4. Session expiry: 7 days absolute; expired rows purged lazily on access.

### B.5 Structured Logging

- `logging_config.configure(app)` installs a JSON formatter:
  `{"ts", "level", "event", "user_id", "request_id", "detail"}`.
- Events: `auth.register`, `auth.login.success`, `auth.login.failure`,
  `auth.logout`, `task.create`, `task.update`, `task.delete`, `http.error`.
- Never logged: passwords, password hashes, session tokens, CSRF tokens.

### B.6 Doc-Sync Contract (README/API docs)

- `task-manager-app/README.md` and `docs/api.md` must list every route in B.3 with
  auth requirements and error codes.
- Any dev-phase route/behavior change updates both files in the same change set;
  the Phase 07 verification gate checks route list parity.

### B.7 Test Design

- Fixtures: temp SQLite DB per test; `auth_client` fixture registers and logs in a user.
- `test_auth.py`: register happy path, duplicate username, short password, login
  success/failure (generic error), logout, guard redirects, per-user isolation
  (user A cannot read/update/delete user B's task), session rotation on login.
- `test_tasks.py`: existing CRUD/validation/filter/CSRF coverage re-run as an
  authenticated user; unknown id -> 404; 200-char title boundary.
- Performance guard: suite wall time asserted < 60 s by CI convention (observed, not enforced in code).
