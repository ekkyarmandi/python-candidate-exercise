# Jellybean CRM — live refactoring exercise

This is a small, working Django CRM screen. It is intentionally messy and resembles a feature that grew quickly in production. Your task is **not** to rewrite everything. Improve it safely while using your preferred IDE and AI coding agent.

## Run it

You need Python 3.10 or newer with `pip` and `venv`. The app uses a local SQLite database; no separate database server or frontend build is needed.

From this directory, create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with `.venv\Scripts\Activate.ps1` instead. If your system uses `python3`, use that for the first command.

Then install the dependencies, prepare the database, and start Jellybean CRM:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_crm
python manage.py runserver
```

Open http://127.0.0.1:8000/. Five sample contacts will be ready to explore; no login is required. You can rerun `seed_crm` without duplicating the sample contacts. Keep the server running in your terminal and stop it with Ctrl+C.

For later sessions, activate `.venv` and run `python manage.py runserver` again. If port 8000 is busy, use `python manage.py runserver 8001` and open http://127.0.0.1:8001/.

Verify the setup with:

```bash
python manage.py check
python manage.py test
```

This setup is for local interview use. Local data lives in the ignored `db.sqlite3` file, and the tests use a separate test database.

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
