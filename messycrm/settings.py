import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "interview-exercise-only"
DEBUG = False
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "inertia",
    "django_vite",
    "crm",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "inertia.middleware.InertiaMiddleware",
    "crm.middleware.ShareInertiaErrorsMiddleware",
]
ROOT_URLCONF = "messycrm.urls"
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
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Inertia.js + Vite -------------------------------------------------------

# Vite writes its bundle here; Django serves the same directory as static files.
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
VITE_MANIFEST = FRONTEND_DIST / ".vite" / "manifest.json"
STATICFILES_DIRS = [("crm", FRONTEND_DIST)]



DJANGO_VITE = {
    "default": {
        "dev_mode": DEBUG,
        "dev_server_port": 5173,
        "static_url_prefix": "crm",
        "manifest_path": VITE_MANIFEST,
    }
}

INERTIA_LAYOUT = "crm/app.html"
INERTIA_SSR_ENABLED = False
# Busts stale Inertia pages whenever a new bundle is built; "dev" before the
# first `bun run build`.
# `INERTIA_VERSION` must be identical across instances of a deployment, mtime is
# only a local fallback: set it from the release id (e.g. the commit SHA) in prod.
INERTIA_VERSION = (
    os.environ.get("INERTIA_VERSION")
    or (str(int(VITE_MANIFEST.stat().st_mtime)) if VITE_MANIFEST.exists() else "dev")
)

# `collectstatic` target for deployment; local dev serves from STATICFILES_DIRS.
STATIC_ROOT = BASE_DIR / "staticfiles"
