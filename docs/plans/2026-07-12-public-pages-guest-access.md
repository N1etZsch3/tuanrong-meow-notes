# Public Pages & Guest Access — Implementation Plan

Companion to `2026-07-12-public-pages-guest-access-design.md`.
Branch: `feature/public-pages` (worktree `.worktrees/public-pages`, from local `dev` `4d00505`).
Dev DB: `catmap_dev` on `catmap-postgis`, role `catmap_dev_app` (non-superuser). Local
backend only. **Do not touch production `catmap` or the running service.**

## Phase 1 — Backend

### 1.1 Guest recording (DB + service)

- Model `WechatGuest` in a new `app/modules/public/models.py` (or `auth/models.py` if
  cohesion favors it): `id`, `openid` (unique, indexed, plaintext), `first_visit_at`,
  `last_visit_at`, `visit_count`, `created_at`, `updated_at`.
- Alembic migration `20260712_0015_create_wechat_guests.py` (next in sequence; upgrade +
  downgrade). Apply to `catmap_dev` only.
- Service helper `record_guest_visit(db, openid)`: upsert (insert or increment
  `visit_count` + bump `last_visit_at`). Best-effort — caller wraps in savepoint/try.
- Wire into `login_with_wechat` in `app/modules/auth/service.py`: on the `user is None`
  branch (openid resolved, unbound), call `record_guest_visit` best-effort **before**
  raising `40104`. Failure must not change the `40104` response.
- Register new model in `tests/conftest.py` imports so the in-memory SQLite schema includes it.

### 1.2 Public module + endpoints

- `app/modules/public/schemas.py`: Pydantic response models — `PublicStats`,
  `PublicCatListItem`, `PublicCatDetail`, `PublicCatList` (paginated), `PublicPostCard`,
  `PublicPostDetail`, `PublicPostList`.
- `app/modules/public/mock_data/*.json`: `stats.json`, `cats.json`, `posts.json`.
  Image URLs = existing COS sample assets or `素材` placeholders.
- `app/modules/public/service.py`: load fixtures, filter/paginate/sort in-memory,
  serialize through schemas. Keep DB-swap seam obvious (one function per endpoint).
- `app/api/v1/public.py`: router, **no auth dependency**, `api_success` envelope +
  `request.state.trace_id`, snake_case. Endpoints: `/public/stats`, `/public/cats`,
  `/public/cats/{cat_id}`, `/public/posts` (type filter), `/public/posts/{post_id}`.
- Register in `app/api/v1/router.py`: `api_router.include_router(public_router, prefix="/public")`.
- Confirm CORS/regex config already allows the local frontend origin (it does:
  `cors_allow_origin_regex` covers localhost).

### 1.3 Backend tests

- `tests/test_public_api.py`: envelope, pagination, cats field whitelist (assert excluded
  fields absent), post `type` filter, unknown-id 404 — all unauthenticated.
- `tests/test_guest_recording.py`: first-visit insert; repeat increments; write-failure
  path still returns `40104`.

## Phase 1 — Frontend

### 2.1 Routing split

- `pages.json`: register `pages/public/home`, `pages/public/cats`, `pages/public/cat-detail`,
  `pages/public/post-detail` (custom nav style, main package).
- `services/app-startup.ts`: add `PUBLIC_HOME_ROUTE = "/pages/public/home"`; extend
  `StartupRoute`; return it wherever unbound/absent-WeChat currently yields `LOGIN_ROUTE`.
  Keep hard auth-expiry → login. Update `loading/index.vue` failure fallback → public home.
- `tests/services/app-startup.test.ts`: add unbound → public, no-code/no-token → public,
  bound → work (unchanged), expiry → login (unchanged).

### 2.2 Public API client + pages

- `api/routes.ts`: add `public` endpoint group.
- `api/public.ts`: typed client (token-less `request` calls; `request` already supports no token).
- `types/`: public DTO types (snake_case aligned).
- Pages with brand theme (background asset, Songti stack, `#267b2f`), loading/empty/error
  states:
  - `pages/public/home` — brand band + member pill (hidden when `isLoggedIn`), stats strip,
    featured cats scroll, trivia cards, merch grid, about block + member button, guest link.
  - `pages/public/cats` — list with filter/sort, bottom-load; reuse a shared cat-card
    component (extract so member cats page can share later, but do not modify member page now).
  - `pages/public/cat-detail` — album + info tags + story.
  - `pages/public/post-detail` — trivia/merch article.

### 2.3 Cross-zone entries

- Login page (`pages/login/index.vue`): add "先随便逛逛 →" → `reLaunch` public home.
- Profile page (`pages/profile/index.vue`, dev version): add "协会公开主页" list item →
  `navigateTo` public home.

## Verification (before handoff)

Backend (in worktree, against `catmap_dev`):

```
cd backend
py -3.11 -m pytest -q
py -3.11 -m ruff check .
py -3.11 -m alembic upgrade head
```

Frontend:

```
cd frontend
npm run test -- --run
npm run type-check
npm run build:mp-weixin
```

Manual (WeChat DevTools, "不校验合法域名" on, local backend running):
- Guest launch (unbound wechat) → public home; browse cats list/detail, posts.
- Member launch (bound wechat) → work home unchanged.
- Member entry from public home → login → bind → work home.
- Browse-as-guest from login; public preview from profile page.
- Guest openid recorded once, increments on repeat (check `catmap_dev.wechat_guests`).

## Safety Checklist

- All DB writes hit `catmap_dev` only; verify `.env` `CATMAP_DATABASE_URL` targets
  `catmap_dev` before running migrations/tests.
- No secrets in commits; `.env` stays ignored.
- Production `catmap` table count and `/api/v1/health` re-checked after any server-side DB op.
- Do not deploy to production in this slice; deployment + privacy-doc update + content-security
  gating are Phase 2 gates.

## Progress

Update `docs/开发进度.md` before handoff: branch/worktree, area, completed work, files,
API/schema changes, migration name (`20260712_0015`), verification commands + results,
manual checks not yet done (real-device), known risks (mock data will drift from real cats
until promoted; guest openid privacy declaration required before prod).
