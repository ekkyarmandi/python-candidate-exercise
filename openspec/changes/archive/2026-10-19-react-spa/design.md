# Design

## Context

See `proposal.md` — Why, and the two delta specs (`specs/crm-dashboard/spec.md`, `specs/crm-api/spec.md`) for the behavior contract.

Verified current state:

- `crm/views.py` renders the shell and the initial payload (`contacts_json`, `detail_json`, `server-data`, `CRM_STATUS_CHOICES`) and still accepts the legacy form-encoded `action` posts through `crm/commands.py`.
- `crm/api.py` provides the JSON endpoints, JSON error handling, and `CSRF_FAILURE_VIEW`; `crm/test_api.py` covers them (25 tests).
- The React screen exists as UMD + `htm` modules under `crm/static/crm/app/` (`lib/`, `data/`, `components/`) loaded by the classic `crm/static/crm/dashboard.js`, with styles in `crm/static/crm/dashboard.css`. Behavior is already verified end to end (URL state, mutations, a11y), but the setup has no types, no HMR, and a runtime CDN dependency.
- `frontend/` is a prepared Vite scaffold: Vite 8, React 19, TypeScript 6, oxlint, `npm` scripts `dev`/`build`/`lint`/`preview`, `package-lock.json` and `node_modules` in place. `vite.config.ts` is still the template default and `src/` is the starter `App.tsx`; `index.html` still mounts `#root`.
- The Django test suite pins the shell hooks, payload shapes, query counts, legacy POSTs, and (in `DashboardTemplateTests`) the asset paths.

This design replaces the UMD/`htm` client with a typed Vite build, keeping the server contract and the behavior already specified.

## Goals / Non-Goals

**Goals:**

- Typed, bundled client source in `frontend/`, built to assets Django serves from its own origin.
- Preserve payload-first paint, URL-driven state, and all interaction/accessibility behavior from the delta specs.
- Dev loop with HMR and API proxying; production build is reproducible from the lockfile.
- Keep the Django API and legacy form contract unchanged; only the template-asset test moves.

**Non-Goals:**

- SSR, Next.js, or a Node server in production.
- Client-side router, state-management, or data-fetching libraries (SWR/React Query/Redux).
- CSS framework or visual redesign; new npm dependencies beyond the prepared scaffold.
- Authentication, multi-page navigation, offline support.
- Changing the data model, migrations, the CSV format, or the legacy POST behavior.

## Decisions

### 1. Vite 8 + React 19 + TypeScript in `frontend/`, built into `crm/static/crm/dist/`

`frontend/vite.config.ts` becomes:

```ts
export default defineConfig({
  plugins: [react()],
  // build only; the dev server uses '/' so URL-state paths match Django
  base: command === 'build' ? '/static/crm/dist/' : '/',
  build: {
    outDir: '../crm/static/crm/dist',
    emptyOutDir: true,
    manifest: true,
  },
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/export': 'http://127.0.0.1:8000',
      '/static': 'http://127.0.0.1:8000',
    },
  },
})
```

- **Why:** the scaffold is already prepared and typed; Vite gives JSX/TSX, fast HMR, tree-shaken production output, and hashed filenames. `outDir` sits inside the Django app's static tree so `runserver` and `collectstatic` both pick it up without an extra settings entry.
- **Why not keep UMD + `htm`:** it worked, but it costs type safety, component-level tooling, and HMR, and it requires network access to a CDN for every first load. It also cannot grow (no code splitting, no npm libraries).
- **Alternatives rejected:** Babel Standalone in the browser (slow, no types), Preact/`htm` with a custom bundler (reinvents this scaffold), Next.js (SSR we do not need and a second server), a separate frontend repo (one screen, one deployable).
- **Hashed output:** default Vite filenames (`assets/index-<hash>.js`, `assets/index-<hash>.css`) with `manifest: true`. Hashed names are what make long-lived caching safe; the manifest is the mapping back to stable entry names.
- **Node requirement:** the build runs on Node 22+ (matches the prepared lockfile and `npm` 9+); documented in the README.

### 2. Asset delivery: manifest tag in the Django template

`crm/templatetags/vite.py` reads `crm/static/crm/dist/.vite/manifest.json` once per process, exposes `{% vite_asset 'src/main.tsx' %}`, and returns:

- `<script type="module" src="…/assets/index-<hash>.js">` for the entry,
- `<link rel="stylesheet" href="…/assets/index-<hash>.css">` for each imported CSS file,
- `preload` hints are unnecessary for a single entry; `crossorigin` is not needed because the assets are same-origin.

`dashboard.html` keeps `#crm-app`, both `json_script` payloads, `#server-data`, and `CRM_STATUS_CHOICES`, drops every CDN script, and adds an `onerror` handler on the entry script that writes "Failed to load the CRM client. Check your connection and reload." into `#crm-app`.

- **Why a custom tag over `django-vite`:** ~25 lines, one manifest read, no new Python dependency, and no settings contract to learn. The alternative was fixed (non-hashed) filenames, which loses cache busting for a marginal template simplification.
- **Why not inject assets at build time into a Django template:** Vite's `index.html` is a dev artifact; keeping Django as the template owner preserves the server payload hooks and CSRF cookie behavior.

### 3. Plain Django JSON views, no DRF (unchanged)

`crm/api.py` keeps the existing six endpoints and adds `GET /api/csrf/` (`@ensure_csrf_cookie`, 204).

- **Why the CSRF endpoint:** under `runserver` the shell's `@ensure_csrf_cookie` sets the cookie, but in Vite dev the page comes from `localhost:5173`, so the client needs a way to obtain a token from the same origin. One endpoint serves both modes: the client calls it only when `document.cookie` has no `csrftoken`.
- **Why not DRF:** six endpoints, existing forms/selectors/services; DRF would add a settings/serializer layer without removing any of that logic.
- **Dev origin handling:** the proxy preserves `Origin: http://localhost:5173` while Django sees its own host, so `messycrm/settings.py` lists the Vite origins in `CSRF_TRUSTED_ORIGINS` for development (`http://localhost:5173`, `http://127.0.0.1:5173`).

### 4. Keep the server-rendered first payload; fetch only when it is absent

`crm_screen` still builds the payload and the template still embeds it, so a normal page load paints data without an extra request and the query-count tests stay at 5. The client boot checks for `contacts-data`; if absent (Vite dev, or a future shell without payload), it calls `GET /api/contacts/` once, takes the status choices from that response, and shows a loading state until it resolves.

- **Why:** dev/prod parity without making production pay a request; the check is a single boolean, not a mode flag.
- **Consequence:** `initialData()` must distinguish "no payload" from "empty list" (a missing `contacts-data` node vs an empty array). The Vite `index.html` therefore omits the payload nodes entirely.

### 5. URL is the state source; no router library (unchanged)

`q`, `status`, and `contact` live in the query string; filter submit and contact selection use `pushState`, fallback selection uses `replaceState`, and one `popstate` listener refetches. Selection renders as `<a href="?q=…&status=…&contact=<id>">` so middle-click and copy-link work.

- **Routes are ported as-is** from `crm/static/crm/app/lib/url.js`; only types are added.
- **Alternatives rejected:** `useState`-only (breaks deep links), hash routing, React Router (one route, no need).

### 6. Server-authoritative mutations, one state owner, race-safe fetches (unchanged)

`useCrmData` owns `{contacts, summary, detail}`; every load aborts the previous request and guards on a request id. Mutations apply the returned payload, and only list-affecting changes refetch the list.

- **React guidance applied:** derive filtered/selected views during render, run request logic in event handlers (the only effect subscribes to `popstate`), keep components at module scope, use explicit ternaries for conditional UI, and `key` rows and the status select.

### 7. Frontend layout under `frontend/src/`

Port the existing module split one-to-one:

```
frontend/src/
  main.tsx                 mounts <App> into #crm-app
  App.tsx                  URL/notice state + mutation handlers
  components/              one component per file (.tsx)
    Stats, Toolbar, Field, ContactsPanel, ContactRow, NewContactForm,
    DetailPanel, ContactDetail, StatusForm, NoteForm, DeleteAction, ActivityFeed
  data/
    payload.ts             payload parsing, status choices, selection fallback
    useCrmData.ts          data hook
  lib/
    api.ts                 request(), ApiError, CSRF header/bootstrap
    url.ts                 query-string state helpers
    format.ts              Intl formatters
  index.css                ported styles (focus, responsive, reduced motion)
```

- **Why keep the same boundaries:** they were chosen for testability and reuse and already match the spec; the port is mechanical (`html\`…\`` → JSX, `props` typed, the `lib/react.js` adapter disappears because hooks import from `react`).
- **Why one component per file:** Vite makes module count cheap (bundled + code splitting later), unlike the CDN setup.
- **Removed:** the Vite starter `App.tsx`, `App.css`, `assets/*`, `public/*`, and `crm/static/crm/{dashboard.js,app/,dashboard.css}`.

### 8. Interaction polish and accessibility (unchanged)

Everything in the previous design still applies: labelled controls (`htmlFor` + `aria-describedby` for errors), correct input types and `inputMode`, inline errors with focus movement, `aria-live` announcements, `:focus-visible` rings, `prefers-reduced-motion`, `tabular-nums`, truncation, mobile stacking, empty/loading states, and `window.confirm` before delete.

- **Carried into `index.css`** rather than rewritten; the `.field`, `.row`, `.panel`, `.activity` class names stay so the ported markup maps directly.
- **Verification stays behavioral** (keyboard pass, 375px viewport, AX tree), not implementation-specific.

### 9. Shared command layer (unchanged)

`crm/commands.py` remains the single validation+mutation path for the legacy POST and the JSON API. No changes are needed for the Vite migration beyond the template/test updates.

### 10. Verification with a real toolchain

- **Static gates:** `npm run build` (runs `tsc -b && vite build`) and `npm run lint` (oxlint) must pass.
- **Server tests:** `python manage.py check`, `python manage.py test` (the only changed test is `DashboardTemplateTests`; `crm/test_api.py` gains the CSRF endpoint cases).
- **Browser checks:** run the CDP end-to-end suite against both `npm run dev` (proxy + cookie bootstrap) and the built `runserver` page; include the blocked-bundle fallback, narrow viewport, reduced motion, and the accessibility tree.
- **Why not a JS unit-test runner yet:** the behavior that matters is server-owned and covered by Django tests; the port is verified by the same end-to-end checks. Adding Vitest is a reasonable follow-up but not required to prove parity.

## Risks / Trade-offs

- **Build step becomes mandatory** → `runserver` alone no longer serves a working UI on a fresh clone. Mitigation: README leads with `npm ci && npm run build`, and CI/deploy runs the build before `collectstatic`.
- **Built assets are not committed** → a deploy that skips the build serves the fallback message. Mitigation: `dist/` is gitignored and the build is an explicit deploy step; the fallback makes the failure obvious instead of blank.
- **Dev/prod parity gaps** → Vite serves the page (no payload) and proxies the API: mitigated by the dev boot fetch, the CSRF endpoint, `CSRF_TRUSTED_ORIGINS`, and running the e2e suite in both modes.
- **CSRF through the proxy** → Origin/Host mismatch can reject mutations. Mitigation: trusted dev origins plus the token endpoint; e2e covers a dev-origin mutation.
- **Stale `dist/` during development** → editing `frontend/src` does not change the built page. Mitigation: use `npm run dev` for iteration; rebuild before manual production-mode checks.
- **Manifest missing after a fresh clone** → the tag cannot resolve assets. Mitigation: raise a clear template error (`ImproperlyConfigured`) naming `npm run build`, and document it.
- **React 19 + strict TS config** (`noUnusedLocals`, `verbatimModuleSyntax`, `erasableSyntaxOnly`) rejects sloppy ports. Mitigation: port module by module with `tsc -b` as the gate; no `any` escape hatches.
- **Two request paths (legacy POST, JSON API) can drift** → shared `crm/commands.py` plus tests (unchanged).
- **Hashed filenames vs tests** → `DashboardTemplateTests` asserts literal asset names. Mitigation: assert the rendered module script/CSS from the manifest instead; the payload-hook assertions stay.
- **`window.confirm` is visually plain** → accepted for scope; a styled dialog is a later change.

## Migration Plan

1. Configure `frontend/vite.config.ts` (`base`, `outDir`, `emptyOutDir`, `manifest`, dev proxy) and add `crm/static/crm/dist/` to `.gitignore`; confirm `npm run build` emits the manifest.
2. Port `lib/`, `data/`, `components/`, and `main.tsx`/`App.tsx` to TypeScript under `frontend/src/`; delete the starter assets; `tsc -b` + `oxlint` clean.
3. Add `crm/templatetags/vite.py` and rewrite `dashboard.html` to load the built entry with an `onerror` fallback; add `GET /api/csrf/` and `CSRF_TRUSTED_ORIGINS`.
4. Delete `crm/static/crm/dashboard.js`, `crm/static/crm/app/`, and `crm/static/crm/dashboard.css`; move the styles into `frontend/src/index.css`.
5. Update only the `DashboardTemplateTests` asset assertions.
6. Verify in both modes (`npm run dev` and `npm run build` + `runserver`): Django tests, `tsc`, `oxlint`, CDP e2e, keyboard/viewport/reduced-motion, blocked bundle.
7. Update the README (Node requirement, build, dev proxy, trusted origins, no CDN).
8. Rollback: restore the previous static app/template from git; the API additions (including `/api/csrf/`) are additive and can stay. No data migration.

## Open Questions

- None blocking. Whether to add Vitest later for component-level tests is deferrable and does not change the specs or task breakdown.
