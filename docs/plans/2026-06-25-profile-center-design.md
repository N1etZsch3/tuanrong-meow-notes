# 个人中心首页与管理员添加账户设计

## 背景

本切片继续个人中心模块，范围是移动端微信小程序的「我的」页、个人资料查看与编辑、统计入口、退出登录，以及管理员入口中的添加账户功能。

## 设计边界

- 「我的」首页按 `frontend/页面原型/我的.png` 复刻移动端卡片布局，保留手机视口优先原则。
- 首页数据来自 `GET /api/v1/me/dashboard`，展示当前用户资料、管理员入口开关、统计摘要和待办摘要。
- 统计入口包括累计任务、本月完成、进行中、观察记录，点击进入对应子页面。
- 收藏猫咪点击进入收藏猫咪子页面；由于猫咪收藏表尚未落地，本切片提供稳定空分页接口和空状态页面。
- 个人资料卡点击进入资料详情页，支持编辑昵称、头像 URL、部门、联系方式。
- 管理员入口只实现添加账户，调用既有 `POST /api/v1/admin/users`；账号可自动生成喵喵号，初始密码默认喵喵号。
- 退出登录调用 `POST /api/v1/auth/logout`，随后清除前端本地 session 并跳转登录页。

## 接口设计

- `GET /api/v1/me/dashboard`
  - 返回 `profile`、`stats`、`todo`、`recent_tasks`、`recent_notifications`。
  - 当前任务、猫咪、通知表未完整落地时，统计返回 0，列表返回空数组。
- `GET /api/v1/me/tasks`
- `GET /api/v1/me/checkins`
- `GET /api/v1/me/observations`
- `GET /api/v1/me/favorite-cats`
  - 返回统一分页空列表，后续业务表落地后替换查询实现。
- `PATCH /api/v1/profile/me`
  - 支持编辑 `nickname`、`avatar_url`、`department`、`contact_info`。

## 前端页面

- `pages/profile/index`：「我的」首页。
- `pages/profile/detail`：个人资料详情与编辑。
- `pages/profile/records`：统计和收藏猫咪子菜单空状态/列表容器。
- `pages/admin/index`：管理员入口，当前只展示添加账户。
- `pages/admin/create-user`：管理员添加账户表单和创建结果。

## 验证策略

- 后端用 pytest 覆盖 dashboard、空分页、资料编辑、权限限制。
- 前端用 Vitest 覆盖 API 封装、页面源码路由/退出登录/管理员入口、表单 payload。
- 最终运行后端测试、ruff、前端测试、type-check、微信小程序构建和 H5 构建。
