"""SSH metrics collector tests (mocked; no real hosts)."""

from unittest.mock import MagicMock

from app.ssh_metrics import MetricsResult, _parse_cpu, _parse_memory, collect_metrics


def test_parse_cpu():
    parsed = _parse_cpu("cpu  100 0 50 850 0 0 0 0")
    assert parsed["usage_percent"] == 15.0


def test_parse_memory():
    raw = "MemTotal:       2048000 kB\nMemAvailable:   1024000 kB\n"
    parsed = _parse_memory(raw)
    assert parsed["total_kb"] == 2048000
    assert parsed["used_percent"] == 50.0


def test_collect_metrics_success():
    mock_client = MagicMock()
    stdout_map = {
        "grep '^cpu ' /proc/stat": "cpu  10 0 5 85 0 0 0 0\n",
        "cat /proc/meminfo": "MemTotal: 1000 kB\nMemAvailable: 400 kB\n",
        "df -h --output=source,size,used,avail,pcent,target": (
            "Filesystem Size Used Avail Use% Mounted\n/dev/sda1 10G 4G 6G 40% /\n"
        ),
        "cat /proc/net/dev": (
            "Inter-|   Receive                                                |  Transmit\n"
            " face |bytes    packets errs drop fifo frame compressed multicast|bytes\n"
            "  eth0: 100 0 0 0 0 0 0 0 200 0 0 0 0 0 0 0\n"
        ),
        "ss -tuln 2>/dev/null || netstat -tuln": (
            "Netid State  Recv-Q Send-Q Local Address:Port Peer Address:Port\n"
            "tcp   LISTEN 0      128    0.0.0.0:22       0.0.0.0:*\n"
        ),
        "ss -tn state established 2>/dev/null || netstat -tn | grep ESTABLISHED": (
            "Netid State      Recv-Q Send-Q Local Address:Port Peer Address:Port\n"
            "tcp   ESTAB      0      0      10.0.0.1:22       10.0.0.2:4444\n"
        ),
    }

    def exec_command(command, timeout=None):
        out = stdout_map[command]
        stdout = MagicMock()
        stdout.read.return_value = out.encode()
        stdout.channel.recv_exit_status.return_value = 0
        stderr = MagicMock()
        stderr.read.return_value = b""
        return MagicMock(), stdout, stderr

    mock_client.exec_command.side_effect = exec_command
    factory = MagicMock(return_value=mock_client)

    result = collect_metrics(
        hostname="10.0.0.1",
        username="ubuntu",
        password="x",
        client_factory=factory,
    )
    assert result.ok is True
    assert result.cpu["usage_percent"] is not None
    assert result.memory["used_percent"] == 60.0
    assert result.disk
    assert result.network[0]["interface"] == "eth0"
    assert any(r["state"] == "LISTEN" for r in result.listening)
    assert any(r["state"] == "ESTAB" for r in result.established)


def test_collect_metrics_auth_failure():
    import paramiko

    mock_client = MagicMock()
    mock_client.connect.side_effect = paramiko.AuthenticationException("nope")
    factory = MagicMock(return_value=mock_client)

    result = collect_metrics(
        hostname="bad.host",
        password="x",
        client_factory=factory,
    )
    assert isinstance(result, MetricsResult)
    assert result.ok is False
    assert "authentication" in result.error.lower()


def test_invalid_hostname_rejected():
    result = collect_metrics(hostname="bad;host", password="x")
    assert result.ok is False
    assert "Invalid" in result.error
