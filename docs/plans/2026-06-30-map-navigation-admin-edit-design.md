# Map Navigation And Admin Point Editing Design

## Scope

This slice improves the map module only:

- Keep walking route planning inside the app map page.
- Simulate realtime navigation by moving the current-location marker along the planned route.
- Search Amap built-in POIs in addition to internal `map_points`.
- Let admins edit existing map points from the point summary card.
- Let admins long-press a marker for two seconds, enter edit mode, drag the point visually, and save the new coordinates.

Out of scope:

- Indoor navigation.
- Custom route-planning algorithms.
- New business records for cats, supplies, or tasks.
- Navigation voice guidance.
- Multi-admin edit locks.

## Technical Feasibility

The existing mini program map page already uses the native `map` component with marker and polyline binding. This supports in-page route drawing. The app should not call `uni.openLocation` for this flow.

Amap Web Service can provide walking route geometry and POI search results. The backend should proxy those calls so the mini program does not expose service details or depend on direct external-domain calls. If no Amap service key is configured or the call fails, the app should fall back gracefully: internal search still works, and route planning can show a straight-line route.

Marker drag support is not consistently exposed by the mini program native map API. The frontend will implement a compatible drag-edit interaction by entering an edit mode on long press and updating the selected point with a draggable overlay/center-based fallback. The backend will expose a clean coordinate update endpoint regardless of the frontend gesture implementation.

## Backend Design

Extend the map module service with:

- `GET /api/v1/map/search?include_external=true` to merge internal `map_points` and external Amap POIs.
- `GET /api/v1/map/points/{point_id}/navigation?from_lng=&from_lat=&mode=walking` to return walking route geometry.
- Admin point APIs under `/api/v1/admin/map`:
  - `GET /points/{point_id}`
  - `PATCH /points/{point_id}`
  - `PATCH /points/{point_id}/location`

The route response will include:

- `route.points`: `{ lng, lat }[]`
- `route.distance_meters`
- `route.duration_seconds`
- `route.steps`
- `route.provider`
- `route.fallback`

The POI search response will keep the current search item shape and mark external results with `result_type = "external_poi"` and `map_point_id = null`.

Admin edits update only `map_points` spatial/display fields. They do not modify related `tasks`, `cats`, or `supply_points`.

## Frontend Design

Map page changes:

- Render navigation route from backend `route.points` in `polyline`.
- Add a navigation status panel with distance, duration, route text, and controls for starting/stopping simulated navigation.
- Add a custom current-location marker so simulated movement is visible in the map.
- Pass `include_external=true` to search and map external POI results into temporary markers.
- For admins, show `编辑点位` in selected point card.
- Admin edit mode:
  - Long-press a marker for two seconds to enter edit mode.
  - Show edit controls and current coordinates.
  - Allow dragging the visual point when platform support is available; otherwise let admins move the map center and save that center as the new point location.
  - Save via `PATCH /api/v1/admin/map/points/{point_id}/location`.

Admin edit form:

- A lightweight page/modal edits map-point fields: name, subtitle, description, location name/detail, route instruction, landmark hint, entrance hint, visibility, status.
- It uses existing Songti typography and shared background.

## Verification

Backend:

- Add tests for merged internal/external search, route fallback/geometry shape, and admin point edit/location authorization.
- Run targeted map tests, then full backend tests if practical.

Frontend:

- Add API tests for new map/admin-map client functions.
- Add page tests for in-page navigation route rendering, simulated navigation state, external POI marker mapping, and admin edit action visibility.
- Run targeted frontend tests, type-check, and `build:mp-weixin`.

