# Phase 03: Design Review

## Review Outcome

**Accepted with implementation constraints.** The HLD/LLD in `phase-02-architecture.md`
covers the approved multi-user scope. The existing codebase implements only the
superseded single-user scope; the gap analysis below defines the Phase 04/05 work.

## Traceability Review

| Phase 01 requirement | Architecture coverage | Review |
| --- | --- | --- |
| Task CRUD | Task routes + `task_store` (B.3) | Covered |
| Status, priority, filtering | Constrained fields + combinable filters | Covered |
| Local username/password auth, server-side sessions | Auth blueprint, `sessions` table, opaque cookie (A.4, B.4) | Covered |
| Per-user task isolation | `user_id` scoping in every task query; 404 for foreign tasks | Covered |
| Structured logging | JSON formatter + event catalog (B.5) | Covered |
| CSRF protection | Flask-WTF on all mutations | Covered |
| Validation & error handling | Server-side rules, 400/404, no stack traces | Covered |
| Performance targets | Indexed per-user queries; <500 ms @ 1k tasks (A.5) | Covered |
| UI expectations | Responsive templates, labeled controls, empty state, flash feedback | Covered |
| Pipeline artifact sync | Orchestrator-owned, live Jira fetch | Covered |
| README/API doc sync | Doc-sync contract (B.6) + Phase 07 parity gate | Covered |

## Gap Analysis — Existing Code vs. Approved Design

| # | Gap | Existing state | Required change |
| --- | --- | --- | --- |
| 1 | No `users` table or registration/login/logout | Absent | Add `user_store.py`, `auth.py`, templates |
| 2 | No server-side sessions | Flask signed-cookie session only (flash) | Add `sessions` table + `session_store.py` |
| 3 | Tasks are global | `tasks` has no `user_id`; queries unscoped | Recreate schema with `user_id`; scope all queries |
| 4 | No route guard | All routes anonymous | `login_required` with safe `next` redirect |
| 5 | No structured logging | No logging configured | Add `logging_config.py` + event calls |
| 6 | Tests assume anonymous access | `conftest.py` has no auth fixture | Add `test_auth.py`; run task tests authenticated |
| 7 | Docs out of sync | README lacks auth; no `docs/api.md` | Write both per doc-sync contract (B.6) |

## Implementation Constraints

1. Bind the development server to loopback (`127.0.0.1`); debug mode off by default.
2. CSRF tokens on all state-changing forms, including login/logout/register.
3. Jinja autoescaping, server-side validation, parameterized SQL only.
4. Store only password hashes (`werkzeug.security`); generic login failure message.
5. Session cookie: `HttpOnly`, `SameSite=Lax`; store only the opaque token; hash tokens at rest; rotate on login.
6. Foreign-owned task access returns 404 (no existence disclosure).
7. Tests use temporary databases; never touch `instance/tasks.db`.
8. Structured logs must never contain passwords, hashes, or tokens.
9. Secret key from `TASK_MANAGER_SECRET_KEY`; no hardcoded secrets.

## Verification Gates (for Phase 07)

- Register -> login -> CRUD -> logout happy path.
- Anonymous requests to task routes redirect to login; mutations without CSRF rejected.
- User A cannot view/update/delete user B's tasks (404, data unchanged).
- Invalid titles/status/priority rejected with 400 and no persistence.
- Filters work independently and combined; invalid filters rejected.
- Expired/rotated sessions no longer authenticate.
- README/API docs list every implemented route (doc-sync parity).
- Full pytest suite < 60 s.

## Deferred Concerns

- SSO/enterprise identity, roles beyond ownership, HA/multi-tenancy, remote deployment.
- Data migration tooling: the local MVP recreates the SQLite schema; production-grade migrations are out of scope.

## Status

Design review complete 2026-11-03. Awaiting HITL approval to proceed to Phase 04
(implementation manifest) and Phase 05 (development) to close the gaps above.
