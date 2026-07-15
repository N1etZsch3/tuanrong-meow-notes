# Public Pages & Guest Access Design

## Goal

Split the app into a **member work zone** and a **public guest zone** so that non-member
visitors (and not-yet-bound / unbound members) can browse a public showcase — association
intro, campus cats library, association trivia, and merchandise display — without a login,
while bound members keep zero-extra-step auto-login into the work zone.

This is an additive `1.2.x`-line feature. It must not change behavior for existing
`1.1.1` clients already in production, and must not touch the production `catmap`
database or the running backend service during development.

## Current Context

- Production baseline: backend `1.1.1` deployed at `trmx.fun` in WeChat auth
  `optional` mode; Mini Program store version still `1.1.0`.
- Dev/prod share one server (`49.235.238.143`, container `catmap-postgis`), so all
  development uses an **isolated `catmap_dev` database** and a **local backend**, never
  the production DB or service.
- Startup flow today (`frontend/src/services/app-startup.ts`):
  loading page → `uni.login` → `POST /auth/wechat/login`.
  - openid bound → JWT issued → password/profile checks → work home (`pages/index/index`).
  - unbound (`40104 WECHAT_OPENID_UNBOUND`) or no token → **login page**.
- Every business API is guarded by `require_profile_completed`; there is currently **no
  public/unauthenticated endpoint** except `/health` and the auth endpoints.
- openid is stored as **plaintext** (`users.wechat_openid`, `String(128)`, unique). Guest
  records follow the same convention (plaintext), for consistency with existing auth and
  to allow later guest→member correlation by openid.

## Scope

In scope for this design:

- Loading-page routing split: unbound / no-session → **public home** instead of login page.
- Public guest zone pages: home, cats library list, cat detail, post detail (trivia + merch).
- Backend public endpoints under a dedicated **`/api/v1/public/*`** namespace, unauthenticated.
- **Mock-data phase**: public endpoints serve versioned JSON fixtures from the backend, not
  real content tables. The frontend calls the real endpoints and real response shapes; only
  the service-layer data source is a fixture. Swapping to real data later touches only the
  service layer.
- Guest openid recording: a `wechat_guests` table + best-effort upsert in the existing
  `40104` unbound path of `login_with_wechat`. No new API, no contract change.
- Cross-zone entries: "member entry" on public home, "public homepage" entry on the work
  profile page, "browse as guest" link on the login page.

Out of scope for this slice:

- Real content backends for cats-public / stats / trivia / merch (tracked separately;
  cats can be promoted to the real `cats` table in a follow-up once `is_public` + a
  field whitelist are added).
- Guest→member conversion analytics beyond storing openid + visit counters.
- Per-visit event logging (only first/last visit + count for now).
- Guest-zone bottom tab bar (v1 uses a single scrolling landing home + secondary pages).
- WeChat share cards (follow-up).

## Routing Split

Decision tree at startup (loading page):

```
启动 → 加载页 (uni.login → POST /auth/wechat/login)
 ├─ openid 已绑定 → 改密检查 → 资料检查 → 工作首页 (pages/index/index)   [成员: 0 额外操作]
 └─ 未绑定(40104) / 无 code / 无 token → 公开首页 (pages/public/home)     [游客默认落点]
        └─ [成员入口] → 登录页 → 首绑/重绑成功 → reLaunch 工作首页
                           └─ [先随便逛逛] → 公开首页
```

Key properties:

- **Stateless rule**: bound → work, unbound → public. No local "member history" flag, so
  reinstall / cache-clear has no edge case. A member whose binding was cleared by an admin
  degrades gracefully to the guest zone and re-enters via the member entry.
- **Members keep zero extra steps.** The judgment is server-side (openid match), not a
  user-facing "who are you" chooser page (which would add a step for members).
- **Session-expiry stays on login.** In-session `40101/40102` still routes to the login
  page via `auth-session.ts` (the affected user is necessarily a member) — unchanged.
- **Compatibility**: the API contract for `/auth/wechat/login` does not change. Existing
  `1.1.1` clients that route `40104` → login page keep working; only the new frontend
  re-points `40104` → public home. This is why the backend can be deployed ahead of the
  Mini Program version with a near-zero risk window.

`resolveStartupRoute()` gains a new terminal route `PUBLIC_HOME_ROUTE`
(`/pages/public/home`) returned wherever it currently returns `LOGIN_ROUTE` due to an
unbound/absent WeChat identity. The hard-failure fallbacks (network error, rejected
session) still clear the session; their landing changes from login to public home for
guest-friendliness, except explicit auth-expiry which stays on login.

## Cross-Zone Navigation

- **Public → member**: public home shows a compact "成员入口" pill (top-right) and a labeled
  button in the "关于我们" block. When `userStore.isLoggedIn` is true (a member previewing
  the public zone), the pill switches to "返回工作区" / hides — never show "成员入口" to a
  logged-in user.
- **Member → public**: the work **profile page ("喵的")** gets a list item "协会公开主页"
  using `navigateTo` (not `reLaunch`) — the member previews with session intact and returns
  via back gesture. This doubles as the admin/content preview channel.
- **Login → public**: a "先随便逛逛 →" link returns to public home so no one is trapped at a
  login wall (also satisfies Mini Program review expectations against pure login walls).

## Public Zone Information Architecture

v1 is a **single scrolling landing home + two secondary pages**, not a guest tab bar
(the global Mini Program tabBar is already owned by the four work pages; three of the four
guest content types are lightweight showcase content that reads better as one page).

Public home (`pages/public/home`), top to bottom:

1. Brand band — reuse loading-page assets (团绒猫 illustration, wordmark, tagline),
   member-entry pill top-right.
2. Stats strip — `GET /public/stats` (in-campus cats, neuter rate, adopted count).
3. Campus cats — horizontal scroll of featured cat cards; "查看全部猫咪 >" → `pages/public/cats`.
4. Association trivia — 2–3 vertical cards (cover + title + date) → `pages/public/post-detail`.
5. Merchandise — two-column grid, **display only** (no price, no buy button, labeled as
   "社团活动纪念品") → `pages/public/post-detail`.
6. About us — intro / how to join / contact / civilized-feeding tips + a labeled member entry.

Secondary pages:

- `pages/public/cats` — public cats list. Whitelisted fields only: name, aliases, avatar/
  photos, coat color, sex, neuter status, personality tags, story. **Excluded**:
  resident-area text, last-seen time/point, feeding/capture/medical notes. Filter by coat/
  sex/status; sort by name or intake time (never "last seen", which leaks activity rhythm).
- `pages/public/cat-detail` — album + basic-info tags + story text.
- `pages/public/post-detail` — trivia / merch article view (cover, title, rich blocks).

All public pages handle loading / empty / error states and reuse the shared brand theme
(background asset, Songti font stack, `#267b2f` green system).

## Backend: Public Endpoints (Mock-Data Phase)

New module `app/modules/public/` + router `app/api/v1/public.py`, mounted at
`/api/v1/public` with **no auth dependency**. Endpoints return the standard `api_success`
envelope (`code/message/data/trace_id`), snake_case fields, existing pagination shape.

Planned endpoints (final contract; mock now, real later):

- `GET /public/stats` → `{ in_campus_cats, neuter_rate, adopted_cats, ... }`
- `GET /public/cats` (keyword/filter/sort/page/page_size) → paginated public cat list
- `GET /public/cats/{cat_id}` → public cat detail (whitelisted)
- `GET /public/posts?type=trivia|merch` (paginated) → post cards
- `GET /public/posts/{post_id}` → post detail

Mock data lives in versioned JSON fixtures under `app/modules/public/mock_data/*.json`,
loaded by the service layer and serialized through Pydantic response schemas so the shape
is contract-accurate. **This phase adds no content tables and no content migrations.**
Image URLs reference existing COS sample assets or repo `素材` placeholders.

Promotion path: replacing mock with real data changes only the service functions
(fixture read → DB query). Routes, schemas, and the frontend stay unchanged. The cats
endpoints are the first promotion candidate (real `cats` + `is_public` flag + whitelist).

## Backend: Guest openid Recording

Reuse the existing `40104` unbound path — the openid is already resolved there via
`exchange_wechat_code_for_openid` before the error is raised. On that path, **best-effort
upsert** a guest record, then raise `40104` as today.

Table `wechat_guests`:

- `id` (UUID pk)
- `openid` (String(128), unique, indexed) — plaintext, consistent with `users.wechat_openid`
- `first_visit_at`, `last_visit_at` (timezone-aware)
- `visit_count` (int)
- `created_at` / `updated_at`

Rules:

- Best-effort: any failure writing the guest record must **not** break the `40104` response
  — the guest still reaches the public zone. Wrap in a savepoint/try and swallow on failure.
- openid never leaves the server; no endpoint returns it. Frontend never touches openid
  (unchanged red line).
- Enables UV, return-rate, and later guest→member correlation (join on
  `users.wechat_openid`).
- Migration name will follow the sequence (next after `20260712_0014`).

## Compatibility & Safety

- API contract for existing endpoints is unchanged; `1.1.1` clients are unaffected by the
  public endpoints, the `40104`-path guest write, or the new `wechat_guests` table.
- Development uses `catmap_dev` (isolated DB, non-superuser role `catmap_dev_app`) via a
  local backend. Production `catmap` and the running `catmap-backend` service are not
  touched during development.
- The guest-table migration is applied to `catmap_dev` during development and only reaches
  production later through the normal deploy path (backup → deploy script → health check).
- Public pages go in the **main package** (guest first screen), not a subpackage.

## Compliance Notes

- Collecting guest openid is personal-information processing on not-yet-consented visitors.
  Before any production release, update the privacy guideline doc + WeChat backend privacy
  declaration to declare openid collection and its purpose (visit statistics).
- Public trivia/merch is outward-facing content. Publishing stays admin-controlled;
  content-security checking (`msgSecCheck`/`mediaCheck`, infra already present via
  `wechat_content_security`) should gate public UGC before it goes live.
- The editorial red line for trivia/merch: no feeding points, no fixed cat locations, no
  member real names / student numbers in public content.

## Testing & Verification

Backend:

- Public endpoint tests: envelope shape, pagination, field whitelist for cats, post type
  filtering, 404 for unknown ids — all without auth.
- Guest-recording tests: first visit creates a row; repeat visit increments `visit_count`
  and updates `last_visit_at`; write failure does not break the `40104` response.
- `pytest -q`, `ruff check .`, `alembic upgrade head` against `catmap_dev`.

Frontend:

- `app-startup` tests extended: unbound → public home; no code / no token → public home;
  bound → work home (unchanged); auth-expiry → login (unchanged).
- Public API client tests.
- `npm run test -- --run`, `npm run type-check`, `npm run build:mp-weixin`.

Manual (Mini Program): loading split for guest vs member, member entry from public home,
public preview from profile page, browse-as-guest link, guest openid recorded once per
identity.

## Rollout Phases

- **Phase 1 (this slice)**: routing split; public home (brand/stats/cats featured/about/
  member entry; trivia + merch from mock posts); public cats list + detail; `/public/*`
  mock endpoints; `wechat_guests` table + `40104`-path recording; login page guest link;
  profile-page public entry.
- **Phase 2**: promote cats-public to real `cats` + `is_public` whitelist; real `public_posts`
  content module + admin publish UI; content-security gating; share cards.
- **Phase 3**: guest→member conversion analytics; guest-zone tab bar if content volume needs it.
