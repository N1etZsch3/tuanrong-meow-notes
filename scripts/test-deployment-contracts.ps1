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

$deployScript = Read-RequiredFile (Join-Path $repoRoot "scripts/deploy-backend.ps1")
$nginxConfig = Read-RequiredFile (Join-Path $repoRoot "deploy/nginx/catmap.conf")
$frontendEnv = Read-RequiredFile (Join-Path $repoRoot "frontend/src/config/app-env.ts")

Assert-NotContains `
    -Content $deployScript `
    -Needle "server_key.txt" `
    -Message "deploy-backend.ps1 must not reference the server password file."

Assert-Contains `
    -Content $deployScript `
    -Needle "http://203.0.113.10/api/v1/health" `
    -Message "deploy-backend.ps1 must verify the temporary HTTP IP health endpoint."

Assert-Contains `
    -Content $nginxConfig `
    -Needle "listen 80 default_server;" `
    -Message "Nginx config must expose the HTTP API on port 80."

Assert-NotContains `
    -Content $nginxConfig `
    -Needle "return 301 https://" `
    -Message "Nginx config must not redirect HTTP to HTTPS for temporary IP access."

Assert-Contains `
    -Content $nginxConfig `
    -Needle "proxy_pass http://127.0.0.1:8000/api/v1/" `
    -Message "Nginx config must proxy /api/v1/ to the local backend."

Assert-Contains `
    -Content $frontendEnv `
    -Needle 'const DEFAULT_API_BASE_URL = "http://203.0.113.10/api/v1";' `
    -Message "Frontend default API base URL must point to the temporary HTTP IP endpoint."

Write-Host "Deployment contract checks passed."
