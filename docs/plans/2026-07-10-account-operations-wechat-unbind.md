# Account Operations And WeChat Self-Unbind Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add safe member account operations, current-user WeChat unbinding, compact settings UI, and merge the complete OpenID feature into `dev` without losing its accepted bug fixes.

**Architecture:** Keep administrator-to-member operations under the existing `/admin/users/{user_id}` boundary and add a separate identity-derived `DELETE /auth/wechat-binding` endpoint for self-unbind. Use a native Mini Program action sheet to aggregate member operations, while account settings becomes a grouped row interface with an explicit logout-after-unbind flow.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic, pytest, uni-app, Vue 3, TypeScript, Pinia, Vitest, WeChat Mini Program.

---

### Task 1: Add The Current-User WeChat Unbind Contract

**Files:**
- Modify: `backend/tests/test_auth_api.py`
- Modify: `backend/app/modules/auth/service.py`
- Modify: `backend/app/api/v1/auth.py`

**Step 1: Write failing backend tests**

Add tests that bind a member and an administrator, call `DELETE /api/v1/auth/wechat-binding` with each account's own JWT, and assert:

```python
assert response.status_code == 200
assert response.json()["data"]["wechat_bound"] is False
assert user.wechat_openid is None
assert user.wechat_bound_at is None
assert user.last_wechat_login_at is None
assert user.token_version == original_token_version + 1
```

Use the old token on `/api/v1/auth/me` and assert HTTP 401. Add an unbound-account test that receives HTTP 400 and keeps the token valid.

**Step 2: Run the tests and observe the red state**

Run:

```powershell
cd backend
py -3.11 -m pytest tests/test_auth_api.py -q
```

Expected: the new tests fail because the route does not exist.

**Step 3: Implement the service and route**

Add a current-user service function that rejects an empty binding, clears only the three WeChat fields, increments `token_version`, commits, and returns:

```python
{
    "user_id": user.id,
    "wechat_bound": False,
    "token_version": user.token_version,
    "token_invalidated": True,
}
```

Expose it as `DELETE /auth/wechat-binding` with `get_current_user`. Do not accept a target user ID and do not weaken the existing administrator endpoint.

**Step 4: Run targeted backend tests**

Run the command from Step 2 and expect all tests in `test_auth_api.py` to pass.

**Step 5: Commit**

Stage the three explicit files and commit:

```text
feat(auth): add wechat self unbind
```

### Task 2: Add The Frontend Self-Unbind API And Store Action

**Files:**
- Modify: `frontend/tests/api/auth.test.ts`
- Modify: `frontend/tests/stores/user.test.ts`
- Modify: `frontend/src/api/routes.ts`
- Modify: `frontend/src/api/auth.ts`
- Modify: `frontend/src/stores/user.ts`

**Step 1: Write failing API and store tests**

Assert that `unbindWechatBinding` sends an authenticated `DELETE` to `/auth/wechat-binding`. Assert that `userStore.unbindCurrentWechat()` clears access token, expiry, current user, and all corresponding storage keys only after a successful response; a rejected request must preserve the session.

**Step 2: Run the tests and observe the red state**

```powershell
cd frontend
npm run test -- --run tests/api/auth.test.ts tests/stores/user.test.ts
```

Expected: failures for missing route, API wrapper, and store action.

**Step 3: Implement the API and store action**

Add `API_ENDPOINTS.auth.wechatBinding`, a typed response, and:

```ts
export function unbindWechatBinding(accessToken: string) {
  return request({
    url: API_ENDPOINTS.auth.wechatBinding,
    method: "DELETE",
    token: accessToken,
  });
}
```

The Pinia action must ensure a fresh token, await the API, then call `clearSession()` before returning.

**Step 4: Run targeted tests and commit**

Expect both files to pass, then commit the five explicit files as:

```text
feat(auth): connect wechat self unbind
```

### Task 3: Redesign Account Settings As Grouped Settings Rows

**Files:**
- Modify: `frontend/tests/pages/profile-page.test.ts`
- Modify: `frontend/src/pages/profile/settings.vue`

**Step 1: Write failing UI contract tests**

Assert the page contains `账号与安全`, `重设密码`, `微信解绑`, a separate `退出登录` group, and no `row-desc`. Assert the self-unbind confirmation contains `解绑后将立即退出登录` and invokes `userStore.unbindCurrentWechat()` before `uni.reLaunch({ url: LOGIN_ROUTE })`.

**Step 2: Run the page test and observe the red state**

```powershell
npm run test -- --run tests/pages/profile-page.test.ts
```

**Step 3: Implement the grouped settings UI**

Build one compact white group with two 88-96rpx rows. Each row contains a project asset icon, a single label, and a chevron; separate rows with a one-pixel divider. Put logout in its own white group with centered red text. Explicitly set row and text line heights so native `button` styles cannot stretch spacing.

Self-unbind flow:

```text
tap 微信解绑
  -> showModal explaining immediate logout and password re-login
  -> confirm
  -> await userStore.unbindCurrentWechat()
  -> reLaunch login
```

On cancellation or API failure, preserve the session and current page. Prevent duplicate submissions while the request is running.

**Step 4: Run the page test, type-check, and commit**

Commit the two explicit files as:

```text
feat(profile): add wechat unbind setting
```

### Task 4: Aggregate Member Account Operations

**Files:**
- Modify: `frontend/tests/pages/admin-page.test.ts`
- Modify: `frontend/src/pages/admin/users/detail.vue`

**Step 1: Write failing UI contract tests**

Assert the old standalone buttons and `成员退出` label are gone. Assert editable members have a two-column `detail-actions` row with `账号操作` and `保存资料`, and that `uni.showActionSheet` contains exactly:

```ts
["重置密码", "重置微信绑定", "删除账号"]
```

Assert an unbound member produces `当前成员尚未绑定微信`, and admin targets remain read-only.

**Step 2: Run the page test and observe the red state**

```powershell
npm run test -- --run tests/pages/admin-page.test.ts
```

**Step 3: Implement minimal aggregation**

Map action-sheet indexes to the existing reset modal, WeChat confirmation, and soft-delete confirmation. Rename destructive user-facing copy from `成员退出` to `删除账号` without changing the backend soft-delete contract. Keep all operation guards and loading flags.

Style the bottom as two stable equal-width grid tracks. Use a neutral outlined secondary button on the left and the existing green primary button on the right.

**Step 4: Run targeted tests and commit**

Commit the two explicit files as:

```text
feat(admin): group member account operations
```

### Task 5: Tighten The Administrator Entry Card

**Files:**
- Modify: `frontend/tests/pages/admin-page.test.ts`
- Modify: `frontend/src/pages/admin/index.vue`

**Step 1: Add a failing style contract**

Require explicit compact line heights for `.admin-action`, `.action-title`, and `.action-subtitle`; require a smaller card minimum height and a title/description gap no greater than `6rpx`.

**Step 2: Run the test and observe failure**

Run the admin page test from Task 4.

**Step 3: Implement compact styling**

Preserve the title and useful description, but reduce card height, padding, icon size, corner radius, and shadow. Set `line-height: 1` or a similarly explicit value on the button and copy elements to remove inherited Mini Program button spacing.

**Step 4: Run tests and commit**

Commit the two explicit files as:

```text
fix(ui): tighten settings and admin entry rows
```

### Task 6: Update Contracts And Verify The Feature Branch

**Files:**
- Modify: `docs/接口文档/鉴权模块_接口文档.md`
- Modify: `docs/接口文档/用户与个人中心模块_接口文档.md`
- Modify: `docs/开发进度.md`

**Step 1: Update API, permission, UI, and progress documentation**

Record the self-unbind endpoint, token invalidation, confirmation behavior, member operation menu, permission matrix, no database migration, verification results, and remaining true-device checks.

**Step 2: Run feature-branch verification**

```powershell
cd backend
py -3.11 -m pytest tests/test_auth_api.py tests/test_admin_users_api.py -q
py -3.11 -m ruff check .

cd ..\frontend
npm run test -- --run
npm run type-check
npm run build:mp-weixin
```

Run `git diff --check`, inspect staged files, and scan the staged diff for secrets. Do not stage root `project.config.json` or `project.private.config.json`.

**Step 3: Commit documentation and final focused changes**

```text
docs(auth): document account operations and self unbind
```

### Task 7: Merge The Completed Feature Into Dev

**Files:**
- Merge worktree: `D:\Study\Project\CatMap\.worktrees\dev`

**Step 1: Reconfirm both worktrees are clean enough to merge**

Check `git status --short --branch` in both worktrees and confirm `dev` remains at or ahead of `37915d6` with its accepted bug-fix merge intact.

**Step 2: Merge only after feature completion**

From `.worktrees/dev`, merge `feature/wechat-openid-auth` with `--no-ff`. Resolve conflicts by preserving both sets of behavior, especially:

- avatar COS upload and avatar error fallbacks in profile/admin pages;
- OpenID fields, APIs, startup login, admin binding reset, and self-unbind;
- task state-machine, task record modal, image preview, and map marker fixes;
- the newest progress entries from both branches.

Do not resolve conflicts by choosing an entire side for overlapping files.

**Step 3: Inspect the merged diff and commit the merge**

Verify the merge commit has both parent histories and that no feature files disappeared.

### Task 8: Verify Merged Dev And Deploy Production Backend

**Files:**
- Verification/deployment worktree: `D:\Study\Project\CatMap\.worktrees\dev`

**Step 1: Run full merged backend verification**

```powershell
cd backend
py -3.11 -m pytest -q
py -3.11 -m ruff check .
py -3.11 -m alembic upgrade head
```

**Step 2: Run full merged frontend verification**

```powershell
cd frontend
npm run test -- --run
npm run type-check
npm run build:mp-weixin
```

Confirm the production artifact contains `https://trmx.fun/api/v1`, the new setting labels, and no actual localhost/bare-IP URL or app secret.

**Step 3: Verify deployment inputs without printing secrets**

Confirm the selected ignored env file contains the required production and WeChat variable names, remains ignored, and uses `CATMAP_WECHAT_AUTH_MODE=optional`. Inspect the commits being deployed for credentials.

**Step 4: Deploy the merged backend**

Run the repository deployment script from merged `dev` using the verified env file:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy-backend.ps1 -EnvFile backend\.env
```

Do not use `-SkipLocalChecks` unless a newly documented unrelated baseline failure makes it necessary.

**Step 5: Verify production**

Check `https://trmx.fun/api/v1/health`, remote service state, Alembic head, deployment logs, and safe unauthenticated behavior of `DELETE /api/v1/auth/wechat-binding`. Do not invoke the endpoint with a real user token during automated verification.

**Step 6: Final progress entry**

Update `docs/开发进度.md` in `dev` with merge commit, deployment backup path, verification counts, production health, manual checks not run, and rollback notes. Commit that deployment record separately.
