# 校园猫协地图任务系统｜COS 图片上传功能流程设计文档

> 版本：V1.0  
> 适用范围：头像、猫咪照片、猫咪头像、点位照片、路线图、入口图、任务打卡照片、观察记录照片  
> 存储服务：腾讯云 COS  
> 后端建议：FastAPI + Pillow + cos-python-sdk-v5  
> 前端建议：uni-app / 微信小程序 `uni.chooseImage` + `uni.uploadFile`  
> 设计目标：所有图片统一经过后端校验、压缩、转码、缩略图生成后再上传腾讯云 COS，业务模块不直接处理图片压缩和对象存储。

---

## 1. 设计背景

本项目已经包含多个图片上传场景：

| 模块 | 图片场景 | 现有/预期承载表 |
|---|---|---|
| 个人中心 | 用户头像 | `user_profiles.avatar_url` |
| 猫咪库 | 猫咪主头像、档案照、近照、健康异常照、观察记录照 | `cats.avatar_url`、`cat_photos` |
| 地图模块 | 点位封面图、现场图、路线图、入口图、参考图 | `map_point_photos` |
| 任务模块 | 任务完成打卡照片 | `task_checkin_photos` |
| 观察记录 | 猫咪现场观察照片 | `cat_photos` 或后续观察记录照片表 |

原库表中多个表都有 `file_url`、`thumbnail_url` 字段。V1 需要统一语义：

```text
file_url 不再表示用户手机原始大图，而是表示压缩后的标准展示图。
thumbnail_url 表示缩略图。
用户上传的原始文件默认不长期保存。
```

---

## 2. 核心结论

V1 推荐采用：

```text
前端选择图片
  ↓
前端可做轻量压缩，但不作为可信结果
  ↓
上传到后端统一文件接口
  ↓
后端校验图片真实类型、大小、尺寸
  ↓
后端用 Pillow 修正方向、去 EXIF、压缩、转码
  ↓
生成 display 图和 thumbnail 图
  ↓
后端上传到腾讯云 COS 隔离对象
  ↓
写入 file_assets
  ↓
user_avatar：状态 pending，使用预签名 URL 调微信 mediaCheckAsync 2.0
  ↓
头像等待微信回调，pass 后服务器自动替换
  ↓
其他 usage_type：状态 legacy，立即向业务返回 asset_id + URL
```

不建议在 V1 直接让小程序把图片直传到 COS 正式目录。原因：

1. 项目要求“先压缩再存入对象存储”。如果小程序直传，COS 里会先出现原始大图。
2. 所有业务模块都需要统一压缩标准，后端集中处理更稳定。
3. COS 永久密钥不能放到小程序前端。
4. 后端可以统一写入文件资产表，方便后续删除、替换、审计和清理孤儿文件。

---

## 3. COS 能力边界

腾讯云 COS 集成数据万象 CI，可以进行图片缩放、裁剪、旋转、格式转换和质量变换等基础图片处理。

COS/CI 也支持图片持久化处理，也就是上传时或云上处理后，将处理结果保存回 COS。

本项目 V1 仍建议优先使用后端 Pillow 处理图片，再上传 COS。原因是：

1. 后端可完全控制“不要保存原图”的策略。
2. 后端可以统一生成 `file_assets` 元数据。
3. 后端压缩结果可本地测试，不依赖 COS 图片处理费用和配置。
4. 后续如访问量变大，可以把缩略图生成迁移到 COS/CI 持久化处理。

### V1 与后续方案对比

| 方案 | 说明 | 适合阶段 |
|---|---|---|
| 后端压缩后上传 COS | 后端接收图片，生成 display/thumb，再上传 COS | V1 推荐 |
| 前端拿 STS 临时密钥直传临时目录，再后端处理 | 前端上传原图到临时目录，后端处理后转正式目录 | V1.5 / 后期 |
| COS/CI 上传时持久化处理 | 上传时通过 CI 生成处理图并保存 | 后期优化 |
| 只存原图，展示时动态压缩 | 每次访问带处理参数 | 不推荐作为本项目主方案 |

---

## 4. 统一图片处理标准

### 4.1 支持格式

| 类型 | 是否支持 | 处理方式 |
|---|---:|---|
| JPEG / JPG | 是 | 统一转 JPEG |
| PNG | 是 | 普通照片转 JPEG；如果后期有透明图标需求，单独走静态资源流程 |
| WebP | 是 | 解码后转 JPEG |
| GIF | V1 不建议 | 先拒绝，后期如需要单独支持 |
| SVG | 用户上传不支持 | 防止脚本注入；SVG 作为前端静态素材管理 |
| HEIC / HEIF | V1 不支持 | 可提示用户换成 JPG/PNG |

### 4.2 文件限制

| 项目 | V1 建议 |
|---|---:|
| 单文件上传上限 | 10MB |
| 最大像素数 | 2000 万像素 |
| 单次最多上传 | 9 张 |
| 输出格式 | JPEG |
| JPEG 色彩空间 | sRGB / RGB |
| 是否保留 EXIF | 不保留 |
| 是否保留原图 | 默认不保留 |

### 4.3 压缩预设

| usage_type | 使用场景 | display 图 | thumbnail 图 | JPEG 质量 | 目标体积 |
|---|---|---:|---:|---:|---:|
| `user_avatar` | 用户头像 | 512×512 居中裁剪 | 128×128 | 82 | 50-150KB |
| `cat_avatar` | 猫咪头像 | 800×800 居中裁剪 | 160×160 | 82 | 80-200KB |
| `cat_photo` | 猫咪照片墙/档案照 | 长边 1280px | 长边 360px | 82 | 200-500KB |
| `cat_health_photo` | 健康异常/受伤照片 | 长边 1600px | 长边 480px | 85 | 400-900KB |
| `map_point_cover` | 点位封面图 | 长边 1280px | 长边 360px | 82 | 200-500KB |
| `map_point_scene` | 点位现场图 | 长边 1280px | 长边 360px | 82 | 200-500KB |
| `map_point_route` | 路线图/入口图 | 长边 1600px | 长边 480px | 85 | 300-700KB |
| `task_checkin_photo` | 任务打卡普通照片 | 长边 1280px | 长边 360px | 82 | 200-500KB |
| `observation_photo` | 观察记录照片 | 长边 1280px | 长边 360px | 82 | 200-500KB |

说明：

1. 头像必须裁剪成 1:1，避免前端各页面反复裁剪。
2. 普通照片长边 1280px 已足够移动端详情页展示。
3. 健康异常图、路线图、入口图需要保留更多细节，因此使用 1600px 和更高质量。
4. 输出质量不要低于 78，否则草丛、猫毛、伤口细节会明显糊掉。

---

## 5. 对象 Key 设计

COS 对象 Key 必须由后端生成，不使用用户原文件名作为最终路径。

### 5.1 推荐路径规则

```text
catmap/{env}/avatars/users/{user_id}/{asset_id}_display.jpg
catmap/{env}/avatars/users/{user_id}/{asset_id}_thumb.jpg

catmap/{env}/cats/{cat_id}/{asset_id}_display.jpg
catmap/{env}/cats/{cat_id}/{asset_id}_thumb.jpg

catmap/{env}/map-points/{map_point_id}/{asset_id}_display.jpg
catmap/{env}/map-points/{map_point_id}/{asset_id}_thumb.jpg

catmap/{env}/task-checkins/{task_id}/{checkin_id}/{asset_id}_display.jpg
catmap/{env}/task-checkins/{task_id}/{checkin_id}/{asset_id}_thumb.jpg

catmap/{env}/observations/{cat_id}/{observation_id}/{asset_id}_display.jpg
catmap/{env}/observations/{cat_id}/{observation_id}/{asset_id}_thumb.jpg
```

### 5.2 env 取值

| env | 说明 |
|---|---|
| `dev` | 本地/开发环境 |
| `test` | 测试环境 |
| `prod` | 正式环境 |

### 5.3 命名原则

1. 不使用原文件名，避免中文、空格、特殊字符和敏感信息。
2. 使用 `asset_id` 或 UUID，避免对象 Key 可被猜测。
3. display 和 thumb 使用同一个 `asset_id`，便于成对清理。
4. 不同环境前缀隔离，避免开发测试污染正式数据。

---

## 6. COS 访问权限策略

### 6.1 V1 推荐配置

| 项目 | 推荐值 |
|---|---|
| Bucket 写权限 | 仅后端服务账号可写 |
| Bucket 读权限 | MVP 可公有读；正式版建议私有读 + 签名 URL/CDN 鉴权 |
| SecretId / SecretKey | 仅保存在后端环境变量 |
| 小程序端是否保存 COS 密钥 | 禁止 |
| 是否允许列举对象 | 禁止普通用户列举 |
| 是否允许用户指定 object_key | 禁止 |

如果你想快速完成 MVP，可以先使用：

```text
公有读 + 私有写 + 后端随机对象 Key
```

如果你更重视内部资料保护，可以使用：

```text
私有读写 + 后端生成临时签名 URL
```

但私有读会让前端图片展示多一步签名刷新逻辑。V1 可以先完成上传闭环，再把读权限升级为签名 URL 或 CDN 鉴权。

---

## 7. 后端模块设计

建议新增独立文件模块：

```text
backend/app/modules/files/
  ├── router.py              # 文件上传接口
  ├── models.py              # file_assets ORM
  ├── schemas.py             # DTO / 响应模型
  ├── service.py             # FileService 业务编排
  ├── image_processor.py     # Pillow 压缩、裁剪、转码
  ├── cos_client.py          # 腾讯云 COS 上传封装
  ├── validators.py          # 文件类型、大小、像素校验
  ├── object_key.py          # COS object key 生成
  └── errors.py              # 文件模块错误码
```

### 7.1 依赖建议

```text
cos-python-sdk-v5
Pillow
python-multipart
filetype 或 python-magic
```

### 7.2 环境变量

```env
TENCENT_COS_SECRET_ID=xxx
TENCENT_COS_SECRET_KEY=xxx
TENCENT_COS_REGION=ap-guangzhou
TENCENT_COS_BUCKET=replace-with-cos-bucket
TENCENT_COS_APP_ID=replace-with-cos-app-id
TENCENT_COS_SCHEME=https
TENCENT_COS_DOMAIN=https://replace-with-cos-bucket.cos.ap-guangzhou.myqcloud.com
TENCENT_COS_CDN_DOMAIN=
TENCENT_COS_ENV_PREFIX=dev
FILE_UPLOAD_MAX_MB=10
FILE_IMAGE_MAX_PIXELS=20000000
```

---

## 8. 统一接口设计

项目接口规范已要求：

```text
Base URL: /api/v1
字段命名: snake_case
文件上传: multipart/form-data
响应结构: { code, message, data, trace_id }
```

因此文件模块接口统一放在：

```text
/api/v1/files
```

---

## 8.1 上传图片

### 基本信息

```http
POST /api/v1/files/images
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

### FormData 字段

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `file` | file | 是 | 图片文件 |
| `usage_type` | string | 是 | 图片用途，如 `user_avatar`、`cat_photo` |
| `owner_type` | string | 否 | 业务归属类型，如 `user`、`cat`、`map_point` |
| `owner_id` | uuid | 否 | 业务归属 ID，可创建业务后再补 |
| `caption` | string | 否 | 图片说明 |

### usage_type 枚举

```text
user_avatar
cat_avatar
cat_photo
cat_health_photo
map_point_cover
map_point_scene
map_point_route
task_checkin_photo
observation_photo
```

### owner_type 枚举

```text
user
cat
map_point
task_checkin
observation
temporary
```

### 响应示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "asset_id": "3e3c6d18-c6ed-4e63-b1d3-8a8cbb8fd6f0",
    "usage_type": "cat_photo",
    "file_url": "https://replace-with-cos-bucket.cos.ap-guangzhou.myqcloud.com/catmap/dev/cats/xxx_display.jpg",
    "thumbnail_url": "https://replace-with-cos-bucket.cos.ap-guangzhou.myqcloud.com/catmap/dev/cats/xxx_thumb.jpg",
    "object_key": "catmap/dev/cats/xxx_display.jpg",
    "thumbnail_object_key": "catmap/dev/cats/xxx_thumb.jpg",
    "width": 1280,
    "height": 853,
    "size_bytes": 286000,
    "thumbnail_width": 360,
    "thumbnail_height": 240,
    "thumbnail_size_bytes": 42000,
    "mime_type": "image/jpeg",
    "process_preset": "cat_photo_v1"
  },
  "trace_id": "018f3c2e9b7e4f1a9a7e6c8d9"
}
```

### 业务规则

1. 需要登录。
2. 如果用户 `must_change_password = true`，不允许上传业务图片。
3. 如果用户 `profile_completed = false`，只允许上传 `user_avatar`。
4. 后端必须校验真实文件类型，不能只信任 `Content-Type` 和文件后缀。
5. 所有图片必须生成 display 和 thumbnail 两个版本。
6. 上传成功后写入 `file_assets`；`user_avatar` 进入 `pending`，其他图片标记为无需微信审核的 `legacy` 并立即可用。
7. 只有用户头像通过服务端调用微信 `mediaCheckAsync` 2.0；前端不得持有 access token 或 AppSecret。
8. 用户头像只有微信 `pass` 后才允许读取和自动应用；`risky/review` 均拒绝发布。
9. 头像通过回调自动生效，待审或拒绝时继续展示旧头像。
10. 接口异常采用关闭失败策略，不能把“审核服务不可用”当成审核通过。

---

## 8.2 查询文件资产

```http
GET /api/v1/files/assets/{asset_id}
Authorization: Bearer <access_token>
```

返回 `file_assets` 的文件元数据。普通成员只能查看自己有权限访问的业务图片；管理员可以查看管理范围内的文件。

---

## 8.3 删除文件资产

```http
DELETE /api/v1/files/assets/{asset_id}
Authorization: Bearer <access_token>
```

V1 推荐逻辑删除：

```text
file_assets.deleted_at = now()
业务表解除关联或软删除图片记录
COS 物理对象暂不立即删除
后续定时任务清理 deleted_at 超过 N 天的对象
```

原因：误删可恢复，也避免业务表和 COS 删除失败导致不一致。

---

## 9. 业务接口如何复用 FileService

### 9.1 用户头像

推荐流程：

```text
1. 前端上传头像到 /files/images，传 usage_type = user_avatar 和新鲜 wechat_code
2. 后端暂存图片并返回 pending asset_id，旧头像保持不变
3. 微信回调 pass 后，后端自动更新 user_profiles.avatar_asset_id、avatar_url
4. risky/review 时保留旧头像并向资料接口暴露通用失败状态
```

也可以封装成专用接口：

```http
POST /api/v1/profile/me/avatar
```

内部仍然调用 FileService。

---

### 9.2 猫咪照片

```http
POST /api/v1/admin/cats/{cat_id}/photos
Content-Type: multipart/form-data
```

业务接口内部流程：

```text
1. 校验当前用户是管理员
2. 校验 cat_id 存在
3. 根据 photo_type 选择 usage_type
4. 调用 FileService 压缩并上传 COS
5. 写入 cat_photos
6. 如果 set_as_avatar = true，更新 cats.avatar_asset_id、cats.avatar_url
7. 写入 admin_operation_logs
```

---

### 9.3 地图点位照片

已有接口：

```http
POST /api/v1/admin/map/points/{point_id}/photos
```

内部改造：

```text
1. 校验点位存在
2. 根据 photo_type 选择 usage_type
   cover -> map_point_cover
   route / entrance -> map_point_route
   scene / reference -> map_point_scene
3. 调用 FileService
4. 写入 map_point_photos.asset_id、file_url、thumbnail_url
5. 如果 set_as_cover = true，更新 map_points.cover_photo_id
6. 写入 admin_operation_logs
```

---

### 9.4 任务打卡照片

```http
POST /api/v1/tasks/{task_id}/checkins
Content-Type: multipart/form-data
```

建议支持一次提交多张图片：

```text
files[]
photo_types[]
captions[]
```

内部流程：

```text
1. 校验当前用户已参与任务
2. 创建 task_checkins
3. 遍历图片，调用 FileService
4. 写入 task_checkin_photos
5. V1 直接完成任务，更新 tasks.status = completed
6. 写入 task_activity_logs 和 notifications
```

---

### 9.5 观察记录照片

V1 可以继续复用 `cat_photos`：

```text
photo_type = observation
observation_record_id = 当前观察记录 ID
```

后期如果观察记录图片量变大，可以独立拆出：

```text
cat_observation_photos
```

---

## 10. 后端处理流程细节

### 10.1 图片处理伪代码

```python
from PIL import Image, ImageOps


def process_image(file_bytes: bytes, preset: ImagePreset) -> ProcessedImage:
    image = Image.open(BytesIO(file_bytes))
    image.verify()  # 初步校验

    image = Image.open(BytesIO(file_bytes))
    image = ImageOps.exif_transpose(image)  # 修正手机拍照方向
    image = image.convert("RGB")            # 统一输出 JPEG

    if image.width * image.height > MAX_PIXELS:
        raise FileUploadError("图片像素过大")

    if preset.crop_square:
        image = center_crop_square(image)

    display = resize_by_long_edge_or_exact(image, preset.display_size)
    thumb = resize_by_long_edge_or_exact(image, preset.thumbnail_size)

    display_bytes = save_jpeg(display, quality=preset.quality)
    thumb_bytes = save_jpeg(thumb, quality=preset.thumbnail_quality)

    return ProcessedImage(display, thumb, display_bytes, thumb_bytes)
```

### 10.2 上传 COS 伪代码

```python
client.put_object(
    Bucket=settings.TENCENT_COS_BUCKET,
    Key=display_key,
    Body=display_bytes,
    ContentType="image/jpeg"
)

client.put_object(
    Bucket=settings.TENCENT_COS_BUCKET,
    Key=thumb_key,
    Body=thumb_bytes,
    ContentType="image/jpeg"
)
```

### 10.3 数据写入顺序

```text
1. 后端校验图片
2. 生成 asset_id
3. 生成 display/thumb bytes
4. 上传 display/thumb 到 COS 隔离路径
5. 所有对象成功后写入 file_assets/file_asset_variants
6. user_avatar 写入 pending，用预签名 display URL 提交微信 mediaCheckAsync，记录 trace_id
7. user_avatar 立即返回待审 asset_id，不返回可发布 URL
8. user_avatar 在微信回调 pass 后开放 URL；risky/review/failed 均不可发布
9. 其他 usage_type 写入 legacy，立即返回可用 URL，不获取 wechat_code、不提交微信审核
```

如果第 4 步成功、第 5 步失败，需要删除第 4 步已上传对象，或者写入失败日志等待清理。V1 推荐失败时尽量回滚已上传对象。

---

## 11. 错误码设计

文件模块使用 `65000 - 65999`。

| code | HTTP | 说明 |
|---:|---:|---|
| 65001 | 400 | 文件不能为空 |
| 65002 | 400 | 文件大小超过限制 |
| 65003 | 400 | 文件类型不支持 |
| 65004 | 400 | 图片内容损坏或无法解析 |
| 65005 | 400 | 图片尺寸超过限制 |
| 65006 | 400 | 图片用途类型不支持 |
| 65007 | 400 | 图片处理失败 |
| 65008 | 500 | 上传 COS 失败 |
| 65009 | 404 | 文件资产不存在 |
| 65010 | 403 | 无权访问该文件 |
| 65011 | 409 | 文件正在处理中 |
| 65012 | 409 | 文件已被删除 |
| 65013 | 400 | 文件数量超过限制 |
| 65014 | 500 | 文件元数据写入失败 |
| 65021 | 400 | 缺少微信登录 code |
| 65022 | 502 | 微信图片审核服务不可用 |
| 65023 | 409 | 图片正在审核 |
| 65024 | 422 | 图片审核未通过或试图绕过审核 |
| 65025 | 400/403 | 微信审核回调无效 |

---

## 12. 前端接入流程

### 12.1 选择图片

```ts
uni.chooseImage({
  count: 9,
  sizeType: ['compressed'],
  sourceType: ['album', 'camera'],
})
```

说明：

1. 前端可以选择 `compressed`，减少上传耗时。
2. 后端仍然会重新压缩，前端压缩只作为网络优化。
3. 用户头像上传时，前端可以先裁剪预览，但最终仍以后端裁剪为准。

### 12.2 上传图片

```ts
uni.uploadFile({
  url: `${API_BASE_URL}/files/images`,
  filePath,
  name: 'file',
  formData: {
    usage_type: 'cat_photo',
    owner_type: 'cat',
    owner_id: catId,
  },
  header: {
    Authorization: `Bearer ${token}`,
  },
})
```

### 12.3 前端展示

| 场景 | 使用 URL |
|---|---|
| 列表卡片 | `thumbnail_url` |
| 地图 Marker 预览 | `thumbnail_url` |
| 详情页轮播 | `file_url` |
| 用户头像小图 | `thumbnail_url` 或头像专用 `avatar_url` |
| 任务打卡详情 | `file_url` |

---

## 13. 测试清单

### 13.1 单元测试

| 测试项 | 预期 |
|---|---|
| JPG 上传 | 成功生成 display/thumb |
| PNG 上传 | 成功转 JPEG |
| WebP 上传 | 成功转 JPEG |
| 伪造后缀 | 被拒绝 |
| 超过 10MB | 被拒绝 |
| 超过像素限制 | 被拒绝 |
| 头像裁剪 | 输出 512×512 和 128×128 |
| EXIF 旋转 | 图片方向正确 |
| COS 上传失败 | 返回 65008 |
| 数据库写入失败 | 已上传对象可回滚或记录待清理 |
| 待审图片访问/绑定 | 返回 65023，不泄露 URL |
| risky/review 回调 | 保留旧头像或旧业务内容，返回通用违规提示 |
| 重复/乱序回调 | 幂等；较旧头像审核结果不得覆盖较新的待审头像 |

### 13.2 集成测试

| 流程 | 验证点 |
|---|---|
| 初始化身份上传头像 | `user_profiles.avatar_url` 正确更新 |
| 管理员添加猫咪照片 | `cat_photos.asset_id` 正确写入 |
| 上传点位路线图 | `map_point_photos` 正确写入，导航接口返回图片 |
| 任务完成打卡上传多图 | `task_checkin_photos` 正确写入 |
| 删除点位照片 | 业务关联解除，操作日志写入 |

---

## 14. 开发任务拆分

### 第一阶段：文件基础能力

1. 新增 `file_assets` 表和 Alembic 迁移。
2. 新增文件模块目录。
3. 接入 COS SDK。
4. 实现图片校验、压缩、缩略图生成。
5. 实现 `POST /api/v1/files/images`。
6. 实现文件模块错误码。
7. 编写后端测试。

### 第二阶段：个人中心头像接入

1. `user_profiles` 增加 `avatar_asset_id`。
2. 初始化身份页和资料编辑页改为走文件上传接口。
3. `avatar_url` 保存压缩后 URL。
4. 增加头像上传测试。

### 第三阶段：猫咪库接入

1. `cats` 增加 `avatar_asset_id`。
2. `cat_photos` 增加 `asset_id`、尺寸和大小字段。
3. 新增猫咪照片上传接口。
4. 支持设为猫咪头像。

### 第四阶段：地图点位照片接入

1. `map_point_photos` 增加 `asset_id`。
2. 改造现有点位照片上传接口。
3. 支持封面图、路线图、入口图。
4. 地图卡片和导航接口返回 COS URL。

### 第五阶段：任务打卡照片接入

1. `task_checkin_photos` 增加 `asset_id`。
2. 任务打卡接口支持多图上传。
3. 个人中心“我的打卡记录”返回缩略图。

---

## 15. V1 最终规范

```text
1. 所有用户上传图片必须经过后端 FileService；只有 `user_avatar` 进入微信内容安全审核。
2. 所有图片先压缩、转码、生成缩略图，再上传腾讯云 COS。
3. V1 不长期保存用户手机原始大图。
4. file_url 表示压缩后的标准展示图。
5. thumbnail_url 表示缩略图。
6. 业务模块只保存图片关联，不直接处理压缩和 COS 上传。
7. COS SecretId / SecretKey 只能保存在后端。
8. 对象 Key 由后端生成，禁止前端传入最终 Key。
9. 删除图片默认先软删除，物理清理后置。
10. 头像、猫咪照片、点位照片、任务打卡照片使用同一套 FileService。
11. 用户头像只有 `security_status = passed` 才自动生效；普通业务图片使用 `legacy` 表示无需本轮微信审核，并可立即绑定。
```

---

## 16. 参考资料

1. 腾讯云对象存储 COS：Python SDK / 上传对象相关文档。
2. 腾讯云数据万象 CI：基础图片处理文档。
3. 腾讯云数据万象 CI：图片持久化处理文档。
4. 腾讯云安全凭证服务 STS：临时访问凭证文档。
5. 项目现有《接口设计规范文档》《校园猫协地图任务系统项目说明文档》《校园猫协地图任务系统库表设计说明》。 
