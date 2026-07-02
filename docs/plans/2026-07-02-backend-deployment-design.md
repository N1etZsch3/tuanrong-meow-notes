# 后端部署与 HTTPS 配置设计

## 背景

本次工作只部署后端模块。前端是微信小程序构建产物，不部署到服务器，只需要把接口地址指向生产域名。

服务器公网地址为 `203.0.113.10`，域名为 `catmap.example.com`，DNS 通过 Cloudflare 代理。服务器上的 PostgreSQL/PostGIS 等中间件已存在，本次不重新部署中间件。

## 方案

采用轻量服务器部署：

- Nginx 在源站配置 Cloudflare Origin Certificate。
- `80` 端口只做 `301` 跳转到 `https://catmap.example.com$request_uri`。
- `443` 端口只提供 HTTPS。
- 后端 FastAPI 由 systemd 管理，监听 `127.0.0.1:8000`。
- Nginx 将 `/api/v1/`、`/docs`、`/redoc`、`/openapi.json` 反代到本机后端。
- 本机一键部署脚本通过 SSH 公钥登录服务器，同步最新版 `backend/`，安装依赖，执行 Alembic 迁移，重启服务并做健康检查。

## SSH 登录

首次引导阶段允许用服务器密码登录，把本机专用部署公钥写入 `root` 的 `~/.ssh/authorized_keys`。

部署稳定后：

- 公钥登录用于一键部署脚本。
- 密码登录保留，用于应急维护。
- 一键部署脚本不保存服务器密码。

## 敏感文件处理

本地 `ssl_key/` 只作为部署输入：

- `Origin _Certificate.txt` 上传为服务器 Nginx 证书。
- `Private_Key.txt` 上传为服务器 Nginx 私钥。
- `server_key.txt` 只用于首次 SSH 公钥引导，不写入部署脚本，不提交。

脚本同步后端时排除 `.env`、缓存、测试缓存、上传文件和其他不应覆盖的运行期数据。

## 前端接口

前端不部署到服务器，只把 API base URL 改为：

```text
https://catmap.example.com/api/v1
```

本地 H5 调试如需访问本地后端，可继续通过 `.env` 覆盖 `VITE_API_BASE_URL`。

## 验证

完成后执行：

- 本机后端测试和 ruff。
- 服务器 `nginx -t`。
- 服务器 `systemctl status catmap-backend`。
- 服务器 Alembic 升级。
- 外部 HTTPS 健康检查：`https://catmap.example.com/api/v1/health`。
- 前端 type-check 和微信小程序构建。
