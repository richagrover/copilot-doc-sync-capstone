from __future__ import annotations

import os
import secrets
from pathlib import Path
from typing import Any

from flask import Flask, abort, flash, g, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.exceptions import HTTPException

import logging_config
from auth import bp as auth_bp, login_required
from db import initialize_database
from logging_config import log_event
from task_store import (
    PRIORITIES,
    STATUSES,
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)

csrf = CSRFProtect()


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("TASK_MANAGER_SECRET_KEY") or secrets.token_hex(32),
        DATABASE=str(Path(app.instance_path) / "tasks.db"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config is not None:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    initialize_database(app.config["DATABASE"])
    logging_config.configure()
    csrf.init_app(app)
    app.register_blueprint(auth_bp)

    @app.get("/")
    @login_required
    def index():
        status = request.args.get("status", "").strip()
        priority = request.args.get("priority", "").strip()
        if status and status not in STATUSES:
            abort(400, description="Unsupported status filter.")
        if priority and priority not in PRIORITIES:
            abort(400, description="Unsupported priority filter.")

        tasks = list_tasks(
            app.config["DATABASE"],
            int(g.user["id"]),
            status=status or None,
            priority=priority or None,
        )
        return render_template(
            "index.html",
            tasks=tasks,
            statuses=STATUSES,
            priorities=PRIORITIES,
            selected_status=status,
            selected_priority=priority,
        )

    @app.post("/tasks")
    @login_required
    def create_task_route():
        title, description, status, priority = _task_form_values(allow_defaults=True)
        _validate_task(title, status, priority)
        task_id = create_task(
            app.config["DATABASE"],
            int(g.user["id"]),
            title=title,
            description=description,
            status=status,
            priority=priority,
        )
        log_event("task.create", user_id=int(g.user["id"]), detail=f"task_id={task_id}")
        flash("Task created.", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>")
    @login_required
    def update_task_route(task_id: int):
        if get_task(app.config["DATABASE"], int(g.user["id"]), task_id) is None:
            abort(404)

        title, description, status, priority = _task_form_values(allow_defaults=False)
        _validate_task(title, status, priority)
        update_task(
            app.config["DATABASE"],
            int(g.user["id"]),
            task_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
        )
        log_event("task.update", user_id=int(g.user["id"]), detail=f"task_id={task_id}")
        flash("Task updated.", "success")
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    @login_required
    def delete_task_route(task_id: int):
        if not delete_task(app.config["DATABASE"], int(g.user["id"]), task_id):
            abort(404)
        log_event("task.delete", user_id=int(g.user["id"]), detail=f"task_id={task_id}")
        flash("Task deleted.", "success")
        return redirect(url_for("index"))

    @app.errorhandler(HTTPException)
    def log_http_error(error: HTTPException):
        user_id = int(g.user["id"]) if getattr(g, "user", None) else None
        log_event(
            "http.error",
            user_id=user_id,
            detail=f"{error.code} {request.method} {request.path}",
        )
        return error

    return app


def _task_form_values(*, allow_defaults: bool) -> tuple[str, str, str, str]:
    return (
        request.form.get("title", "").strip(),
        request.form.get("description", "").strip(),
        request.form.get("status", "todo" if allow_defaults else "").strip(),
        request.form.get("priority", "medium" if allow_defaults else "").strip(),
    )


def _validate_task(title: str, status: str, priority: str) -> None:
    if not title:
        abort(400, description="Task title is required.")
    if len(title) > 200:
        abort(400, description="Task title must be 200 characters or fewer.")
    if status not in STATUSES:
        abort(400, description="Unsupported task status.")
    if priority not in PRIORITIES:
        abort(400, description="Unsupported task priority.")


if __name__ == "__main__":
    create_app().run(host="127.0.0.1")
