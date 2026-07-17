# 阶段③ 成员多部门（设计）

- 日期：2026-07-17
- 分支：`feat/member-departments`（自 `feat/list-pagination` tip `53b1d3d`）
- 来源需求：`test/bug清单/下一步优化方案.md` 一、3.2/3.3
- 已对齐决策：新建 `user_departments` 关联表（非单列 JSON）；5 个固定部门（生存保障部/活动部/宣传部/秘书部/养护部）；历史脏值原样迁入，编辑界面只允许从 5 部门增删；部门标签行超出可左右滑动（scroll-x，微信原生）；管理员可在个人编辑页改自己部门、在成员编辑页改成员部门。

## 目标

成员可同时属于多个部门。部门从「单选一个」改为「可增删的多部门标签（带 x）」。

## 数据模型

新表 `user_departments`（UUID PK 惯例、无 DB enum、软删不需要——部门关系直接增删）：
- `id` UUID PK
- `user_id` FK users.id ondelete CASCADE, index
- `department` String(128)（部门名，与现有 5 部门文案一致；历史脏值原样迁入）
- `sort_order` Integer（展示顺序，第 0 个视为主部门）
- `created_at`
- 唯一约束 `(user_id, department)`（同一用户同一部门不重复）

`UserProfile.department` 单列**保留不删**（作为「主部门」兼容字段，= sort_order 最小的部门），避免破坏线上 1.1.0/1.1.3 旧前端与既有查询；新逻辑以关联表为准，写入时双写主部门到 `profile.department`。

迁移 `20260717_0017_create_user_departments`：
- 建表 + 索引 + 唯一约束
- 数据回填：对每个 `user_profiles.department` 非空的行，插入一条 `user_departments(user_id, department, sort_order=0)`
- downgrade：drop 表（`profile.department` 保留，数据不丢）
- 分支合并：down_revision = `20260716_0016`（当前唯一 head）

## 后端契约（增量兼容，不破坏旧客户端）

统一响应新增 `departments: list[str]`，同时**保留** `department: str | None`（= departments[0] 或 null）：
- `profile_payload`（profile/service）+ auth `profile_payload`（auth/service）+ `admin_user_payload` 都补 `departments`。
- 自助 `CompleteProfileRequest`/`UpdateProfileRequest`：新增 `departments: list[Department]`（Literal 校验 5 部门，去重、限长）；`department` 单值入参保留可选以兼容旧前端（若只传 department 则等价单元素 departments）。complete 时 departments 必填非空。
- 管理员 `AdminUserProfileRequest`：新增 `departments: list[str]`（管理员路径历史上不校验部门取值，保持自由文本兼容；但新前端只会传 5 部门）。
- 列表筛选 `GET /admin/users?department=`：语义改为「任一部门命中」——用 `EXISTS(user_departments WHERE user_id=... AND department=...)`；保留旧 `department` 单值参数。
- 部门写入 helper：`set_user_departments(db, user, departments)` 统一处理增删 + 回写主部门 + sort_order，供 complete/update/admin-create/admin-update 复用（按功能拆文件，放 auth/service 或新 `departments_service`）。
- 5 部门常量收敛到后端一处（`profile/schemas.Department` 已是 Literal，作为唯一真源；管理员路径校验可选收紧留到后续，本阶段先接受 list 并清洗）。

## 前端

- 共享部门常量 `constants/departments.ts`（`DEPARTMENTS = ["生存保障部",...]`），替换 5 处重复硬编码。
- 类型：`CurrentUser`/`MeDashboardProfile`/`MyProfileResponse`/`AdminUserItem` 等补 `departments: string[]`，`department` 保留。
- 多部门选择组件 `components/DepartmentTagPicker.vue`（可增删标签，带 x；「+ 添加部门」从未选部门的 action-sheet/picker 选择；至少约束由页面决定）。5 个表单页（create-user / admin users detail / profile detail / profile complete / admin users list filter）改用它（list filter 是单选筛选，保持单选或改「任一」——本阶段筛选保持单选下拉，仅表单改多标签）。
- 编辑守卫 `member-edit-guard.ts`/`profile-edit-guard.ts`：department 快照从 string 改为 string[]（有序比较）。
- 喵的页资料卡：第 3 行部门从单值文本改为多标签，**超出显示范围时 `scroll-view scroll-x` 左右滑动**（对齐用户补充要求 4）。

## 测试影响

- 后端：迁移回填测试；complete/update 多部门读写；admin create/update 多部门；列表 department 筛选「任一命中」；旧单值 department 入参兼容。
- 前端：DepartmentTagPicker 单测；5 表单 ?raw 断言改用共享常量 + 多标签；编辑守卫 string[] 快照；资料卡多标签 scroll-x 断言。

## 验证

- 后端 `pytest -q` + `alembic upgrade head`（+ 尽量 downgrade）+ ruff
- 前端 test / type-check / build:mp-weixin
- H5：资料卡多部门标签渲染+横滑；个人编辑/成员编辑多部门增删。

## 风险

- 迁移回填必须幂等、可回滚，不丢 `profile.department`。
- 增量兼容：线上旧前端仍读 `department` 单值——务必双写主部门。
- 唯一约束 + 去重避免重复部门。
- 不动 main / 发布 / 生产。
