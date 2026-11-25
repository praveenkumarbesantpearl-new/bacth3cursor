"""Collect Linux metrics over SSH (read-only remote commands)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any

import paramiko


CONNECT_TIMEOUT = 8
COMMAND_TIMEOUT = 10


@dataclass
class MetricsResult:
    ok: bool
    error: str | None = None
    cpu: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    disk: list[dict[str, Any]] = field(default_factory=list)
    network: list[dict[str, Any]] = field(default_factory=list)
    listening: list[dict[str, Any]] = field(default_factory=list)
    established: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _validate_host(hostname: str) -> str:
    host = (hostname or "").strip()
    if not host or len(host) > 253:
        raise ValueError("Invalid hostname")
    # Block shell metacharacters; host is passed to SSH library, not a shell.
    if re.search(r"[\s;|&`$<>\"'\\]", host):
        raise ValueError("Invalid hostname characters")
    return host


def _run(client: paramiko.SSHClient, command: str) -> str:
    _stdin, stdout, stderr = client.exec_command(command, timeout=COMMAND_TIMEOUT)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    if code != 0 and not out.strip():
        raise RuntimeError(err.strip() or f"Command failed ({code})")
    return out


def _parse_cpu(raw: str) -> dict[str, Any]:
    # Prefer /proc/stat idle snapshot style via top batch, or mpstat-less fallback.
    # Format from: grep 'cpu ' /proc/stat
    parts = raw.strip().split()
    if len(parts) < 5 or parts[0] != "cpu":
        return {"usage_percent": None, "raw": raw.strip()}
    values = [int(x) for x in parts[1:]]
    total = sum(values)
    idle = values[3] if len(values) > 3 else 0
    usage = round(100.0 * (1 - idle / total), 1) if total else None
    return {"usage_percent": usage, "total_jiffies": total, "idle_jiffies": idle}


def _parse_memory(raw: str) -> dict[str, Any]:
    data: dict[str, int] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        num = val.strip().split()[0]
        if num.isdigit():
            data[key] = int(num)
    total = data.get("MemTotal")
    available = data.get("MemAvailable") or data.get("MemFree")
    used = (total - available) if total is not None and available is not None else None
    pct = round(100.0 * used / total, 1) if total and used is not None else None
    return {
        "total_kb": total,
        "available_kb": available,
        "used_kb": used,
        "used_percent": pct,
    }


def _parse_disk(raw: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lines = raw.strip().splitlines()
    for line in lines[1:]:
        cols = line.split()
        if len(cols) < 6:
            continue
        rows.append(
            {
                "filesystem": cols[0],
                "size": cols[1],
                "used": cols[2],
                "available": cols[3],
                "use_percent": cols[4],
                "mounted_on": cols[5],
            }
        )
    return rows


def _parse_network(raw: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines()[2:]:
        if ":" not in line:
            continue
        name, rest = line.split(":", 1)
        cols = rest.split()
        if len(cols) < 9:
            continue
        iface = name.strip()
        if iface == "lo":
            continue
        rows.append(
            {
                "interface": iface,
                "rx_bytes": int(cols[0]),
                "tx_bytes": int(cols[8]),
            }
        )
    return rows


def _parse_ss(raw: str, state_filter: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines()[1:]:
        cols = line.split()
        if len(cols) < 5:
            continue
        state = cols[1] if cols[0] in {"tcp", "udp", "tcp6", "udp6"} else cols[0]
        # ss -tulnH / ss -tn state established
        if cols[0] in {"Netid", "State"}:
            continue
        if state_filter and state.upper() != state_filter.upper():
            # listening listing uses "LISTEN"
            pass
        if cols[0] in {"tcp", "udp", "tcp6", "udp6"}:
            proto, st, _recvq, _sendq, local, peer = (
                cols[0],
                cols[1],
                cols[2],
                cols[3],
                cols[4],
                cols[5] if len(cols) > 5 else "-",
            )
        else:
            # Fallback: State Recv-Q Send-Q Local Address:Port Peer Address:Port
            proto, st, local, peer = "tcp", cols[0], cols[3], cols[4]
        rows.append(
            {
                "protocol": proto,
                "state": st,
                "local": local,
                "peer": peer,
            }
        )
    return rows


def collect_metrics(
    *,
    hostname: str,
    port: int = 22,
    username: str = "root",
    password: str | None = None,
    key_path: str | None = None,
    client_factory=None,
) -> MetricsResult:
    """SSH to host and gather CPU, memory, disk, network, listening, established."""
    try:
        host = _validate_host(hostname)
    except ValueError as exc:
        return MetricsResult(ok=False, error=str(exc))

    factory = client_factory or paramiko.SSHClient
    client = factory()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        connect_kwargs: dict[str, Any] = {
            "hostname": host,
            "port": int(port),
            "username": username,
            "timeout": CONNECT_TIMEOUT,
            "allow_agent": False,
            "look_for_keys": False,
        }
        if key_path:
            connect_kwargs["key_filename"] = key_path
        elif password is not None:
            connect_kwargs["password"] = password
        else:
            return MetricsResult(ok=False, error="No SSH credentials configured")

        client.connect(**connect_kwargs)

        cpu_raw = _run(client, "grep '^cpu ' /proc/stat")
        mem_raw = _run(client, "cat /proc/meminfo")
        disk_raw = _run(client, "df -h --output=source,size,used,avail,pcent,target")
        # Portable df fallback if --output unsupported
        if "df:" in disk_raw or not disk_raw.strip():
            disk_raw = _run(client, "df -h")
        net_raw = _run(client, "cat /proc/net/dev")
        listen_raw = _run(client, "ss -tuln 2>/dev/null || netstat -tuln")
        est_raw = _run(
            client,
            "ss -tn state established 2>/dev/null || netstat -tn | grep ESTABLISHED",
        )

        return MetricsResult(
            ok=True,
            cpu=_parse_cpu(cpu_raw),
            memory=_parse_memory(mem_raw),
            disk=_parse_disk(disk_raw),
            network=_parse_network(net_raw),
            listening=_parse_ss(listen_raw),
            established=_parse_ss(est_raw),
        )
    except paramiko.AuthenticationException:
        return MetricsResult(ok=False, error="SSH authentication failed")
    except (paramiko.SSHException, OSError, TimeoutError, RuntimeError) as exc:
        # Do not include credentials; message only.
        return MetricsResult(ok=False, error=f"SSH error: {exc}")
    finally:
        try:
            client.close()
        except Exception:
            pass
