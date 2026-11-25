"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(db_path),
        }
    )
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_client(client):
    """Logged-in admin client."""
    client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "csrf_token": _csrf(client)},
        follow_redirects=True,
    )
    return client


def _csrf(client) -> str:
    # Hitting login GET ensures a session + CSRF token exist.
    client.get("/login")
    with client.session_transaction() as sess:
        return sess["_csrf"]


@pytest.fixture()
def csrf(client):
    return lambda: _csrf(client)
