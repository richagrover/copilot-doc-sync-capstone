# Phase 06: Code Review

Run: 2026-11-03, reviewing the multi-user implementation delivered in Phase 05
against the 7-point checklist in `.github/agents/sub-agents/review-agent.agent.md`.

## Review Result

**Passed with non-blocking observations.** No blocking defects. Four observations
are recorded for follow-up; none violate the approved Phase 01/03 requirements.

## Scope Reviewed

- `app.py`, `auth.py`, `db.py`, `user_store.py`, `session_store.py`,
  `task_store.py`, `logging_config.py`
- Templates `base.html`, `login.html`, `register.html`, `index.html`; `styles.css`
- `tests/conftest.py`, `tests/test_auth.py`, `tests/test_tasks.py`
- `requirements.txt`, `README.md`, `docs/api.md`

## Checklist Status

### 1. Correctness — PASS
- Register/login/logout, guarded task routes, and per-user scoping behave per
  `phase-01-requirements.md`; all 32 tests pass.
- Every task query includes `user_id = ?`; foreign-owned ids return 404 without
  disclosing existence, matching the Phase 03 constraint.
- Legacy single-user `tasks` table is rebuilt on startup as approved.

### 2. Security — PASS
- Passwords stored only as salted hashes (`werkzeug.security`); generic login
  failure message; register/login/logout all CSRF-protected.
- Server-side session tokens are 256-bit random, SHA-256-hashed at rest, expire in
  7 days, and are rotated on login (fixation defense). Cookie is `HttpOnly`,
  `SameSite=Lax`.
- Parameterized SQL throughout; query structure assembled only from fixed clauses.
- Jinja autoescaping on; `next` redirects restricted to local absolute paths.
- Secrets: `SECRET_KEY` from env with ephemeral fallback; structured logs exclude
  passwords, hashes, and tokens (verified in `logging_config.log_event` call sites).

### 3. Error Handling — PASS
- Validation and CSRF failures return 400 with human-readable descriptions; missing
  or foreign resources return 404; no stack traces (debug off by default).
- All `HTTPException`s emit a structured `http.error` event; the handler tolerates
  errors raised before request dispatch (`getattr(g, "user", None)`).
- Duplicate usernames are mapped from `sqlite3.IntegrityError` to a form error.

### 4. Test Coverage — PASS
- 32 tests: auth (13) and tasks (19) cover happy paths plus edge cases — duplicate
  username, short password, generic login failure, anonymous redirects, unsafe
  `next`, cross-user access (404 + data unchanged), session rotation, unknown-id
  404s, 200/201-character title boundary, no-match filters, missing/invalid/valid
  CSRF tokens, isolated database initialization.
- Suite wall time 5.91 s — within the 60 s performance gate.

### 5. Code Clarity — PASS
- Route, store, and helper names are self-explanatory (`login_required`,
  `_rotate_session`, `_safe_next`, `resolve_session`); comments appear only where
  rationale is non-obvious (legacy rebuild, rotation, logging constraints).

### 6. DRY Principle — PASS
- Connection handling, timestamps, and schema live once in `db.py`; form parsing
  and validation are shared helpers; templates share `base.html`.
- Minor duplication of status/priority `<select>` markup between the create and
  edit forms is accepted for template readability.

### 7. Dependency Safety — PASS
- Installed: Flask 3.1.3, Werkzeug 3.1.9, Jinja2 3.1.6, itsdangerous 2.2.0,
  WTForms 3.2.2, pytest 8.3.5 — all current major lines with no known unpatched
  advisories; version ranges in `requirements.txt` are upper-bounded.

## Non-Blocking Observations

| # | Observation | Risk | Recommendation |
| --- | --- | --- | --- |
| 1 | No rate limiting / lockout on login attempts | Online guessing on a local MVP is low risk | Add Flask-Limiter or lockout counters before any non-local deployment |
| 2 | Registration reveals taken usernames ("already taken") | Username enumeration; inherent to open self-registration | Acceptable for MVP; consider email-style opaque flows later |
| 3 | Session expiry is absolute (7 days), no sliding renewal | Users re-authenticate weekly | Acceptable; document if user feedback warrants |
| 4 | No security response headers (CSP, X-Frame-Options) | Low for loopback-only serving | Add a small after_request header set before remote deployment |

## Review Boundary

This review certifies the local multi-user MVP. Remote deployment hardening
(TLS, rate limiting, security headers) and live Jira integration remain out of
scope per Phase 01.
