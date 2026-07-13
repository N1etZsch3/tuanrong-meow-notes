# 同机开发环境隔离 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在不改变生产部署契约的情况下，增加可验证、可拒绝误操作的同机开发后端发布路径，并明确开发前端 API 配置和服务器启用顺序。

**Architecture:** 生产服务继续使用 `/opt/catmap/backend`、`catmap-backend`、`127.0.0.1:8000` 和生产域名。新增开发服务固定使用 `/opt/catmap-dev/backend`、`catmap-backend-dev`、`127.0.0.1:8001` 与 `dev-api.trmx.fun`；Nginx 根据域名反向代理。开发服务的环境文件必须指向 `catmap_dev` 并使用对象存储 `dev/` 前缀。

**Tech Stack:** PowerShell 7、Pester 风格部署契约测试、systemd、Nginx、Let's Encrypt/现有证书工具、FastAPI、Alembic、uni-app/Vite。

---

## 前置条件与边界

- 不编辑 `scripts/deploy-backend.ps1`、`deploy/systemd/catmap-backend.service` 或 `deploy/nginx/catmap.conf`。
- 不重启、替换或迁移生产服务；不对 `catmap` 数据库进行写入。
- 实际部署前，`public-pages` 中包含 `20260712_0015` 的改动必须先形成用户认可的提交。当前未提交工作不能作为部署来源。
- 不在提交、终端输出、计划或进度文档中记录环境变量实际值、密码、令牌、私有主机地址或证书私钥。

### Task 1: 为开发部署契约添加失败测试

**Files:**
- Modify: `scripts/test-deployment-contracts.ps1`
- Test: `scripts/test-deployment-contracts.ps1`

**Step 1: 写入开发工件存在性的失败断言**

在现有脚本的生产契约断言之后，增加以下五个必需文件的 `Read-RequiredFile` 调用：

```powershell
$devDeployScript = Read-RequiredFile -Path (Join-Path $projectRoot 'scripts/deploy-backend-dev.ps1')
$devUnit = Read-RequiredFile -Path (Join-Path $projectRoot 'deploy/systemd/catmap-backend-dev.service')
$devNginx = Read-RequiredFile -Path (Join-Path $projectRoot 'deploy/nginx/catmap-dev.conf')
$devNginxBootstrap = Read-RequiredFile -Path (Join-Path $projectRoot 'deploy/nginx/catmap-dev-http-bootstrap.conf')
$devFrontendEnv = Read-RequiredFile -Path (Join-Path $projectRoot 'frontend/.env.development.example')
```

**Step 2: 运行测试确认其因缺少开发工件失败**

Run: `powershell -ExecutionPolicy Bypass -File scripts/test-deployment-contracts.ps1`

Expected: FAIL，错误明确指出缺少 `deploy-backend-dev.ps1`，而不是 PowerShell 语法错误。

**Step 3: 添加开发隔离的静态契约断言**

为未来实现写入精确断言：开发脚本必须包含开发目录、服务名、开发域名、8001、`catmap_dev` 和 `CATMAP_TENCENT_COS_ENV_PREFIX` 的拒绝式校验；不得将 `catmap-backend`、`/opt/catmap/backend` 或生产 Nginx 文件名作为目标。断言开发 unit 的 `WorkingDirectory`、`EnvironmentFile` 和 `--port 8001`；断言 HTTPS Nginx 和 HTTP bootstrap Nginx 都只含开发 `server_name`、非 `default_server` 和 ACME challenge 位置，且 HTTPS 配置代理至开发端口；断言前端环境显式给出 `https://dev-api.trmx.fun/api/v1`。

**Step 4: 再次运行测试确认仍因工件缺失失败**

Run: `powershell -ExecutionPolicy Bypass -File scripts/test-deployment-contracts.ps1`

Expected: FAIL，第一处失败仍是缺少开发工件；新增断言尚未因变量未定义而掩盖根因。

**Step 5: 提交红灯测试**

```powershell
git add -- scripts/test-deployment-contracts.ps1
git commit -m "test: define development deployment contracts"
```

### Task 2: 添加独立的 systemd 与 Nginx 模板

**Files:**
- Create: `deploy/systemd/catmap-backend-dev.service`
- Create: `deploy/nginx/catmap-dev.conf`
- Create: `deploy/nginx/catmap-dev-http-bootstrap.conf`
- Test: `scripts/test-deployment-contracts.ps1`

**Step 1: 创建最小开发 systemd unit**

以生产 unit 为参考但不修改它；新文件必须固定：

```ini
WorkingDirectory=/opt/catmap-dev/backend
EnvironmentFile=/opt/catmap-dev/backend/.env
ExecStart=/opt/catmap-dev/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

服务名和描述必须包含 `dev`；不开放 `0.0.0.0`，不引用生产目录。

**Step 2: 创建 HTTP 证书签发引导 vhost**

仅为 `dev-api.trmx.fun` 建立 80 端口 server block，允许 `/.well-known/acme-challenge/` 从固定 webroot 提供静态文件。其余请求可返回临时状态或跳转说明，但不能劫持生产域名，不能使用 `default_server`。

**Step 3: 创建最终 HTTPS vhost**

新 `catmap-dev.conf` 必须仅包含开发域名；80 端口 block 保留同一 ACME challenge location 并将其他请求重定向至 HTTPS；443 端口 block 读取该开发子域名专用证书，将 `/api/` 代理至 `http://127.0.0.1:8001`，并保留生产配置中必要的上传大小、超时和转发头设置。

**Step 4: 运行部署契约测试确认变为下一处失败**

Run: `powershell -ExecutionPolicy Bypass -File scripts/test-deployment-contracts.ps1`

Expected: FAIL，失败原因应为缺少开发部署脚本或开发前端环境示例，说明 unit/Nginx 文本满足测试。

**Step 5: 审查模板不触碰生产路径并提交**

```powershell
git diff --check
git diff -- deploy/systemd/catmap-backend-dev.service deploy/nginx/catmap-dev.conf deploy/nginx/catmap-dev-http-bootstrap.conf
git add -- deploy/systemd/catmap-backend-dev.service deploy/nginx/catmap-dev.conf deploy/nginx/catmap-dev-http-bootstrap.conf
git commit -m "feat: add isolated development service templates"
```

### Task 3: 实现带硬性防误操作校验的开发部署脚本

**Files:**
- Create: `scripts/deploy-backend-dev.ps1`
- Modify: `scripts/test-deployment-contracts.ps1`
- Test: `scripts/test-deployment-contracts.ps1`

**Step 1: 从生产脚本提取最小必要的发布流程，但不修改生产脚本**

开发脚本独立定义固定值：

```powershell
$DeployDir = '/opt/catmap-dev/backend'
$ServiceName = 'catmap-backend-dev'
$Domain = 'dev-api.trmx.fun'
$NginxConfigName = 'catmap-dev.conf'
$SystemdUnitName = 'catmap-backend-dev.service'
```

保留与生产脚本一致的本地依赖检查、打包、远程 `.venv` 管理、`alembic upgrade head`、systemd daemon-reload/restart、`nginx -t` 和 HTTPS health check 的行为，但所有临时归档和远程路径使用 `catmap-dev` 名称。

**Step 2: 在本地上传前加入环境护栏**

脚本只读取键名和值的匹配结果，不输出原始环境文件。必须拒绝以下情形：环境文件不存在；数据库连接字符串未标识 `catmap_dev`；`CATMAP_TENCENT_COS_ENV_PREFIX` 不是 `dev`；部署目录、服务名、域名或 Nginx 文件名意外等于生产值。开发环境的内容安全模式应在注释/校验中明确为开发专用策略，不能假装生产审核已覆盖。

**Step 3: 在远程命令中重复校验关键目标**

远程 shell 仅操作 `/opt/catmap-dev/backend`，安装 `catmap-backend-dev.service` 和 `catmap-dev.conf`。在删除旧代码前，检查计算后的目录和文件名完全等于开发固定值；保留开发目录中的 `.env`、`.venv`、`uploads`。不引用或覆盖生产 unit/Nginx 文件。

**Step 4: 运行部署契约测试确认通过**

Run: `powershell -ExecutionPolicy Bypass -File scripts/test-deployment-contracts.ps1`

Expected: PASS，输出所有生产与开发静态部署契约均已验证。

**Step 5: 做不连接服务器的 PowerShell 语法检查**

Run: `powershell -NoProfile -Command "$tokens = $errors = $null; [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path 'scripts/deploy-backend-dev.ps1'), [ref]$tokens, [ref]$errors) | Out-Null; if ($errors) { $errors | ForEach-Object { $_.Message }; exit 1 }"`

Expected: PASS，无解析错误。

**Step 6: 提交实现**

```powershell
git add -- scripts/deploy-backend-dev.ps1 scripts/test-deployment-contracts.ps1
git commit -m "feat: add guarded development deployment"
```

### Task 4: 明确开发前端 API 环境

**Files:**
- Create: `frontend/.env.development.example`
- Modify: `frontend/tests/config/app-env.test.ts`
- Test: `frontend/tests/config/app-env.test.ts`

**Step 1: 写入失败测试，描述显式开发 API 覆盖行为**

使用 `resolveApiBaseUrl` 的真实实现，先写一个 `development` 环境变量包含 `VITE_API_BASE_URL=https://dev-api.trmx.fun/api/v1` 的断言：

```ts
expect(resolveApiBaseUrl({
  MODE: 'development',
  VITE_API_BASE_URL: 'https://dev-api.trmx.fun/api/v1',
})).toBe('https://dev-api.trmx.fun/api/v1')
```

**Step 2: 运行单测确认失败原因有效**

Run: `npm run test -- --run tests/config/app-env.test.ts`

Expected: 如果解析器已支持显式值，该测试会直接通过；此时不改解析器，记录其是对现有契约的回归覆盖，并在下一步只添加环境示例。若失败，应仅因 URL 解析行为与期望不符。

**Step 3: 创建最小开发环境示例**

文件只含非敏感值和使用说明：

```dotenv
# Copy to .env.development.local for local mini-program development.
VITE_API_BASE_URL=https://dev-api.trmx.fun/api/v1
```

不改 `frontend/.env.example` 中的生产示例，不提交 `.env.development.local`。

**Step 4: 运行前端测试、类型检查和小程序构建**

Run: `npm run test -- --run tests/config/app-env.test.ts; npm run type-check; npm run build:mp-weixin`

Expected: PASS。若测试在步骤 2 已通过，步骤 4 验证环境示例没有改变 API 解析或构建。

**Step 5: 提交前端环境文档与回归测试**

```powershell
git add -- frontend/.env.development.example frontend/tests/config/app-env.test.ts
git commit -m "docs: add development API environment example"
```

### Task 5: 更新部署文档、进度和本地验证

**Files:**
- Modify: `docs/开发进度.md`
- Modify: `docs/plans/2026-07-13-dev-environment-isolation.md`
- Test: `scripts/test-deployment-contracts.ps1`

**Step 1: 记录本地完成范围与未执行的服务器操作**

在 `docs/开发进度.md` 增加带 `+08:00` 时间戳的条目：分支、模板/脚本/前端示例、静态验证结果，以及“服务器部署等待 public-pages 迁移代码提交”的明确阻塞条件。

**Step 2: 运行全部本地验证**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/test-deployment-contracts.ps1
cd backend; $env:CATMAP_WECHAT_CONTENT_SECURITY_MODE='off'; py -3.11 -m pytest -q; py -3.11 -m ruff check .
cd ../frontend; npm run test -- --run; npm run type-check; npm run build:mp-weixin
```

Expected: 全部 PASS。若任何失败，按失败类别单独调查，不绕过验证。

**Step 3: 检查变更范围和敏感信息**

Run:

```powershell
git diff --check dev...HEAD
git diff dev...HEAD -- . ':!docs/plans'
git status --short --ignored -- backend/.env frontend/.env.development.local
```

Expected: 不包含 `.env`、凭据、私有地址、证书或生产文件改动；本地环境文件仍为 ignored。

**Step 4: 提交文档更新**

```powershell
git add -- docs/开发进度.md docs/plans/2026-07-13-dev-environment-isolation.md
git commit -m "docs: record development isolation readiness"
```

### Task 6: 在可追溯代码基线到位后执行服务器部署

**Files:**
- Use: `scripts/deploy-backend-dev.ps1`
- Use: `deploy/nginx/catmap-dev-http-bootstrap.conf`
- Use: `backend/.env` (ignored, development-only)
- Verify: 生产与开发 `/api/v1/health`

**Step 1: 确认待部署提交包含开发库迁移**

Run: `git log --oneline -- backend/alembic/versions/20260712_0015_create_wechat_guests.py`

Expected: 输出一个已提交、经用户认可的提交；若文件仍只存在于 dirty worktree，停止，不部署。

**Step 2: 无输出地准备开发环境文件**

从已确认的开发环境来源复制到部署工作树的 `backend/.env`；仅检查数据库名匹配和对象前缀匹配的布尔结果，不打印值。再次用 `git status --short --ignored -- backend/.env` 确认文件被忽略。

**Step 3: 服务器只读预检**

检查现有 Nginx include 目录、可用 ACME 工具、证书续期方式、8001 监听状态、`catmap-backend-dev` 是否存在、开发数据库 migration 版本及生产 health。任何生产服务异常时停止。

**Step 4: 仅安装 HTTP bootstrap vhost 并签发开发域名证书**

在确认 DNS 已解析后，安装开发 HTTP vhost 至现有 Nginx include 目录，执行 `nginx -t` 后 reload；用现有 ACME 工具执行 webroot challenge。不得使用会暂时占用或停止生产 80/443 的 standalone 模式。

**Step 5: 执行受护栏保护的开发部署脚本**

Run: `powershell -ExecutionPolicy Bypass -File scripts/deploy-backend-dev.ps1`

Expected: 只创建/更新 `/opt/catmap-dev/backend`、`catmap-backend-dev`、开发 vhost；Alembic 对 `catmap_dev` 成功；开发 health 返回 200。

**Step 6: 双健康检查与运行时身份检查**

分别请求生产和开发 health，检查两个 systemd unit 均 active，并以只读 SQL 确认开发服务的连接用户/数据库为开发专用组合。确认 8001 仅监听回环地址；确认没有修改生产 unit、生产 vhost 或生产数据库版本。

**Step 7: 记录部署事实与回滚方式**

在 `docs/开发进度.md` 填入实际时间、部署提交、验证命令结果与未验证的小程序人工项。回滚只允许停止/回退开发 unit 或恢复开发目录上一个归档，不能回滚或重启生产服务。
