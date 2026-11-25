"""SQLite init / seed tests."""

from pathlib import Path

from app import db


def test_init_db_creates_admin(tmp_path):
    path = tmp_path / "a.db"
    db.init_db(path)
    user = db.get_user_by_username(path, "admin")
    assert user is not None
    assert user["username"] == "admin"
    assert user["password_hash"]
    assert "admin123" not in user["password_hash"]


def test_init_db_idempotent(tmp_path):
    path = tmp_path / "b.db"
    db.init_db(path)
    db.init_db(path)
    conn = db.connect(path)
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    finally:
        conn.close()
    assert count == 1
    assert Path(path).exists()
