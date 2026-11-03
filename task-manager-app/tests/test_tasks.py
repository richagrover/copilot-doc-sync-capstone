from __future__ import annotations

import re

import pytest

from app import create_app
from task_store import list_tasks


def _create_task(client, **overrides):
    values = {
        "title": "Prepare release",
        "description": "Write release notes",
        "status": "todo",
        "priority": "medium",
    }
    values.update(overrides)
    response = client.post("/tasks", data=values)
    assert response.status_code == 302
    return response


def test_home_shows_empty_state(auth_client):
    response = auth_client.get("/")

    assert response.status_code == 200
    assert b"No tasks yet" in response.data


def test_create_task_persists_defaults(auth_client):
    response = auth_client.post("/tasks", data={"title": "Plan sprint"})
    page = auth_client.get("/")

    assert response.status_code == 302
    assert b"Plan sprint" in page.data
    assert b"Medium" in page.data
    assert b"todo" in page.data


def test_update_task_changes_fields_and_timestamp(auth_client, app, user_id):
    _create_task(auth_client)
    original = list_tasks(app.config["DATABASE"], user_id)[0]

    response = auth_client.post(
        f"/tasks/{original['id']}",
        data={
            "title": "Release version 1",
            "description": "Publish notes",
            "status": "done",
            "priority": "high",
        },
    )
    page = auth_client.get("/")

    assert response.status_code == 302
    assert b"Release version 1" in page.data
    assert b"done" in page.data
    updated = list_tasks(app.config["DATABASE"], user_id)[0]
    assert updated["updated_at"] > original["updated_at"]


def test_delete_task_removes_task(auth_client):
    _create_task(auth_client)
    task_page = auth_client.get("/")
    task_id = re.search(rb"/tasks/(\d+)/delete", task_page.data).group(1).decode()

    response = auth_client.post(f"/tasks/{task_id}/delete")
    page = auth_client.get("/")

    assert response.status_code == 302
    assert b"Prepare release" not in page.data
    assert b"No tasks yet" in page.data


def test_update_or_delete_unknown_task_returns_404(auth_client):
    update = auth_client.post(
        "/tasks/9999",
        data={"title": "Ghost", "status": "todo", "priority": "low"},
    )
    delete = auth_client.post("/tasks/9999/delete")

    assert update.status_code == 404
    assert delete.status_code == 404


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({"title": " "}, b"Task title is required."),
        ({"title": "x" * 201}, b"Task title must be 200 characters or fewer."),
        ({"title": "Task", "status": "blocked"}, b"Unsupported task status."),
        ({"title": "Task", "priority": "urgent"}, b"Unsupported task priority."),
    ],
)
def test_invalid_task_input_is_rejected_without_persistence(
    auth_client, payload, error, app, user_id
):
    response = auth_client.post("/tasks", data=payload)

    assert response.status_code == 400
    assert error in response.data
    assert list_tasks(app.config["DATABASE"], user_id) == []


def test_title_boundary_of_200_characters_is_accepted(auth_client, app, user_id):
    response = auth_client.post("/tasks", data={"title": "y" * 200})

    assert response.status_code == 302
    assert len(list_tasks(app.config["DATABASE"], user_id)[0]["title"]) == 200


def test_update_rejects_missing_status_or_priority(auth_client, app, user_id):
    _create_task(auth_client)
    task = list_tasks(app.config["DATABASE"], user_id)[0]

    response = auth_client.post(
        f"/tasks/{task['id']}",
        data={"title": "Changed title", "description": ""},
    )

    assert response.status_code == 400
    assert b"Unsupported task status." in response.data
    assert list_tasks(app.config["DATABASE"], user_id)[0] == task


def test_filters_can_be_combined(auth_client):
    _create_task(auth_client, title="Urgent done", status="done", priority="high")
    _create_task(auth_client, title="Urgent todo", status="todo", priority="high")
    _create_task(auth_client, title="Low done", status="done", priority="low")

    response = auth_client.get("/?status=done&priority=high")

    assert response.status_code == 200
    assert b"Urgent done" in response.data
    assert b"Urgent todo" not in response.data
    assert b"Low done" not in response.data


def test_no_match_filters_show_empty_state_not_error(auth_client):
    _create_task(auth_client, status="todo", priority="low")

    response = auth_client.get("/?status=done&priority=high")

    assert response.status_code == 200
    assert b"No matching tasks" in response.data


def test_invalid_filter_is_rejected(auth_client):
    response = auth_client.get("/?status=unknown")

    assert response.status_code == 400
    assert b"Unsupported status filter." in response.data


def _csrf_app(tmp_path, name):
    return create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / f"{name}.db"),
            "SECRET_KEY": "test-only-secret",
            "WTF_CSRF_ENABLED": True,
        }
    )


def _extract_csrf_token(page_bytes):
    return re.search(rb'name="csrf_token"[^>]*value="([^"]+)"', page_bytes).group(1).decode()


def _register_and_login_with_csrf(client):
    register_page = client.get("/register")
    client.post(
        "/register",
        data={
            "username": "csrfuser",
            "password": "long-enough-pass",
            "csrf_token": _extract_csrf_token(register_page.data),
        },
    )
    login_page = client.get("/login")
    response = client.post(
        "/login",
        data={
            "username": "csrfuser",
            "password": "long-enough-pass",
            "csrf_token": _extract_csrf_token(login_page.data),
        },
    )
    assert response.status_code == 302


@pytest.mark.parametrize("token", [None, "invalid-token"])
def test_mutation_rejects_missing_or_invalid_csrf_token(tmp_path, token):
    app = _csrf_app(tmp_path, "csrf-tasks")
    client = app.test_client()
    _register_and_login_with_csrf(client)

    response = client.post(
        "/tasks",
        data={"title": "Must not persist", **({"csrf_token": token} if token else {})},
    )

    assert response.status_code == 400
    assert b"CSRF" in response.data


def test_valid_csrf_token_allows_mutation(tmp_path):
    app = _csrf_app(tmp_path, "csrf-valid-tasks")
    client = app.test_client()
    _register_and_login_with_csrf(client)

    page = client.get("/")
    response = client.post(
        "/tasks",
        data={"title": "Protected task", "csrf_token": _extract_csrf_token(page.data)},
    )
    listing = client.get("/")

    assert response.status_code == 302
    assert b"Protected task" in listing.data


def test_factory_initializes_configured_database(tmp_path):
    database_path = tmp_path / "isolated.db"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database_path),
            "SECRET_KEY": "test-only-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )

    assert app.config["DATABASE"] == str(database_path)
    assert database_path.exists()
