$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot

function Read-RequiredFile {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required file is missing: $Path"
    }

    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

function Assert-Contains {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Content,
        [Parameter(Mandatory = $true)]
        [string] $Needle,
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    if (-not $Content.Contains($Needle)) {
        throw $Message
    }
}

function Assert-NotContains {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Content,
        [Parameter(Mandatory = $true)]
        [string] $Needle,
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    if ($Content.Contains($Needle)) {
        throw $Message
    }
}

function Assert-Before {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Content,
        [Parameter(Mandatory = $true)]
        [string] $EarlierNeedle,
        [Parameter(Mandatory = $true)]
        [string] $LaterNeedle,
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    $earlierIndex = $Content.IndexOf($EarlierNeedle)
    $laterIndex = $Content.IndexOf($LaterNeedle)
    if ($earlierIndex -lt 0 -or $laterIndex -lt 0 -or $earlierIndex -gt $laterIndex) {
        throw $Message
    }
}

$deployScript = Read-RequiredFile (Join-Path $repoRoot "scripts/deploy-backend.ps1")
$bootstrapScript = Read-RequiredFile (Join-Path $repoRoot "scripts/bootstrap-server-ssh-key.ps1")
$nginxConfig = Read-RequiredFile (Join-Path $repoRoot "deploy/nginx/catmap.conf")
$frontendEnv = Read-RequiredFile (Join-Path $repoRoot "frontend/src/config/app-env.ts")
$frontendEnvExample = Read-RequiredFile (Join-Path $repoRoot "frontend/.env.example")
$devDeployScript = Read-RequiredFile (Join-Path $repoRoot "scripts/deploy-backend-dev.ps1")
$devUnit = Read-RequiredFile (Join-Path $repoRoot "deploy/systemd/catmap-backend-dev.service")
$devNginx = Read-RequiredFile (Join-Path $repoRoot "deploy/nginx/catmap-dev.conf")
$devNginxBootstrap = Read-RequiredFile (Join-Path $repoRoot "deploy/nginx/catmap-dev-http-bootstrap.conf")
$devFrontendEnvExample = Read-RequiredFile (Join-Path $repoRoot "frontend/.env.development.example")
$devFrontendEnv = Read-RequiredFile (Join-Path $repoRoot "frontend/.env.development")
$frontendPackage = Read-RequiredFile (Join-Path $repoRoot "frontend/package.json")

Assert-NotContains `
    -Content $deployScript `
    -Needle "server_key.txt" `
    -Message "deploy-backend.ps1 must not reference the server password file."

Assert-Contains `
    -Content $deployScript `
    -Needle '[string] $ServerHost = "49.235.238.143"' `
    -Message "deploy-backend.ps1 must default to the current backend deployment host."

Assert-Contains `
    -Content $bootstrapScript `
    -Needle '[string] $ServerHost = "49.235.238.143"' `
    -Message "bootstrap-server-ssh-key.ps1 must default to the current backend deployment host."

Assert-NotContains `
    -Content $deployScript `
    -Needle '[string] $ServerHost = "203.0.113.10"' `
    -Message "deploy-backend.ps1 must not default to the old documentation placeholder host."

Assert-NotContains `
    -Content $bootstrapScript `
    -Needle '[string] $ServerHost = "203.0.113.10"' `
    -Message "bootstrap-server-ssh-key.ps1 must not default to the old documentation placeholder host."

Assert-Contains `
    -Content $deployScript `
    -Needle 'if [ -f "`$ENV_UPLOAD" ]; then' `
    -Message "deploy-backend.ps1 must update the remote .env when -EnvFile is provided."

Assert-Contains `
    -Content $deployScript `
    -Needle 'install -m 600 "`$ENV_UPLOAD" "`$DEPLOY_DIR/.env"' `
    -Message "deploy-backend.ps1 must install the uploaded env file into the backend deploy directory."

Assert-Contains `
    -Content $deployScript `
    -Needle 'CATMAP_WECHAT_CONTENT_SECURITY_MODE=enforced' `
    -Message "deploy-backend.ps1 must require production image content security."

Assert-Contains `
    -Content $deployScript `
    -Needle 'CATMAP_WECHAT_CONTENT_SECURITY_CALLBACK_TOKEN=' `
    -Message "deploy-backend.ps1 must require a content security callback token."

Assert-Contains `
    -Content $deployScript `
    -Needle "grep -Eq '^CATMAP_WECHAT_CONTENT_SECURITY_MODE=enforced" `
    -Message "deploy-backend.ps1 must verify the effective remote content security mode."

Assert-Contains `
    -Content $deployScript `
    -Needle 'unset callback_token' `
    -Message "deploy-backend.ps1 must clear the callback token shell variable after validation."

Assert-Contains `
    -Content $deployScript `
    -Needle '$env:CATMAP_WECHAT_CONTENT_SECURITY_MODE = "off"' `
    -Message "deploy-backend.ps1 must isolate ordinary local tests from production content security mode."

Assert-Contains `
    -Content $deployScript `
    -Needle 'Remove-Item Env:CATMAP_WECHAT_CONTENT_SECURITY_MODE' `
    -Message "deploy-backend.ps1 must restore an unset local content security mode after checks."

Assert-Before `
    -Content $deployScript `
    -EarlierNeedle 'if [ -f "`$ENV_UPLOAD" ]; then' `
    -LaterNeedle 'if [ ! -f "`$DEPLOY_DIR/.env" ]; then' `
    -Message "deploy-backend.ps1 must apply an uploaded env file before checking whether the remote .env already exists."

Assert-Contains `
    -Content $deployScript `
    -Needle '$healthUrl = "https://$Domain/api/v1/health"' `
    -Message "deploy-backend.ps1 must verify the HTTPS health endpoint for the configured domain."

Assert-Contains `
    -Content $nginxConfig `
    -Needle "server_name trmx.fun" `
    -Message "Nginx config must serve the production API domain."

Assert-Contains `
    -Content $nginxConfig `
    -Needle "listen 80 default_server;" `
    -Message "Nginx config must listen on HTTP for redirects."

Assert-Contains `
    -Content $nginxConfig `
    -Needle "return 301 https://" `
    -Message "Nginx config must redirect HTTP to HTTPS."

Assert-Contains `
    -Content $nginxConfig `
    -Needle "listen 443 ssl default_server;" `
    -Message "Nginx config must expose the HTTPS API on port 443."

Assert-Contains `
    -Content $nginxConfig `
    -Needle "/etc/letsencrypt/live/trmx.fun/fullchain.pem" `
    -Message "Nginx config must use the public CA full certificate chain."

Assert-Contains `
    -Content $nginxConfig `
    -Needle "proxy_pass http://127.0.0.1:8000/api/v1/" `
    -Message "Nginx config must proxy /api/v1/ to the local backend."

Assert-Contains `
    -Content $frontendEnv `
    -Needle 'apiBaseUrl: resolveApiBaseUrl(import.meta.env)' `
    -Message "Frontend API base URL must be resolved from the build environment."

Assert-Contains `
    -Content $frontendEnvExample `
    -Needle "VITE_API_BASE_URL=https://trmx.fun/api/v1" `
    -Message "Frontend env example must document the production HTTPS API endpoint."

Assert-Contains `
    -Content $devDeployScript `
    -Needle '$DeployDir = "/opt/catmap-dev/backend"' `
    -Message "Development deployment must use its isolated backend directory."

Assert-Contains `
    -Content $devDeployScript `
    -Needle '$ServiceName = "catmap-backend-dev"' `
    -Message "Development deployment must target the development systemd service."

Assert-Contains `
    -Content $devDeployScript `
    -Needle '$Domain = "dev-api.trmx.fun"' `
    -Message "Development deployment must target the development HTTPS domain."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "CATMAP_TENCENT_COS_ENV_PREFIX" `
    -Message "Development deployment must validate the object storage environment prefix."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "must define `$Name exactly once" `
    -Message "Development deployment must reject duplicate protected environment keys."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "catmap_dev" `
    -Message "Development deployment must validate the development database target."

Assert-Contains `
    -Content $devDeployScript `
    -Needle '$DevelopmentDatabaseRole = "catmap_dev_app"' `
    -Message "Development deployment must require the development database role."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "trap cleanup EXIT" `
    -Message "Development deployment must clean remote uploads when a deployment step fails."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "install -d -m 700" `
    -Message "Development deployment must place uploaded environment files in a root-only temporary directory."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "status --porcelain=v1 --untracked-files=all" `
    -Message "Development deployment must reject uncommitted deployment sources."

Assert-Contains `
    -Content $devDeployScript `
    -Needle 'EXTRACT_DIR="$DEPLOY_TMP/backend-new"' `
    -Message "Development deployment must extract code inside its protected per-deployment directory."

Assert-NotContains `
    -Content $devDeployScript `
    -Needle "/tmp/catmap-dev-backend-new" `
    -Message "Development deployment must not use a shared predictable extraction directory."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "Development Nginx upload references an unexpected runtime target." `
    -Message "Development deployment must revalidate the uploaded Nginx target before installation."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "Development systemd upload references a production runtime target." `
    -Message "Development deployment must revalidate the uploaded systemd target before installation."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "NGINX_LINK_TARGET_BACKUP" `
    -Message "Development deployment must restore a pre-existing Nginx sites-enabled link after a failed config test."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "useradd --system" `
    -Message "Development deployment must provision its dedicated unprivileged system user."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "chown -R catmap-dev:catmap-dev" `
    -Message "Development deployment must grant the development service user access only to its own deploy directory."

Assert-Contains `
    -Content $devDeployScript `
    -Needle "nginx -t" `
    -Message "Development deployment must validate Nginx before reloading it."

Assert-Contains `
    -Content $devDeployScript `
    -Needle 'https://$Domain/api/v1/health' `
    -Message "Development deployment must verify its HTTPS health endpoint."

Assert-Contains `
    -Content $devUnit `
    -Needle "WorkingDirectory=/opt/catmap-dev/backend" `
    -Message "Development systemd unit must use the isolated backend directory."

Assert-Contains `
    -Content $devUnit `
    -Needle "EnvironmentFile=/opt/catmap-dev/backend/.env" `
    -Message "Development systemd unit must use its own environment file."

Assert-Contains `
    -Content $devUnit `
    -Needle "User=catmap-dev" `
    -Message "Development systemd unit must run as its dedicated unprivileged user."

Assert-Contains `
    -Content $devUnit `
    -Needle "Group=catmap-dev" `
    -Message "Development systemd unit must use its dedicated unprivileged group."

Assert-NotContains `
    -Content $devUnit `
    -Needle "User=root" `
    -Message "Development systemd unit must not run application code as root."

Assert-Contains `
    -Content $devUnit `
    -Needle "--host 127.0.0.1 --port 8001" `
    -Message "Development systemd unit must keep port 8001 on loopback."

Assert-Contains `
    -Content $devNginxBootstrap `
    -Needle "server_name dev-api.trmx.fun" `
    -Message "Development certificate bootstrap must only serve the development domain."

Assert-Contains `
    -Content $devNginxBootstrap `
    -Needle "location ^~ /.well-known/acme-challenge/" `
    -Message "Development certificate bootstrap must serve ACME webroot challenges."

Assert-NotContains `
    -Content $devNginxBootstrap `
    -Needle "default_server" `
    -Message "Development certificate bootstrap must not become the default Nginx server."

Assert-Contains `
    -Content $devNginx `
    -Needle "server_name dev-api.trmx.fun" `
    -Message "Development Nginx config must serve the development domain."

Assert-Contains `
    -Content $devNginx `
    -Needle "location ^~ /.well-known/acme-challenge/" `
    -Message "Development Nginx config must retain the ACME webroot location."

Assert-Contains `
    -Content $devNginx `
    -Needle "proxy_pass http://127.0.0.1:8001/api/v1/" `
    -Message "Development Nginx config must proxy API requests to port 8001."

Assert-NotContains `
    -Content $devNginx `
    -Needle "default_server" `
    -Message "Development Nginx config must not become the default Nginx server."

Assert-Contains `
    -Content $devFrontendEnvExample `
    -Needle "VITE_API_BASE_URL=https://dev-api.trmx.fun/api/v1" `
    -Message "Development frontend env example must document the development HTTPS API endpoint."

Assert-Contains `
    -Content $devFrontendEnv `
    -Needle "VITE_API_BASE_URL=https://dev-api.trmx.fun/api/v1" `
    -Message "Development frontend build env must use the development HTTPS API endpoint."

Assert-Contains `
    -Content $frontendPackage `
    -Needle '"build:mp-weixin:dev": "uni build -p mp-weixin --mode development"' `
    -Message "Frontend package scripts must provide a dedicated development mini-program build command."

Assert-Contains `
    -Content $frontendPackage `
    -Needle '"build:mp-weixin": "uni build -p mp-weixin --mode development"' `
    -Message "The default mini-program build command must target the development API environment."

Assert-Contains `
    -Content $frontendPackage `
    -Needle '"build": "npm run build:mp-weixin:dev"' `
    -Message "The generic frontend build command must not bypass the development API environment."

Assert-Contains `
    -Content $frontendPackage `
    -Needle '"build:mp-weixin:prod": "uni build -p mp-weixin --mode production"' `
    -Message "Production mini-program builds must require the explicit production command."

Write-Host "Deployment contract checks passed."
