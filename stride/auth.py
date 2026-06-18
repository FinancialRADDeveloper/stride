"""Flask-Login wiring — User model, LoginManager, session guard.

Imported once inside create_app(); nothing here touches Dash directly.
"""

from __future__ import annotations

from flask import Flask, redirect, request
from flask_login import LoginManager, UserMixin, current_user

from stride.db import app_db
from stride.services.auth import get_user_by_id, touch_last_login


# ---------------------------------------------------------------------------
# User model (Flask-Login contract)
# ---------------------------------------------------------------------------

class User(UserMixin):
    """Thin wrapper around a users DB row for Flask-Login."""

    def __init__(self, id: str, email: str, display_name: str, is_admin: bool):
        self.id = id
        self.email = email
        self.display_name = display_name
        self.is_admin = is_admin

    @classmethod
    def from_row(cls, row) -> "User":
        return cls(
            id=row["id"],
            email=row["email"],
            display_name=row["display_name"],
            is_admin=bool(row["is_admin"]),
        )


# ---------------------------------------------------------------------------
# Paths that do not require authentication
# ---------------------------------------------------------------------------

_PUBLIC_PREFIXES = (
    "/login",
    "/logout",
    "/forgot-password",
    "/reset-password",
    "/health",
    "/favicon.ico",
)


# ---------------------------------------------------------------------------
# Setup function — called from create_app()
# ---------------------------------------------------------------------------

def init_login(server: Flask, secret_key: str) -> LoginManager:
    """Attach Flask-Login to the Flask server and return the LoginManager."""

    server.secret_key = secret_key

    login_manager = LoginManager()
    login_manager.init_app(server)
    login_manager.login_view = "login_bp.login"

    @login_manager.user_loader
    def load_user(user_id: str):
        conn = app_db()
        row = get_user_by_id(conn, user_id)
        if row is None:
            return None
        return User.from_row(row)

    @server.before_request
    def _require_login():
        # Let public paths and Dash static assets through unauthenticated
        if any(request.path.startswith(p) for p in _PUBLIC_PREFIXES):
            return
        # Dash's own asset serving — no sensitive data
        if request.path.startswith("/assets/"):
            return
        if not current_user.is_authenticated:
            return redirect("/login")

    return login_manager
