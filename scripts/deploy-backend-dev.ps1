param(
    [Parameter(Mandatory = $true)]
    [string] $ServerHost,
    [string] $ServerUser = "root",
    [int] $SshPort = 22,
    [string] $SshKeyPath = (Join-Path $env:USERPROFILE ".ssh\catmap_deploy_ed25519"),
    [Parameter(Mandatory = $true)]
    [string] $EnvFile,
    [switch] $SkipLocalChecks
)

$ErrorActionPreference = "Stop"

$DeployDir = "/opt/catmap-dev/backend"
$ServiceName = "catmap-backend-dev"
$Domain = "dev-api.trmx.fun"
$NginxConfigName = "catmap-dev.conf"
$SystemdUnitName = "catmap-backend-dev.service"
$DevelopmentDatabaseRole = "catmap_dev_app"
$ProductionDeployDir = "/opt/catmap/backend"
$ProductionServiceName = "catmap-backend"
$ProductionDomain = "trmx.fun"
$ProductionNginxConfigName = "catmap.conf"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$nginxConfig = Join-Path $repoRoot "deploy\nginx\$NginxConfigName"
$systemdService = Join-Path $repoRoot "deploy\systemd\$SystemdUnitName"
$healthUrl = "https://$Domain/api/v1/health"

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments,
        [string] $WorkingDirectory = ""
    )

    $previousLocation = Get-Location
    try {
        if ($WorkingDirectory) {
            Set-Location -LiteralPath $WorkingDirectory
        }
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$FilePath exited with code $LASTEXITCODE"
        }
    }
    finally {
        Set-Location $previousLocation
    }
}

function Invoke-Remote {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Command
    )

    Invoke-Native "ssh" @(
        "-i", $SshKeyPath,
        "-p", [string] $SshPort,
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        "$ServerUser@$ServerHost",
        $Command
    )
}

function Copy-ToRemote {
    param(
        [Parameter(Mandatory = $true)]
        [string] $LocalPath,
        [Parameter(Mandatory = $true)]
        [string] $RemotePath
    )

    Invoke-Native "scp" @(
        "-i", $SshKeyPath,
        "-P", [string] $SshPort,
        "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=accept-new",
        $LocalPath,
        "$ServerUser@$ServerHost`:$RemotePath"
    )
}

function Get-RequiredEnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Content,
        [Parameter(Mandatory = $true)]
        [string] $Name
    )

    $matches = [regex]::Matches($Content, "(?m)^$([regex]::Escape($Name))=(?<value>[^\r\n]*)\s*$")
    if ($matches.Count -ne 1) {
        throw "Development EnvFile must define $Name exactly once."
    }

    $value = $matches[0].Groups['value'].Value.Trim()
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Development EnvFile must define a non-empty $Name value."
    }

    return $value
}

if (
    $DeployDir -ne "/opt/catmap-dev/backend" -or
    $ServiceName -ne "catmap-backend-dev" -or
    $Domain -ne "dev-api.trmx.fun" -or
    $NginxConfigName -ne "catmap-dev.conf" -or
    $SystemdUnitName -ne "catmap-backend-dev.service"
) {
    throw "Development deployment targets are immutable."
}

if (
    $DeployDir -eq $ProductionDeployDir -or
    $ServiceName -eq $ProductionServiceName -or
    $Domain -eq $ProductionDomain -or
    $NginxConfigName -eq $ProductionNginxConfigName
) {
    throw "Development deployment must never target production resources."
}

if (-not (Test-Path -LiteralPath $backendDir)) {
    throw "Backend directory not found: $backendDir"
}
if (-not (Test-Path -LiteralPath $nginxConfig)) {
    throw "Development Nginx config not found: $nginxConfig"
}
if (-not (Test-Path -LiteralPath $systemdService)) {
    throw "Development systemd service not found: $systemdService"
}

$nginxContent = Get-Content -LiteralPath $nginxConfig -Raw -Encoding UTF8
$serverNameMatches = [regex]::Matches(
    $nginxContent,
    "(?m)^\s*server_name\s+(?<value>[^;]+);\s*`r?$"
)
$unexpectedServerNames = @(
    $serverNameMatches | Where-Object { $_.Groups['value'].Value.Trim() -ne $Domain }
)
if ($serverNameMatches.Count -ne 2 -or $unexpectedServerNames.Count -gt 0) {
    throw "Development Nginx config must contain only the two expected $Domain server_name entries."
}

$proxyPassMatches = [regex]::Matches(
    $nginxContent,
    "(?m)^\s*proxy_pass\s+(?<value>[^;]+);\s*`r?$"
)
$unexpectedProxyTargets = @(
    $proxyPassMatches | Where-Object {
        $_.Groups['value'].Value.Trim() -notmatch '^http://127\.0\.0\.1:8001(?:/|$)'
    }
)
if ($proxyPassMatches.Count -eq 0 -or $unexpectedProxyTargets.Count -gt 0) {
    throw "Development Nginx config must proxy only to the loopback development port 8001."
}
if ($nginxContent -match '(?m)\bdefault_server\b') {
    throw "Development Nginx config must not become the default server."
}

$systemdContent = Get-Content -LiteralPath $systemdService -Raw -Encoding UTF8
$requiredSystemdLines = @(
    "User=catmap-dev",
    "Group=catmap-dev",
    "WorkingDirectory=/opt/catmap-dev/backend",
    "EnvironmentFile=/opt/catmap-dev/backend/.env",
    "ExecStart=/opt/catmap-dev/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001"
)
foreach ($requiredLine in $requiredSystemdLines) {
    if ($systemdContent -notmatch "(?m)^$([regex]::Escape($requiredLine))`r?$") {
        throw "Development systemd template is missing a required isolated runtime setting."
    }
}
if (
    $systemdContent.Contains($ProductionDeployDir) -or
    $systemdContent -match '(?m)^User=root\s*$' -or
    $systemdContent.Contains('--port 8000')
) {
    throw "Development systemd template references a production runtime target."
}

$deploymentSourcePaths = @(
    "backend",
    "deploy/nginx/$NginxConfigName",
    "deploy/systemd/$SystemdUnitName",
    "scripts/deploy-backend-dev.ps1"
)
$sourceStatus = & git -C $repoRoot status --porcelain=v1 --untracked-files=all -- @deploymentSourcePaths
if ($LASTEXITCODE -ne 0) {
    throw "Could not verify the development deployment source baseline."
}
if ($sourceStatus) {
    throw "Development deployment requires committed backend, template, and deployment-script sources."
}

if (-not (Test-Path -LiteralPath $SshKeyPath)) {
    throw "SSH key not found: $SshKeyPath. Run scripts/bootstrap-server-ssh-key.ps1 first."
}
if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Development EnvFile not found: $EnvFile"
}

$envContent = Get-Content -LiteralPath $EnvFile -Raw -Encoding UTF8
$databaseUrl = Get-RequiredEnvValue -Content $envContent -Name "CATMAP_DATABASE_URL"
if ($databaseUrl -notmatch '/catmap_dev(?:\?|$)') {
    throw "Development EnvFile must target the catmap_dev database."
}
if ($databaseUrl -notmatch "^[a-z0-9+]+://$([regex]::Escape($DevelopmentDatabaseRole))(?::[^@]*)?@") {
    throw "Development EnvFile must use the $DevelopmentDatabaseRole database role."
}

$cosEnvPrefix = Get-RequiredEnvValue -Content $envContent -Name "CATMAP_TENCENT_COS_ENV_PREFIX"
if ($cosEnvPrefix -ne "dev") {
    throw "Development EnvFile must use CATMAP_TENCENT_COS_ENV_PREFIX=dev."
}

$insecureDevelopmentSecrets = @(
    "dev-only-change-me-with-at-least-32-bytes",
    "dev-captcha-secret-change-me",
    "replace-with-at-least-32-random-bytes",
    "replace-with-another-32-byte-secret"
)
foreach ($secretName in @("CATMAP_JWT_SECRET_KEY", "CATMAP_CAPTCHA_SECRET_KEY")) {
    $secretValue = Get-RequiredEnvValue -Content $envContent -Name $secretName
    if ($secretValue.Length -lt 32 -or $insecureDevelopmentSecrets -contains $secretValue) {
        throw "Development EnvFile must use a dedicated random $secretName value."
    }
}

$contentSecurityMode = Get-RequiredEnvValue `
    -Content $envContent `
    -Name "CATMAP_WECHAT_CONTENT_SECURITY_MODE"
if ($contentSecurityMode -ne "off") {
    throw "Development EnvFile must use CATMAP_WECHAT_CONTENT_SECURITY_MODE=off."
}

if (-not $SkipLocalChecks) {
    $previousContentSecurityMode = [Environment]::GetEnvironmentVariable(
        "CATMAP_WECHAT_CONTENT_SECURITY_MODE",
        "Process"
    )
    try {
        $env:CATMAP_WECHAT_CONTENT_SECURITY_MODE = "off"
        Invoke-Native "py" @("-3.11", "-m", "pytest", "-q") $backendDir
        Invoke-Native "py" @("-3.11", "-m", "ruff", "check", ".") $backendDir
    }
    finally {
        if ($null -eq $previousContentSecurityMode) {
            Remove-Item Env:CATMAP_WECHAT_CONTENT_SECURITY_MODE -ErrorAction SilentlyContinue
        }
        else {
            $env:CATMAP_WECHAT_CONTENT_SECURITY_MODE = $previousContentSecurityMode
        }
    }
}

$deploymentId = [Guid]::NewGuid().ToString("N")
$tempDir = Join-Path ([IO.Path]::GetTempPath()) "catmap-dev-deploy-$deploymentId"
New-Item -ItemType Directory -Path $tempDir | Out-Null
$archivePath = Join-Path $tempDir "catmap-dev-backend.tar"
$remoteScriptPath = Join-Path $tempDir "catmap-dev-remote-deploy.sh"
$remoteTempDir = "/opt/catmap-dev/.deploy-$deploymentId"

try {
    Invoke-Native "tar" @(
        "--exclude=.env",
        "--exclude=.venv",
        "--exclude=uploads",
        "--exclude=__pycache__",
        "--exclude=.pytest_cache",
        "--exclude=.ruff_cache",
        "-cf", $archivePath,
        "-C", $backendDir,
        "."
    )

    $remoteScript = @'
#!/usr/bin/env bash
set -euo pipefail

DEPLOY_DIR='__DEPLOY_DIR__'
SERVICE_NAME='__SERVICE_NAME__'
NGINX_CONFIG_NAME='__NGINX_CONFIG_NAME__'
DEVELOPMENT_DATABASE_ROLE='__DATABASE_ROLE__'
DEPLOY_TMP='__REMOTE_TEMP_DIR__'
ARCHIVE="$DEPLOY_TMP/backend.tar"
ENV_UPLOAD="$DEPLOY_TMP/backend.env"
NGINX_UPLOAD="$DEPLOY_TMP/catmap-dev.conf"
SERVICE_UPLOAD="$DEPLOY_TMP/catmap-backend-dev.service"
EXTRACT_DIR="$DEPLOY_TMP/backend-new"

EXPECTED_DEPLOY_DIR='/opt/catmap-dev/backend'
EXPECTED_SERVICE_NAME='catmap-backend-dev'
EXPECTED_NGINX_CONFIG_NAME='catmap-dev.conf'

if [ "$DEPLOY_DIR" != "$EXPECTED_DEPLOY_DIR" ] || \
   [ "$SERVICE_NAME" != "$EXPECTED_SERVICE_NAME" ] || \
   [ "$NGINX_CONFIG_NAME" != "$EXPECTED_NGINX_CONFIG_NAME" ]; then
    echo 'Refusing a deployment target outside the development slot.' >&2
    exit 1
fi

if [ "$DEPLOY_DIR" = '/opt/catmap/backend' ] || [ "$SERVICE_NAME" = 'catmap-backend' ]; then
    echo 'Refusing to target production resources.' >&2
    exit 1
fi

cleanup() {
    rm -rf "$DEPLOY_TMP"
}
trap cleanup EXIT

install -d -m 700 "$DEPLOY_TMP"

command -v nginx >/dev/null 2>&1 || { echo 'nginx is not installed.' >&2; exit 1; }
command -v python3.11 >/dev/null 2>&1 || { echo 'python3.11 is not installed.' >&2; exit 1; }

if [ ! -f "$ENV_UPLOAD" ]; then
    echo 'Development environment file upload is missing.' >&2
    exit 1
fi

if [ "$(grep -Ec '^CATMAP_DATABASE_URL=' "$ENV_UPLOAD")" -ne 1 ]; then
    echo 'Development database URL must be defined exactly once.' >&2
    exit 1
fi

if ! grep -Eq '^CATMAP_DATABASE_URL=.*/catmap_dev([?[:space:]]|$)' "$ENV_UPLOAD"; then
    echo 'Development environment file must target catmap_dev.' >&2
    exit 1
fi

if ! grep -Eq "^CATMAP_DATABASE_URL=[a-zA-Z0-9+]+://${DEVELOPMENT_DATABASE_ROLE}(:[^@[:space:]]*)?@" "$ENV_UPLOAD"; then
    echo 'Development environment file must use the development database role.' >&2
    exit 1
fi

if [ "$(grep -Ec '^CATMAP_TENCENT_COS_ENV_PREFIX=' "$ENV_UPLOAD")" -ne 1 ]; then
    echo 'Development object storage prefix must be defined exactly once.' >&2
    exit 1
fi

if ! grep -Eq '^CATMAP_TENCENT_COS_ENV_PREFIX=dev[[:space:]]*$' "$ENV_UPLOAD"; then
    echo 'Development object storage prefix must be dev.' >&2
    exit 1
fi

for secret_name in CATMAP_JWT_SECRET_KEY CATMAP_CAPTCHA_SECRET_KEY; do
    if [ "$(grep -Ec "^${secret_name}=" "$ENV_UPLOAD")" -ne 1 ]; then
        echo "Development ${secret_name} must be defined exactly once." >&2
        exit 1
    fi
    secret_value="$(sed -n "s/^${secret_name}=//p" "$ENV_UPLOAD" | tr -d '\r')"
    if [ "${#secret_value}" -lt 32 ] || \
       [ "$secret_value" = 'dev-only-change-me-with-at-least-32-bytes' ] || \
       [ "$secret_value" = 'dev-captcha-secret-change-me' ] || \
       [ "$secret_value" = 'replace-with-at-least-32-random-bytes' ] || \
       [ "$secret_value" = 'replace-with-another-32-byte-secret' ]; then
        echo "Development ${secret_name} must use a dedicated random value." >&2
        unset secret_value
        exit 1
    fi
    unset secret_value
done

if [ "$(grep -Ec '^CATMAP_WECHAT_CONTENT_SECURITY_MODE=' "$ENV_UPLOAD")" -ne 1 ] || \
   ! grep -Eq '^CATMAP_WECHAT_CONTENT_SECURITY_MODE=off[[:space:]]*$' "$ENV_UPLOAD"; then
    echo 'Development content security mode must be explicitly off.' >&2
    exit 1
fi

if [ "$(grep -Ec '^[[:space:]]*server_name[[:space:]]+dev-api\.trmx\.fun;[[:space:]]*$' "$NGINX_UPLOAD")" -ne 2 ] || \
   grep -Eq 'default_server|127\.0\.0\.1:8000|/opt/catmap/backend' "$NGINX_UPLOAD"; then
    echo 'Development Nginx upload references an unexpected runtime target.' >&2
    exit 1
fi

if grep -E '^[[:space:]]*server_name[[:space:]]+' "$NGINX_UPLOAD" | \
   grep -Evq '^[[:space:]]*server_name[[:space:]]+dev-api\.trmx\.fun;[[:space:]]*$'; then
    echo 'Development Nginx upload contains a non-development server name.' >&2
    exit 1
fi

if ! grep -Eq '^[[:space:]]*proxy_pass[[:space:]]+http://127\.0\.0\.1:8001(/|;)' "$NGINX_UPLOAD" || \
   grep -E '^[[:space:]]*proxy_pass[[:space:]]+' "$NGINX_UPLOAD" | \
   grep -Evq '^[[:space:]]*proxy_pass[[:space:]]+http://127\.0\.0\.1:8001(/[^;]*)?;[[:space:]]*$'; then
    echo 'Development Nginx upload must proxy only to port 8001.' >&2
    exit 1
fi

for required_setting in \
    'User=catmap-dev' \
    'Group=catmap-dev' \
    'WorkingDirectory=/opt/catmap-dev/backend' \
    'EnvironmentFile=/opt/catmap-dev/backend/.env' \
    'ExecStart=/opt/catmap-dev/backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001'; do
    if ! grep -Fqx "$required_setting" "$SERVICE_UPLOAD"; then
        echo 'Development systemd upload is missing an isolated runtime setting.' >&2
        exit 1
    fi
done

if grep -Eq '/opt/catmap/backend|^User=root[[:space:]]*$|--port 8000([[:space:]]|$)' "$SERVICE_UPLOAD"; then
    echo 'Development systemd upload references a production runtime target.' >&2
    exit 1
fi

if [ -d /etc/nginx/sites-available ]; then
    NGINX_DIR='/etc/nginx/sites-available'
    NGINX_LINK_DIR='/etc/nginx/sites-enabled'
elif [ -d /www/server/panel/vhost/nginx ]; then
    NGINX_DIR='/www/server/panel/vhost/nginx'
    NGINX_LINK_DIR=''
elif [ -d /www/server/nginx/conf/vhost ]; then
    NGINX_DIR='/www/server/nginx/conf/vhost'
    NGINX_LINK_DIR=''
elif [ -d /etc/nginx/conf.d ]; then
    NGINX_DIR='/etc/nginx/conf.d'
    NGINX_LINK_DIR=''
else
    echo 'No supported Nginx vhost directory exists.' >&2
    exit 1
fi

NGINX_TARGET="$NGINX_DIR/$NGINX_CONFIG_NAME"
NGINX_BACKUP="${NGINX_TARGET}.catmap-dev-backup"
NGINX_LINK_PATH=''
NGINX_LINK_TARGET_BACKUP=''
if [ -n "$NGINX_LINK_DIR" ]; then
    NGINX_LINK_PATH="$NGINX_LINK_DIR/$NGINX_CONFIG_NAME"
    if [ -L "$NGINX_LINK_PATH" ]; then
        NGINX_LINK_TARGET_BACKUP="$(readlink "$NGINX_LINK_PATH")"
    elif [ -e "$NGINX_LINK_PATH" ]; then
        echo 'Development Nginx sites-enabled target is not a symbolic link.' >&2
        exit 1
    fi
fi

if [ -f "$NGINX_TARGET" ]; then
    cp -a "$NGINX_TARGET" "$NGINX_BACKUP"
else
    rm -f "$NGINX_BACKUP"
fi

restore_nginx_target() {
    if [ -f "$NGINX_BACKUP" ]; then
        mv -f "$NGINX_BACKUP" "$NGINX_TARGET"
    else
        rm -f "$NGINX_TARGET"
    fi

    if [ -n "$NGINX_LINK_PATH" ]; then
        if [ -n "$NGINX_LINK_TARGET_BACKUP" ]; then
            ln -sfn "$NGINX_LINK_TARGET_BACKUP" "$NGINX_LINK_PATH"
        else
            rm -f "$NGINX_LINK_PATH"
        fi
    fi
}

install -d -m 700 "$EXTRACT_DIR"
tar -xf "$ARCHIVE" -C "$EXTRACT_DIR"

mkdir -p "$(dirname "$DEPLOY_DIR")" "$DEPLOY_DIR"
find "$DEPLOY_DIR" -mindepth 1 -maxdepth 1 \
    ! -name '.env' \
    ! -name '.venv' \
    ! -name 'uploads' \
    -exec rm -rf {} +
cp -a "$EXTRACT_DIR"/. "$DEPLOY_DIR"/
install -m 600 "$ENV_UPLOAD" "$DEPLOY_DIR/.env"

cd "$DEPLOY_DIR"
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/python -m alembic upgrade head

if ! id -u catmap-dev >/dev/null 2>&1; then
    useradd --system --home-dir /opt/catmap-dev --create-home --shell /sbin/nologin catmap-dev
fi
chown -R catmap-dev:catmap-dev "$DEPLOY_DIR"

install -m 644 "$SERVICE_UPLOAD" "/etc/systemd/system/$SERVICE_NAME.service"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
systemctl is-active --quiet "$SERVICE_NAME"

install -m 644 "$NGINX_UPLOAD" "$NGINX_TARGET"
if [ -n "$NGINX_LINK_DIR" ]; then
    ln -sfn "$NGINX_TARGET" "$NGINX_LINK_DIR/$NGINX_CONFIG_NAME"
fi

if ! nginx -t; then
    restore_nginx_target
    nginx -t || true
    exit 1
fi

if ! systemctl is-active --quiet nginx; then
    restore_nginx_target
    echo 'nginx is not active.' >&2
    exit 1
fi

if ! systemctl reload nginx; then
    restore_nginx_target
    echo 'nginx reload failed; restored the previous development vhost state.' >&2
    exit 1
fi

rm -f "$NGINX_BACKUP"
'@
    $remoteScript = $remoteScript.
        Replace('__DEPLOY_DIR__', $DeployDir).
        Replace('__SERVICE_NAME__', $ServiceName).
        Replace('__NGINX_CONFIG_NAME__', $NginxConfigName).
        Replace('__DATABASE_ROLE__', $DevelopmentDatabaseRole).
        Replace('__REMOTE_TEMP_DIR__', $remoteTempDir)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($remoteScriptPath, $remoteScript, $utf8NoBom)

    Invoke-Remote "install -d -m 700 '$remoteTempDir'"
    Copy-ToRemote $archivePath "$remoteTempDir/backend.tar"
    Copy-ToRemote $remoteScriptPath "$remoteTempDir/remote-deploy.sh"
    Copy-ToRemote $nginxConfig "$remoteTempDir/catmap-dev.conf"
    Copy-ToRemote $systemdService "$remoteTempDir/catmap-backend-dev.service"
    Copy-ToRemote $EnvFile "$remoteTempDir/backend.env"

    Invoke-Remote "bash '$remoteTempDir/remote-deploy.sh'"

    $healthBody = ""
    $healthStatusCode = ""
    $healthOutput = Join-Path $tempDir "health-response.json"
    for ($attempt = 1; $attempt -le 8; $attempt++) {
        $healthStatusCode = & curl.exe --noproxy "*" --max-time 10 -sS -o $healthOutput -w "%{http_code}" $healthUrl
        $curlExitCode = $LASTEXITCODE
        $healthBody = if (Test-Path -LiteralPath $healthOutput) {
            (Get-Content -LiteralPath $healthOutput -Raw -Encoding UTF8).Trim()
        }
        else {
            ""
        }

        if ($curlExitCode -eq 0 -and $healthStatusCode -eq "200" -and $healthBody.Contains('"code":0')) {
            break
        }

        if ($attempt -lt 8) {
            Start-Sleep -Seconds 2
        }
    }

    if ($healthStatusCode -ne "200" -or -not $healthBody.Contains('"code":0')) {
        throw "Development health check failed. HTTP $healthStatusCode. Body: $healthBody"
    }

    Write-Host "Development backend deployed and verified: $healthUrl"
}
finally {
    try {
        Invoke-Remote "rm -rf '$remoteTempDir'"
    }
    catch {
        Write-Warning "Could not remove the protected development deployment temporary directory."
    }
    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
