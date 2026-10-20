#!/usr/bin/env bash
# The single CI entrypoint.
#
# GitHub Actions (and every other runner, later) calls only this script, so the
# checks that gate a merge are exactly the ones a developer can run locally.
# There is no second copy in YAML to drift out of sync.
#
#   ./scripts/ci.sh
#   AUDIT=1 ./scripts/ci.sh      # also run the network dependency audit
#
# Requirements: uv, Node.js 22+ with npm, and a reachable PostgreSQL.
#   DATABASE_URL=postgres://user:password@host:5432/database
#     ...set in the environment or in .env. Required, with no fallback.
#   DB_WAIT_SECONDS=60
#     ...how long to wait for the server before failing. The test database
#     itself is created and dropped by Django; it is never the configured one.

set -euo pipefail

# The suite runs against fixed test settings: no secrets are needed and CI does
# not depend on a developer's .env.
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-messycrm.settings.test}"

if [ -t 1 ]; then
  BOLD=$(printf '\033[1m')
  RESET=$(printf '\033[0m')
else
  BOLD=''
  RESET=''
fi

step() { printf '\n%s==> %s%s\n' "$BOLD" "$*" "$RESET"; }

step "Dependencies: install from the lockfile"
uv sync --locked

# One step, two jobs: prove the effective settings are PostgreSQL,
# wait for the server to accept connections.
# Resolving through Django means a DATABASE_URL in .env counts, exactly as it
# does for the suite itself.
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

step "Python: lint and formatting"
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .

step "Django: system checks"
uv run --no-sync python manage.py check

# Deployment checks run against prod settings with throwaway secrets, so a
# missing security setting fails here instead of in production. Nothing
# connects to the database during `check`.
step "Django: deployment checks (prod settings)"
DJANGO_SETTINGS_MODULE=messycrm.settings.prod \
  DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-ci-only-key-with-enough-unique-characters-0123456789}" \
  DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-localhost,127.0.0.1}" \
  uv run --no-sync python manage.py check --deploy --fail-level WARNING

step "Django: migrations are committed"
uv run --no-sync python manage.py makemigrations --check --dry-run

# The suite renders the real dashboard template, which resolves the Vite
# manifest, so the bundle has to be built before the tests run.
step "Frontend: lint, type check and build"
npm --prefix frontend ci --no-audit --no-fund
npm --prefix frontend run lint
npm --prefix frontend run build

# Coverage is collected in one process on purpose: Django's --parallel workers
# are separate interpreters, and coverage would only see the parent. The suite
# runs in well under a second, so there is nothing to gain from parallelism yet.
step "Tests: Django suite against PostgreSQL with coverage"
uv run --no-sync coverage run manage.py test
uv run --no-sync coverage report

step "AI review: unit tests"
uv run --no-sync python -m unittest discover -s scripts -p "test_*.py"

step "Security: static analysis"
uv run --no-sync bandit -q -r crm messycrm -x '*/migrations/*'

# Vulnerability data changes without the code changing, so the audit is not a
# per-pull-request gate; run it on a schedule (AUDIT=1) instead.
if [ "${AUDIT:-0}" = "1" ]; then
  step "Security: dependency audit"
  uv run --no-sync pip-audit --progress-spinner off
fi

step "All checks passed"
