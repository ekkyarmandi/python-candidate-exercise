"""Development settings.

SQLite is the zero-configuration default; set ``DATABASE_URL`` to use the
PostgreSQL container from ``compose.yml`` instead. Defaults are the safe ones,
so ``DJANGO_DEBUG`` has to be opted into.
"""

from decouple import Csv

from .base import *  # noqa: F403
from .base import BASE_DIR, database_from_url, env, required

DEBUG = env("DJANGO_DEBUG", default=False, cast=bool)
SECRET_KEY = required("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())
CSRF_TRUSTED_ORIGINS = env(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)

DATABASES = database_from_url(
    env("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
    conn_max_age=env("DB_CONN_MAX_AGE", default=0, cast=int),
)
