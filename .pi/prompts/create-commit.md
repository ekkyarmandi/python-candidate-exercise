---
description: "Commit staged changes with a Conventional Commit message"
argument-hint: "[scope or extra context]"
---

Commit the currently staged changes using the `creating-conventional-commits` skill at `.pi/skills/creating-conventional-commits/SKILL.md`.

Workflow:

1. Run the skill's preflight (`git status --short --branch`).
2. Stop and report if there are unresolved conflicts, no staged changes, or only unrelated unstaged/untracked files. Do not use `git add .`.
3. Inspect `git diff --cached` and choose one logical change set.
4. Pick the appropriate Conventional Commit type (`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`) and an optional scope.
5. Write a concise imperative subject (under 72 characters) and a body that explains what changed and why when the subject alone is not enough.
6. Commit only the intended staged files. Do not push.
7. Report the commit hash and subject.

Additional context from the caller: ${@:-none}
