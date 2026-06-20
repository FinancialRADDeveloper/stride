"""Flask Blueprint for auth routes: login, logout, forgot/reset password."""

from __future__ import annotations

import logging

from flask import Blueprint, redirect, render_template, request
from flask_login import login_user, logout_user

from stride.auth import User
from stride.db import app_db
from stride.services import auth as auth_svc

log = logging.getLogger(__name__)

login_bp = Blueprint("login_bp", __name__)


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", email="")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    conn = app_db()
    row = auth_svc.get_user_by_email(conn, email)
    if row is None or not row["password_hash"]:
        return render_template("login.html", email=email, error="Invalid email or password.")
    if not auth_svc.verify_password(row["password_hash"], password):
        return render_template("login.html", email=email, error="Invalid email or password.")

    user = User.from_row(row)
    login_user(user, remember=True)
    auth_svc.touch_last_login(conn, user.id)

    # Guard against open-redirect attacks
    next_url = request.args.get("next", "/")
    if not next_url.startswith("/"):
        next_url = "/"
    return redirect(next_url)


@login_bp.route("/logout")
def logout():
    logout_user()
    return redirect("/login")


@login_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = request.form.get("email", "").strip()
    conn = app_db()
    row = auth_svc.get_user_by_email(conn, email)

    # Generate token but always show the same message — prevents user enumeration
    if row is not None:
        token = auth_svc.generate_reset_token(conn, row["id"])
        reset_link = f"{request.host_url.rstrip('/')}reset-password?token={token}"
        # TODO: send via Mailgun once configured; logging for now
        log.info("Password reset link for %s: %s", email, reset_link)

    return render_template(
        "forgot_password.html",
        info="If that address is registered, a reset link has been sent.",
    )


@login_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    token = request.args.get("token") or request.form.get("token", "")
    conn = app_db()

    if request.method == "GET":
        token_row = auth_svc.validate_reset_token(conn, token)
        if token_row is None:
            return render_template(
                "reset_password.html",
                valid_token=False,
                token=token,
                error="This reset link is invalid or has expired. Please request a new one.",
            )
        return render_template("reset_password.html", valid_token=True, token=token)

    # POST — validate token then set new password
    token_row = auth_svc.validate_reset_token(conn, token)
    if token_row is None:
        return render_template(
            "reset_password.html",
            valid_token=False,
            token=token,
            error="This reset link is invalid or has expired.",
        )

    password = request.form.get("password", "")
    password2 = request.form.get("password2", "")
    if len(password) < 8:
        return render_template(
            "reset_password.html",
            valid_token=True,
            token=token,
            error="Password must be at least 8 characters.",
        )
    if password != password2:
        return render_template(
            "reset_password.html",
            valid_token=True,
            token=token,
            error="Passwords do not match.",
        )

    auth_svc.set_password(conn, token_row["user_id"], password)
    auth_svc.consume_reset_token(conn, token)
    return redirect("/login?reset=1")
