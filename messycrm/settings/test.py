"""Test settings: no secrets required.

``SECRET_KEY`` and the hosts are fixed here so the suite never depends on the
developer's ``.env``. The database comes from ``DATABASE_URL``; it defaults to
SQLite for a quick local run, while ``scripts/ci.sh`` requires PostgreSQL.
"""

from .base import *  # noqa: F403
from .base import BASE_DIR, database_from_url, env

DEBUG = False
# A public constant, not a credential: test settings must be independent of
# the environment, and this key is never used outside the suite.
SECRET_KEY = "test-only-key-that-is-never-used-outside-the-test-suite"  # nosec B105
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

# Hashing speed is irrelevant to test correctness and dominates suite runtime
# once authentication is covered.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

DATABASES = database_from_url(
    env("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    conn_max_age=0,
)
