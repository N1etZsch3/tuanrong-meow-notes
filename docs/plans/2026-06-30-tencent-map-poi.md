# 腾讯地图 POI 与任务点关联实施任务文档

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将现有地图模块从高德外部 POI/路线能力扩展为腾讯位置服务能力，并补齐公共 POI 点击、搜索、附近 POI 推荐、任务点 POI 关联保存、任务详情展示与路线预览。

**Architecture:** 后端统一封装腾讯位置服务请求，前端只消费 `/api/v1/map` 和 `/api/v1/admin/tasks` 既有接口。数据库在 `map_points` 上扩展腾讯 POI 关联字段，保留任务真实坐标为导航和路线规划目标。

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL/PostGIS, uni-app, Vue 3, TypeScript, 微信小程序 map 组件。

---

## 模块启动检查

- 修改模块：地图模块、暑假喂食任务模块、管理员选点页、任务详情页。
- 已读文档：
  - `AGENTS.md`
  - `docs/Prompt/地图模块.md`
  - `docs/校园猫协地图任务系统_项目说明文档.md`
  - `docs/校园猫协地图任务系统_库表设计说明.md`
  - `docs/接口文档/接口设计规范文档.md`
  - `docs/模块功能/地图模块_详细功能说明.md`
  - `docs/接口文档/地图模块_接口设计文档.md`
  - `docs/库表文档/地图模块_库表设计说明.md`
  - `docs/接口文档/暑假喂食任务模块_接口文档.md`
  - `docs/库表文档/暑假喂食任务模块_库表设计文档.md`
- 影响 API：
  - `GET /api/v1/map/init`
  - `GET /api/v1/map/search`
  - `GET /api/v1/map/poi/resolve`
  - `GET /api/v1/map/poi/nearby`
  - `GET /api/v1/map/route/walking`
  - `GET /api/v1/map/points/{point_id}/summary`
  - `GET /api/v1/map/points/{point_id}/navigation`
  - `POST /api/v1/admin/tasks/summer-feeding`
  - `PATCH /api/v1/admin/tasks/{task_id}`
- 影响表：
  - `campuses.map_provider`
  - `map_points.tencent_poi_id`
  - `map_points.tencent_poi_name`
  - `map_points.tencent_poi_address`
  - `map_points.tencent_poi_category`
  - `map_points.tencent_poi_lng`
  - `map_points.tencent_poi_lat`
  - `map_points.tencent_poi_distance_meters`
  - `map_points.tencent_poi_match_method`
- 相关页面/原型：
  - `frontend/页面原型/地图模块/首页-常规状态.png`
  - `frontend/页面原型/地图模块/下拉菜单.png`
  - `frontend/页面原型/地图模块/地图选点.png`
  - `frontend/页面原型/任务模块/发布任务-地图选点.png`
  - `frontend/页面原型/任务模块/任务详情.png`
- 上游依赖：鉴权登录态、地图基础表、暑假喂食任务发布/详情接口、文件上传。
- 最小可用切片：后端腾讯 POI/路线接口 + 数据字段 + 管理员选点推荐 + 任务发布保存关联 POI + 地图搜索/点击详情 + 任务详情关联 POI 展示和导航。
- 本分支不做：
  - WebSocket 或 Redis。
  - 自研地图引擎。
  - 室内级导航或自研路线算法。
  - 复杂 Web 管理后台。
  - AI 猫识别。
- 验证方式：
  - 后端先写失败测试，再实现，通过 `py -3.11 -m pytest tests/test_map_api.py tests/test_tasks_api.py -q`。
  - 前端先写失败测试，再实现，通过 `npm run test -- --run tests/api/map.test.ts tests/api/tasks.test.ts tests/pages/map-page.test.ts tests/pages/tasks-page.test.ts`。
  - 最终运行后端全量测试、ruff、前端全量测试、type-check、微信小程序构建。

## 任务清单

### Task 1: 后端腾讯位置服务封装

- 新增腾讯配置：`CATMAP_TENCENT_MAP_KEY`、请求超时。
- 保留旧高德配置作为兼容，但地图初始化优先返回 `tencent_config`。
- 封装腾讯地点搜索、POI 匹配、附近搜索、步行路线解析。
- 外部失败时保留直线兜底路线。

状态：已完成。

### Task 2: 地图点位腾讯 POI 字段和迁移

- 扩展 `map_points` 模型和 Alembic 迁移。
- 任务点真实坐标继续使用 `lng/lat/geom`。
- 腾讯 POI 字段只用于辅助展示、搜索和关联说明。

状态：已完成。

### Task 3: 地图 API 扩展

- `GET /map/search` 的外部 POI 改为腾讯结果。
- 新增公共 POI 二次匹配接口。
- 新增附近 POI 推荐接口。
- 新增临时坐标步行路线接口，供公共 POI 或任务详情无 map_point_id 场景使用。
- summary/navigation 返回腾讯 POI 信息。

状态：已完成。

### Task 4: 任务发布与编辑保存关联 POI

- `TaskMapPointRequest` 增加腾讯 POI 字段。
- 创建/编辑任务点时保存关联 POI 信息。
- 任务详情响应展示关联 POI 名称、地址、分类、距离、匹配方式。

状态：已完成。

### Task 5: 地图页公共 POI 点击与搜索体验

- 微信小程序 map 接入 `@poitap`，从名称和坐标调用后端匹配。
- 搜索结果点击后移动地图、高亮临时 POI、展示详情卡片。
- 公共 POI 导航仍以选中的 POI 坐标为临时目标，任务点导航仍以任务点真实坐标为准。

状态：已完成。

### Task 6: 管理员选点附近 POI 推荐

- 地图选点后调用附近 POI 推荐接口。
- 展示“检测到附近地点”交互。
- 支持关联、换一个、不关联。
- 喂食点名称和位置补充说明默认空，提交时强制填写。

状态：已完成。

### Task 7: 文档与进度同步

- 更新地图接口文档、地图库表文档、任务接口/库表文档中的腾讯字段。
- 更新 `docs/开发进度.md`。

状态：已完成。
