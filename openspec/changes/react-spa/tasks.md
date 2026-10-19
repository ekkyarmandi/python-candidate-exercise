# Tasks

## 1. Shared command layer (no behavior change) — done

- [x] 1.1 Extract the four `crm_screen` POST branches into `crm/commands.py` functions that call the existing forms and services and return `(errors, contact)`; keep redirect targets, the "Name is required" message, and activity bodies identical. Verify with `python manage.py test crm.tests` (all tests green, `crm/tests.py` unchanged).
- [x] 1.2 Rewire `crm_screen` to call the new command functions for `add_contact`, `change_status`, `add_note`, and `delete_contact`. Verify `python manage.py test crm.tests` stays green and `git diff crm/tests.py` is empty.

## 2. JSON API — done

- [x] 2.1 Add serializers in `crm/api.py` (`contact_to_dict`, `activity_to_dict`, `summary_to_dict`) and reuse them from `crm_screen` so `contacts_json`/`detail_json` keep their current keys plus `created_at_iso`. Verify `python manage.py test crm.tests` stays green and `dashboard.js`-consumed keys (`id`, `url`, `selected`, `status_label`, `created_at`) are present.
- [x] 2.2 Add `GET /api/contacts/` (filters `q`, `status`; returns `{contacts, summary}`) and `GET /api/contacts/<id>/` (20 newest activities, 404/JSON errors for missing or non-numeric ids), wired in `crm/urls.py`. Verify new tests in `crm/test_api.py` cover unfiltered, search, status filter, empty result, detail, 404, and non-numeric id.
- [x] 2.3 Add `POST /api/contacts/` (201 with contact + summary; 400 `{errors: {name: "Name is required"}}` on blank name; value fallback 0; unknown status → lead) and `DELETE /api/contacts/<id>/` (204; 404 when missing). Verify with tests for each validation rule and status code.
- [x] 2.4 Add `POST /api/contacts/<id>/status/` (400 on unknown status, activity body `Status changed from <old> to <new>`) and `POST /api/contacts/<id>/notes/` (blank note creates no activity, non-blank creates a `note` activity). Verify with tests asserting status codes, activity rows, and unchanged state on rejection.
- [x] 2.5 Add CSRF enforcement and malformed-JSON handling to the API views: 403 JSON without a valid token, 400 JSON on unparsable bodies, and no mutation in either case. Verify with `Client(enforce_csrf_checks=True)` tests and a `json.loads` assertion that error bodies are JSON.
- [x] 2.6 Add `@ensure_csrf_cookie` to `crm_screen` so the SPA always receives a CSRF cookie. Verify `DashboardQueryCountTests` still passes (`GET /` query count stays 5) and a test asserts the `csrftoken` cookie is set.

## 3. Vite toolchain and asset delivery

- [x] 3.1 Configure `frontend/vite.config.ts` with a build-only `base` of `'/static/crm/dist/'` (dev serves `/`), `build.outDir: '../crm/static/crm/dist'`, `emptyOutDir: true`, `manifest: true`, and a dev proxy for `/api`, `/export`, and `/static` to `http://127.0.0.1:8000`; add `crm/static/crm/dist/` to the root `.gitignore`. Verify `npm run build` in `frontend/` emits `.vite/manifest.json` plus a hashed JS/CSS pair and that `crm/static/crm/dist/` is untracked by git.
- [x] 3.2 Replace the scaffold shell: `frontend/index.html` mounts `#crm-app` with no payload hooks, `frontend/src/main.tsx` creates the root and renders the app, and the starter `App.tsx`/`App.css`/`assets/`/`public/` files are removed. Verify `npm run dev` serves the screen at the Vite origin, proxies `/api/contacts/`, and renders seeded contacts.
- [x] 3.3 Add `GET /api/csrf/` (204, `@ensure_csrf_cookie`) with tests asserting the status and the `csrftoken` cookie, and add `http://localhost:5173` / `http://127.0.0.1:5173` to `CSRF_TRUSTED_ORIGINS` in `messycrm/settings.py`. Verify a dev-origin mutation using the fetched token succeeds and the same request without a token gets a JSON 403.
- [x] 3.4 Add `crm/templatetags/vite.py` (read `.vite/manifest.json`, resolve the `src/main.tsx` entry, expose `{% vite_asset %}`) and rewrite `crm/templates/crm/dashboard.html` to load the manifest-resolved module script and CSS while keeping `#crm-app`, `contacts-data`, `detail-data`, `server-data`, and `CRM_STATUS_CHOICES`; add an `onerror` handler that writes the failure message. Verify the built page renders and that blocking the built JS URL shows "Failed to load the CRM client. Check your connection and reload." instead of a blank panel.
- [x] 3.5 Delete `crm/static/crm/dashboard.js`, `crm/static/crm/app/`, and `crm/static/crm/dashboard.css` once the ported build passes. Verify `grep -rn "crm/dashboard.js\|crm/dashboard.css\|window.React\|htm" crm/ frontend/ --include='*.py' --include='*.html' --include='*.ts*' --include='*.js'` finds only intentional references (e.g. migration notes), and the built page still loads.
- [x] 3.6 Update only the `DashboardTemplateTests` asset assertions to expect the manifest-resolved module script and stylesheet (keep the payload-hook and `data-q` assertions). Verify `python manage.py test crm` is green and `git diff crm/tests.py` touches only that test class.

## 4. Port the data layer and list

- [x] 4.1 Port `crm/static/crm/app/lib/*` and `data/*` to `frontend/src/lib/{api,url,format}.ts` and `frontend/src/data/{payload,useCrmData}.ts`, keeping the request/abort/stale-response semantics and adding types. Verify `npm run build` (which runs `tsc -b`) and `npm run lint` pass with no `any` escape hatches.
- [x] 4.2 Port the app skeleton (`App`, `Stats`, `Toolbar`, `ContactsPanel`, `DetailPanel`) to TSX, rendering from the embedded payload and falling back to one `GET /api/contacts/` boot fetch when the payload hooks are absent. Verify the built `runserver` page renders without an extra list request and the Vite dev page renders after its boot fetch.
- [x] 4.3 Port search and status filter with `pushState`, refetch, request cancellation, and the empty state. Verify deep links (`/?q=…&status=…`) and that two rapid submissions leave the last request's results on screen, in both dev and built modes.
- [x] 4.4 Port contact selection as keyed `<a href="?q=…&status=…&contact=<id>">` rows with `pushState`, `popstate` refetch, and stale/missing id fallback via `replaceState`. Verify browser back/forward and reloading a `?contact=` URL restore the selection.

## 5. Detail, mutations, and creation

- [x] 5.1 Port `ContactDetail`, `ActivityFeed`, and the fact list with `Intl` date/currency formatting, newest-first activities, the no-selection prompt, and per-action pending/error states. Verify each field and the 20-activity cap against seeded data.
- [x] 5.2 Port status change and note submission to event handlers that apply the returned payload and refetch the list only when the summary or active filter can change. Verify a status change updates row, detail, summary, and feed, and a blank note shows "Enter a note before saving." without a request.
- [x] 5.3 Port delete with `window.confirm("Delete <name>? This cannot be undone.")`, `DELETE`, next-contact selection, and a list refetch. Verify cancel leaves data untouched and confirm removes the contact and its activities.
- [x] 5.4 Port `NewContactForm` and `Field` with labelled inputs, correct types/`inputMode`, inline "Name is required", focus on the first invalid field, preserved values, and a disabled "Saving…" submit. Verify blank-name, non-numeric-value, unknown-status, and successful-create paths.

## 6. Styling, accessibility, and docs

- [x] 6.1 Move the styles into `frontend/src/index.css`, keeping `:focus-visible` rings, `touch-action: manipulation`, `tabular-nums`, truncation/`min-w-0`, narrow-viewport stacking without horizontal overflow, and the `prefers-reduced-motion` guard. Verify with a keyboard-only pass, a 375px viewport, and reduced-motion emulation on the built page.
- [x] 6.2 Keep `aria-live="polite"` announcements, a single `h1`, a skip link, named list/detail regions, labelled form controls, and named action buttons. Verify with an accessibility-tree inspection that async results, validation errors, and the confirm dialog are announced.
- [x] 6.3 Document the new workflow in `README.md`: Node 22+, `npm ci && npm run build` before `runserver`, `npm run dev` with the API proxy and the CSRF token bootstrap, `dist/` not committed, no CDN at runtime, and the legacy form-post shim (keep the `crm/views.py` comment). Verify the README commands work from a clean checkout (`npm ci`, `npm run build`, `python manage.py seed_crm`, `python manage.py runserver`).

## 7. Integration verification

- [x] 7.1 Run `python manage.py check`, `python manage.py test`, `npm run build` (`tsc -b` + Vite), and `npm run lint`; confirm the full Django suite passes and `git diff crm/tests.py` is limited to `DashboardTemplateTests`.
- [x] 7.2 Run the manual checklist in both modes — `npm run dev` and built `runserver` — covering search, filter, deep link, back/forward, create (blank and valid), status change, note, delete cancel/confirm, CSV export download, keyboard-only pass, narrow viewport, reduced motion, and the blocked-bundle fallback. Record any deviation in the change notes rather than silently adjusting specs.

## Workflow follow-up

- Archive `react-spa` after review; confirm the delta specs sync into `openspec/specs/crm-api/` and `openspec/specs/crm-dashboard/`.
