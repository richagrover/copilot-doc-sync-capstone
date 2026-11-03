from __future__ import annotations

import pytest

from app import create_app
from user_store import find_by_username

DEFAULT_USERNAME = "alice"
DEFAULT_PASSWORD = "correct-horse-battery"


@pytest.fixture
def app(tmp_path):
    database_path = tmp_path / "test-tasks.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database_path),
            "SECRET_KEY": "test-only-secret",
            "WTF_CSRF_ENABLED": False,
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def register_and_login(client, username=DEFAULT_USERNAME, password=DEFAULT_PASSWORD):
    response = client.post(
        "/register", data={"username": username, "password": password}
    )
    assert response.status_code == 302
    response = client.post("/login", data={"username": username, "password": password})
    assert response.status_code == 302
    return response


@pytest.fixture
def auth_client(app, client):
    """A test client with a registered and signed-in default user."""
    register_and_login(client)
    return client


@pytest.fixture
def user_id(app, auth_client):
    return int(find_by_username(app.config["DATABASE"], DEFAULT_USERNAME)["id"])
