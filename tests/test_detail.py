"""Server detail route tests with mocked SSH collector."""

from unittest.mock import patch

from app.ssh_metrics import MetricsResult
from tests.conftest import _csrf


def _add_server(client):
    client.post(
        "/servers/add",
        data={
            "csrf_token": _csrf(client),
            "hostname": "metrics.host",
            "ssh_port": "22",
            "ssh_username": "ubuntu",
            "auth_type": "password",
            "ssh_password": "x",
            "label": "metrics",
        },
    )


def test_detail_success(auth_client):
    _add_server(auth_client)
    fake = MetricsResult(
        ok=True,
        cpu={"usage_percent": 12.5},
        memory={"used_percent": 40.0, "used_kb": 400, "total_kb": 1000},
        disk=[
            {
                "filesystem": "/dev/sda1",
                "size": "10G",
                "used": "4G",
                "available": "6G",
                "use_percent": "40%",
                "mounted_on": "/",
            }
        ],
        network=[{"interface": "eth0", "rx_bytes": 1, "tx_bytes": 2}],
        listening=[
            {"protocol": "tcp", "state": "LISTEN", "local": "0.0.0.0:22", "peer": "*"}
        ],
        established=[
            {
                "protocol": "tcp",
                "state": "ESTAB",
                "local": "10.0.0.1:22",
                "peer": "10.0.0.2:9",
            }
        ],
    )
    with patch("app.routes.collect_metrics", return_value=fake):
        resp = auth_client.get("/servers/1")
    assert resp.status_code == 200
    assert b"12.5" in resp.data
    assert b"Listening ports" in resp.data
    assert b"Established connections" in resp.data
    assert b"0.0.0.0:22" in resp.data


def test_detail_ssh_failure(auth_client):
    _add_server(auth_client)
    fake = MetricsResult(ok=False, error="SSH authentication failed")
    with patch("app.routes.collect_metrics", return_value=fake):
        resp = auth_client.get("/servers/1")
    assert resp.status_code == 200
    assert b"SSH authentication failed" in resp.data
