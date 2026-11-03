# Phase 04: Implementation Manifest

## Scope

Implement the approved local Flask/SQLite task manager in `task-manager-app/`. The Jira-driven orchestrator continues to own Jira snapshots, SDLC artifact generation, and `pipeline-state.json`.

## Planned Files

| Path | Purpose |
| --- | --- |
| `task-manager-app/app.py` | Flask app factory, configuration, CSRF integration, list/create/edit/delete routes, and local-only development entry point |
| `task-manager-app/task_store.py` | SQLite schema initialization and parameterized CRUD/filter operations |
| `task-manager-app/templates/index.html` | Accessible task list, create/edit forms, status/priority controls, and filters |
| `task-manager-app/static/styles.css` | Responsive styling |
| `task-manager-app/tests/conftest.py` | Flask test client and temporary-database fixtures |
| `task-manager-app/tests/test_tasks.py` | CRUD, persistence, validation, filters, and CSRF tests |
| `task-manager-app/requirements.txt` | Flask, Flask-WTF, and pytest dependencies |
| `task-manager-app/README.md` | Local setup, run, configuration, and test instructions |
| `task-manager-app/.gitignore` | Exclude the generated SQLite database and Python cache files |

## Implementation Sequence

1. Add the dependency manifest, ignore rules, app factory, and isolated SQLite task store.
2. Implement server-rendered task list and create/update/delete flows with field validation and CSRF protection.
3. Add status and priority filters and responsive, labeled form controls.
4. Add pytest coverage against a temporary database, including malformed input and missing/invalid CSRF tokens.
5. Document local startup, loopback binding, secret-key configuration, and test commands.

## Test Plan

- Create a task and verify its defaults and persistence.
- View and update a task; verify `updated_at` changes.
- Delete a task and verify it is absent.
- Reject empty titles and unsupported status/priority values without changing stored data.
- Filter by status, by priority, and by both together.
- Reject mutations without a valid CSRF token.
- Verify application tests do not create or modify the developer's local database.

## Run Commands

- Install: `python -m pip install -r requirements.txt`
- Test: `python -m pytest -q`
- Run locally: `python -m flask --app app run --host 127.0.0.1`

The Flask app will use an application-owned `instance/tasks.db` database by default. A secret key can be supplied through `TASK_MANAGER_SECRET_KEY`; the app must not enable debug mode by default.
