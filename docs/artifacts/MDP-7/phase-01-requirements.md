# Phase 01: Requirements Specification

## Source and Confidence

- Jira key: `MDP-7` (verified live on 2026-11-03 via the Jira REST API using the `.github/mcp.json` server configuration; see `jira_snapshot.json`)
- Summary: "Build Task Manager Application with Agentic SDLC Sync" (the earlier "paste karein" template residue was removed in Jira on 2026-10-30)
- Description: "Implement enterprise-grade task manager application with automated SDLC documentation sync"
- Type / Status / Priority: Idea / Parking lot / Medium
- Comments: 0; no subtasks or issue links.
- Acceptance criteria in Jira: none. Criteria below are derived and were **approved by the user in the interactive HITL Q&A on 2026-11-03**.
- Scope confidence: High for the clarified items below (directly user-answered); the Jira ticket itself remains two lines.

## Scope

A multi-user task manager application with authentication, plus automated synchronization of SDLC documentation — both pipeline phase artifacts and application README/API docs.

> **Scope change vs. 2026-10-28 baseline:** multi-user authentication with per-user task isolation (was single-user), SDLC sync expanded to include app README/API docs (was pipeline artifacts only), and structured logging added. The existing implementation predates these items; gap analysis belongs to Phase 02/03.

## Functional Requirements

1. **Task CRUD**: create, view, edit, and delete tasks.
2. **Status and priority**: each task has a status (`todo`, `in_progress`, `done`) and a priority (`low`, `medium`, `high`); tasks can be filtered by either or both.
3. **Authentication**: local username/password accounts with server-side sessions. Users must sign in to manage tasks.
4. **Per-user isolation**: each user sees and modifies only their own tasks.
5. **SDLC pipeline sync**: the pipeline accepts a Jira key and an application folder, and writes phase artifacts and `pipeline-state.json` under `docs/artifacts/${JIRA_KEY}/`.
6. **App documentation sync**: the application README and API documentation are kept in sync with source changes as part of the SDLC flow.
7. Completed phases are skipped on resume unless the user explicitly requests a full re-run.
8. Each phase requires human approval before the next begins.

## Non-Functional Requirements

1. **Validation**: server-side input validation for all fields (required title, max 200 chars, allowlisted status/priority, valid credentials format).
2. **Error handling**: clear 400/404 responses; no stack traces or internal errors exposed to users.
3. **CSRF protection** on all state-changing requests (confirmed in HITL Round 2).
4. **Automated tests**: pytest suite covering positive and negative scenarios.
5. **Maintainable structure**: Flask app factory, separated persistence layer.
6. **Structured logging**: application events (auth attempts, task mutations, errors) logged in a structured, machine-parseable format without sensitive data.
7. **Performance targets**: page responses < 500 ms with up to 1,000 tasks; test suite completes in < 60 s.
8. **UI expectations**: responsive server-rendered HTML; labeled, accessible form controls; empty-state message; flash feedback on actions.
9. Technology stack: Flask + SQLite (confirmed).

## Acceptance Criteria (derived, BDD — approved)

### Positive scenarios

- Given a registered user is signed in, when they submit a valid task, then it appears in their task list.
- Given a user's task exists, when the owner edits or deletes it, then their list reflects the change.
- Given mixed tasks, when the owner filters by status and/or priority, then only matching tasks are shown.
- Given valid credentials, when a user signs in, then a server-side session is established and their tasks are shown.
- Given a valid Jira key and app folder, when the pipeline runs, then phase artifacts are written and state is recorded.
- Given source changes land, when the SDLC sync runs, then the app README/API docs reflect the changes.

### Negative scenarios

- Given a visitor is not signed in, when they request task pages or submit mutations, then they are denied and redirected to sign-in.
- Given user B's task, when user A attempts to view, edit, or delete it, then the request is rejected (404 or 403) and the task is unchanged.
- Given an empty or over-long title, or an unsupported status/priority, when submitted, then the app responds 400 and persists nothing.
- Given a missing or invalid CSRF token, when a mutation is submitted, then it is rejected with 400 and nothing is persisted.
- Given invalid credentials, when sign-in is attempted, then access is denied without revealing which field was wrong.
- Given an unknown task id, when it is updated or deleted, then the app responds 404.

### Edge cases

- Title of exactly 200 characters is accepted; 201 is rejected.
- Filtering combinations that match nothing show the empty state, not an error.
- Concurrent sessions for the same user both see consistent task data.
- A deleted task's id, if re-requested, yields 404 rather than a stale record.

## Out of Scope

- SSO / enterprise identity providers, high availability, multi-tenancy.
- Roles/permissions beyond per-user task ownership.
- Due dates, tags, search, and sorting (not selected for MVP).

## Clarifications Q&A Log

### Round 1 (2026-11-03, interactive HITL)

| # | Category | Question | User Answer |
| --- | --- | --- | --- |
| 1 | Functional | Task manager feature scope (MVP) | Task CRUD (status/priority/filtering resolved in Round 2) |
| 2 | Functional | User scope | Multi-user with authentication |
| 3 | NFR | What does "enterprise-grade" mean concretely? | Validation, clear error handling, pytest suite, maintainable structure, structured logging |
| 4 | Scope | Scope of "automated SDLC documentation sync" | Pipeline artifacts + app README/API docs synced from source changes |
| 5 | Technical | Technology stack | Keep Flask + SQLite (existing implementation) |
| 6 | Process | Approve derived acceptance criteria? | Yes |
| 7 | General | Additional requirements | Capture edge cases, performance targets, UI expectations, positive and negative scenarios |

### Round 2 (2026-11-03, interactive HITL — conflict resolution)

| # | Category | Question | User Answer |
| --- | --- | --- | --- |
| 1 | Functional | Keep status/priority/filtering, or plain CRUD only? | Keep status, priority, and filtering |
| 2 | Functional | Authentication model | Local username/password accounts with server-side sessions; each user sees only their own tasks |
| 3 | Security | Keep CSRF protection? (deselected in Round 1) | Yes, keep it |
| 4 | NFR | Performance targets | Page responses < 500 ms with up to 1,000 tasks; test suite < 60 s |
| 5 | NFR | UI expectations | Responsive server-rendered HTML; labeled accessible controls; empty state; flash feedback |

## Status

Phase 01 regenerated on 2026-11-03 via interactive HITL Q&A (2 rounds). **Approved.** Scope changed from the prior baseline (multi-user auth, per-user isolation, expanded doc sync, structured logging); Phases 02+ must perform gap analysis against the existing single-user implementation.
