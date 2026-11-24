"""Demo Linux server monitoring Flask application."""

from flask import Flask


def create_app() -> Flask:
    """Application factory for the local demo app."""
    app = Flask(__name__)

    # Demo-only: override SECRET_KEY via env before any shared use.
    app.config["SECRET_KEY"] = "dev-only-change-me"

    from app.routes import bp

    app.register_blueprint(bp)
    return app
