"""Settings shared by every environment.

``local``, ``test`` and ``prod`` import everything from here and override what
differs. Keeping the shared structure in one place means a new installed app or
middleware is added once, in a module that every environment already reads.
"""

from pathlib import Path

import dj_database_url
from decouple import UndefinedValueError, config
from django.core.exceptions import ImproperlyConfigured

# messycrm/settings/base.py -> repository root
BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env(name, default=None, cast=str):
    """Read an optional variable, falling back to ``default``."""
    return config(name, default=default, cast=cast)


def required(name, cast=str):
    """Read a mandatory variable, failing with an actionable message."""
    try:
        return config(name, cast=cast)
    except UndefinedValueError:
        raise ImproperlyConfigured(
            f"{name} is not set. Copy .env.example to .env and fill it in, "
            f"or export {name} in the environment."
        ) from None


def database_from_url(url, conn_max_age=0):
    """Build the ``DATABASES`` mapping from a ``dj-database-url`` URL string."""
    return {
        "default": dj_database_url.parse(
            url,
            conn_max_age=conn_max_age,
            conn_health_checks=True,
        )
    }


DEBUG = False

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "crm",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "messycrm.urls"
CSRF_FAILURE_VIEW = "crm.api.csrf_failure"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "messycrm.wsgi.application"

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
