"""Auth unit tests."""

from tests.conftest import _csrf


def test_valid_login(client):
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "csrf_token": _csrf(client)},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Sign out" in resp.data
    assert b"Infrastructure at a glance" in resp.data


def test_invalid_login(client):
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "wrong", "csrf_token": _csrf(client)},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Invalid username or password" in resp.data


def test_protected_route_redirect(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_logout(client):
    client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "csrf_token": _csrf(client)},
    )
    resp = client.post(
        "/logout",
        data={"csrf_token": _csrf(client)},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    assert client.get("/").status_code == 302
