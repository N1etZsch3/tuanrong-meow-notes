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

Write-Host "Deployment contract checks passed."
