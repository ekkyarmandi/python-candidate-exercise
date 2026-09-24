# Jellybean CRM — live refactoring exercise

This is a small, working Django CRM screen. It is intentionally messy and resembles a feature that grew quickly in production. Your task is **not** to rewrite everything. Improve it safely while using your preferred IDE and AI coding agent.

## Run it

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_crm
python manage.py runserver
```

Open http://127.0.0.1:8000/. Run tests with `python manage.py test`.

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
