# Phase 07: Verification

Run: 2026-11-03 (multi-user scope). All verification gates from
`phase-03-design-review.md` executed.

## Result

**Passed.** 32/32 tests green, 99% statement coverage (gate: 80%), all HTTP smoke
checks returned expected codes, and README/API doc route parity holds.

## Environment and Commands

- Python: 3.14.6; pytest: 8.3.5; pytest-cov: 7.1.0
- Working directory: `task-manager-app/`
- `python -m pytest -q` -> **32 passed in 9.52s** (< 60 s performance gate)
- `python -m pytest -q --cov=. --cov-report=term` -> **TOTAL 99%** (517 stmts, 6 miss)

### Coverage by module

| Module | Coverage |
| --- | --- |
| `app.py` | 98% |
| `auth.py` | 97% |
| `db.py` | 96% |
| `logging_config.py`, `session_store.py`, `task_store.py`, `user_store.py` | 100% |

## Requirement Traceability

| Phase 01 criterion | Evidence |
| --- | --- |
| Signed-in user's task appears in list | `test_create_task_persists_defaults` |
| Edit/delete reflected for owner | `test_update_task_changes_fields_and_timestamp`, `test_delete_task_removes_task` |
| Filter by status/priority (combinable) | `test_filters_can_be_combined`, `test_no_match_filters_show_empty_state_not_error`, `test_invalid_filter_is_rejected` |
| Valid credentials establish a session | `test_login_with_valid_credentials_shows_tasks` |
| Anonymous access denied, redirect to sign-in | `test_anonymous_task_access_redirects_to_login` + smoke check `GET / -> 302 /login?next=/` |
| Cross-user access rejected, data unchanged | `test_users_cannot_access_each_others_tasks` |
| Invalid input rejected without persistence | `test_invalid_task_input_is_rejected_without_persistence`, `test_update_rejects_missing_status_or_priority` |
| CSRF enforcement | `test_mutation_rejects_missing_or_invalid_csrf_token`, `test_valid_csrf_token_allows_mutation` |
| Generic login failure | `test_login_failure_is_generic` |
| Session rotation / fixation defense | `test_login_rotates_session_token` |
| 200-char boundary; 201 rejected | `test_title_boundary_of_200_characters_is_accepted`, parametrized invalid-input case |
| Unknown/foreign id -> 404 | `test_update_or_delete_unknown_task_returns_404` |
| Pipeline writes artifacts and state | `docs/artifacts/MDP-7/` phase files + `pipeline-state.json` (this run) |
| README/API docs synced | Route parity check below |
| Test results recorded | This file |

## HTTP Smoke Checks (live server, 127.0.0.1:5001)

| Probe | Result | Expectation |
| --- | --- | --- |
| `GET /` | 302 -> `/login?next=/` | Anonymous redirect ✓ |
| `GET /login` | 200 | ✓ |
| `GET /register` | 200 | ✓ |
| `GET /static/styles.css` | 200 | ✓ |
| `GET /?status=bogus` | 302 (to login) | Guard precedes filter validation ✓ |
| `POST /tasks` (anonymous, no token) | 400 | CSRF validation precedes auth redirect ✓ |

The smoke-test server was stopped afterwards and its generated `instance/tasks.db`
was removed.

## Doc-Parity Gate (README / docs/api.md)

Implemented route map (from `app.url_map`):
`GET /`, `GET+POST /login`, `POST /logout`, `GET+POST /register`, `POST /tasks`,
`POST /tasks/<id>`, `POST /tasks/<id>/delete` — **exactly matches** the route
tables in `task-manager-app/README.md` and `docs/api.md`. No undocumented or
missing routes.

## Limits

- Jira details came from the live 2026-11-03 REST fetch recorded in
  `jira_snapshot.json`; no further Jira calls were made during verification.
- Verification covers the local multi-user MVP; remote deployment is out of scope.
- Performance target (<500 ms @ 1,000 tasks) is supported by the indexed
  single-query design; no load test was executed on the local MVP.
