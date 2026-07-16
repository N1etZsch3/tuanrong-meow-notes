# 阶段① 喵的页 / 喵记页信息架构重构（设计）

- 日期：2026-07-17
- 分支：`feat/profile-notes-ia`（自 `dev@c430e59`）
- 来源需求：`test/bug清单/下一步优化方案.md` 一、1/2/5
- 上位记录：本次为「下一步优化方案」epic 的第 1 阶段（共 6 阶段，拆分支分批做）。开发进度长期把「喵记页与记录整合」标注为「设计中，需先补设计文档」——本文件即补此设计。

## 目标（本阶段范围）

纯前端信息架构调整，**不新增后端接口、不改库表、不改后端行为**。四件事：

1. **账号设置 → 改名「设置」**，把「消息通知」「帮助与反馈」两个菜单项从「喵的」页收进设置页。
2. **去掉「喵的」页的「管理员入口」菜单行**，改由「喵记」书架承载。
3. **喵记书架新增第 2 页「管理」书架**：放一本「成员」书，直达现有人员管理列表页 `/pages/admin/users/index`；标题副文案随当前书架页切换；非管理员完全看不到第 2 页，也不显示多余页数。
4. **公开主页入口**（已存在于「喵的」页菜单第 2 行）按新结构保留/微调。

明确 **不在本阶段做**（属后续阶段）：通知开关的真实后端（阶段④）、徽章/多部门/头衔（阶段③⑤⑥）、列表分页（阶段②）。

## 现状事实（已勘察）

- 「喵的」页 `pages/profile/index.vue`：菜单卡 5 行——账号设置 / 协会公开主页 / 消息通知(toast占位) / 帮助与反馈(toast占位) / 管理员入口(`v-if="dashboard?.profile.show_admin_entry"`)。
- 「喵记」页 `pages/tasks/index.vue`：书架已有「上一页/下一页 + X/Y」分页脚手架（`bookPages: NoteBook[][]`，当前仅 1 页），`buildBookRows` 把每页切成 3 行（前两行放书、第三行空板）。标题副文案 `记录与管理入口` 为静态。`<script setup>` 当前**未引入任何 store**。
- 管理员入口页 `pages/admin/index.vue`：仅一张「人员管理」动作卡 → `/pages/admin/users/index`。其余管理入口（发布任务/物资点/地标）本就散在各自列表页右下角 `v-if="userStore.isAdmin"` 浮动按钮，**与本阶段无关、保持不变**。
- 角色判定：客户端 `userStore.isAdmin`（`stores/user.ts:55-57`，同步从 storage hydrate，页面 setup 即可用）；服务端 `dashboard.profile.show_admin_entry`（= role ∈ {admin,super_admin}）。
- 设置页 `pages/profile/settings.vue`：现有「账号与安全」分组（重设密码/微信解绑）+ 退出登录。
- 公开主页入口在 dev 上已实现（菜单第 2 行「协会公开主页」→ `PUBLIC_HOME_ROUTE`）；代码中不存在「隐私设置」。

## 设计决策

### A. 设置页改造（`settings.vue` + `profile/index.vue` + `pages.json`）

- `pages.json` 中 `pages/profile/settings` 的 `navigationBarTitleText`：`账号设置` → `设置`。
- `settings.vue` nav-title `账号设置` → `设置`；nav-subtitle 由「管理登录密码与当前会话」改为覆盖面更广的文案（如「账号安全与通知偏好」）。
- 在设置页新增一个「通用」分组，含两行：
  - **消息通知**：本阶段仍是占位（跳转到一个占位提示或保留 toast「暂未开放」），阶段④落地后改为真正的「通知开关设置页」。为避免阶段④返工，把这一行的目标抽成常量/函数，集中一处。
  - **帮助与反馈**：跳转到新建的静态页 `pages/profile/help-feedback`（静态 FAQ + 协会联系方式，纯前端，无后端）。
- 「喵的」页 `profile/index.vue`：菜单卡删除「消息通知」「帮助与反馈」「管理员入口」三行，只留「设置」（改名）+「协会公开主页」。清理随之无用的 import（`notificationsIcon`/`feedbackIcon`/`adminIcon`/`goAdmin`/`showPendingToast`）——除非设置行仍复用。菜单文案「账号设置」→「设置」。
- 后端 `show_admin_entry` 字段与 `api/me.ts` 类型**保留不动**（其它地方可能读；删除属后端清理，不在本阶段）。

### B. 帮助与反馈静态页（新建 `pages/profile/help-feedback.vue` + 逻辑 `help-feedback.ts`）

- 纯静态：常见问题 FAQ（问题/答案数组）+ 协会联系方式（占位内容，待用户提供真实信息，先用明显占位并标注）。
- 遵循规范「按功能拆文件」：FAQ 数据 + 类型放 `help-feedback.ts`，页面只渲染。
- 复用共享页面标题样式（`--catmap-page-title-*`）、共享背景 `素材/加载页素材/背景.jpg`、宋体字族、卡片圆角规范。
- 注册进 `pages.json`。

### C. 喵记书架第 2 页「管理」（`tasks/index.vue`）

- 引入 `useUserStore`，`bookPages` 由 `const` 改为 `computed`：
  - 第 1 页恒为现有 5 本记录书（任务/物资/校园地标/药品/猫咪库）。
  - 第 2 页仅当 `userStore.isAdmin` 为真时存在，内含一本「成员」书 → `/pages/admin/users/index`，图标用现有 `素材/svg/登录页/部门管理.svg`（贴近人员语义，避免新增素材）。
- 标题副文案改为 computed，随 `currentBookPage` 切换：第 1 页「记录入口」、第 2 页「管理入口」（非管理员只会看到第 1 页，恒为「记录入口」）。
- 「不显示多余页数」：当 `totalBookPages === 1`（非管理员）时，隐藏整个 `.shelf-pager`（现状即使 1 页也显示「1/1」+禁用按钮，属多余，隐藏更干净）。管理员有 2 页时正常显示 pager。
- `currentBookPage` 若因角色变化越界需夹紧（`onShow` 时 clamp 到 `totalBookPages-1`），避免管理员翻到第 2 页后角色态变化导致空页。
- 其余管理入口（发布任务/物资点/地标）**不动**；人员管理列表页逻辑**不动**；仅改书架展示。
- `/pages/admin/index` hub 页保留文件（不再有入口链接，成为孤立页，避免连带删除引发的测试/路由波动；后续阶段可清理）。admin-page.test.ts 对 `pages/admin/index` 注册与「仅人员管理」的断言因此仍成立。

### D. 公开主页入口

- 保留「喵的」页菜单第 2 行「协会公开主页」。本阶段菜单从 5 行缩到 2 行后，它自然上移到「设置」下方，符合原型「隐私设置位置＝公开主页入口」的意图。图标/文案暂不改（可后续微调）。

## 测试影响（frontend/tests）

- `tests/pages/profile-page.test.ts`：
  - 第 105-116 行 `uses the provided profile svg assets`：断言 profileIndex 含 `通知.svg`/`帮助和反馈.svg`——移动后「喵的」页不再引用这两个，需把断言迁到 settings 页或调整。`任务.svg`/`进行中.svg`/`设置.svg` 仍在。
  - 第 278-313 行设置相关：`navigationBarTitleText` 从「账号设置」语义变「设置」，需同步；新增「通用」分组与「帮助与反馈」入口断言。
- `tests/pages/admin-page.test.ts`：`pages/admin/index` 仍注册、仍「仅人员管理」——不受影响。新增对喵记书架管理页的断言（可选，放到新的 notes 书架测试或 admin 测试）。
- 新增：喵记书架 role-conditional 第 2 页 + 副文案切换的 `?raw` 断言（`tasks/index.vue` 目前无专属测试，可新建 `tests/pages/notes-page.test.ts` 或并入现有）。
- `tests/api/me.test.ts`：保留 `show_admin_entry` 字段，不动。

## 验证

- `npm run test -- --run`（基线 374 passed，改后须全绿）
- `npm run type-check`
- `npm run build:mp-weixin`（开发构建）
- H5 验证页面效果（规范三）：`npm run dev:h5`，按 [catmap-h5-verify-recipe] 若登录受阻则临时注释微信 login+验证码，验证完恢复。重点看：喵的页菜单收敛、设置页新分组、帮助反馈页、喵记书架管理员两页切换 + 非管理员单页无 pager。

## 风险

- 书架 `bookPages` 改 computed 后，pager 的 clamp 边界要处理好，否则管理员→非管理员切换态可能停在空第 2 页。
- 「消息通知」占位在阶段④前维持占位，需在设置页明确「暂未开放」提示，避免用户误以为坏了。
- 不触碰 main / 发布 / 生产部署（1.1.3 重审在飞）。
