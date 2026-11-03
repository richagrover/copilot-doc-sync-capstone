# Phase 03: Design Review

## Review Outcome

**Accepted with implementation constraints.** The Flask/SQLite architecture meets the approved single-user task-management scope and supports isolated pytest coverage. The following controls are required during implementation.

## Traceability Review

| Requirement | Architecture coverage | Review |
| --- | --- | --- |
| Task create, view, edit, delete | Flask routes and SQLite task store | Covered |
| Status and priority | Constrained task fields and form controls | Covered |
| Filtering | Optional status and priority query filters | Covered |
| Local persistence | SQLite database in the app-owned `instance/` directory | Covered |
| Jira-driven SDLC artifacts | Orchestrator writes artifacts outside the app | Covered; no live Jira client is in scope |
| Verification | pytest with an isolated temporary database | Covered |

## Implementation Constraints

1. Bind the development server to loopback (`127.0.0.1`) and keep debug mode disabled by default.
2. Protect state-changing form submissions with a session-backed CSRF token.
3. Use Jinja autoescaping, server-side field/enum validation, and parameterized SQL.
4. Restrict database access to the configured application database path; tests must use a temporary database.
5. Do not expose stack traces or database errors in user-facing responses.

## Verification Gates

- Exercise successful CRUD flows and persistence across requests.
- Verify invalid/missing titles and unsupported status/priority values are rejected without modifying stored data.
- Verify status and priority filters can be used independently and together.
- Verify state-changing forms reject a missing or invalid CSRF token.

## Deferred Concerns

- User authentication, multi-user authorization, remote deployment, and live Jira connectivity remain out of scope for the agreed local MVP.
