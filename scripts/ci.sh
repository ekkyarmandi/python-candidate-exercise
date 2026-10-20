#!/usr/bin/env bash
# CI entrypoint. No argument runs every stage; pass one stage to run only it.
#
#   ./scripts/ci.sh [all|static|frontend|test|unit|audit]
#
# Requires uv, Node.js 22+ and PostgreSQL for `test`.
# DATABASE_URL=postgres://user:password@host:5432/database (or a .env file)
# DB_WAIT_SECONDS=60

set -euo pipefail

STAGE="${1:-all}"

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-messycrm.settings.test}"

if [ -t 1 ]; then
  BOLD=$(printf '\033[1m')
  RESET=$(printf '\033[0m')
else
  BOLD=''
  RESET=''
fi

step() { printf '\n%s==> %s%s\n' "$BOLD" "$*" "$RESET"; }

usage() {
  printf 'usage: %s [all|static|frontend|test|unit|audit]\n' "$0" >&2
  exit 2
}

case "$STAGE" in
  all | static | frontend | test | unit | audit) ;;
  *) usage ;;
esac

dependencies() {
  step "Dependencies: install from the lockfile"
  uv sync --locked
}

static() {
  step "Python: lint and formatting"
  uv run --no-sync ruff check .
  uv run --no-sync ruff format --check .

  step "Django: system checks"
  uv run --no-sync python manage.py check

  step "Django: deployment checks (prod settings)"
  DJANGO_SETTINGS_MODULE=messycrm.settings.prod \
    DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-ci-only-key-with-enough-unique-characters-0123456789}" \
    DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1}" \
    DATABASE_URL="${DATABASE_URL:-postgres://ci:ci@localhost:5432/ci}" \
    uv run --no-sync python manage.py check --deploy --fail-level WARNING

  step "Django: migrations are committed"
  uv run --no-sync python manage.py makemigrations --check --dry-run

  step "Security: static analysis"
  uv run --no-sync bandit -q -r crm messycrm -x '*/migrations/*'
}

frontend() {
  step "Frontend: lint, type check and build"
  npm --prefix frontend ci --no-audit --no-fund
  npm --prefix frontend run lint
  npm --prefix frontend run build
}

require_frontend_build() {
  if [ ! -f crm/static/crm/dist/.vite/manifest.json ]; then
    printf '%s\n' \
      "The Vite manifest is missing: the dashboard template cannot resolve the bundle." \
      "Run './scripts/ci.sh frontend' first (CI passes it on as an artifact)." >&2
    exit 1
  fi
}

test_suite() {
  step "Frontend: bundle is present"
  require_frontend_build

  step "Database: require PostgreSQL and wait for it"
  uv run --no-sync python - <<'PY'
import os
import sys
import time

import django
from django.conf import settings
from django.db import connections
from django.db.utils import Error as DatabaseError

django.setup()

database = settings.DATABASES["default"]
if database["ENGINE"] != "django.db.backends.postgresql":
    sys.exit(
        "This pipeline runs against PostgreSQL only.\n"
        f"  effective engine: {database['ENGINE']}\n"
        "  Set DATABASE_URL=postgres://user:password@host:5432/database\n"
        "  in the environment or in .env, then run the script again."
    )

deadline = time.monotonic() + float(os.environ.get("DB_WAIT_SECONDS", "60"))
while True:
    try:
        connections["default"].ensure_connection()
        break
    except DatabaseError as exc:
        if time.monotonic() >= deadline:
            sys.exit(f"PostgreSQL at {database['HOST']} did not become available: {exc}")
        time.sleep(1)

port = database["PORT"] or 5432
print(f"connected: {database['HOST']}:{port}/{database['NAME']}")
PY

  step "Tests: Django suite against PostgreSQL with coverage"
  uv run --no-sync coverage run manage.py test
  uv run --no-sync coverage report
}

unit() {
  step "AI review: unit tests"
  uv run --no-sync python -m unittest discover -s scripts -p "test_*.py"
}

audit() {
  step "Security: dependency audit"
  uv run --no-sync pip-audit --progress-spinner off
}

if [ "$STAGE" = "all" ]; then
  dependencies
  static
  frontend
  test_suite
  unit

  if [ "${AUDIT:-0}" = "1" ]; then
    audit
  fi

  step "All checks passed"
  exit 0
fi

if [ "$STAGE" != "frontend" ]; then
  dependencies
fi

case "$STAGE" in
  static) static ;;
  frontend) frontend ;;
  test) test_suite ;;
  unit) unit ;;
  audit) audit ;;
esac

step "Stage '$STAGE' passed"
