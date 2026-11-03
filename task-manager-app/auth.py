from __future__ import annotations

import functools
from typing import Callable

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

import session_store
import user_store
from logging_config import log_event

bp = Blueprint("auth", __name__)

SESSION_TOKEN_KEY = "session_token"
GENERIC_LOGIN_ERROR = "Invalid username or password."


@bp.before_app_request
def load_logged_in_user() -> None:
    g.user = None
    token = session.get(SESSION_TOKEN_KEY)
    if not token:
        return
    database = current_app.config["DATABASE"]
    user_id = session_store.resolve_session(database, token)
    if user_id is not None:
        g.user = user_store.get_user(database, user_id)
    if g.user is None:
        session.clear()


def login_required(view: Callable) -> Callable:
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped_view


@bp.get("/register")
def register_form():
    if g.user is not None:
        return redirect(url_for("index"))
    return render_template("register.html")


@bp.post("/register")
def register():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    error = _validate_registration(username, password)
    if error is None:
        user_id = user_store.create_user(
            current_app.config["DATABASE"],
            username=username,
            password_hash=generate_password_hash(password),
        )
        if user_id is None:
            error = "That username is already taken."

    if error is not None:
        return render_template("register.html", error=error, username=username), 400

    log_event("auth.register", user_id=user_id)
    flash("Account created. Please sign in.", "success")
    return redirect(url_for("auth.login"))


@bp.get("/login")
def login_form():
    if g.user is not None:
        return redirect(url_for("index"))
    return render_template("login.html", next=_safe_next(request.args.get("next")))


@bp.post("/login")
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    database = current_app.config["DATABASE"]

    user = user_store.find_by_username(database, username)
    if user is None or not check_password_hash(str(user["password_hash"]), password):
        log_event("auth.login.failure", detail="invalid credentials")
        return render_template("login.html", error=GENERIC_LOGIN_ERROR, username=username), 400

    _rotate_session(database, int(user["id"]))
    log_event("auth.login.success", user_id=int(user["id"]))
    return redirect(_safe_next(request.form.get("next")) or url_for("index"))


@bp.post("/logout")
@login_required
def logout():
    database = current_app.config["DATABASE"]
    token = session.get(SESSION_TOKEN_KEY)
    if token:
        session_store.delete_session(database, token)
    user_id = int(g.user["id"])
    session.clear()
    log_event("auth.logout", user_id=user_id)
    flash("Signed out.", "success")
    return redirect(url_for("auth.login"))


def _rotate_session(database: str, user_id: int) -> None:
    """Issue a fresh server-side session, invalidating any previous token."""
    old_token = session.get(SESSION_TOKEN_KEY)
    if old_token:
        session_store.delete_session(database, old_token)
    session.clear()
    session[SESSION_TOKEN_KEY] = session_store.create_session(database, user_id)


def _validate_registration(username: str, password: str) -> str | None:
    if not (user_store.USERNAME_MIN <= len(username) <= user_store.USERNAME_MAX):
        return (
            f"Username must be between {user_store.USERNAME_MIN} and "
            f"{user_store.USERNAME_MAX} characters."
        )
    if len(password) < user_store.PASSWORD_MIN:
        return f"Password must be at least {user_store.PASSWORD_MIN} characters."
    return None


def _safe_next(target: str | None) -> str | None:
    """Allow only local absolute paths as post-login redirect targets."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None
