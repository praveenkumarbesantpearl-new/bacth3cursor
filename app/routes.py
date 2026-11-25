"""HTTP routes for the demo monitoring UI."""

from __future__ import annotations

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from app import db
from app.auth import login_required, login_user, logout_user, verify_admin
from app.csrf import validate_csrf
from app.ssh_metrics import collect_metrics

bp = Blueprint("main", __name__)


def _db_path() -> str:
    return current_app.config["DATABASE"]


@bp.route("/")
@login_required
def home():
    """Read-only home / dashboard."""
    servers = db.list_servers(_db_path())
    return render_template("home.html", servers=servers)


@bp.route("/login", methods=["GET", "POST"])
def login():
    from app.auth import current_user

    if current_user():
        return redirect(url_for("main.home"))

    if request.method == "POST":
        validate_csrf(request.form.get("csrf_token"))
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if verify_admin(username, password):
            login_user(username)
            flash("Signed in.", "ok")
            next_url = request.args.get("next") or url_for("main.home")
            if not next_url.startswith("/"):
                next_url = url_for("main.home")
            return redirect(next_url)
        flash("Invalid username or password.", "error")

    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    validate_csrf(request.form.get("csrf_token"))
    logout_user()
    flash("Signed out.", "ok")
    return redirect(url_for("main.login"))


@bp.route("/servers")
@login_required
def servers_list():
    servers = db.list_servers(_db_path())
    return render_template("servers.html", servers=servers)


@bp.route("/servers/add", methods=["GET", "POST"])
@login_required
def servers_add():
    if request.method == "POST":
        validate_csrf(request.form.get("csrf_token"))
        hostname = (request.form.get("hostname") or "").strip()
        if not hostname:
            flash("Hostname / IP is required.", "error")
            return render_template("server_form.html", server=None, mode="add")

        auth_type = request.form.get("auth_type") or "password"
        if auth_type not in {"password", "key"}:
            auth_type = "password"

        try:
            port = int(request.form.get("ssh_port") or 22)
        except ValueError:
            flash("SSH port must be a number.", "error")
            return render_template("server_form.html", server=None, mode="add")

        db.add_server(
            _db_path(),
            hostname=hostname,
            ssh_port=port,
            ssh_username=(request.form.get("ssh_username") or "root").strip(),
            auth_type=auth_type,
            ssh_password=request.form.get("ssh_password") or None,
            ssh_key_path=(request.form.get("ssh_key_path") or "").strip() or None,
            label=(request.form.get("label") or "").strip() or None,
        )
        flash("Server added.", "ok")
        return redirect(url_for("main.servers_list"))

    return render_template("server_form.html", server=None, mode="add")


@bp.route("/servers/<int:server_id>/edit", methods=["GET", "POST"])
@login_required
def servers_edit(server_id: int):
    server = db.get_server_public(_db_path(), server_id)
    if not server:
        flash("Server not found.", "error")
        return redirect(url_for("main.servers_list"))

    if request.method == "POST":
        validate_csrf(request.form.get("csrf_token"))
        hostname = (request.form.get("hostname") or "").strip()
        if not hostname:
            flash("Hostname / IP is required.", "error")
            return render_template("server_form.html", server=server, mode="edit")

        auth_type = request.form.get("auth_type") or "password"
        if auth_type not in {"password", "key"}:
            auth_type = "password"

        try:
            port = int(request.form.get("ssh_port") or 22)
        except ValueError:
            flash("SSH port must be a number.", "error")
            return render_template("server_form.html", server=server, mode="edit")

        new_password = request.form.get("ssh_password") or ""
        keep_password = auth_type == "password" and new_password == ""

        db.update_server(
            _db_path(),
            server_id,
            hostname=hostname,
            ssh_port=port,
            ssh_username=(request.form.get("ssh_username") or "root").strip(),
            auth_type=auth_type,
            ssh_password=new_password or None,
            ssh_key_path=(request.form.get("ssh_key_path") or "").strip() or None,
            label=(request.form.get("label") or "").strip() or None,
            keep_password=keep_password,
        )
        flash("Server updated.", "ok")
        return redirect(url_for("main.servers_list"))

    return render_template("server_form.html", server=server, mode="edit")


@bp.route("/servers/<int:server_id>/delete", methods=["POST"])
@login_required
def servers_delete(server_id: int):
    validate_csrf(request.form.get("csrf_token"))
    if db.delete_server(_db_path(), server_id):
        flash("Server removed.", "ok")
    else:
        flash("Server not found.", "error")
    return redirect(url_for("main.servers_list"))


@bp.route("/servers/<int:server_id>")
@login_required
def server_detail(server_id: int):
    server = db.get_server(_db_path(), server_id)
    if not server:
        flash("Server not found.", "error")
        return redirect(url_for("main.servers_list"))

    public = db.get_server_public(_db_path(), server_id)
    metrics = collect_metrics(
        hostname=server["hostname"],
        port=server["ssh_port"],
        username=server["ssh_username"],
        password=server.get("ssh_password"),
        key_path=server.get("ssh_key_path"),
    )
    return render_template(
        "server_detail.html",
        server=public,
        metrics=metrics.to_dict(),
    )
