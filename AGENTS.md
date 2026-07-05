# AGENTS.md

This file is the development playbook for agents working on the Campus Cat Association Map Task System.

The project documents are written in Chinese and are the source of truth for product scope, module behavior, API rules, and database design. Read the relevant documents before changing code or creating new implementation plans.

## Project Positioning

This project is a mobile-first internal collaboration tool for a campus cat association.

The MVP is not a general map product. It is designed to help association members find campus task locations, view cat and supply points, join multi-person tasks, abandon tasks, complete photo check-ins, and keep task/cat records over time.

## Release Status

Version `1.0.0` is the first production release and the baseline for post-launch maintenance.

Treat the current online behavior as the `1.0.0` release baseline. Do not make breaking API, schema, deployment, or user-flow changes on `main` without an explicit release plan and progress entry.

For the `1.0.x` line, prioritize production stability, bug fixes, data safety, deployment rollback ability, and small scoped improvements. Unfinished or postponed MVP ideas should move into `1.1.0+` planning instead of being silently added to patch releases.

The launched `1.0.x` product line should stay focused on:

- Campus map with task, cat, and supply points.
- Member login using student number, password, letter captcha, and JWT.
- Admin-created member accounts; no public registration.
- Multi-person task join, full-capacity display, abandon, completion, and photo check-in.
- Admin map point selection for publishing tasks and adding cat/supply points.
- Cat archive and basic observation data.
- Personal task history and notification center.
- Duty schedule and task assignment support.

Do not add these to V1 unless the user explicitly asks:

- Self-developed map engine.
- Complex Web admin dashboard.
- WebSocket real-time system.
- Redis.
- Public registration.
- Phone, email, OAuth, WeChat, QQ, or other third-party login.
- Password recovery workflow.
- AI cat recognition.
- Complex data dashboard.
- Complex role approval workflow.
- Indoor-grade navigation or custom route planning algorithm.

## Required Reading Order

Before starting any development task, read documents in this order.

1. `docs/校园猫协地图任务系统_项目说明文档.md`
2. `docs/校园猫协地图任务系统_库表设计说明.md`
3. `docs/接口文档/接口设计规范文档.md`
4. `docs/开发进度.md`, focusing on the most recent entries for the modules affected by the task.
5. The module-specific product or interface document for the task.
6. The relevant table design document if the task touches persistence.
7. The relevant non-prototype visual asset if the task touches UI.

For authentication work, also read:

- `docs/接口文档/鉴权模块_接口文档.md`
- `docs/库表文档/鉴权模块_库表设计文档.md`

For map work, also read:

- `docs/模块功能/地图模块_详细功能说明.md`

When more module documents are added under `docs/模块功能`, `docs/接口文档`, or `docs/库表文档`, prefer the latest module-specific document over inferred behavior.

## Technology Stack

Use the stack specified in the project docs unless the user changes it.

- Frontend: `uni-app`, `Vue 3`, `TypeScript`, `Pinia`.
- UI: `uView Plus` or lightweight custom components.
- Map: Amap/Gaode Map SDK.
- Backend: `FastAPI`, `Pydantic`, `SQLAlchemy 2.0`, `Alembic`.
- Database: `PostgreSQL` with `PostGIS`.
- Auth: student number, password, letter captcha, JWT.
- File storage: local storage for V1, with later migration path to OSS/COS/MinIO.
- Notifications: database notification table plus frontend polling for V1.
- Deployment: `Docker Compose`.

Avoid introducing extra infrastructure until the documented MVP needs it.

## Development Workflow

Work module by module. Keep changes small, reviewable, and tied to one product area.

Recommended post-`1.0.0` branch model:

- `main`: production-stable branch. It should match the latest released version or an approved release/hotfix candidate.
- `dev`: integration branch for accepted `1.x` work before the next release branch.
- `release/<version>`: stabilization branch for a planned release, such as `release/1.1.0`.
- `hotfix/<version-or-topic>`: urgent production fix branch created from `main`, such as `hotfix/1.0.1-login-token`.
- `feature/<module-or-task>`: one focused feature or module slice.
- `fix/<bug-or-module>`: one focused bug fix.
- `docs/<topic>`: documentation-only changes.

Recommended module branch examples:

- `feature/auth`
- `feature/map`
- `feature/tasks`
- `feature/cats`
- `feature/profile`
- `feature/admin`
- `feature/notifications`
- `feature/duty-assignment`

### Default AI Git Workflow

Future agents should use this path unless the user explicitly asks for a different branch strategy.

1. Before starting work, run `git status --short --branch`, check the current branch, and notice untracked local files.
2. For normal feature, fix, or documentation work, start from `dev`:

```bash
git switch dev
git pull --ff-only origin dev
git switch -c feature/<module-or-task>
```

If local `dev` is checked out in another worktree, fetch first and create the focused branch from `origin/dev`, or work inside the existing `dev` worktree.

Use `fix/<bug-or-module>` for non-urgent bug fixes and `docs/<topic>` for documentation-only changes.

3. Finish the focused branch, run the relevant verification, update `docs/开发进度.md`, then merge the branch back into `dev`.
4. Do not develop normal feature work directly on `main`. `main` is for released code, release candidates, and urgent production hotfixes.
5. When a planned version is ready, create `release/<version>` from `dev`. Freeze new features there; only allow release bug fixes, version notes, documentation updates, and deployment hardening. After verification, merge `release/<version>` into `main`, create an annotated tag such as `v1.1.0`, push `main` and the tag, then merge the release branch back into `dev`.
6. For an urgent production fix, create `hotfix/<version-or-topic>` from `main`, verify the fix, merge it into `main`, tag the patch release such as `v1.0.1`, push `main` and the tag, then merge or cherry-pick the same fix back into `dev`.
7. Before committing or pushing, stage explicit files only. Do not use `git add .` when untracked local files, private documents, secrets, screenshots, or scratch directories are present.
8. Before pushing, check for information leaks in the staged diff and relevant files. Look for real server IPs, private domains, map keys, Mini Program AppIDs, COS identifiers, access tokens, private keys, passwords, `.env` values, and deployment credentials.
9. Push only the intended branch or tag. Never run `git push --all origin`, and do not push old local `feature/`, `fix/`, or `codex/` branches unless the user explicitly asks.

For every feature branch:

1. Read the required docs.
2. Identify module boundaries and dependencies.
3. Update or create API/schema contracts first when needed.
4. Implement database models and migrations before backend endpoints that depend on them.
5. Implement backend APIs before frontend screens that consume them, unless building a static prototype.
6. Keep frontend types aligned with backend response fields.
7. Add focused tests or verification steps for the changed behavior.
8. Update progress notes before handing off.

Do not mix unrelated module changes in one branch.

## Git Version Management

Use semantic versioning after `1.0.0`:

- `MAJOR.MINOR.PATCH`, for example `1.0.1`, `1.1.0`, `2.0.0`.
- Patch releases such as `1.0.1` are for production bug fixes, security fixes, deployment fixes, and documentation corrections. They should not introduce breaking API or database changes.
- Minor releases such as `1.1.0` are for backward-compatible feature improvements or deferred MVP modules.
- Major releases such as `2.0.0` are reserved for breaking API, data model, or product behavior changes.

Every production release should have an annotated Git tag:

```bash
git switch main
git pull
git tag -a v1.0.0 -m "release: v1.0.0"
git push origin v1.0.0
```

Create the tag on the exact commit that was deployed. If the tag was missed during deployment, add it later only after confirming the deployed commit hash.

Mandatory workflow summary:

1. Normal feature release: branch from `dev`, merge back to `dev`, stabilize on `release/<version>`, merge into `main`, then tag `v<version>`.
2. Production hotfix: branch from `main`, merge the fix into `main`, tag the next patch version, then merge or cherry-pick the same fix back to `dev`.
3. Documentation-only update: use `docs/<topic>` when the change is not tied to code. Release process documentation can go directly through the same review path as code.

For merge strategy, keep release and hotfix history easy to audit. Squash noisy feature branches if needed, but preserve release and hotfix merge commits when they explain what shipped.

Each release progress entry in `docs/开发进度.md` should include:

- Version number and release date.
- Source branch and Git tag.
- Important changes or known exclusions.
- Verification commands and manual checks.
- Deployment notes, rollback notes, and next planned version.

## Commit Rules

Use concise conventional commit messages.

Recommended prefixes:

- `feat:` new feature.
- `fix:` bug fix.
- `docs:` documentation.
- `refactor:` behavior-preserving code restructuring.
- `test:` tests only.
- `chore:` tooling or maintenance.
- `db:` database schema or migration work.
- `release:` release notes, version tagging, or release coordination.

Examples:

```text
feat(auth): add student number login endpoint
db(tasks): add task participants table
feat(map): show task and cat markers
docs(progress): update task module status
release: publish v1.0.0 baseline
```

Before committing:

- Check `git status`.
- Do not revert or overwrite unrelated user changes.
- Include only files related to the current task.
- Run the relevant tests, type checks, linters, or manual verification.
- If verification cannot run, record why in the handoff.

## Module Development Order

Prefer this order unless the user gives a different priority:

1. Project skeleton and shared conventions.
2. Authentication and member account management.
3. Database base models, migrations, and common utilities.
4. Map module.
5. Task module.
6. Cat archive module.
7. Personal center module.
8. Admin module.
9. Notification center.
10. Duty schedule and task assignment.
11. File upload and photo check-in hardening.
12. Cross-module polish and deployment.

This order keeps the authentication, user identity, point data, and task flow stable before building dependent UI.

## Module Start Checklist

Before coding a module, answer these points in the task notes or progress file:

- What module is being changed?
- Which docs were read?
- Which APIs are needed or affected?
- Which tables are needed or affected?
- Which non-image references or assets are relevant?
- Which upstream modules are required?
- What is the smallest useful vertical slice?
- What is explicitly out of scope for this branch?
- How will the change be verified?

## Module Guides

### Authentication

Core scope:

- Captcha generation and validation.
- Student number and password login.
- JWT authentication.
- `token_version` validation.
- First-login password change.
- Admin-created member accounts.
- Admin password reset.
- Admin disable/restore account.

Required docs:

- `docs/接口文档/鉴权模块_接口文档.md`
- `docs/库表文档/鉴权模块_库表设计文档.md`
- `docs/接口文档/接口设计规范文档.md`

Key rules:

- `student_no` is the V1 login identifier.
- Store password hashes only.
- Store captcha hashes only.
- Do not implement refresh tokens for V1.
- When passwords are changed or reset, increment `users.token_version`.
- When `must_change_password` is true, allow only `GET /api/v1/auth/me`, `PATCH /api/v1/auth/password`, and `POST /api/v1/auth/logout`.

### Map Module

Core scope:

- Campus-centered map homepage.
- Task, cat, supply, and emergency task markers.
- Marker filtering.
- Bottom detail card after marker click.
- Navigation through Amap/Gaode capability.
- Admin map point selection.

Required docs:

- `docs/模块功能/地图模块_详细功能说明.md`
- `docs/校园猫协地图任务系统_项目说明文档.md`
- `docs/校园猫协地图任务系统_库表设计说明.md`

Key rules:

- `map_points` stores spatial and display information only.
- Do not put full task, cat health, or supply inventory data into `map_points`.
- Route text, location notes, and onsite photos are part of the system's own business data.
- Limit or de-emphasize areas outside the campus.
- Clicking a marker should first show a bottom detail card instead of immediately navigating to a full detail page.

### Task Module

Core scope:

- Task list and detail.
- Task status.
- Multi-person joining.
- Full-capacity display.
- Participant list.
- Abandon task.
- Complete task with check-in photo and feedback.
- Task activity logs.

Key rules:

- Task process status belongs in `tasks.status`.
- User participation status belongs in `task_participants.status`.
- Do not store "full" as a task status. Compute it with `participant_count >= max_participants`.
- V1 does not require admin completion review.
- V1 completion flow is: member submits check-in, write `task_checkins`, mark task completed, create activity logs and notifications.

### Cat Archive Module

Core scope:

- Cat list.
- Cat detail.
- Cat photos.
- Cat aliases.
- Health status.
- Resident area and related map points.
- Observation records.

Key rules:

- Cat archive is long-term association data, not just a gallery.
- Observation records should help update recent appearance, health signals, and activity area.
- Future conversion from abnormal observation to task should be kept possible, but not overbuilt in V1.

### Personal Center

Core scope:

- Current user profile.
- Edit basic profile.
- Current tasks.
- Historical tasks.
- Check-in records.
- Observation records.
- Basic personal statistics.
- Notification entry.
- Admin entry when role is `admin`.

Key rules:

- Do not create a duplicate `my_tasks` table.
- Personal center data should be queried or aggregated from existing business tables.
- Admin entry belongs in the personal center, not in the bottom tab bar.

### Admin Module

Core scope:

- Admin home.
- Publish task.
- Map point selection.
- Add/edit cat.
- Add/edit supply point.
- Edit or hide map points.
- Member account management.
- Batch import members.
- Reset passwords.
- Disable or restore accounts.
- Task management.

Key rules:

- Admin module is a management layer, not an isolated business domain.
- Admin task publishing may write `map_points`, `tasks`, `task_activity_logs`, `notifications`, and `admin_operation_logs`.
- Prefer hiding map points over hard deletion in V1.
- Complex statistics and review workflows can be reserved for later versions.

### Notification Module

Core scope:

- Notification table records.
- Unread count.
- Notification center.
- Link notification to task or cat details when applicable.
- Frontend polling.

Key rules:

- V1 uses database records plus polling.
- Do not introduce WebSocket or Redis for V1 unless explicitly requested.
- Notifications are user-facing reminders.
- Task activity logs are part of task detail history.
- Keep those two concepts separate.

### Duty Schedule And Task Assignment

Core scope:

- Duty schedules.
- Admin task assignment.
- Assignment acceptance flow.
- Sync accepted assignment into task participants.

Key rules:

- `duty_schedules` and `task_assignments` are MVP tables.
- `task_assignments` records admin assignment intent.
- `task_participants` records actual task participation.
- Free joining and admin assignment are different sources of participation.

### File Upload And Photos

Core scope:

- User avatar.
- Cat photos.
- Task reference photos.
- Task check-in photos.
- Observation photos.
- Supply point photos.
- Route explanation photos.

Key rules:

- V1 can use local file storage.
- Keep a future migration path to OSS/COS/MinIO.
- Frontend should compress images before upload where practical.
- Store file metadata consistently so records can reference uploaded photos.

## API Conventions

Follow `docs/接口文档/接口设计规范文档.md`.

Base path:

```text
/api/v1
```

Use lowercase plural resource names:

```http
GET /api/v1/tasks
GET /api/v1/tasks/{task_id}
POST /api/v1/tasks/{task_id}/join
```

Use `snake_case` for request and response fields:

```json
{
  "student_no": "20252160A1010",
  "must_change_password": true,
  "created_at": "2026-06-19T10:00:00+08:00"
}
```

Use the unified response envelope:

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "trace_id": "018f3c2e9b7e4f1a9a7e6c8d9"
}
```

Authenticated endpoints use:

```http
Authorization: Bearer <access_token>
```

Use action subpaths for action-like operations:

```http
POST /api/v1/tasks/{task_id}/join
POST /api/v1/tasks/{task_id}/abandon
POST /api/v1/tasks/{task_id}/checkins
POST /api/v1/auth/logout
```

## Database And Migration Rules

Use PostgreSQL and PostGIS.

Use SQLAlchemy models and Alembic migrations for schema changes.

General rules:

- Prefer UUID primary keys.
- Use `created_at`, `updated_at`, and `deleted_at` where the table needs lifecycle tracking.
- Use soft deletion or hidden status for user-facing records when accidental deletion is risky.
- Keep spatial point data separate from business details.
- Keep task status separate from participant status.
- Keep notification records persistent in the database.
- Keep admin operations auditable when they affect accounts, tasks, points, or roles.

When changing schema:

1. Check the relevant table design document.
2. Create or update the model.
3. Create an Alembic migration.
4. Verify upgrade and downgrade where practical.
5. Update API schemas if the change affects responses.
6. Update progress notes with the migration name.

## Frontend Rules

The frontend is a uni-app WeChat Mini Program. Mobile is the primary experience, and WeChat Mini Program behavior is the primary target. H5 can be used for local debugging, but it must not drive platform-specific decisions when it conflicts with the Mini Program target.

- Every frontend page must be designed and checked against phone-sized 微信小程序视口 first. Keep onboarding and form pages within the visible 手机 viewport when the flow is intended to fit one screen; use responsive `rpx`, bounded heights, and remove non-essential decorative blocks before allowing layout overflow.
- All frontend pages should use `frontend/素材/加载页素材/背景.jpg` as the shared page background unless the user explicitly asks for a page-specific exception.

Bottom tab pages:

```text
地图
猫咪库
任务
我的
```

Admin entry belongs under `我的`.

Frontend typography and 中文字体 rules:

- All Chinese UI text must use Songti-style fonts.
- Use this font stack for app pages and components: `"Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif`.
- Do not override Chinese UI text with unrelated sans-serif fonts unless the user explicitly asks for a page-specific exception.
- If an SVG or generated asset contains visible Chinese text, set the text font to the same Songti stack where the asset format supports it.

Frontend development workflow:

1. Work from a feature branch such as `feature/frontend-login`, `feature/frontend-map`, or `feature/frontend-tasks`.
2. Do not read or open images under `frontend/页面原型` unless the user explicitly asks.
3. Reproduce page layout, spacing, colors, typography, icons, empty states, and interaction states from module docs, existing implementation, `frontend/页面原型代码` when available, and approved assets.
4. Check `frontend/页面原型代码` when it exists, but do not treat images under `frontend/页面原型` as required reading or visual source of truth.
5. Check `frontend/素材` before adding any icon, image, illustration, marker, empty-state image, or decorative asset.
6. If the needed visual asset is not in `frontend/素材`, use a clear placeholder component or placeholder block with a meaningful label. Do not use a random replacement icon, third-party image, or near-match asset.
7. Keep page implementation scoped to the current page or module. Do not redesign other pages while matching one prototype or reference.
8. Run `npm run type-check` and the relevant uni-app build command before handoff.

Frontend data rules:

- Keep TypeScript types aligned with backend `snake_case` fields.
- Use Pinia for user identity, task state, map filters, and other shared state.
- Handle loading, empty, error, permission-denied, and image-failed states using existing implementation/assets where available.
- Do not invent unrelated visual systems when page references exist.
- Do not substitute missing icons or components with arbitrary online assets or unrelated local assets.
- Prefer existing assets and reference styles over new visual abstractions.
- Map pages should prioritize usable map area and task/cat/supply point interaction.

Prototype and asset folders:

- `frontend/页面原型` is ignored by git and should not be read for images unless the user explicitly asks.
- `frontend/页面原型代码`
- `frontend/素材`

Asset rules:

- `frontend/素材/icon` contains the original icon assets.
- `frontend/素材/svg` contains the original SVG assets.
- Keep new frontend-used assets under `frontend/素材`.
- Do not store frontend page assets in the repository root.
- When an asset is missing, create an obvious placeholder in the UI and record the missing asset in the handoff or progress notes.

## Backend Rules

Backend APIs should follow FastAPI and Pydantic conventions.

General rules:

- Keep route handlers thin.
- Put business logic in services or clearly named helper modules.
- Use Pydantic schemas for request and response validation.
- Keep database access consistent and transaction-aware.
- Use password hashing utilities rather than custom hash logic.
- Avoid storing secrets or credentials in source files.
- Include trace IDs in API responses as specified by the interface docs.

## Progress Synchronization

Every agent should update development progress before ending a development handoff.

Recommended progress file:

```text
docs/开发进度.md
```

If the file does not exist, create it when the first development module starts. Keep it short and factual.

Use this format:

```md
# 开发进度

## 当前总览

- 当前阶段：MVP / 已上线维护（x.y.z）
- 当前线上版本：
- 当前重点模块：
- 当前分支：
- 推荐 Git 标签：
- 最近更新时间：

## 模块状态

| 模块 | 状态 | 分支 | 负责人/Agent | 备注 |
|---|---|---|---|---|
| 鉴权模块 | 未开始 |  |  |  |
| 地图模块 | 未开始 |  |  |  |
| 任务模块 | 未开始 |  |  |  |
| 猫咪库模块 | 未开始 |  |  |  |
| 个人中心模块 | 未开始 |  |  |  |
| 管理员模块 | 未开始 |  |  |  |
| 通知模块 | 未开始 |  |  |  |
| 排班与任务指派 | 未开始 |  |  |  |

## 最近进展

### YYYY-MM-DD

- 分支：
- 完成：
- 修改文件：
- 验证：
- 阻塞：
- 下一步：
```

Suggested statuses:

- `未开始`
- `设计中`
- `开发中`
- `待联调`
- `待测试`
- `已完成`
- `已上线维护`
- `1.x 规划复核`
- `阻塞`

Progress updates should include:

- Branch name.
- Completed work.
- Important files changed.
- API or table changes.
- Migration names.
- Verification commands and results.
- Known blockers.
- Next recommended task.
- Release version and Git tag when the work changes or documents a production release.

## Handoff Format

When ending a coding session, summarize in this order:

1. What changed.
2. Files touched.
3. Verification run.
4. What was not verified.
5. Known risks or blockers.
6. Next step.

Keep handoffs short enough for another agent to continue quickly.

## Definition Of Done

A module slice is done only when:

- Relevant docs were read.
- Scope matches the MVP boundary.
- API contracts follow `/api/v1`, `snake_case`, and unified response rules.
- Database changes have migrations when needed.
- Frontend screens handle loading, empty, error, and permission states where relevant.
- Auth and role checks are enforced where relevant.
- Task/map/cat/admin behavior respects the documented module boundaries.
- Tests, type checks, or manual verification were run.
- Development progress was updated.
- Remaining risks are documented.

Do not mark a module as complete just because code was written.

## Quick Start For A New Agent

1. Read this file.
2. Read `docs/校园猫协地图任务系统_项目说明文档.md`.
3. Read `docs/校园猫协地图任务系统_库表设计说明.md`.
4. Read `docs/接口文档/接口设计规范文档.md`.
5. Read `docs/开发进度.md`, especially the recent entries for the module you will change.
6. Check current files and branch state.
7. Select one module slice.
8. Read that module's docs and non-image references.
9. Implement the smallest useful vertical slice.
10. Verify and update progress before handoff.
