# 文件上传模块实施计划

## 模块起始清单

- 变更模块：后端文件上传 / 图片上传模块
- 已读文档：`AGENTS.md`、`docs/校园猫协地图任务系统_项目说明文档.md`、`docs/校园猫协地图任务系统_库表设计说明.md`、`docs/接口文档/接口设计规范文档.md`、`docs/模块功能/COS图片上传功能流程设计文档.md`、`docs/接口文档/文件上传模块_接口文档.md`、`docs/库表文档/图片上传模块_库表优化设计文档.md`
- 影响 API：新增 `/api/v1/files/config`、`/api/v1/files/images`、`/api/v1/files/images/batch`、`/api/v1/files/assets/{asset_id}`、`/api/v1/files/assets/{asset_id}/variant`、`/api/v1/files/assets/{asset_id}/owner`、`DELETE /api/v1/files/assets/{asset_id}`、`GET /api/v1/files/assets`
- 影响表：新增 `file_assets`、`file_asset_variants`；本阶段只补 `user_profiles.avatar_asset_id`、`user_profiles.avatar_thumb_url`，其余业务图片表随猫咪、任务模块落地后再接
- 相关页面/资产：无前端页面改造；仅为后续头像、猫咪、点位、任务打卡提供后端能力
- 上游模块：鉴权、用户资料初始化状态、统一响应、数据库基础设施
- 最小可用切片：后端可接收图片、生成多尺寸 JPEG 变体、上传 COS、写入文件资产表，并能查询/选择/绑定/逻辑删除资产
- 本分支不做：前端页面接入、COS STS 直传、上传日志表、物理删除 COS 对象、视频/音频/文档上传、复杂独立文件权限表
- 验证方式：新增文件模块测试，运行后端 pytest、ruff、Alembic 升级验证；真实 COS 配置待用户填入 `.env` 后再做联调

## 实施顺序

1. 先写失败测试，覆盖配置、上传权限、图片处理、批量上传、资产查询、变体选择、归属绑定、逻辑删除。
2. 新增文件模块模型、schemas、预设、图片处理器、存储封装、服务和 API 路由。
3. 新增 Alembic 迁移和 `.env.example` / Settings 配置项。
4. 通过依赖注入或测试替身让单元测试不依赖真实 COS。
5. 更新开发进度，记录尚未用真实 COS 配置验证。
