# Proposal

## Why

The CRM screen is a single Django template plus a hand-written renderer that builds HTML strings, re-renders the whole page on every interaction, and has no component boundaries. That renderer has since been replaced with React, but the no-build setup (UMD globals + `htm`) was a stopgap: no type checking, no component-level tooling, no hot reload, and a runtime dependency on a third-party CDN. The project now has a prepared Vite + React + TypeScript scaffold in `frontend/`, so the frontend can be a real, typed, bundled client while Django keeps serving the screen and the API.

## What Changes

- Move the client to `frontend/` (Vite 8, React 19, TypeScript, npm) and build it to `crm/static/crm/dist/`; Django serves the hashed bundle from its own origin.
- Replace the CDN/`htm` bootstrap: no third-party script tags at runtime, no `window.React` globals, no hand-written static app.
- Keep `/` as the entry point: Django renders the HTML shell, embeds the initial payload, and the built bundle mounts `#crm-app`.
- Add plain Django JSON endpoints under `/api/` for contact list/search, contact detail, create, status change, add note, and delete, plus a CSRF token endpoint for client-rendered pages; reuse `forms.py`, `selectors.py`, and `services.py`; no DRF dependency.
- Make the URL the source of truth for `q`, `status`, and `contact`, using the History API so search results and the open contact are deep-linkable and survive reload.
- Preserve feature parity: list, search, status filter, dashboard summary, contact detail with activity feed, create contact with inline validation, change status, add note, delete with confirmation, and the CSV export link.
- Harden the interaction details the original renderer missed: labelled form controls, visible focus, keyboard-operable rows, `aria-live` announcements, destructive-action confirmation, and empty/loading states.
- Add a dev workflow: `npm run dev` serves the client with HMR and proxies `/api`, `/export`, and `/static` to Django.
- **BREAKING (internal contract)**: `crm/static/crm/dashboard.js`, `crm/static/crm/app/`, and `crm/static/crm/dashboard.css` are removed; the template loads manifest-resolved hashed assets instead, so nothing may depend on those paths or on the old global/DOM-mutation behavior.
- Compatibility constraint: the GET payload context (`contacts_json`, `detail_json`, `status_choices`, `q`, `status`, `error`, `total`, `pipeline`), the `server-data` / `contacts-data` / `detail-data` hooks, and the form-encoded POST action handling on `/` keep working. Only the asset assertions in `crm/tests.py::DashboardTemplateTests` change; the rest of that suite stays pinned.

## Capabilities

### New Capabilities

- `crm-api`: JSON endpoints for reading and mutating contacts, their status, and their activity feed, plus CSRF token issuance, including validation errors and CSRF handling for the SPA.
- `crm-dashboard`: The CRM screen as a React SPA — bootstrap from a built client, search/filter, contact selection and detail, create/status/note/delete workflows, summary, URL state, and accessibility behavior.

### Modified Capabilities

None. The project has no established specs yet; both capabilities above are new.

## Impact

- **Frontend**: `frontend/` becomes the source of truth (`src/`, `vite.config.ts`, `index.html`, `package.json`/lockfile); build output in `crm/static/crm/dist/` is generated and not committed; styles move from `crm/static/crm/dashboard.css` to `frontend/src/index.css`.
- **Django**: `crm/templates/crm/dashboard.html` loads the built entry via a new `crm/templatetags/vite.py` manifest tag; `crm/api.py` gains the CSRF endpoint; `messycrm/settings.py` gains the Vite dev origins for CSRF; `crm/tests.py` template-asset assertions are updated.
- **Dependencies**: npm packages already pinned in `frontend/package-lock.json` (React, Vite, TypeScript, oxlint); `requirements.txt` is unchanged. Building requires Node 22+; running the app requires a build (or the Vite dev server).
- **Out of scope**: SSR, a client-side router library, a state-management or data-fetching library, a CSS framework, authentication/login, visual redesign, and any change to the CSV export format. Models, migrations, and the legacy form contract are unchanged.
