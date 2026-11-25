"""SQLite persistence for the local demo."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "monitor.db"


def get_db_path(app=None) -> Path:
    if app is not None:
        return Path(app.config["DATABASE"])
    return DEFAULT_DB_PATH


def connect(db_path: Path | str) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path | str) -> None:
    """Create tables and seed admin user (idempotent)."""
    conn = connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT,
                hostname TEXT NOT NULL,
                ssh_port INTEGER NOT NULL DEFAULT 22,
                ssh_username TEXT NOT NULL DEFAULT 'root',
                auth_type TEXT NOT NULL DEFAULT 'password',
                ssh_password TEXT,
                ssh_key_path TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", ("admin",)
        ).fetchone()
        if row is None:
            password = os.environ.get("ADMIN_PASSWORD", "admin123")
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                ("admin", generate_password_hash(password)),
            )
        conn.commit()
    finally:
        conn.close()


def get_user_by_username(db_path: Path | str, username: str):
    conn = connect(db_path)
    try:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    finally:
        conn.close()


def list_servers(db_path: Path | str) -> list:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, label, hostname, ssh_port, ssh_username, auth_type, "
            "ssh_key_path, created_at FROM servers ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_server(db_path: Path | str, server_id: int):
    """Return server including auth secrets for SSH (never pass to templates)."""
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM servers WHERE id = ?", (server_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_server_public(db_path: Path | str, server_id: int):
    """Return server fields safe for templates (no SSH password)."""
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT id, label, hostname, ssh_port, ssh_username, auth_type, "
            "ssh_key_path, created_at FROM servers WHERE id = ?",
            (server_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_server(
    db_path: Path | str,
    *,
    hostname: str,
    ssh_port: int = 22,
    ssh_username: str = "root",
    auth_type: str = "password",
    ssh_password: str | None = None,
    ssh_key_path: str | None = None,
    label: str | None = None,
) -> int:
    conn = connect(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO servers
              (label, hostname, ssh_port, ssh_username, auth_type, ssh_password, ssh_key_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                label or None,
                hostname.strip(),
                int(ssh_port),
                ssh_username.strip() or "root",
                auth_type,
                ssh_password if auth_type == "password" else None,
                ssh_key_path if auth_type == "key" else None,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def update_server(
    db_path: Path | str,
    server_id: int,
    *,
    hostname: str,
    ssh_port: int = 22,
    ssh_username: str = "root",
    auth_type: str = "password",
    ssh_password: str | None = None,
    ssh_key_path: str | None = None,
    label: str | None = None,
    keep_password: bool = False,
) -> bool:
    existing = get_server(db_path, server_id)
    if not existing:
        return False

    password = existing["ssh_password"] if keep_password else ssh_password
    if auth_type != "password":
        password = None

    conn = connect(db_path)
    try:
        conn.execute(
            """
            UPDATE servers SET
              label = ?, hostname = ?, ssh_port = ?, ssh_username = ?,
              auth_type = ?, ssh_password = ?, ssh_key_path = ?
            WHERE id = ?
            """,
            (
                label or None,
                hostname.strip(),
                int(ssh_port),
                ssh_username.strip() or "root",
                auth_type,
                password,
                ssh_key_path if auth_type == "key" else None,
                server_id,
            ),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def delete_server(db_path: Path | str, server_id: int) -> bool:
    conn = connect(db_path)
    try:
        cur = conn.execute("DELETE FROM servers WHERE id = ?", (server_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()
