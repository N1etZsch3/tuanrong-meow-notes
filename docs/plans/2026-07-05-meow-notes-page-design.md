# 喵记页重构设计

## 背景

1.1.0 需要把原底部「任务」入口重构为「喵记」，作为记录与管理入口集合。当前任务列表页已经上线维护，不能破坏既有任务列表、详情、投喂与缓存逻辑。

本次视觉参考 `test/组件/页面原型.png` 和 `test/组件/书架书本.html`。根目录 `test/` 目录已按项目整理规则不再纳入 Git，本次只复用其书架和书本结构，不把测试目录文件加入版本控制。

## 范围

- 底部第三个 Tab 文案从「任务」改为「喵记」，路由仍指向 `pages/tasks/index`。
- `pages/tasks/index` 改为喵记书架入口页。
- 原任务列表页保留业务逻辑，迁移到新的 `pages/tasks/list`，喵记第一本书跳转到该列表。
- 新增物资列表页 `pages/supplies/index`，复用任务列表卡片视觉，只保留搜索栏。
- 新增校园地标列表页 `pages/landmarks/index`，复用任务列表卡片视觉，只保留搜索栏。
- 药品只提供入口，点击提示暂未开放，不新增药品列表页或药品业务接口。

## 数据来源

- 任务列表继续使用现有 `GET /api/v1/tasks`。
- 物资列表使用现有地图点接口 `GET /api/v1/map/points?point_types=supply`。
- 校园地标列表使用现有地图点接口 `GET /api/v1/map/points?point_types=landmark`。
- 物资卡片点击进入 `/pages/supplies/detail?supply_point_id=<business_id>`。
- 地标卡片点击进入 `/pages/landmarks/detail?landmark_id=<business_id>`。

本次不新增后端接口、数据库表或 Alembic 迁移。

## 页面设计

喵记页使用共享背景 `frontend/素材/加载页素材/背景.jpg`、宋体字体栈和现有自定义底部导航。书架组件抽取自测试参考 HTML 的结构和 CSS 思路，转写为 uni-app `view`/`button`/`text` 可用样式。

书本顺序：

1. 任务
2. 物资
3. 校园地标
4. 药品

四本书都是入口。任务、物资、校园地标导航到对应列表；药品弹出建设中提示。页面右上角搜索和更多按钮作为视觉入口保留，其中搜索按钮进入任务列表，更多按钮提示暂未开放，避免加入未完成业务。

## 列表设计

物资和地标列表复用任务列表的页面结构、搜索框、卡片比例、封面占位和空/错/加载态。与任务列表不同：

- 不展示筛选栏。
- 卡片只展示封面图、标题、附近地标名称。
- 搜索通过 `keyword` 调用地图搜索接口，非搜索状态通过地图点列表接口加载全部对应类型。
- 列表卡片点击直接进入详情页。

附近地标名称优先级：

1. `extra.associated_poi.name`
2. `extra.location_detail`
3. `subtitle`
4. `area_name`
5. `暂无附近地标`

## 验证

- 前端测试覆盖：Tab 文案、喵记书架入口、原任务列表迁移、物资/地标列表注册和列表行为。
- 运行 `npm run type-check`。
- 运行 `npm run build:mp-weixin`。
- 更新 `docs/开发进度.md`，记录分支、范围、验证和未做事项。
