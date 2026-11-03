# Task Manager API Documentation

Synced with the implementation in `task-manager-app/` (MDP-7, 2026-11-03).
All routes are served by the Flask application; responses are server-rendered HTML.
State-changing requests use `application/x-www-form-urlencoded` form posts and
require a valid `csrf_token` field.

## Authentication model

- Local username/password accounts. Passwords are stored as salted hashes
  (`werkzeug.security`); plaintext is never persisted or logged.
- Sessions are server-side: the browser cookie holds an opaque token (inside the
  signed Flask session cookie, `HttpOnly`, `SameSite=Lax`); the server stores a
  SHA-256 hash of the token with a 7-day expiry. Tokens are rotated on every login.
- Routes marked **session** below redirect anonymous requests to
  `GET /login?next=<path>` (302). `next` is honored only for local absolute paths.

## Routes

### `GET /register`

Registration form. Redirects to `/` if already signed in.

### `POST /register` — CSRF

| Form field | Rules |
| --- | --- |
| `username` | required, trimmed, 3–50 characters, unique |
| `password` | required, at least 8 characters |

- `302` → `/login` on success (flash: "Account created. Please sign in.")
- `400` with form error for invalid username/password or taken username

### `GET /login`

Sign-in form. Accepts optional `next` query parameter. Redirects to `/` if already signed in.

### `POST /login` — CSRF

| Form field | Rules |
| --- | --- |
| `username` | required |
| `password` | required |
| `next` | optional; local absolute paths only |

- `302` → `next` or `/` on success; session token rotated
- `400` with the generic message "Invalid username or password." on any failure

### `POST /logout` — session + CSRF

Deletes the server-side session record and clears the cookie. `302` → `/login`.

### `GET /` — session

The signed-in user's task list.

| Query parameter | Rules |
| --- | --- |
| `status` | optional; one of `todo`, `in_progress`, `done` |
| `priority` | optional; one of `low`, `medium`, `high` |

- `200` task list (filters combinable; non-matching filters render the empty state)
- `400` "Unsupported status filter." / "Unsupported priority filter."

### `POST /tasks` — session + CSRF

Create a task owned by the current user.

| Form field | Rules |
| --- | --- |
| `title` | required, trimmed, 1–200 characters |
| `description` | optional |
| `status` | defaults to `todo`; must be a supported status |
| `priority` | defaults to `medium`; must be a supported priority |

- `302` → `/` on success
- `400` with a specific validation message otherwise

### `POST /tasks/<id>` — session + CSRF

Update a task owned by the current user. Same field rules as create, but `status`
and `priority` have no defaults and must be supplied.

- `302` → `/` on success
- `400` validation failure (task unchanged)
- `404` if the task does not exist **or belongs to another user**

### `POST /tasks/<id>/delete` — session + CSRF

Delete a task owned by the current user.

- `302` → `/` on success
- `404` if the task does not exist or belongs to another user

## Error handling

- Validation and CSRF failures return `400` with a human-readable description; no
  stack traces are exposed.
- Missing or foreign-owned resources return `404` (ownership is not disclosed).
- Every handled HTTP error emits a structured `http.error` log event.

## Data model

| Table | Columns |
| --- | --- |
| `users` | `id`, `username` (unique, 3–50), `password_hash`, `created_at` |
| `sessions` | `token_hash` (PK), `user_id` (FK), `created_at`, `expires_at` |
| `tasks` | `id`, `user_id` (FK), `title` (1–200), `description`, `status`, `priority`, `created_at`, `updated_at` |

Indexes: `idx_tasks_user` on `tasks(user_id, status, priority)`.
Foreign keys are enforced (`PRAGMA foreign_keys = ON`); deleting a user cascades to
their sessions and tasks.
