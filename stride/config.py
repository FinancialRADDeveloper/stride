import os
from pathlib import Path

# Root of the repo (one level up from this file's package directory)
REPO_ROOT = Path(__file__).parent.parent

# DATA_DIR holds the SQLite file (and the Fernet key).
# In Docker the volume is mounted at /data; locally it stays at REPO_ROOT/data.
DATA_DIR = Path(os.environ.get("DATA_DIR", str(REPO_ROOT / "data")))
DB_PATH = DATA_DIR / "stride.db"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Google OAuth redirect — Dash runs on this port by default
OAUTH_REDIRECT_URI = "http://localhost:8050/oauth/callback"

# Fernet key for encrypting OAuth tokens; generate once and store at this path
FERNET_KEY_PATH = DATA_DIR / ".fernet.key"

# Override with env var in production / CI
STRIDE_SECRET = os.environ.get("STRIDE_SECRET")

DASH_PORT = int(os.environ.get("STRIDE_PORT", 8050))
DASH_DEBUG = os.environ.get("STRIDE_DEBUG", "false").lower() == "true"
