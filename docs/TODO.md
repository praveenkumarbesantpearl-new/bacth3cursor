# TODO: Demo Linux Server Monitoring

Small increments for AI-assisted local demo work. Check items off as you complete them.

Reference: [requirements.md](./requirements.md)

---

## 1. Project initialization and basic UI

- [x] Create project layout (`app/`, `tests/`, `docs/`, `.gitignore`)
- [x] Add `requirements.txt` (Flask, and later: bcrypt/werkzeug, paramiko, pytest)
- [x] Add minimal Flask app entry (`app/__init__.py` or `app.py`) that serves a home page
- [x] Add basic read-only UI shell (HTML + simple CSS): header, nav placeholder, content area
- [x] **Security:** Do not commit secrets; ignore `.env`, `*.db`, venv; no debug secrets in templates
- [x] **Docs:** README with venv create/activate, `pip install -r requirements.txt`, how to run locally

---

## 2. Sign-in and unit tests

- [x] Add login route + simple login form (username + password)
- [x] Seed single `admin` user; store **hashed** password only (Werkzeug or bcrypt)
- [x] Protect routes with session auth; redirect unauthenticated users to login
- [x] Logout clears session
- [x] Unit tests: valid login, invalid login, protected route redirect, logout
- [x] **Security:** Constant-time hash verify; no password in logs/templates; HTTP-only session cookie; demo default password documented, not hardcoded in plaintext in repo if avoidable
- [x] **Docs:** README section for default admin credentials and how to set/override password hash

---

## 3. CI/CD (GitHub Actions) — early, keep green

- [x] Add `.github/workflows/ci.yml`: install deps, run unit tests on push/PR
- [x] Pin Python version in workflow (e.g. 3.11 or 3.12)
- [x] Fail CI on test failure
- [x] **Security:** No secrets in workflow logs; use GitHub secrets only if needed later (demo likely needs none)
- [x] **Docs:** Short CI note in README (what runs on PR)

---

## 4. SQLite persistence skeleton

- [x] Add SQLite DB init (servers table + users/admin seed if not already)
- [x] App creates DB file on first run (local path; gitignored)
- [x] Unit tests for DB init / seed idempotency
- [x] **Security:** Parameterized SQL only; DB file outside VCS; restrict file permissions in docs
- [x] **Docs:** Where the DB lives and how to reset it locally

---

## 5. Server inventory — add / list (UI)

- [x] Read-only list page of monitored servers
- [x] Add-server form: hostname/IP, SSH port, SSH username, auth fields (password or key path), optional label
- [x] Persist new server to SQLite; show on list after add
- [x] Unit/integration tests for add + list
- [x] **Security:** Auth required for all inventory routes; never render SSH passwords back to the page; prefer key path over storing passwords when possible
- [x] **Docs:** How to add a server for the local demo

---

## 6. Server inventory — edit hostname/IP and delete

- [x] Edit form: hostname/IP (and SSH fields) editable
- [x] Delete server from inventory (with simple confirm)
- [x] Tests for edit and delete
- [x] **Security:** CSRF-safe pattern if forms are used (Flask-WTF or equivalent minimal check); auth required; no mass-assignment of unexpected fields
- [x] **Docs:** Update inventory usage notes (edit / remove)

---

## 7. SSH metrics collector (library, no UI yet)

- [x] Add SSH client helper (e.g. Paramiko) with connect timeout
- [x] Collect CPU, memory, disk, network via remote commands
- [x] Collect listening ports and established connections
- [x] Return structured data + clear error on failure (auth/unreachable)
- [x] Unit tests with mocked SSH (no real hosts required in CI)
- [x] **Security:** Timeouts; do not log credentials; sanitize/validate host input; disable agent forwarding; treat remote output as untrusted
- [x] **Docs:** Required SSH access from the Cursor host; which remote commands are used

---

## 8. Server detail UI — CPU, memory, disk, network

- [x] Detail page for one server (read-only)
- [x] Call collector and display CPU, memory, disk, network
- [x] Show friendly error if SSH fails
- [x] Manual refresh button (optional light auto-refresh)
- [x] Tests for detail route success and failure paths (mocked)
- [x] **Security:** Auth required; read-only UI only (no remote write actions); escape all metric output in templates
- [x] **Docs:** Screenshot or short note on reading the detail page

---

## 9. Ports / connections UI

- [x] On detail (or tab): list **listening** sockets
- [x] List **established** connections
- [x] Tests with mocked collector output
- [x] **Security:** Escape connection fields; avoid exposing sensitive remote usernames beyond what is needed for demo
- [x] **Docs:** What “listening” vs “established” means in the UI

---

## 10. Polish UI (still minimal) and final local demo pass

- [x] Consistent styling; empty states; loading/error messaging
- [x] Confirm all monitoring views remain read-only
- [x] Smoke-check full path: login → add server → edit hostname/IP → view metrics + ports
- [x] **Security:** Quick review — no secrets in repo, debug off for any shared run, session secret from env
- [x] **Docs:** Final README “Demo walkthrough” (minimal steps only)

---

## 11. CI hardening and wrap-up

- [x] Ensure GitHub Actions runs full test suite (auth, inventory, mocked SSH metrics)
- [x] Add optional lint step only if it stays low-friction (e.g. `ruff` or `flake8`) — skipped for minimal demo; pytest is the CI gate
- [x] **Security:** Confirm workflow does not print env secrets; dependency install from lock/requirements only
- [x] **Docs:** Link TODO completion status / point to requirements acceptance checklist

---

## Suggested order (do not skip ahead)

1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11

Each step should leave the app runnable locally and tests (once added) passing before the next step.
