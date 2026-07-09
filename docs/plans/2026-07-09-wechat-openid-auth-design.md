# WeChat OpenID Auth Design

## Goal

Ship a `1.1.1` authentication upgrade for the WeChat Mini Program: keep CatMap invite-only through existing meow-number accounts, bind the first verified login to the user's Mini Program OpenID, and allow later startup auto-login without asking for the password again.

## Current Context

- Current production baseline is `v1.1.0`.
- The backend at `trmx.fun` is already production-facing.
- Development and production currently share the same server path, so authentication changes must be compatible and feature-gated.
- Existing auth is `meow_no/student_no + password + captcha + JWT`.
- Existing JWT invalidation relies on `users.token_version`.

## Scope

This `1.1.1` slice adds:

- Backend OpenID exchange using the WeChat Mini Program `code2Session` API.
- Nullable OpenID binding fields on `users`.
- First verified meow-number password login can bind the current WeChat identity after explicit user acknowledgement.
- Startup auto-login by `wx.login` / `uni.login` code when the OpenID is already bound.
- Admin endpoint to clear a member's WeChat binding.
- Compatibility mode so the existing password login keeps working until strict mode is enabled.

Out of scope:

- Member self-registration.
- Phone number, email, unionid, or non-WeChat OAuth login.
- Multi-WeChat-account binding per user.
- Refresh token or server-side session table.
- Silent binding without user-facing notice.

## Recommended Architecture

The frontend never receives or submits OpenID directly. It calls `wx.login` / `uni.login` and sends the short-lived `code` to the backend. The backend exchanges that code with WeChat using server-side `CATMAP_WECHAT_MINIAPP_APPID` and `CATMAP_WECHAT_MINIAPP_SECRET`, then treats the returned `openid` as trusted identity data.

For this small version, add fields directly to `users` instead of introducing `oauth_accounts`:

- `wechat_openid`
- `wechat_bound_at`
- `last_wechat_login_at`

`wechat_openid` remains nullable and unique. This keeps migration and service code small. A separate identity table can be introduced later if multiple identity providers or multiple WeChat identities become a real requirement.

## Auth Modes

Add a backend environment switch:

```text
CATMAP_WECHAT_AUTH_MODE=off|optional|enforced
```

- `off`: current password/JWT behavior only; new endpoints may return disabled. Use as emergency rollback.
- `optional`: password login remains valid and can bind OpenID; OpenID auto-login works when bound. This is the first production deployment mode.
- `enforced`: bound accounts must use matching OpenID for normal login; password login is reserved for unbound accounts or accounts after admin unbind.

Because the server is production-facing, deploy backend support in `optional` mode first, then ship the Mini Program frontend, then switch to `enforced` only after real-device verification.

## Login Flows

### First Binding Login

1. User enters meow number, password, captcha, and confirms the binding notice.
2. Frontend obtains a WeChat login code.
3. Frontend posts existing login payload plus `wechat_code` and `agree_wechat_bind=true`.
4. Backend validates captcha, account, password, status, lock state, and first-login agreement rules.
5. Backend exchanges the code for OpenID.
6. If the user has no OpenID binding and the OpenID is not bound to another account, backend writes the binding.
7. Backend returns the normal JWT payload and `next_action`.

### Startup Auto-Login

1. Loading page calls `wx.login` / `uni.login`.
2. Frontend posts `code` to `POST /api/v1/auth/wechat/login`.
3. Backend exchanges code for OpenID and finds an active, undeleted user.
4. Backend updates `last_login_at` and `last_wechat_login_at`, then returns a normal JWT payload.
5. Frontend follows the existing route decisions: change password, complete profile, or enter app.

If no binding exists, frontend clears local session and falls back to the existing login page.

### Admin Unbind

Admin clears a member's binding through:

```http
DELETE /api/v1/admin/users/{user_id}/wechat-binding
```

The backend clears binding fields, increments `token_version`, and records an admin operation log. Incrementing `token_version` invalidates existing JWTs, so the next app launch requires the member to log in with meow number and password and bind again.

## User Notice

Binding must be explicit. The login UI should tell the user:

```text
登录后，当前微信将与该喵喵号绑定，用于后续自动登录和账号保护。如需更换微信，请联系管理员解绑。
```

The backend should require `agree_wechat_bind=true` whenever a password login attempts to create a new WeChat binding.

## Error Handling

Use project-style API envelopes and avoid leaking OpenID values.

Planned new auth errors:

- WeChat login unavailable or `code2Session` failed.
- OpenID has not been bound to any account.
- Current WeChat has already been bound to another account.
- Current meow account has already been bound to another WeChat identity.
- Binding notice was not acknowledged.

All user-facing messages should direct members to retry login or contact an administrator. Logs may include trace IDs and high-level error categories, but must not print secrets or raw environment values.

## Testing And Verification

Backend:

- Unit tests for settings and WeChat code exchange with mocked HTTP responses.
- Migration/model tests for nullable unique `wechat_openid`.
- Auth API tests for first binding, bound auto-login, mismatched binding rejection, and auth mode behavior.
- Admin API tests for clearing binding and invalidating token_version.

Frontend:

- API tests for new auth endpoints.
- Startup tests proving auto-login falls back to password login when unbound or unavailable.
- Store tests for saving the returned JWT/session from WeChat auto-login.
- Login page tests for the binding notice and required acknowledgement.

Release verification:

- Deploy backend in `optional` mode first.
- Run backend tests, ruff, Alembic upgrade, frontend tests, type-check, and `build:mp-weixin`.
- In WeChat Developer Tools or a real device, verify first bind, startup auto-login, admin unbind, and rebind.
- Switch to `enforced` only after successful manual checks.
