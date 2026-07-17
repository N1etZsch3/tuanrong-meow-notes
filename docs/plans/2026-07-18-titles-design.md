# 阶段⑤ 头衔系统（设计）

- 日期：2026-07-18
- 分支：`codex/feature/titles-completion`（继承 `feat/titles` 与阶段①–④提交链）
- 来源需求：优化方案一、3.4 + 3.5
- 已对齐决策：本轮只做「身份与归属管理」（不做按头衔的权限划分）；会长首次由开发者代码 seed；头衔操作必须走**独立授权通道**（绕开「管理员不能改管理员/自己」护栏）；盾牌 3 色（会长一色 / 副会长一色 / 部长+副部长一色）；12 个标签背景色各不相同。

## 方案选择

- **采用：`user_profiles.title` + 部分唯一索引 + 独立 titles 服务。** 头衔是用户当前身份的单值属性，放在资料表最直接；数据库保证 12 个非空头衔全局唯一，服务层负责授权、占用检查、事务和审计。
- 不采用独立“头衔占用表”：当前没有任期、历史或一人多头衔需求，会增加联表与双写复杂度。
- 不把逻辑继续堆入 `auth/service.py` 或人员详情页面：后端拆 `titles/constants.py`、`schemas.py`、`service.py`、`dependencies.py`；前端拆常量、API、`TitleBadge` 与交互辅助模块。

## 微信小程序官方方案调研

- [`picker`](https://developers.weixin.qq.com/miniprogram/dev/component/picker.html)：`mode="selector"` 支持对象数组、索引值与 `change` 事件，适合 12 个头衔的单选；不使用 `showActionSheet` 承载头衔列表，因为官方限制 `itemList` 最多 6 项。
- [`wx.showModal`](https://developers.weixin.qq.com/miniprogram/dev/api/ui/interaction/wx.showModal.html)：用于授予、剥夺、转让与放弃前的明确确认；只在 `confirm=true` 时执行写操作，不在取消分支承载业务逻辑。
- [`scroll-view`](https://developers.weixin.qq.com/miniprogram/dev/component/scroll-view.html)：横向滚动需 `scroll-x`，WebView 兼容时启用 `enable-flex`；沿用资料卡既有部门横向滚动，不新增复杂嵌套滚动。
- [自定义组件](https://developers.weixin.qq.com/miniprogram/dev/framework/custom-component/)：把头衔盾牌与标签封装为 `TitleBadge.vue`，由资料卡、人员详情等页面复用，避免页面内重复注册表与样式。

## 13 头衔

`none`（无，默认，不显示标签）+ 12 个全局唯一头衔：
- `president` 会长、`vice_president` 副会长
- 5 部门 × (部长 `_head`, 副部长 `_deputy`)：survival/activity/publicity/secretary/care × head/deputy

盾牌色组：president=金 / vice_president=紫 / 其余 head+deputy=绿。标签背景色每个头衔一色（前后端共享注册表）。

## 不变量与规则

- 每用户恰好一个头衔（默认 none）。12 非 none 头衔全局唯一。
- **会长必须是管理员**（seed 与转让都维持）。
- 会长（且仅会长）可：授予/剥夺其他成员头衔（president 除外）、原子转让会长。
- 除会长外，任何持有者可主动放弃自己头衔（→none）。放弃后该头衔可被重新授予。
- 会长不能走普通放弃接口，只能通过原子转让交接，避免权限真空。
- 会长不能直接授予「已被占用」的头衔（占用中→409，须先让持有者放弃或会长先剥夺）。
- president 头衔不经普通授予流转：只由 seed 或原子转让产生。
- 原子转让：一个事务内 successor.title=president + president.title=none（+ successor 老头衔释放）；successor 非管理员则自动升 admin 并 token_version++。
- 软删除用户时释放其头衔（置 none），避免占用悬挂。

## 数据模型

`user_profiles` 新增 `title varchar(64) nullable`（NULL/'none' 皆表示无头衔，统一存 NULL）。全局唯一：部分唯一索引 `WHERE title IS NOT NULL`（SQLite/PG 均支持 partial unique index，ORM 用 `Index(unique=True, sqlite_where=, postgresql_where=)`）。迁移 `20260718_0019_add_profile_title`（加列 + 部分唯一索引；down 删）。

## 后端

- `app/modules/titles/constants.py`：TITLE_KEYS、TITLE_LABELS、TITLE_SHIELD（color group）、DEPARTMENT_TITLE 映射；`is_president_title` 等。前端镜像。
- `app/modules/titles/service.py`：
  - `title_holder(db, title)`、`user_title(user)`、`title_payload`（key+label+shield）。
  - `set_member_title(db, actor, target, title)`：actor 必须 president；title ∈ 非 president（含 none）；target 不能是 president 持有者；title!=none 须未占用；释放 target 老头衔→设新；写 AdminOperationLog。
  - `transfer_president(db, president, successor)`：原子；successor!=self；升 admin 若需；日志。
  - `resign_title(db, user)`：非 president 持有者从非 none → none；会长调用返回 403，必须走转让；写日志。
  - `seed_president(db, user)`：开发者用，置 president + 确保 admin（供脚本/测试）。
  - `title_catalog(db)`：一次查询返回 12 个头衔的标签、盾牌分组、占用状态和持有者摘要，供会长选择器使用；不得从分页成员列表推算。
- 授权：`require_president` 依赖（登录+active+持 president 头衔）。**不复用** require_admin 的 target 护栏。
- 接口：
  - `PATCH /api/v1/admin/users/{id}/title`（require_president）body `{title}` — 授予/剥夺（none）。
  - `GET /api/v1/admin/titles`（require_president）— 返回全部非空头衔及当前占用者。
  - `POST /api/v1/admin/titles/transfer`（require_president）body `{successor_id}` — 原子转让。
  - `POST /api/v1/profile/me/title/resign`（require_profile_completed）— 自助放弃。
  - 管理员建号 `AdminCreateUserRequest.profile.title`：仅当创建者为 president 且头衔未占用才接受非 none；其他管理员提交非空头衔明确返回 403，不静默忽略。
- payload：`admin_user_payload`、auth `profile_payload`、`/me/dashboard`、`/auth/me` profile 均补 `title` + `title_label` + `title_shield`。
- 软删 `soft_delete_user` 释放头衔。
- 开发者 seed 脚本 `backend/scripts/grant_president.py`（按 meow_no 置会长）。错误码新增 63009（头衔占用）/63010（非会长无权）/63011（头衔非法）/63012（会长必须转让）。

## 前端

- `constants/titles.ts`：镜像注册表（key/label/tagBg/tagColor/shieldVariant）。
- 3 盾牌 SVG 变体（复用素材/svg/猫咪库/盾牌.svg 加 fill + 尺寸）：gold/purple/green，放 `素材/svg/头衔/`。
- 组件 `components/TitleBadge.vue`：给定 title key 渲染盾牌+彩色标签；none 不渲染。
- 喵的页资料卡：昵称行「猫协管理员」pill 之后加头衔标签（dashboard.profile.title）。
- 人员管理详情账号操作（president 可见）：原生 selector picker 展示全部非 president 头衔并标记/禁用已占用项；授予、剥夺、转让均使用原生确认框。转让会长以当前详情用户为继承者，非管理员时确认文案明确提示「将自动升为管理员」。
- 设置页新增「放弃头衔」行（当前用户持非 none 时显示）。
- 管理员建号表单：president 创建者可选初始头衔。
- 类型补 title 字段；store 同步。

## 测试（阶段⑤业务完成后，与阶段④一并补）

后端：唯一性（授予占用→409）、占用目录、剥夺、普通头衔放弃后可重授、会长放弃→403/63012、原子转让（successor 升 admin+token_version++、president→none）、非会长调用→403、president 不能经授予接口流转、非会长建号指定头衔→403、软删释放、seed。前端：注册表、TitleBadge、资料卡展示、账号操作 president 门控、原生 picker/确认框、放弃头衔、类型与 API。

## 验证

后端 pytest + ruff + 单迁移 head；前端 type-check + build。H5：资料卡头衔标签、账号操作授予/转让、放弃。

## 风险

- 全局唯一并发：DB 部分唯一索引兜底 + 服务层校验。
- 会长权限真空：普通放弃接口禁止 president，只有单事务转让可以移交；seed 仅用于首次初始化或开发者恢复。
- 转让升 admin 改 role→token_version++ 使 successor 旧 JWT 失效（符合既有惯例）。
- 不合 dev / 不推远端 / 不部署 / 不动 main。
