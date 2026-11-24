"""HTTP routes for the demo monitoring UI."""

from flask import Blueprint, render_template

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    """Read-only home / dashboard shell."""
    return render_template("home.html")
