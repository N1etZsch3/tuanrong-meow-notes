# 阶段② 列表分页 + 前端懒加载 + 任务归档语义（设计）

- 日期：2026-07-17
- 分支：`feat/list-pagination`（自 `feat/profile-notes-ia` tip `7e2b96c`）
- 来源需求：`test/bug清单/下一步优化方案.md` 二、1/2
- 已对齐决策：每页 10 条＝前端显式传 `page_size=10`，后端默认保持 20（不破契约）；归档+取消默认隐藏，改在前端查询层；「已归档/已取消」筛选改发父任务 `status=`，修 `execution_display_status=archived` 恒空 bug；列表懒加载优先用微信/uni 原生 `scroll-view @scrolltolower`。

## 目标

1. 所有列表页真实后端分页 + 前端 `scroll-view` 懒加载，每页 10 条。
2. 任务列表：默认隐藏「已归档」「已取消」父任务；仅显式选中对应筛选才展示。父任务归档整条不展示；父 active 时子任务终态照常展示（现状即满足）。

## 范围与现状差距

| 列表页 | 后端分页 | 前端懒加载 | 本阶段动作 |
|---|---|---|---|
| 任务 tasks/list | ✅ SQL 真分页 | ❌ 一次拉 50 | 前端加 scrolltolower + size=10 + 归档语义 + 缓存改造 |
| 药品 medicines | ✅ SQL | ❌ 一次拉 50 | 前端加 scrolltolower + size=10 |
| 个人记录 profile/records | ✅ SQL(checkins) | ❌ 仅第一页 | 前端加 scrolltolower + size=10 |
| 猫咪库 cats | ⚠️ 假分页(Python切片) | ✅ 已懒加载 | 后端下推 SQL 真分页；前端 size 20→10 |
| 成员 admin/users | ⚠️ total 全量 len() | ✅ 已懒加载 | 后端 total 改 SQL count；前端 size 20→10 |
| 物资 supplies | ❌ 借 /map/points 无分页 | ❌ | 新增后端 `GET /supply-points` 分页列表端点；前端改用 + 懒加载 |
| 校园地标 landmarks | ❌ 借 /map/points 无分页 | ❌ | 新增后端 `GET /landmarks` 分页列表端点；前端改用 + 懒加载 |
| 喵息 messages | ❌ 后端不存在 | ❌ | **不在本阶段**——通知后端属阶段④，届时一并真分页 |

## 后端设计

统一沿用既有分页契约：请求 `page`(≥1,默认20) + `page_size`(1..100)；响应 `{items,page,page_size,total,has_more}`；`api_success` 信封。新端点保持一致，不发明新形态。

1. **cats 真分页**（`cats/service.py`）：把「取全量 `.all()` → Python 切片」改为 SQL `COUNT` + `ORDER BY ... LIMIT/OFFSET`。难点：`personality_tag` JSON 数组过滤、`health_priority`/`not_neutered_first` 两种排序目前在 Python。方案：能下推 SQL 的下推（JSON 包含查询、CASE 排序）；确认可行性后实现，排序 tie-break 追加 `id` 保证跨页稳定。保持响应字段不变。
2. **admin users total**（`auth/service.py:611`）：`total = len(db.scalars(stmt).all())` 改为 `db.scalar(select(func.count()).select_from(subquery))`，页行仍 OFFSET/LIMIT，避免全量加载。
3. **supplies 列表端点**（新增 `GET /api/v1/supply-points`）：分页返回物资点列表项（复用 map point → 列表项的既有映射字段，保证前端 `associated_poi` 等展示字段不丢），支持 `keyword` 服务端过滤、`page/page_size`。放 `supplies/` 模块，router + service + schema + 测试。
4. **landmarks 列表端点**（新增 `GET /api/v1/landmarks`）：同上，分页 + keyword。

migration：本阶段**不改库表**（仅查询/端点）。

## 前端设计

- 新增共享分页懒加载 composable `composables/use-paged-list.ts`（微信原生 scroll-view 方案的封装：reset/loadMore/hasMore/loading/error + 去重），供各列表页复用（规范：按功能拆文件、避免每页复制）。参考现有 cats/index.vue 已验证的 scrolltolower + 去重 + footer 模式。
- 各列表页：`<scroll-view scroll-y lower-threshold="140" @scrolltolower="loadMore">` + footer（加载中/已全部）+ 每页 10 条。
- 任务列表归档语义（`tasks/list.vue` + `task-page.ts`）：
  - 默认查询不再无条件带 `archived,cancelled`。默认 `status` 只含 `in_progress,completed`（或不传 status 用后端默认）。
  - 状态筛选项拆两类：`未开始/进行中/已完成` 走子任务 `execution_display_status`（保持现状）；`已归档/已取消` 改发父任务 `status=archived` / `status=cancelled`（修 execution_display_status=archived 恒空 bug）。
  - 「全部」= 默认（in_progress+completed），不含归档/取消。
- 任务列表缓存 `task-list-cache.ts`：分页后按 query 缓存整包不再适用；改为只缓存第一页做秒开，翻页不进缓存（或按 query+page）。
- 各页 page_size 统一 10。

## 测试影响

- 后端：新增 cats 分页跨页不重不漏 + total 正确测试；admin users total SQL count 测试（现有 test_admin_users_api 部门筛选排序保留）；新增 supplies/landmarks 列表端点测试（分页 + keyword + 鉴权）。
- 前端：tasks-page.test.ts 归档 query 语义断言更新（DEFAULT_TASK_STATUS_QUERY 变化、已归档发 status=archived）；各列表页 scrolltolower/size=10 的 ?raw 断言；use-paged-list 单测。

## 验证

- 后端 `pytest -q`（基线 234，须全绿 + 新增）
- 前端 `npm run test -- --run` / `type-check` / `build:mp-weixin`
- H5：任务列表默认不含归档/取消、选「已归档」能看到归档、翻页懒加载；物资/地标列表懒加载。

## 风险

- cats 的 JSON 标签过滤/特殊排序下推 SQL 若不可行，退化为「SQL 分页 + 该维度近似」，需 log 说明。
- supplies/landmarks 新端点必须保住前端依赖的 `associated_poi`/坐标等字段，否则详情/导航文案回归。
- 归档语义改动别影响管理端 `/admin/tasks`（默认 status=None 看全部，含归档，管理端保持）。
- 不动 main / 发布 / 生产。
