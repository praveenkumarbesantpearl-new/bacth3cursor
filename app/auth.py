"""Session auth helpers for the demo admin user."""

from __future__ import annotations

import functools

from flask import current_app, flash, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash

from app import db


def login_user(username: str) -> None:
    session.clear()
    session["user"] = username
    session.permanent = False


def logout_user() -> None:
    session.clear()


def current_user() -> str | None:
    return session.get("user")


def verify_admin(username: str, password: str) -> bool:
    if username != "admin":
        return False
    row = db.get_user_by_username(current_app.config["DATABASE"], username)
    if row is None:
        return False
    return check_password_hash(row["password_hash"], password)


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def load_user():
    g.user = current_user()
