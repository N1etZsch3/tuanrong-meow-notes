# AGENTS.md

This file is the development playbook for agents working on the Campus Cat Association Map Task System.

The project documents are written in Chinese and are the source of truth for product scope, module behavior, API rules, and database design. Read the relevant documents before changing code or creating new implementation plans.

## Project Positioning

This project is a mobile-first internal collaboration tool for a campus cat association.

The MVP is not a general map product. It is designed to help association members find campus task locations, view cat and supply points, join multi-person tasks, abandon tasks, complete photo check-ins, and keep task/cat records over time.

The first version should stay focused on:

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
4. The module-specific product or interface document for the task.
5. The relevant table design document if the task touches persistence.
6. The page prototype or visual asset if the task touches UI.

For authentication work, also read:

- `docs/接口文档/鉴权模块_接口文档.md`
- `docs/库表文档/鉴权模块_库表设计文档.md`

For map work, also read:

- `docs/模块功能/地图模块_详细功能说明.md`
- `页面原型/首页.png`
- `页面原型/地图选点.png`

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

Recommended branch model:

- `main`: stable branch.
- `dev`: integration branch for completed module work.
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

Examples:

```text
feat(auth): add student number login endpoint
db(tasks): add task participants table
feat(map): show task and cat markers
docs(progress): update task module status
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
- Which page prototypes or assets are relevant?
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

Mobile is the primary experience.

Bottom tab pages:

```text
地图
猫咪库
任务
我的
```

Admin entry belongs under `我的`.

Frontend data rules:

- Keep TypeScript types aligned with backend `snake_case` fields.
- Use Pinia for user identity, task state, map filters, and other shared state.
- Handle loading, empty, error, permission-denied, and image-failed states using existing prototype/assets where available.
- Do not invent unrelated visual systems when page prototypes already exist.
- Map pages should prioritize usable map area and task/cat/supply point interaction.

Prototype and asset folders:

- `页面原型`
- `svg`
- `icon`
- `素材`

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

- 当前阶段：MVP
- 当前重点模块：
- 当前分支：
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
5. Check `docs/开发进度.md` if it exists.
6. Check current files and branch state.
7. Select one module slice.
8. Read that module's docs and prototypes.
9. Implement the smallest useful vertical slice.
10. Verify and update progress before handoff.
