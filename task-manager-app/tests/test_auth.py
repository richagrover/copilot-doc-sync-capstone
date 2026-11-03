from __future__ import annotations

import pytest

from conftest import DEFAULT_PASSWORD, DEFAULT_USERNAME, register_and_login
from task_store import list_tasks
from user_store import find_by_username


def test_register_creates_account_and_redirects_to_login(client, app):
    response = client.post(
        "/register", data={"username": "newuser", "password": "long-enough-pass"}
    )

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert find_by_username(app.config["DATABASE"], "newuser") is not None


def test_register_stores_hash_not_password(client, app):
    client.post("/register", data={"username": "hashcheck", "password": "long-enough-pass"})

    user = find_by_username(app.config["DATABASE"], "hashcheck")
    assert user["password_hash"] != "long-enough-pass"
    assert "long-enough-pass" not in user["password_hash"]


@pytest.mark.parametrize(
    ("username", "password", "error"),
    [
        ("ab", "long-enough-pass", b"Username must be between 3 and 50 characters."),
        ("x" * 51, "long-enough-pass", b"Username must be between 3 and 50 characters."),
        ("validname", "short", b"Password must be at least 8 characters."),
    ],
)
def test_register_rejects_invalid_input(client, app, username, password, error):
    response = client.post("/register", data={"username": username, "password": password})

    assert response.status_code == 400
    assert error in response.data
    assert find_by_username(app.config["DATABASE"], username) is None


def test_register_rejects_duplicate_username(client):
    client.post("/register", data={"username": "duped", "password": "long-enough-pass"})
    response = client.post(
        "/register", data={"username": "duped", "password": "other-long-pass"}
    )

    assert response.status_code == 400
    assert b"already taken" in response.data


def test_login_with_valid_credentials_shows_tasks(client):
    register_and_login(client)
    page = client.get("/")

    assert page.status_code == 200
    assert DEFAULT_USERNAME.encode() in page.data
    assert b"No tasks yet" in page.data


@pytest.mark.parametrize(
    "credentials",
    [
        {"username": DEFAULT_USERNAME, "password": "wrong-password"},
        {"username": "ghost", "password": "irrelevant-pass"},
    ],
)
def test_login_failure_is_generic(client, credentials):
    client.post(
        "/register", data={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD}
    )
    response = client.post("/login", data=credentials)

    assert response.status_code == 400
    assert b"Invalid username or password." in response.data


def test_anonymous_task_access_redirects_to_login(client):
    for path, method in [("/", client.get), ("/tasks", client.post), ("/tasks/1", client.post), ("/tasks/1/delete", client.post)]:
        response = method(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_logout_ends_session(auth_client):
    response = auth_client.post("/logout")
    page = auth_client.get("/")

    assert response.status_code == 302
    assert page.status_code == 302
    assert "/login" in page.headers["Location"]


def test_login_redirects_to_safe_next_only(client):
    client.post(
        "/register", data={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD}
    )
    response = client.post(
        "/login",
        data={
            "username": DEFAULT_USERNAME,
            "password": DEFAULT_PASSWORD,
            "next": "//evil.example.com/",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"] in ("/", "http://localhost/")


def test_users_cannot_access_each_others_tasks(app, client):
    register_and_login(client, "owner", "owner-password-1")
    client.post("/tasks", data={"title": "Owner task"})
    owner_id = int(find_by_username(app.config["DATABASE"], "owner")["id"])
    task_id = list_tasks(app.config["DATABASE"], owner_id)[0]["id"]
    client.post("/logout")

    register_and_login(client, "intruder", "intruder-pass-1")
    page = client.get("/")
    update = client.post(f"/tasks/{task_id}", data={"title": "Hijacked", "status": "todo", "priority": "low"})
    delete = client.post(f"/tasks/{task_id}/delete")

    assert b"Owner task" not in page.data
    assert update.status_code == 404
    assert delete.status_code == 404
    owner_tasks = list_tasks(app.config["DATABASE"], owner_id)
    assert owner_tasks[0]["title"] == "Owner task"


def test_login_rotates_session_token(app, client):
    register_and_login(client)
    first_cookie = client.get_cookie("session").value

    client.post(
        "/login", data={"username": DEFAULT_USERNAME, "password": DEFAULT_PASSWORD}
    )

    # Restoring the pre-rotation cookie must no longer authenticate.
    client.set_cookie("session", first_cookie)
    response = client.get("/")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
