"""Demo Linux server monitoring Flask application."""

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask

from app import db
from app.auth import load_user
from app.csrf import ensure_csrf_token


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory for the local demo app."""
    app = Flask(__name__)

    default_db = Path(__file__).resolve().parent.parent / "data" / "monitor.db"
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=str(default_db),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config:
        app.config.update(test_config)

    db.init_db(app.config["DATABASE"])

    @app.before_request
    def _before_request():
        load_user()
        ensure_csrf_token()

    @app.context_processor
    def inject_globals():
        from app.auth import current_user
        from app.csrf import ensure_csrf_token as csrf_token

        return {
            "current_user": current_user(),
            "csrf_token": csrf_token(),
        }

    from app.routes import bp

    app.register_blueprint(bp)
    return app
