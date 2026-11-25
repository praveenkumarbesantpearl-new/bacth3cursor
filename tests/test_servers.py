"""Server inventory tests."""

from tests.conftest import _csrf


def test_add_and_list_server(auth_client):
    token = _csrf(auth_client)
    resp = auth_client.post(
        "/servers/add",
        data={
            "csrf_token": token,
            "hostname": "10.0.0.5",
            "ssh_port": "22",
            "ssh_username": "ubuntu",
            "auth_type": "password",
            "ssh_password": "secret",
            "label": "demo-box",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"demo-box" in resp.data
    assert b"10.0.0.5" in resp.data
    # Password must never be rendered
    assert b"secret" not in resp.data


def test_edit_hostname(auth_client):
    auth_client.post(
        "/servers/add",
        data={
            "csrf_token": _csrf(auth_client),
            "hostname": "old.example",
            "ssh_port": "22",
            "ssh_username": "root",
            "auth_type": "key",
            "ssh_key_path": "/tmp/id_rsa",
        },
        follow_redirects=True,
    )
    resp = auth_client.post(
        "/servers/1/edit",
        data={
            "csrf_token": _csrf(auth_client),
            "hostname": "new.example",
            "ssh_port": "2222",
            "ssh_username": "root",
            "auth_type": "key",
            "ssh_key_path": "/tmp/id_rsa",
            "label": "renamed",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"new.example" in resp.data
    assert b"renamed" in resp.data


def test_delete_server(auth_client):
    auth_client.post(
        "/servers/add",
        data={
            "csrf_token": _csrf(auth_client),
            "hostname": "gone.example",
            "ssh_port": "22",
            "ssh_username": "root",
            "auth_type": "password",
            "ssh_password": "x",
        },
    )
    resp = auth_client.post(
        "/servers/1/delete",
        data={"csrf_token": _csrf(auth_client)},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"gone.example" not in resp.data
