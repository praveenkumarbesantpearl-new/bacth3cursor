# Server Monitor (Demo)

Local Flask demo for **read-only** Linux server monitoring (CPU, memory, disk, network, ports).

Spec: [docs/requirements.md](docs/requirements.md) · Tasks: [docs/TODO.md](docs/TODO.md)

## Setup (local)

```bash
cd /path/to/batch3_monitoring
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
source .venv/bin/activate
python app.py
```

Open [http://127.0.0.1:5027](http://127.0.0.1:5027) (port `5027` by default; override with `PORT=...`).

## Demo admin credentials

| Field | Default |
|-------|---------|
| Username | `admin` |
| Password | `admin123` |

Password is stored **hashed** in SQLite (never plaintext in the DB). Override at first seed with:

```bash
export ADMIN_PASSWORD='your-strong-password'
# delete data/monitor.db if admin was already seeded, then restart
python app.py
```

Optional:

```bash
export SECRET_KEY='replace-me-for-any-shared-use'
```

## Demo walkthrough

1. Sign in as `admin` / `admin123`
2. **Servers → Add server** (hostname/IP + SSH user + password or key path)
3. Open the host → view CPU, memory, disk, network, listening ports, established connections
4. Edit hostname/IP anytime; delete removes inventory only (no remote changes)

## Database

- File: `data/monitor.db` (created on first run; gitignored)
- Reset: stop the app, delete `data/monitor.db`, restart

## SSH metrics

The app SSHs from this Cursor host to each Linux target (Paramiko). Remote commands (read-only):

- `grep '^cpu ' /proc/stat`
- `cat /proc/meminfo`
- `df -h ...`
- `cat /proc/net/dev`
- `ss` / `netstat` for listening and established sockets

Ensure SSH reachability and credentials from this machine. Host input is validated; credentials are not logged; agent forwarding is disabled.

### Listening vs established

- **Listening** — sockets waiting for inbound connections (services).
- **Established** — active TCP connections currently connected.

## CI

GitHub Actions (`.github/workflows/ci.yml`) on push/PR: Python 3.12, install `requirements.txt`, run `pytest`. No repo secrets required for the demo suite (SSH is mocked in tests).

```bash
pytest -q
```

## Security notes (demo)

- Do not commit `.env`, SQLite DB files, or virtualenvs (see `.gitignore`).
- Set `SECRET_KEY` / `ADMIN_PASSWORD` before any shared use.
- Session cookies are HTTP-only; forms use CSRF tokens.
- SSH passwords are never rendered back in the UI; prefer key paths when possible.
- Templates escape output; monitoring UI is read-only (no remote write actions).
- Parameterized SQL only.

## Current status

Sections 1–11 of [docs/TODO.md](docs/TODO.md) implemented for the local demo.
