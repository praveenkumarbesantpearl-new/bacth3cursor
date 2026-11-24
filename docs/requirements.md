# PRD: Demo Linux Server Monitoring (Local)

## 1. Overview

Local demo web app for **read-only** real-time monitoring of Linux servers (CPU, memory, disk, network, ports/connections) so L1/L2/L3 and app teams do not need to SSH in just to check current usage.

**Scope:** Demo only — run on the same machine as Cursor. Keep setup and features minimal.

## 2. Problem

Today, checking live memory, CPU, network, and port usage means logging into each server. That is slow and error-prone for support and development teams.

## 3. Users

Internal teams only: L1, L2, L3 infrastructure and application development. Single shared **admin** account for the demo.

## 4. Goals / Success

Demo is done when a user can:

1. Sign in as `admin`
2. Add 1–2 Linux servers (hostname/IP)
3. Open a server and see live CPU, memory, disk, network, and port/connection details in a read-only UI
4. Complete local setup in roughly a few minutes

## 5. Non-Goals (Out of Scope)

- Alerting / notifications
- Historical graphs or long-term metrics storage
- Multi-user / SSO / LDAP
- Windows hosts
- Write actions on servers (restart, kill process, config changes, etc.)
- Production hardening (HA, TLS termination, audit trails)

## 6. Tech Stack

| Layer | Choice |
|-------|--------|
| Backend / UI | Python, Flask |
| Auth | Session login; password stored hashed |
| Persistence | SQLite (local file) |
| Metrics | SSH from the Flask app to target Linux hosts |
| Deploy | Local only (`python app.py` or `flask run`) |

## 7. Features

### 7.1 Read-only UI

- Clean, simple dashboard suitable for internal demo use
- All monitoring views are **read-only** (no remote actions)
- Manual refresh and/or light auto-refresh (e.g. every 10–30s) is acceptable

### 7.2 Sign-in

- Default username: `admin`
- Password verified against a **hashed** value (config/env or seeded DB)
- No password-change UI required for the demo
- Unauthenticated users cannot access monitoring pages

### 7.3 Server inventory

- Add Linux servers to monitor
- Required: **hostname or IP**
- Recommended: SSH port (default `22`), SSH username, auth (password or key path), optional display name/label
- **Hostname/IP must be editable** after add
- Delete server from inventory is allowed for demo convenience
- Store inventory in SQLite

### 7.4 Live metrics (via SSH)

For a selected server, collect and display:

| Metric | Detail |
|--------|--------|
| CPU | Usage % (overall; per-core optional) |
| Memory | Used / total / available (and % used) |
| Disk | Per-mount or summary: used / total / % |
| Network | Interface throughput or simple RX/TX counters/rates |
| Ports / connections | **Listening** sockets and **established** connections |

If SSH fails, show a clear error state for that server (unreachable / auth failed) without crashing the app.

## 8. Functional Requirements (Minimal)

| ID | Requirement |
|----|-------------|
| FR-1 | User can sign in with username `admin` and hashed password |
| FR-2 | User can add a Linux server with hostname/IP and SSH details |
| FR-3 | User can edit hostname/IP (and SSH details) for an existing server |
| FR-4 | User can remove a server from inventory |
| FR-5 | User can open a server detail view and see CPU, memory, disk, network |
| FR-6 | User can see listening ports and established connections for a server |
| FR-7 | UI is read-only regarding remote system changes |
| FR-8 | App runs locally with SQLite; no external cloud dependency |

## 9. Local Run (Minimal)

1. Create/activate a Python venv and install dependencies (`requirements.txt`)
2. Set admin password hash (or use seeded default documented in README)
3. Ensure SSH reachability from this machine to target Linux hosts
4. Start app: `python app.py` (or `flask run`)
5. Open browser to local URL (e.g. `http://127.0.0.1:5000`)
6. Sign in → add server → view metrics

Exact commands and default port belong in the project README when the app is implemented.

## 10. Acceptance Criteria

- [ ] Login works with `admin` + hashed password; protected pages redirect to login
- [ ] Can add, edit hostname/IP, and delete servers
- [ ] Server detail shows CPU, memory, disk, network from SSH
- [ ] Ports view lists listening and established connections
- [ ] Failed SSH shows a readable error, app remains usable
- [ ] UI is clearly read-only (no control actions)
- [ ] Runs locally with Flask + SQLite without extra infra

## 11. Open Assumptions

- Targets are Linux with SSH enabled and credentials provided by the operator
- Metric commands on the remote host are standard (`/proc`, `ss`/`netstat`, `df`, etc.)
- Demo may use a documented default admin password; operators should change the hash for any shared environment
