-- Users table — one row per person who can log in.
-- password_hash is nullable so future OAuth-only users can exist
-- without a local password.
CREATE TABLE IF NOT EXISTS users (
    id             TEXT PRIMARY KEY,          -- 'u' + ulid
    email          TEXT UNIQUE NOT NULL,      -- lowercased, used as login identity
    display_name   TEXT NOT NULL DEFAULT '',
    password_hash  TEXT,                      -- Werkzeug PBKDF2; NULL for OAuth-only accounts
    is_admin       INTEGER NOT NULL DEFAULT 0,
    created_at     INTEGER NOT NULL,          -- unix ms
    last_login_at  INTEGER                    -- unix ms, NULL = never
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Short-lived single-use tokens for password reset.
CREATE TABLE IF NOT EXISTS login_tokens (
    token       TEXT PRIMARY KEY,             -- UUID, cryptographically random
    user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    purpose     TEXT NOT NULL CHECK (purpose IN ('reset')),
    expires_at  INTEGER NOT NULL,             -- unix ms
    used_at     INTEGER                       -- unix ms; NULL = not yet used
);
