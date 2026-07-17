# 头衔系统 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完成 13 个头衔的唯一占用、会长授权与原子转让、成员放弃、前端展示及人员管理交互。

**Architecture:** `user_profiles.title` 保存单值头衔，NULL 表示无；数据库部分唯一索引保证 12 个非空头衔唯一。后端独立 `titles` 模块负责目录、授权、事务和审计，现有 auth/profile/me 仅接入 payload 与生命周期钩子。前端用共享注册表、独立 API 和 `TitleBadge` 组件接入现有资料卡、设置和人员管理页面。

**Tech Stack:** FastAPI、Pydantic、SQLAlchemy 2.0、Alembic、PostgreSQL/SQLite 测试；uni-app、Vue 3、TypeScript、Pinia、Vitest、微信小程序原生 picker/showModal。

---

### Task 1: 固化头衔契约、迁移和基础 payload

**Files:**
- Modify: `backend/tests/test_auth_models.py`
- Create: `backend/tests/test_titles_api.py`
- Create: `backend/alembic/versions/20260718_0019_add_profile_title.py`
- Modify: `backend/app/modules/titles/constants.py`
- Modify: `backend/app/modules/auth/schemas.py`
- Modify: `backend/app/modules/auth/service.py`
- Modify: `backend/app/modules/profile/service.py`
- Modify: `backend/app/modules/me/service.py`

**Step 1: Write the failing tests**

- 断言 `UserProfile.title` 存在且 `uq_user_profiles_title` 只约束非 NULL。
- 断言 `/auth/me`、`/profile/me`、`/me/dashboard`、管理员用户 payload 都返回：

```python
assert data["title"] == "vice_president"
assert data["title_label"] == "副会长"
assert data["title_shield"] == "purple"
```

**Step 2: Run tests to verify RED**

Run: `py -3.11 -m pytest tests/test_auth_models.py tests/test_titles_api.py -q -p no:randomly`

Expected: FAIL，因为 schema 与 payload 尚未返回头衔字段。

**Step 3: Implement the minimal contract**

- 完成迁移 `20260718_0019`：添加 nullable `title varchar(64)`，创建 PostgreSQL/SQLite 可用的 `WHERE title IS NOT NULL` 唯一索引；downgrade 先删索引再删列。
- 在常量模块提供 `title_payload(title)`，无头衔返回三个字段的 NULL 值。
- 为 Pydantic 与四处 payload 补齐 `title/title_label/title_shield`。

**Step 4: Verify GREEN**

Run: `py -3.11 -m pytest tests/test_auth_models.py tests/test_titles_api.py -q -p no:randomly`

Expected: PASS。

### Task 2: 头衔目录与会长独立授权

**Files:**
- Create: `backend/app/modules/titles/schemas.py`
- Create: `backend/app/modules/titles/dependencies.py`
- Create: `backend/app/modules/titles/service.py`
- Create: `backend/app/api/v1/admin_titles.py`
- Modify: `backend/app/api/v1/admin_users.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/app/core/errors.py`
- Modify: `backend/tests/test_titles_api.py`

**Step 1: Write the failing catalog/authorization tests**

```python
response = client.get("/api/v1/admin/titles", headers=president_headers)
assert response.status_code == 200
assert len(response.json()["data"]["items"]) == 12
assert response.json()["data"]["items"][0].keys() >= {
    "key", "label", "shield", "is_available", "holder"
}
```

- 普通管理员访问目录返回 403/63010。
- 占用项返回持有者 `user_id/meow_no/nickname`，空闲项 holder 为 NULL。

**Step 2: Verify RED**

Run: `py -3.11 -m pytest tests/test_titles_api.py -q -p no:randomly -k 'catalog or president_authorization'`

Expected: FAIL/404，因为路由和依赖尚不存在。

**Step 3: Implement minimal catalog and dependency**

- `require_president` 依赖 `require_password_changed`，检查 active 用户资料的 `title == president`，不复用 `ensure_target_is_editable`。
- `title_catalog` 用一次查询加载全部已占用头衔和持有者，按常量注册顺序返回 12 项。
- 注册 `GET /api/v1/admin/titles`。

**Step 4: Verify GREEN**

Run: 同 Step 2；Expected: PASS。

### Task 3: 授予、剥夺和创建成员初始头衔

**Files:**
- Modify: `backend/app/modules/titles/schemas.py`
- Modify: `backend/app/modules/titles/service.py`
- Modify: `backend/app/api/v1/admin_users.py`
- Modify: `backend/app/modules/auth/schemas.py`
- Modify: `backend/app/modules/auth/service.py`
- Modify: `backend/tests/test_titles_api.py`
- Modify: `backend/tests/test_admin_users_api.py`

**Step 1: Write one failing test per behavior**

- 会长可 `PATCH /admin/users/{id}/title` 授予空闲非 president 头衔。
- `none` 剥夺目标旧头衔。
- 已占用返回 409/63009，不改动任何持有者。
- 非法 key 或普通授予 president 返回 422/63011。
- 不能通过普通接口修改当前 president。
- 普通管理员建号提交非空 `profile.title` 返回 403/63010；会长建号可指定空闲头衔。
- 所有成功写入产生 `AdminOperationLog`。

**Step 2: Verify RED for each behavior**

Run targeted node for each new test and confirm the expected missing-behavior failure.

**Step 3: Implement minimal behavior**

- 服务层锁定目标资料并检查占用；捕获唯一约束冲突并映射为 409。
- 创建用户的 title 与用户、资料、部门、审计处于同一事务；不在 service 内提前 commit。
- 非会长提交非空初始头衔明确拒绝。

**Step 4: Verify GREEN and refactor**

Run: `py -3.11 -m pytest tests/test_titles_api.py tests/test_admin_users_api.py -q -p no:randomly`

Expected: PASS。

### Task 4: 放弃、原子转让、删除释放与 seed

**Files:**
- Modify: `backend/app/modules/titles/service.py`
- Create: `backend/app/api/v1/profile_titles.py`
- Modify: `backend/app/api/v1/admin_titles.py`
- Modify: `backend/app/api/v1/router.py`
- Modify: `backend/app/modules/auth/service.py`
- Create: `backend/scripts/grant_president.py`
- Modify: `backend/tests/test_titles_api.py`
- Modify: `backend/tests/test_admin_users_api.py`

**Step 1: Write failing lifecycle tests**

- 非会长头衔持有者调用 `POST /profile/me/title/resign` 成功释放。
- 无头衔调用幂等返回无头衔。
- president 调用放弃返回 403/63012，头衔保持不变。
- 转让给普通成员：旧会长→NULL、继承者→president、继承者旧头衔释放、role→admin、`token_version + 1`。
- 转让给管理员不额外增加 token_version。
- 自转让、非会长转让失败且事务无部分写入。
- 软删除带头衔的普通成员释放头衔。
- seed 在无会长时授予并确保 admin；已有其他会长时拒绝覆盖。

**Step 2: Verify RED**

Run targeted test nodes; Expected: route missing or assertions fail for missing lifecycle behavior.

**Step 3: Implement atomic operations**

- 同一事务锁定旧会长和继承者资料。
- 先将旧会长置 NULL 并 flush，再给继承者赋 president；任何错误 rollback，外部不可观察中间状态。
- 所有成功操作写审计；路由层统一 commit/rollback 边界或服务保持项目现有事务风格，但不得双 commit。

**Step 4: Verify GREEN**

Run: `py -3.11 -m pytest tests/test_titles_api.py tests/test_admin_users_api.py -q -p no:randomly`

Expected: PASS。

### Task 5: 前端注册表、API 与可复用 TitleBadge

**Files:**
- Create: `frontend/src/constants/titles.ts`
- Create: `frontend/src/api/titles.ts`
- Modify: `frontend/src/api/routes.ts`
- Modify: `frontend/src/api/admin-users.ts`
- Modify: `frontend/src/api/auth.ts`
- Modify: `frontend/src/api/me.ts`
- Modify: `frontend/src/api/profile.ts`
- Modify: `frontend/src/types/user.ts`
- Modify: `frontend/src/stores/user.ts`
- Create: `frontend/src/components/TitleBadge.vue`
- Create: `frontend/素材/svg/头衔/会长.svg`
- Create: `frontend/素材/svg/头衔/副会长.svg`
- Create: `frontend/素材/svg/头衔/部长.svg`
- Create: `frontend/tests/components/title-badge.test.ts`
- Create: `frontend/tests/api/titles.test.ts`

**Step 1: Write failing tests**

- 注册表恰好包含 12 个非空 key、12 个不同 tag 背景色和 3 个盾牌 variant。
- `TitleBadge` 对 none 不渲染，对合法 key 渲染 SVG、标签和可读颜色类。
- API 路由和请求方法映射正确。

**Step 2: Verify RED**

Run: `npm run test -- --run tests/components/title-badge.test.ts tests/api/titles.test.ts`

Expected: FAIL，因为模块尚不存在。

**Step 3: Implement minimal reusable layer**

- 复用项目盾牌 path，仅生成三种 fill 变体；不引入网络素材。
- `TitleBadge.vue` 只负责显示，不持有业务请求状态。

**Step 4: Verify GREEN**

Run: 同 Step 2；Expected: PASS。

### Task 6: 资料卡、设置放弃和人员管理交互

**Files:**
- Modify: `frontend/src/pages/profile/index.vue`
- Modify: `frontend/src/pages/profile/settings.vue`
- Modify: `frontend/src/pages/admin/create-user.vue`
- Modify: `frontend/src/pages/admin/users/detail.vue`
- Create: `frontend/src/pages/admin/users/title-actions.ts`
- Create: `frontend/tests/pages/title-management.test.ts`
- Modify: `frontend/tests/pages/profile-page.test.ts`

**Step 1: Write failing page/helper tests**

- 资料卡昵称行复用 `TitleBadge`，无头衔不占位。
- 设置仅对非 president 的非空头衔显示“放弃头衔”，确认后调用 API 并刷新 store。
- 只有当前用户是 president 时，建号页显示原生 `picker mode="selector"`。
- 人员详情保留原账号操作，同时给 president 独立展示头衔操作；已占用项不可提交。
- 转让给非管理员的确认文案包含“自动升格为管理员”。
- 所有危险操作仅在 `showModal` 的 confirm 分支调用 API。

**Step 2: Verify RED**

Run: `npm run test -- --run tests/pages/title-management.test.ts tests/pages/profile-page.test.ts`

Expected: FAIL，因为页面尚未接入头衔。

**Step 3: Implement minimal UI**

- 选择使用微信原生 selector picker；不使用最多 6 项的 action sheet 承载 12 头衔。
- 页面仅协调加载、确认和刷新；过滤、文案与可用性判断放入 `title-actions.ts`。
- 保持宋体、公共背景、手机视口与现有页面状态处理。

**Step 4: Verify GREEN and run frontend gates**

Run:

```powershell
npm run test -- --run tests/pages/title-management.test.ts tests/pages/profile-page.test.ts
npm run type-check
npm run build:mp-weixin
```

Expected: 全部通过。

### Task 7: 契约文档、全量验证与进度记录

**Files:**
- Create: `docs/模块功能/头衔系统_功能说明文档.md`
- Modify: `docs/接口文档/用户与个人中心模块_接口文档.md`
- Modify: `docs/库表文档/用户与个人中心模块_库表设计文档.md`
- Modify: `docs/开发进度.md`

**Step 1: Update current docs**

- 写明 13 个取值、唯一性、会长权限边界、转让事务、API、迁移 `20260718_0019`、前端原生组件选择与未实现的按头衔业务权限。
- `docs/开发进度.md` 使用 `YYYY-MM-DD HH:mm:ss +08:00`，记录分支、文件、迁移、验证、未做真机项和风险。

**Step 2: Run backend gates**

```powershell
py -3.11 -m pytest -q -p no:randomly
py -3.11 -m ruff check .
py -3.11 -m alembic heads
py -3.11 -m alembic upgrade head
```

Expected: 全量通过、唯一 head 为 `20260718_0019`。仅对从 dev 复制且确认安全的开发环境配置执行迁移，禁止触碰生产。

**Step 3: Run frontend gates**

```powershell
npm run test -- --run
npm run type-check
npm run build:mp-weixin
```

Expected: 全量通过。

**Step 4: Review and commit explicit files**

- `git diff --check`
- 检查未跟踪文件、环境文件仍 ignored、差异无秘密或真实凭据。
- 只 `git add <explicit files>`，提交 `feat(titles): add unique title ownership and transfer`。
- 不合 dev、不推远端、不部署。
