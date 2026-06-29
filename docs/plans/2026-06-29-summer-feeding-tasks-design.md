# Summer Feeding Tasks Design

## Goal

Build the first usable summer feeding task slice: admins can publish a feeding task with title, description, dates, location, materials, route notes, and task point photos; members can see it in task pages and the new task point appears on the map.

## Scope

- Only `task_type = feeding` is supported.
- Publishing writes `map_points`, `tasks`, `task_execution_dates`, `task_photos`, and `task_activity_logs`.
- The parent task stays `in_progress` while individual execution dates are completed independently.
- Materials default to `猫粮、水`.
- Route instruction is supported and may be empty.
- Images are referenced from the existing file upload module. The task API stores uploaded file references; raw file upload stays outside task endpoints.
- Map display is intentionally simple for this slice: creating a public active task map point makes it visible through existing `/api/v1/map/points` and bottom content.

## Out Of Scope

- Join, abandon, participant capacity, assignment, duty schedule, and completion review.
- Dragging map points, navigation refinement, and post-publish point relocation.
- Complex task inventory or stock deduction.
- WebSocket or Redis notification flow.
- The `frontend/页面原型/任务模块后期` pages.

## Backend Design

Add a task module with SQLAlchemy models, schemas, services, and routers.

The minimal tables are:

- `tasks`: feeding task parent record, linked to `map_points`.
- `task_execution_dates`: one row per selected feeding date.
- `task_photos`: carousel and cover images for task detail.
- `task_checkins`: completion record for one execution date.
- `task_checkin_photos`: optional completion photos, kept for compatibility.
- `task_activity_logs`: timeline entries rendered by the frontend.

The admin publish endpoint is `POST /api/v1/admin/tasks/summer-feeding`. It validates admin role, title, point, dates, materials, photos, and route fields, then commits all records in one transaction. New map points use `point_type = task`, `point_scope = long_term`, `icon_key = task_feeding`, `visibility = public`, and `status = active`.

The member endpoints are:

- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `POST /api/v1/tasks/{task_id}/checkins`

The admin endpoints included in this slice are:

- `GET /api/v1/admin/tasks`
- `POST /api/v1/admin/tasks/summer-feeding`
- `PATCH /api/v1/admin/tasks/{task_id}`
- `PATCH /api/v1/admin/tasks/{task_id}/status`

## Frontend Design

Add task API wrappers under `frontend/src/api/tasks.ts`.

Replace the task tab placeholder with a summer feeding list using backend data, with loading, empty, error, and image-failed states. Add a task detail page matching the prototype: title area, image carousel or placeholder, feeding point name, date/address cards, description/materials/route content, timeline, and bottom navigation/check-in actions.

Add admin publish pages:

- `/pages/admin/tasks/create`
- `/pages/admin/tasks/location`

The publish form has six submission groups:

1. 任务标题
2. 任务说明
3. 时间
4. 位置
5. 物资
6. 任务点图片

Route instruction is shown in the location group as an optional route note field. The location page uses a native mini program map with a selectable marker and returns the chosen point to the create page.

The admin entry page gets a "发布喂食任务" action while keeping existing account management.

## Map Integration

The existing map page already loads public task markers from `/api/v1/map/points` after a marker layer is selected. This slice adds the backend data needed for newly published feeding task points to appear there.

The map summary link should resolve task map points to the task detail page when the point is linked to a task. If the map endpoint does not yet know the task ID, the detail page can also resolve by `map_point_id` as a fallback.

## UI Rules

- Use the shared loading page background.
- Keep Chinese UI in the Songti font stack.
- Match the map title height variables used by the map page.
- Use existing SVG assets only. Feeding task markers use the provided completed/failed task SVG variants after recoloring assets as required.
- Missing image assets render as clear placeholders, not random substitutes.

## Verification

- Backend pytest for task API and map marker visibility.
- Alembic migration upgrade validation.
- Frontend API and page tests.
- `npm run type-check`.
- `npm run build:mp-weixin`.
- Progress update in `docs/开发进度.md`.
