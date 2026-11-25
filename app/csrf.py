"""Minimal CSRF protection for form POSTs."""

from __future__ import annotations

import secrets

from flask import abort, session


def ensure_csrf_token() -> str:
    token = session.get("_csrf")
    if not token:
        token = secrets.token_hex(16)
        session["_csrf"] = token
    return token


def validate_csrf(token: str | None) -> None:
    expected = session.get("_csrf")
    if not token or not expected or not secrets.compare_digest(token, expected):
        abort(400, description="Invalid CSRF token")
