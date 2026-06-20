"""Auth service — zero Dash imports, independently testable.

Handles user lookup, password hashing/verification, and reset tokens.
All functions take a sqlite3.Connection as the first argument.
"""

from __future__ import annotations

import sqlite3
import time
import uuid

from werkzeug.security import check_password_hash, generate_password_hash

try:
    from python_ulid import ULID
    def _new_id(prefix: str) -> str:
        return prefix + str(ULID())
except ImportError:
    import random, string
    def _new_id(prefix: str) -> str:
        return prefix + "".join(random.choices(string.ascii_lowercase + string.digits, k=20))


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------

def create_user(
    conn: sqlite3.Connection,
    email: str,
    display_name: str,
    password: str,
    is_admin: bool = False,
) -> str:
    """Create a new user. Returns the new user id."""
    user_id = _new_id("u")
    password_hash = generate_password_hash(password)
    now = int(time.time() * 1000)
    conn.execute(
        """INSERT INTO users (id, email, display_name, password_hash, is_admin, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, email.strip().lower(), display_name.strip(), password_hash, int(is_admin), now),
    )
    conn.commit()
    return user_id


def get_user_by_email(conn: sqlite3.Connection, email: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
    ).fetchone()


def get_user_by_id(conn: sqlite3.Connection, user_id: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def verify_password(stored_hash: str, candidate: str) -> bool:
    """Return True if candidate matches the stored Werkzeug hash."""
    return check_password_hash(stored_hash, candidate)


def set_password(conn: sqlite3.Connection, user_id: str, new_password: str) -> None:
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), user_id),
    )
    conn.commit()


def touch_last_login(conn: sqlite3.Connection, user_id: str) -> None:
    conn.execute(
        "UPDATE users SET last_login_at = ? WHERE id = ?",
        (int(time.time() * 1000), user_id),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------

RESET_TOKEN_TTL_MS = 15 * 60 * 1000  # 15 minutes


def generate_reset_token(conn: sqlite3.Connection, user_id: str) -> str:
    """Create a single-use reset token valid for 15 minutes. Returns the token string."""
    token = str(uuid.uuid4())
    expires_at = int(time.time() * 1000) + RESET_TOKEN_TTL_MS
    conn.execute(
        "INSERT INTO login_tokens (token, user_id, purpose, expires_at) VALUES (?, ?, 'reset', ?)",
        (token, user_id, expires_at),
    )
    conn.commit()
    return token


def validate_reset_token(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    """Return the token row if valid and unexpired, else None."""
    now = int(time.time() * 1000)
    return conn.execute(
        """SELECT * FROM login_tokens
           WHERE token = ? AND purpose = 'reset' AND used_at IS NULL AND expires_at > ?""",
        (token, now),
    ).fetchone()


def consume_reset_token(conn: sqlite3.Connection, token: str) -> None:
    """Mark a token as used so it cannot be replayed."""
    conn.execute(
        "UPDATE login_tokens SET used_at = ? WHERE token = ?",
        (int(time.time() * 1000), token),
    )
    conn.commit()
