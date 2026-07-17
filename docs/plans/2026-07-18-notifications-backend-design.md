# 阶段④ 喵息通知后端 + WebSocket + 通知开关（设计）

- 日期：2026-07-18
- 分支：`feat/notifications-backend`（自 `feat/member-departments` tip `be94b93`）
- 来源需求：优化方案一、1（消息通知收进设置=通知开关设置页）+ 二、1（喵息列表真分页）
- 已对齐决策：REST + WebSocket 一起做；置顶/标签/完成保留本地个人偏好不进通知表；每页 10 条懒加载；阶段①设置页的「消息通知」占位在本阶段变为真开关页。

## 契约来源（既有，遵守不发明）

- REST：《用户与个人中心模块_接口文档》§8——`GET /me/notifications`（is_read/notification_type/page/page_size）、`GET /me/notifications/unread-count`、`PATCH /me/notifications/{id}/read`（63007 不存在 / 63008 非本人）、`PATCH /me/notifications/read-all`（updated_count）。
- 表：《用户与个人中心模块_库表设计文档》notifications——id/user_id/notification_type/title/content/related_type/related_id/is_read/read_at/created_at + (user_id,is_read)、(user_id,created_at) 索引。
- WS：前端 `services/notification-socket.ts` 已约定——端点 `wss(API base)/ws/notifications?token=`（即 `/api/v1/ws/notifications`），信封 `{"type":"notification.new","data":NotificationItemDto}`，另有 ping/pong；live 驱动已实现。
- DTO/类型：前端 `messages-page.ts` NotificationType 15 值 + 7 频道（task/feeding/medicine/supply/member/cat/announcement）+ TYPE_TO_CHANNEL 映射。

## 后端设计（新模块 `app/modules/notifications`）

1. **models.py**：
   - `Notification`：按表设计文档；notification_type String(64) 无 DB enum（项目惯例）；两个复合索引。
   - `UserNotificationSetting`：user_id 唯一 FK + 7 个频道开关布尔列（task/feeding/medicine/supply/member/cat/announcement，默认全开）+ updated_at。频道分组镜像前端 NOTIFICATION_CHANNELS，避免 15 类型开关过碎。
2. **迁移** `20260718_0018_create_notifications`：两表 + 索引；downgrade drop。顺带补 `alembic/env.py` 漏掉的 `supplies` models import（勘察发现的存量隐患）与新 notifications import。
3. **constants.py**：TYPE→CHANNEL 映射（镜像前端），频道集合。
4. **service.py**：`list_notifications`（SQL 分页 + is_read/type 筛选，倒序）、`unread_count`、`mark_read`（63007/63008）、`mark_all_read`、`get_settings`/`update_settings`（惰性建默认行）、`notification_payload`。
5. **dispatch.py**：`create_notifications(db, recipients, type, title, content, related_type, related_id)`——按接收者的频道开关过滤、批量插入（调用方负责 commit）、commit 后经 hub 线程安全推送 WS 信封。
6. **hub.py**：进程内连接注册表 `{user_id: set[WebSocket]}`；`register/unregister`（async）；`notify_threadsafe(user_ids, payload)` 供同步业务线程调用（`asyncio.run_coroutine_threadsafe` 到启动时捕获的事件循环）；单 uvicorn 进程部署（现状）足够，多进程扩展留待将来（进度文档记录该边界）。
7. **WS 端点** `app/api/v1/ws_notifications.py`：`/ws/notifications`（挂在 api_router → 全路径 `/api/v1/ws/notifications`）；`?token=` 用与 `get_current_user` 相同校验（存在/未删/active/token_version），失败 close(4401)；收 `{"type":"ping"}` 回 `{"type":"pong"}`。
8. **生成钩子（本阶段最小集）**：管理员发布暑期喂食任务成功后 → 通知除发布者外全部 active 用户；priority=urgent → `emergency_task`，否则 `new_task`；related=task。其余类型的生成接线留后续（基础设施已通用）。
9. **dashboard**：`me/service.py` `todo.unread_notifications` 从硬编码 0 接到真实计数。

## 前端设计

1. `api/notifications.ts` + routes.ts：列表/未读数/单条已读/全部已读/`GET|PATCH /me/notification-settings`（新契约，文档同步补）。
2. **喵息页切真数据**：初始 `getNotifications(page=1,page_size=10)`；scroll-view `@scrolltolower` 追加（复用手势 defer 机制：追加时走 `shouldDeferMessageListUpdate` 既有互斥）；下拉刷新 reset；WS 切 `mode:"live"`；点卡片/滑动「标为已读」调 REST（乐观更新）；「全部已读」调 REST；未读 tab 长按清空 → read-all。置顶/标签/完成仍走本地 storage（决策⑤）。`mock-notifications.ts` 删除（其文件头即约定"后端落地后删除"）；详情页回退改为仅读快照。
3. **通知开关设置页** `pages/profile/notifications.vue`：7 频道开关（uni 原生 `switch`），读改 settings API；设置页「消息通知」行从占位 toast 改 `navigateTo` 此页（阶段①预留的单点替换）。
4. AppTabBar 喵息未读红点：现状读本地（message-unread-indicator）；本阶段在喵息页加载后把服务端未读数写入既有指示器存储，逻辑不变。
5. 类型：NotificationItemDto 已存在于 messages-page.ts，api 层复用。

## 测试

- 后端：REST 四端点契约（分页/筛选/63007/63008/read-all 计数）、设置默认全开+更新、dispatch 按开关过滤+批量插入、任务发布钩子（member 收到 / publisher 不收 / urgent→emergency_task / 关闭 task 频道者不收）、WS 鉴权（坏 token 拒绝、好 token ping/pong）、dashboard 未读数。
- 前端：api 层单测；喵息页 ?raw 断言（getNotifications/live 模式/scrolltolower/mock 文件移除）；通知开关页测试；messages-page 纯函数测试保留。

## 验证

- 后端 pytest + ruff + alembic 单 head；前端 test/type-check/build。
- H5：生产后端无本阶段接口——喵息页需优雅处理列表接口 404/失败（错误态），开关页同理；真实链路由后端集成测试覆盖；本地起后端联调 WS 不可行（无本地 PostGIS），WS 由 TestClient websocket 测试覆盖。

## 风险与边界

- WS hub 为进程内实现：当前单 uvicorn 进程部署成立；未来多 worker 需换 Redis pub/sub（写入进度文档）。
- 通知生成仅接任务发布钩子，其余类型后续接线。
- 全员广播在成员量大时的写入量：现阶段协会规模（<100 人）无碍；后续可改按部门/指派人。
- 不合 dev / 不推远端 / 不部署。
