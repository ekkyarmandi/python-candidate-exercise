# Jellybean CRM — live refactoring exercise

This is a small, working Django CRM screen. It is intentionally messy and resembles a feature that grew quickly in production. Your task is **not** to rewrite everything. Improve it safely while using your preferred IDE and AI coding agent.

## Run it

You need Python 3.10 or newer with `pip` and `venv`, plus Node.js 22+ for the frontend build. The app uses a local SQLite database; no separate database server is needed.

From this directory, create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with `.venv\Scripts\Activate.ps1` instead. If your system uses `python3`, use that for the first command.

Then install the dependencies, prepare the database, and start Jellybean CRM:

```bash
python -m pip install -r requirements.txt
cd frontend && npm ci && npm run build && cd ..
python manage.py migrate
python manage.py seed_crm
python manage.py runserver
```

The `npm run build` step is required: Django serves the compiled bundle from
`crm/static/crm/dist/`, which is generated and not committed. Skip it and the page
shows "Failed to load the CRM client. Check your connection and reload."

Open http://127.0.0.1:8000/. Five sample contacts will be ready to explore; no login is required. You can rerun `seed_crm` without duplicating the sample contacts. Keep the server running in your terminal and stop it with Ctrl+C.

For later sessions, activate `.venv` and run `python manage.py runserver` again. If port 8000 is busy, use `python manage.py runserver 8001` and open http://127.0.0.1:8001/.

Verify the setup with:

```bash
python manage.py check
python manage.py test
```

This setup is for local interview use. Local data lives in the ignored `db.sqlite3` file, and the tests use a separate test database.

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
