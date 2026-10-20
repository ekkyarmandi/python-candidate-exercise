# Jellybean CRM — live refactoring exercise

This is a small, working Django CRM screen. It is intentionally messy and resembles a feature that grew quickly in production. Your task is **not** to rewrite everything. Improve it safely while using your preferred IDE and AI coding agent.

## Run it

You need Python 3.14 (the version in `pyproject.toml`) with `pip` and `venv`, plus Node.js 22+ for the frontend build. The default database is SQLite; `compose.yml` provides PostgreSQL 16 when you want parity with CI.

From this directory, create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with `.venv\Scripts\Activate.ps1` instead. If your system uses `python3`, use that for the first command.

Then install the dependencies, start the database, create your local
configuration, prepare the schema, and start Jellybean CRM:

```bash
python -m pip install -r requirements.txt
docker compose up -d     # PostgreSQL 16; skip if DATABASE_URL points at SQLite
cp .env.example .env     # then fill in DJANGO_SECRET_KEY and the DB_* values
cd frontend && npm ci && npm run build && cd ..
python manage.py migrate
python manage.py seed_crm
python manage.py runserver
```

The project also ships `pyproject.toml` and `uv.lock`; `uv sync` is an equivalent,
faster way to install the same dependencies, and it also installs the quality
tooling (`ruff`, `coverage`, `bandit`, `pip-audit`) that `scripts/ci.sh` needs.
Production installs skip that group with `uv sync --no-dev --locked`.

The `npm run build` step is required: Django serves the compiled bundle from
`crm/static/crm/dist/`, which is generated and not committed. Skip it and the page
shows "Failed to load the CRM client. Check your connection and reload."

Open http://127.0.0.1:8000/. Five sample contacts will be ready to explore; no login is required. You can rerun `seed_crm` without duplicating the sample contacts. Keep the server running in your terminal and stop it with Ctrl+C.

## Configuration

Settings are read from the environment, with `.env` (git-ignored) as the local
default. Real environment variables always take precedence over `.env`, so CI and
production never need the file. `.env.example` documents every supported variable.

### Settings modules

`messycrm/settings/` contains one module per environment, chosen with
`DJANGO_SETTINGS_MODULE`:

| Module | Selected by | Behaviour |
|---|---|---|
| `messycrm.settings.local` | `manage.py` default | Reads `.env`; SQLite unless `DATABASE_URL` points at PostgreSQL |
| `messycrm.settings.test` | `scripts/ci.sh` | Fixed key, `DEBUG` off, no `.env` necessary; `DATABASE_URL` may default to SQLite for a quick local run |
| `messycrm.settings.prod` | `wsgi.py` default | `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and `DATABASE_URL` are mandatory; HTTPS and cookie hardening on |

`messycrm/settings/base.py` holds everything the three share; only the values
that genuinely differ between environments live in the modules above.

### Environment variables

| Variable | Required | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | yes | — |
| `DJANGO_DEBUG` | no | `False` |
| `DJANGO_ALLOWED_HOSTS` | no | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | no | `http://localhost:5173,http://127.0.0.1:5173` |
| `DATABASE_URL` | no | `sqlite:///<project>/db.sqlite3` |
| `DB_CONN_MAX_AGE` | no | `0` |

Generate a key for your local `.env` with:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

The defaults are the safe ones (`DEBUG` off, no wildcard `ALLOWED_HOSTS`), so set
`DJANGO_DEBUG=True` in `.env` for local development — Django only serves the
compiled frontend assets when `DEBUG` is on.

The database is a single `DATABASE_URL` string parsed by `dj-database-url`. The
local setup uses PostgreSQL through `docker compose up -d` (see below), and the
`.env` values drive both sides:

```
DATABASE_URL=postgres://messycrm:secret@localhost:5432/messycrm
```

Omit `DATABASE_URL` entirely to fall back to SQLite. `postgres://`,
`postgresql://` and `sqlite:///relative/path.db` all work; URL-encode the password
if it contains `@ : / ? # %`.

## Database

PostgreSQL 16 runs in Docker and is defined in `compose.yml`:

```bash
docker compose up -d      # start it (first run creates the messycrm database)
docker compose ps         # check it is healthy
docker compose logs db    # if a connection fails
docker compose down       # stop, keeping data in the pgdata volume
docker compose down -v    # stop and delete the data
```

The container creates the `messycrm` database and a `messycrm` role from the
`POSTGRES_*` values in `.env`, so Django and the container never disagree about
credentials. To inspect it:

```bash
docker exec -it messycrm-db psql -U messycrm -d messycrm
```

`docker` needs group membership: `sudo usermod -aG docker $USER`, then log out and
back in (or use `sg docker -c "<command>"` in the current shell).

To go back to a file-based database, remove `DATABASE_URL` from `.env` (or set
it to `sqlite:///db.sqlite3`) and stop the container; nothing else changes.

For later sessions, activate `.venv` and run `python manage.py runserver` again. If port 8000 is busy, use `python manage.py runserver 8001` and open http://127.0.0.1:8001/.

Verify the setup with the same script CI runs:

```bash
./scripts/ci.sh
```

For just the suite, use the test settings (no `.env` needed):

```bash
DJANGO_SETTINGS_MODULE=messycrm.settings.test python manage.py test
```

This setup is for local interview use. Local data lives in the database
`DATABASE_URL` points at, and the tests use a separate test database.

### Backend container

The backend can run in Docker the way it will be deployed: gunicorn, production
settings, static files served by WhiteNoise and a non-root user. The image builds
the Vite bundle and installs only the locked production dependencies.

```bash
docker compose --profile app up -d --build   # db + migrate + web
curl http://127.0.0.1:8000/health/
docker compose --profile app logs -f web
docker compose --profile app down            # the database keeps its data
```

Use the profile for `down` as well: a plain `docker compose down` only stops
services in the active profiles, so it removes the database, leaves the backend
running, and reports that the network is still in use.

`migrate` is a one-shot service that must exit successfully before `web` starts,
so the app never comes up against a half-migrated schema. Inside the compose
network `DATABASE_URL` points at the `db` service, and
`DJANGO_SECURE_SSL_REDIRECT` is off because TLS is terminated in front of the
stack. `WEB_PORT` changes the published port.

### Frontend

The CRM screen is a React 19 + TypeScript single-page app built with Vite 8.
Django renders the shell and the initial payload, and the built bundle takes over
in the browser. Source lives in `frontend/`; the build lands in
`crm/static/crm/dist/` and is served by Django, so there is no third-party CDN and
no separate frontend service in production.

Build and run:

```bash
cd frontend
npm ci
npm run build          # tsc -b && vite build
cd ..
python manage.py runserver
```

For UI work, run the Vite dev server next to Django:

```bash
python manage.py runserver 127.0.0.1:8000   # terminal 1
cd frontend && npm run dev                  # terminal 2 → http://localhost:5173
```

The dev server proxies `/api`, `/export`, and `/static` to Django and keeps
`localhost:5173` (and `127.0.0.1:5173`) in `CSRF_TRUSTED_ORIGINS`. Because the
Vite page has no embedded payload, the client fetches the list on boot and calls
`/api/csrf/` to obtain a CSRF token before its first mutation.

`crm/templatetags/vite.py` resolves the hashed entry from the Vite manifest, so
the template never hardcodes asset names. Do not commit `crm/static/crm/dist/`;
rebuild it in CI or before deploying. The Django test suite renders the real
template, so run `npm run build` before `python manage.py test`.

The client talks to the JSON endpoints under `/api/contacts/` (list, detail,
create, status, notes, delete). The original form-encoded `action` posts on `/`
are still accepted for compatibility; they are handled by the same validation and
service code.

Client structure:

```
frontend/src/
  main.tsx               mounts <App> into #crm-app
  App.tsx                URL/notice state + mutation handlers
  types.ts               API payload and UI types
  components/            one component per file
    Stats, Toolbar, Field, ContactsPanel, ContactRow, NewContactForm,
    DetailPanel, ContactDetail, StatusForm, NoteForm, DeleteAction, ActivityFeed
  data/
    payload.ts           embedded-payload parsing, status choices, selection fallback
    useCrmData.ts        data hook (abort + stale-response guard)
  lib/
    api.ts               fetch wrapper, CSRF bootstrap, ApiError
    url.ts               query-string state helpers
    format.ts            Intl money/date formatters
  index.css              focus, responsive, and reduced-motion styles
```

## Continuous integration

`scripts/ci.sh` is the single entrypoint, split into stages. CI runs one stage
per job, so independent checks finish in parallel, and a final `gate` job
requires all of them. With no argument the script runs every stage in order, so
the merge gate cannot drift from what a developer can run locally:

```bash
./scripts/ci.sh              # every stage, against PostgreSQL from the environment or .env
./scripts/ci.sh static       # ruff, Django checks, migrations, bandit
./scripts/ci.sh frontend     # npm ci, lint, Vite build
./scripts/ci.sh test         # Django suite; needs the built frontend
./scripts/ci.sh unit         # the AI reviewer's own tests
./scripts/ci.sh audit        # dependency audit (needs network)
AUDIT=1 ./scripts/ci.sh      # every stage, including the audit
```

It requires `uv`, Node.js 22+, and a reachable PostgreSQL for `test`.
`DATABASE_URL` must resolve to a `postgres://` URL (in the environment or
`.env`); a SQLite fallback
is refused, because a SQLite pass hides the query, ordering and cast differences
that only appear on the engine production uses. Start the database with
`docker compose up -d`; `DB_WAIT_SECONDS` (default 60) controls how long the
script waits for it to accept connections. Django creates and drops its own test
database, so the configured one is never touched.

`all` runs the stages in this order:

| Stage | Step | Command | Fails when |
|---|---|---|---|
| all | Dependencies | `uv sync --locked` | `uv.lock` is out of date with `pyproject.toml` |
| static | Lint and format | `ruff check .`, `ruff format --check .` | style or import problems |
| static | System checks | `manage.py check` | the project is misconfigured |
| static | Deployment checks | `manage.py check --deploy --fail-level WARNING` with prod settings | a security setting regresses, e.g. `DEBUG` or insecure cookies |
| static | Migrations | `manage.py makemigrations --check --dry-run` | a model change was committed without its migration |
| static | Static security | `bandit -r crm messycrm` | a new medium or high finding |
| frontend | Frontend | `npm ci`, `oxlint`, `tsc -b && vite build` | the bundle does not build; the suite renders the real template, so the build comes first |
| test | Database | resolves settings, waits for connections | the effective engine is not PostgreSQL, or the server never answers |
| test | Tests | `coverage run manage.py test`, `coverage report` | a test fails, or coverage drops below `fail_under` in `pyproject.toml` |
| unit | AI review script | `python -m unittest discover -s scripts` | the advisory reviewer's own logic breaks |
| audit | Dependency audit | `pip-audit` | a pinned dependency has a known vulnerability |

The checks are deterministic because the dependency set is locked, migrations
must be committed, the test settings module needs no ambient secrets, and the
same commands run locally and in CI. `pip-audit` is opt-in: its findings change
without the code changing, so it belongs on a schedule rather than on every pull
request.

### Merge gate in GitHub Actions

| Workflow | Trigger | Required |
|---|---|---|
| `.github/workflows/test.yml` | `pull_request`, `push` to `main`, manual | yes — the merge gate |
| `.github/workflows/ai-review.yml` | `pull_request` | no — advisory |
| `.github/workflows/audit.yml` | weekly schedule, manual | no — dependency audit |

`test.yml` runs one job per stage:

```
static ────┐
unit ──────┼──> gate
frontend ──┤
test ──────┘   (test also needs frontend)
```

`test` needs `frontend` because the suite resolves the Vite manifest; the
frontend job uploads the bundle as a short-lived artifact and `test` downloads
it instead of rebuilding. Everything else runs in parallel, and `gate` is a
fan-in job with `if: always()` that fails unless every stage succeeded.

`gate` is the only required status check. Adding, removing or reordering a
stage is therefore a change to the workflow, not to the repository settings.
`test.yml` needs no secrets, so pull requests from forks run it as well.

To make it a gate:

1. Open a pull request once so GitHub has seen the check.
2. Settings → Branches → add a protection rule for `main`, enable "Require
   status checks to pass", and select `CI / gate`.
3. Leave `AI review / review` unselected so the reviewer can fail without
   blocking a merge.

The same through the API:

```bash
gh api --method PUT repos/{owner}/{repo}/branches/main/protection --input - <<'JSON'
{
  "required_status_checks": {"strict": false, "contexts": ["CI / gate"]},
  "enforce_admins": true,
  "required_pull_request_reviews": null,
  "restrictions": null
}
JSON
```

Keep `strict` off: with it on, every merge to `main` forces every open pull
request to re-run CI. Do not add `paths-ignore` to `test.yml` either — a required
check that never runs leaves docs-only pull requests unmergeable.

## AI review (advisory)

`.github/workflows/ai-review.yml` runs `scripts/ai_review.py` on pull requests
that touch application code, and keeps **one** sticky comment up to date. The
workflow's `paths` filter lists the code roots (`crm/`, `messycrm/`, `scripts/`,
`frontend/src/`, plus `frontend/index.html` and `manage.py`), so a pull request
that only changes documentation,
configuration, workflows or lockfiles never starts the job or pays for a model
call. A mixed pull request still runs, but the script drops the non-code files
from the reviewed set. It is not a gate: the job exits 0 when the model errors,
times out, the secret is missing, or the PR comes from a fork, so it can never
block a merge.

What it sends: the diff (capped at 60k characters), the full contents of the
changed files plus their first-party imports (capped), and the same rubric the
local agent uses — `.pi/skills/django-reviewer/SKILL.md`. Documentation, YAML/TOML
configuration, lockfiles, the Vite bundle, binaries and migrations (unless the
PR is migration-only) are skipped.
PR text and code are wrapped in an `<untrusted>` block and the system prompt says
to treat them as data, never as instructions.

| Variable | Purpose |
|---|---|
| `DEEPSEEK_API_KEY` | repository secret; without it the job skips and exits 0 |
| `AI_REVIEW_MODEL` | optional, defaults to `deepseek-chat` |
| `GITHUB_TOKEN` | provided by Actions; posts or updates the comment |

Run it locally against a saved diff; this prints the comment instead of posting:

```bash
git show HEAD --format= > /tmp/pr.diff
AI_REVIEW_DIFF_FILE=/tmp/pr.diff DEEPSEEK_API_KEY=... python scripts/ai_review.py
```

Findings are labelled `blocking`, `should-fix` or `nit`, ordered by severity, and
the workflow step summary records the model, latency and counts. The metric that
matters is the accept rate: if findings are consistently wrong, fix the rubric in
`.pi/skills/django-reviewer`, which both the local agent and CI read.

## OpenSpec

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) to plan changes. Install the CLI globally with npm (Node.js required):

```bash
npm install -g @fission-ai/openspec@latest
```

Then initialize OpenSpec in the project root:

```bash
openspec init
```

Planning artifacts live under `openspec/`. Once initialized, you can list and inspect changes with:

```bash
openspec list
openspec status --change <change-name>
```

## Timebox

45 minutes total. Spend the first 5 minutes inspecting and explaining your plan. Make one or more meaningful improvements, then verify them.

## Goal

Improve maintainability without breaking current behaviour. Choose the highest-value work you can finish. Examples include:

- Separate responsibilities in the Django code.
- Improve the frontend structure.
- Remove duplication or unsafe/manual URL handling.
- Improve validation, queries, tests or error handling.
- Introduce a clear pattern that future engineers can follow.

## Rules

- Use any AI coding agent you normally use. Screen-share your process.
- You may ask the interviewer questions and make reasonable assumptions.
- Keep the app runnable. Do not spend the session polishing visuals.
- Explain what you asked the agent to do, what you accepted/rejected, and why.
- Finish by showing the diff and running relevant tests.

We assess judgement, AI collaboration, code quality, verification and communication—not the amount of code changed.
