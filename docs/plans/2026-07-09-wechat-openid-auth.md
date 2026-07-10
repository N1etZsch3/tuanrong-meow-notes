# WeChat OpenID Auth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the `1.1.1` WeChat Mini Program OpenID binding login flow while keeping the existing meow-number password login as the invite-only first-login and admin-unbind fallback.

**Architecture:** Add nullable WeChat binding fields to `users`, backend-only WeChat `code2Session` exchange, feature-gated auth behavior, an OpenID auto-login endpoint, and an admin unbind endpoint that increments `token_version`. Frontend startup tries WeChat auto-login first and falls back to the existing login page; password login can bind OpenID only after the user acknowledges the binding notice.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL, httpx or standard HTTP client for WeChat API, uni-app, Vue 3, TypeScript, Pinia, Vitest.

---

### Task 1: Backend Settings And WeChat Client

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`
- Create: `backend/app/modules/auth/wechat.py`
- Test: `backend/tests/test_auth_wechat.py`

**Step 1: Write failing settings/client tests**

Add tests that:

- Assert settings expose `wechat_miniapp_appid`, `wechat_miniapp_secret`, and `wechat_auth_mode`.
- Assert valid auth modes are `off`, `optional`, and `enforced`.
- Mock a successful `code2Session` response and return `openid`.
- Mock WeChat error responses and raise a project `APIError`.

Run:

```powershell
cd backend
python -m pytest tests/test_auth_wechat.py -q
```

Expected: fail because settings and `auth.wechat` do not exist.

**Step 2: Implement settings and client**

Add `CATMAP_WECHAT_MINIAPP_APPID`, `CATMAP_WECHAT_MINIAPP_SECRET`, `CATMAP_WECHAT_AUTH_MODE`, and a small `exchange_wechat_code_for_openid(code: str) -> str` helper. Do not log app secret, session key, or OpenID.

**Step 3: Verify**

Run:

```powershell
cd backend
python -m pytest tests/test_auth_wechat.py -q
python -m ruff check app/modules/auth app/core tests/test_auth_wechat.py
```

Expected: tests and ruff pass.

---

### Task 2: Database Model And Migration

**Files:**
- Modify: `backend/app/modules/auth/models.py`
- Create: `backend/alembic/versions/20260709_0013_add_wechat_openid_to_users.py`
- Modify: `docs/库表文档/鉴权模块_库表设计文档.md`
- Test: `backend/tests/test_auth_models.py`

**Step 1: Write failing model tests**

Add assertions that `users` contains:

- `wechat_openid`
- `wechat_bound_at`
- `last_wechat_login_at`

Run:

```powershell
cd backend
python -m pytest tests/test_auth_models.py -q
```

Expected: fail because fields are absent.

**Step 2: Implement model and migration**

Add nullable SQLAlchemy fields. Migration should add columns and a unique index:

```sql
CREATE UNIQUE INDEX uq_users_wechat_openid
ON users (wechat_openid)
WHERE wechat_openid IS NOT NULL;
```

Add downgrade logic to drop the index and columns.

**Step 3: Verify migration**

Run:

```powershell
cd backend
python -m pytest tests/test_auth_models.py -q
python -m alembic upgrade head
python -m alembic downgrade 20260706_0012
python -m alembic upgrade head
```

Expected: tests pass and migration upgrades/downgrades cleanly.

---

### Task 3: Backend Binding And Auto-Login APIs

**Files:**
- Modify: `backend/app/core/errors.py`
- Modify: `backend/app/modules/auth/schemas.py`
- Modify: `backend/app/modules/auth/service.py`
- Modify: `backend/app/api/v1/auth.py`
- Modify: `docs/接口文档/鉴权模块_接口文档.md`
- Test: `backend/tests/test_auth_api.py`

**Step 1: Write failing API tests**

Cover:

- Password login with `wechat_code` and `agree_wechat_bind=true` binds an unbound account.
- Password login rejects binding when the OpenID already belongs to another account.
- Password login rejects when the account is already bound to another OpenID.
- `POST /api/v1/auth/wechat/login` returns JWT for a bound active account.
- `POST /api/v1/auth/wechat/login` rejects unbound OpenID and inactive/deleted users.
- `CATMAP_WECHAT_AUTH_MODE=off` disables WeChat auto-login and binding.
- `CATMAP_WECHAT_AUTH_MODE=optional` preserves old password login for compatibility.
- `CATMAP_WECHAT_AUTH_MODE=enforced` rejects password login for already-bound accounts unless OpenID matches.

Run:

```powershell
cd backend
python -m pytest tests/test_auth_api.py -q
```

Expected: fail because schemas, service rules, and route do not exist.

**Step 2: Implement minimal service behavior**

Add request/response schemas:

- `wechat_code?: string`
- `agree_wechat_bind?: boolean`
- `WeChatLoginRequest`

Refactor token response construction so password login and WeChat auto-login share one response shape. Keep route handlers thin.

**Step 3: Verify targeted backend auth**

Run:

```powershell
cd backend
python -m pytest tests/test_auth_api.py tests/test_auth_wechat.py tests/test_auth_models.py -q
python -m ruff check app/modules/auth app/api/v1/auth.py app/core tests/test_auth_api.py tests/test_auth_wechat.py tests/test_auth_models.py
```

Expected: auth tests and ruff pass.

---

### Task 4: Admin Clear WeChat Binding

**Files:**
- Modify: `backend/app/modules/auth/service.py`
- Modify: `backend/app/modules/auth/schemas.py`
- Modify: `backend/app/api/v1/admin_users.py`
- Modify: `frontend/src/api/admin-users.ts`
- Modify: `frontend/src/api/routes.ts`
- Test: `backend/tests/test_admin_users_api.py`
- Test: `frontend/tests/api/admin-users.test.ts`

**Step 1: Write failing backend admin tests**

Cover:

- Admin can clear a member's WeChat binding.
- Clearing binding sets `wechat_openid`, `wechat_bound_at`, and `last_wechat_login_at` to null as appropriate.
- Clearing binding increments `token_version`.
- Old JWT fails after unbind.
- Admin operation log records the action without storing raw OpenID in chat or logs.
- Non-admin cannot clear binding.

Run:

```powershell
cd backend
python -m pytest tests/test_admin_users_api.py -q
```

Expected: fail because route and service do not exist.

**Step 2: Implement admin route**

Add:

```http
DELETE /api/v1/admin/users/{user_id}/wechat-binding
```

Use existing `require_admin`, target editability checks, `token_version + 1`, and admin operation logging.

**Step 3: Add frontend API wrapper**

Add the route builder and typed `clearAdminUserWechatBinding` API function. UI wiring can be a later task if the current admin detail page is not ready for the button.

**Step 4: Verify**

Run:

```powershell
cd backend
python -m pytest tests/test_admin_users_api.py tests/test_auth_api.py -q
cd ..\frontend
npm run test -- --run tests/api/admin-users.test.ts tests/api/routes.test.ts
```

Expected: targeted backend and frontend API tests pass.

---

### Task 5: Frontend Auth API, Store, And Startup

**Files:**
- Modify: `frontend/src/api/auth.ts`
- Modify: `frontend/src/api/routes.ts`
- Modify: `frontend/src/stores/user.ts`
- Create: `frontend/src/services/wechat-auth.ts`
- Modify: `frontend/src/services/app-startup.ts`
- Test: `frontend/tests/api/auth.test.ts`
- Test: `frontend/tests/stores/user.test.ts`
- Test: `frontend/tests/services/app-startup.test.ts`

**Step 1: Write failing frontend tests**

Cover:

- `wechatLogin(code)` posts to `/auth/wechat/login`.
- `loginWithPassword` can include `wechat_code` and `agree_wechat_bind`.
- User store saves JWT/session returned by WeChat auto-login.
- Startup calls WeChat auto-login before falling back to password login.
- Startup falls back to login when `uni.login` is unavailable, fails, or backend returns unbound.

Run:

```powershell
cd frontend
npm run test -- --run tests/api/auth.test.ts tests/stores/user.test.ts tests/services/app-startup.test.ts
```

Expected: fail because frontend helpers do not exist.

**Step 2: Implement frontend helpers**

Create a small `requestWechatLoginCode()` wrapper around `uni.login({ provider: "weixin" })`. Keep H5/development fallback graceful: if `uni.login` is missing or not WeChat, return a controlled failure and continue to the login page.

**Step 3: Verify**

Run:

```powershell
cd frontend
npm run test -- --run tests/api/auth.test.ts tests/stores/user.test.ts tests/services/app-startup.test.ts
npm run type-check
```

Expected: targeted tests and type-check pass.

---

### Task 6: Login Page Binding Notice

**Files:**
- Modify: `frontend/src/pages/login/index.vue`
- Test: `frontend/tests/pages/login-agreement.test.ts`

**Step 1: Write failing page tests**

Assert:

- The page contains the binding notice text.
- Login submission sends `agree_wechat_bind=true` only after acknowledgement.
- Missing binding acknowledgement blocks submission before hitting backend.
- If `uni.login` fails, password login can still proceed in optional mode without binding only when backend accepts it.

Run:

```powershell
cd frontend
npm run test -- --run tests/pages/login-agreement.test.ts
```

Expected: fail because binding notice and code handling do not exist.

**Step 2: Implement UI**

Add concise text near the existing agreement area:

```text
登录后，当前微信将与该喵喵号绑定，用于后续自动登录和账号保护。如需更换微信，请联系管理员解绑。
```

Collect `wechat_code` before submit when possible. Keep layout mobile-first and preserve the existing Songti font stack.

**Step 3: Verify**

Run:

```powershell
cd frontend
npm run test -- --run tests/pages/login-agreement.test.ts tests/services/app-startup.test.ts
npm run type-check
npm run build:mp-weixin
```

Expected: tests, type-check, and Mini Program build pass.

---

### Task 7: Documentation, Release Safety, And Full Verification

**Files:**
- Modify: `docs/开发进度.md`
- Modify: `docs/接口文档/鉴权模块_接口文档.md`
- Modify: `docs/库表文档/鉴权模块_库表设计文档.md`
- Modify: `docs/接口文档/用户与个人中心模块_接口文档.md`
- Modify: `docs/库表文档/用户与个人中心模块_库表设计文档.md`

**Step 1: Update docs**

Record:

- `1.1.1` target version.
- `CATMAP_WECHAT_AUTH_MODE=optional` first deployment mode.
- Manual WeChat Developer Tools checks required before `enforced`.
- Admin unbind as the password fallback recovery path.

**Step 2: Run full verification**

Run:

```powershell
cd backend
python -m pytest -q
python -m ruff check .
python -m alembic upgrade head
cd ..\frontend
npm run test -- --run
npm run type-check
npm run build:mp-weixin
```

Expected: all automated checks pass.

**Step 3: Deployment gate**

Before deploying to the shared production server:

- Confirm backend env has WeChat appid/secret configured privately.
- Deploy with `CATMAP_WECHAT_AUTH_MODE=optional`.
- Run deployment contract checks.
- Verify existing password login still works.
- Verify bound WeChat auto-login in WeChat Developer Tools or on a real device.

Only after manual verification should production switch to `CATMAP_WECHAT_AUTH_MODE=enforced`.
