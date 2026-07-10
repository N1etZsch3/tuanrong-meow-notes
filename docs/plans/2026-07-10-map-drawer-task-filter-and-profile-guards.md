# 地图抽屉、任务筛选与资料保护实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复地图抽屉和任务筛选体验，更新文案与任务详情，保护未保存资料，并让微信绑定确认仅出现在首次绑定时。

**Architecture:** 地图任务筛选使用一次 `/map/points` 响应作为本地数据源，抽屉标题仅改变本地状态。密码登录由后端精确区分“需要确认首次绑定”和“已绑定微信不匹配”，前端据此决定是否显示确认框。

**Tech Stack:** uni-app、Vue 3、TypeScript、Vitest、FastAPI、SQLAlchemy、pytest。

---

### Task 1: 任务筛选纯函数与回归测试

**Files:**
- Modify: `frontend/src/pages/index/map-page.ts`
- Test: `frontend/tests/pages/map-page.test.ts`

1. 先为“任务”聚合选项、全部/已完成/未完成的单选状态，以及按 `status_key` 过滤 Marker 写失败断言。
2. 运行 `npm run test -- --run tests/pages/map-page.test.ts`，确认新增断言因缺少实现失败。
3. 最小化实现聚合 option、任务请求 query 和共享 Marker 过滤函数；不增加地图 API 参数。
4. 重跑同一测试，确认通过。

### Task 2: 地图任务缓存、单选标题和布局回归

**Files:**
- Modify: `frontend/src/pages/index/index.vue`
- Modify: `frontend/src/pages/index/drawer.wxs`
- Test: `frontend/tests/pages/map-page.test.ts`

1. 先写失败测试，要求选择“任务”只由 `activeFilter` 请求一次，标题状态切换不调用刷新函数，原生 Marker、列表和计数读取同一过滤结果。
2. 先写失败测试，要求标题点击使用单选 action sheet、任务下拉无说明文字、抽屉最大高度按 `windowHeight` 比例计算且底部保留 Tab 空间。
3. 实现任务默认“未完成”、标题单选、共享计算属性与抽屉比例布局。
4. 运行地图测试，确认通过。

### Task 3: 地图和导航文案、任务详情照片展示

**Files:**
- Modify: `frontend/src/pages/index/index.vue`
- Modify: `frontend/src/components/app-tab-bar.ts`
- Modify: `frontend/src/pages.json`
- Modify: `frontend/src/pages/tasks/detail.vue`
- Test: `frontend/tests/pages/map-page.test.ts`
- Test: `frontend/tests/pages/tasks-page.test.ts`
- Test: `frontend/tests/components/app-tab-bar.test.ts`

1. 先增加文案与“任务详情没有独立完成照片区、但记录详情仍有照片”的失败断言。
2. 将页面和 Tab 文字改为“喵图 / 喵的”，删除独立完成照片卡片及仅供它使用的状态。
3. 运行这三个前端测试文件，确认通过。

### Task 4: 个人资料未保存退出确认

**Files:**
- Modify: `frontend/src/pages/profile/detail.vue`
- Test: `frontend/tests/pages/profile-page.test.ts`

1. 写失败测试，要求资料加载/保存时更新快照，字段或头像改变后点击返回出现放弃确认，取消不返回、确认才调用 `uni.navigateBack`。
2. 实现可比较的资料快照、脏状态判定和异步返回确认；保存成功后刷新快照。
3. 运行 `npm run test -- --run tests/pages/profile-page.test.ts`，确认通过。

### Task 5: 首次微信绑定确认契约

**Files:**
- Modify: `backend/app/core/errors.py`
- Modify: `backend/app/modules/auth/service.py`
- Modify: `backend/tests/test_auth_api.py`
- Modify: `frontend/src/pages/login/index.vue`
- Modify: `frontend/tests/pages/login-agreement.test.ts`
- Modify: `docs/接口文档/鉴权模块_接口文档.md`

1. 写后端失败测试：未绑定且未确认的有效密码登录返回专用确认错误、不绑定且不签发会话；已绑定且 code 匹配可直接成功。
2. 写前端失败测试：初始密码登录不先弹框，只有专用错误才弹确认并用新 code 以同意状态重试。
3. 增加专用错误码，保留已绑定微信不匹配的原有错误路径；实现前端分支和重试。
4. 跑针对性前后端测试，确认通过。

### Task 6: 头像跨账号可见性验证

**Files:**
- Modify: `backend/tests/test_files_api.py` 或 `backend/tests/test_admin_users_api.py`
- Modify: `frontend/src/api/files.ts`、三个头像上传入口
- Test: `frontend/tests/pages/profile-page.test.ts`

1. 写失败的端到端契约测试：成员上传 `user_avatar` 并保存内容路由 `avatar_url` 后，另一具管理员身份读取成员资料并能加载图片内容。
2. 验证裸 COS URL 在私有读策略下不能作为跨账号展示地址后，新增统一内容路由构造函数，并让资料编辑、资料初始化、管理员成员编辑三处入口保存该 URL；展示层同时将可识别的旧 COS 用户头像 URL 转换为该路由。
3. 运行文件、管理员资料与前端头像入口的相关测试，确认通过。

### Task 7: 文档、完整验证和进度记录

**Files:**
- Modify: `docs/开发进度.md`
- Modify: 相关接口文档（仅鉴权契约）

1. 使用 `YYYY-MM-DD HH:mm:ss +08:00` 记录分支、改动、头像验证结论、命令、真机未验项和定位明确排除项。
2. 运行 `npm run test -- --run`、`npm run type-check`、`npm run build:mp-weixin`。
3. 运行 `py -3.11 -m pytest -q`、`py -3.11 -m ruff check .`、`py -3.11 -m alembic upgrade head`。
4. 检查 diff、暂存内容与提交范围不含密钥或环境文件；使用显式文件列表提交。
