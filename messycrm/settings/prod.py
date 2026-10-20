"""Production settings.

Nothing that matters has a default: a missing ``DJANGO_SECRET_KEY``,
``DJANGO_ALLOWED_HOSTS`` or ``DATABASE_URL`` stops the process at startup
instead of falling back to something insecure. ``DEBUG`` is not read from the
environment at all, so a stray variable cannot turn it on.
"""

from decouple import Csv

from .base import *  # noqa: F403
from .base import database_from_url, env, required

DEBUG = False

MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

SECRET_KEY = required("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = required("DJANGO_ALLOWED_HOSTS", cast=Csv())
CSRF_TRUSTED_ORIGINS = env("DJANGO_CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

DATABASES = database_from_url(
    required("DATABASE_URL"),
    conn_max_age=env("DB_CONN_MAX_AGE", default=60, cast=int),
)

# TLS is terminated by the reverse proxy in front of the app. Django has to be
# told the original request was secure, and must never answer over plain HTTP.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env("DJANGO_SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_HSTS_SECONDS = env("DJANGO_SECURE_HSTS_SECONDS", default=3600, cast=int)
# Only correct when every subdomain is served over HTTPS; keep it True and
# serve subdomains over HTTPS, or set SECURE_HSTS_SECONDS=0 while migrating.
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# Adds the `preload` token to the header. Being preloaded is a separate,
# deliberate submission to the browser vendors' list.
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
