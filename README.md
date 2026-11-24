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

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Security notes (demo)

- Do not commit `.env`, SQLite DB files, or virtualenvs (see `.gitignore`).
- `SECRET_KEY` is a local placeholder — change it before any shared use.
- Templates must never show passwords or secrets.
- Monitoring UI is read-only; no remote write actions.

## Current status

Step 1 complete: project layout and basic read-only UI shell. Sign-in, inventory, and SSH metrics come next.
