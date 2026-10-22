---
description: "Commit staged work, push the branch, and open a PR to main"
argument-hint: "[base branch]"
---

Prepare the current branch and open a pull request using the `pushing-and-creating-pull-request` skill at `.pi/skills/pushing-and-creating-pull-request/SKILL.md`.

Workflow:

1. Run the skill's preflight (`git status --short --branch`). Stop if there are unresolved conflicts or if the current branch is the base branch.
2. If staged changes exist, commit them first using `.pi/skills/creating-conventional-commits/SKILL.md`. Do not commit unrelated unstaged or untracked files.
3. Push the current branch to `origin` with upstream tracking.
4. Determine the base branch from `${1:-main}` and check for an existing open PR for the current head/base. If one exists, report its URL instead of creating a duplicate.
5. Open a PR against `ekkysoftware/python-candidate-exercise`:
   - Base: `${1:-main}`
   - Head: the current branch
   - Title: Conventional Commit style, synthesized from the commits
   - Body: a short summary plus one bullet per logical change; include issue-closing lines only when an issue is actually resolved
6. Prefer `gh pr create` when `gh` is installed and authenticated.
7. If `gh` is unavailable, read `GH_TOKEN` from `.env` and use the GitHub REST API (`POST /repos/ekkysoftware/python-candidate-exercise/pulls`). Never print, commit, or otherwise expose the token. Check the token against `GET /user` first and report a permission error instead of retrying blindly.
8. Do not push from or create a PR whose head is `main`. Do not force-push.
9. Return the PR URL and the final branch status.

Additional context from the caller: ${@:-none}
