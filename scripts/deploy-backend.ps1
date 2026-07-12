param(
    [string] $ServerHost = "49.235.238.143",
    [string] $ServerUser = "root",
    [int] $SshPort = 22,
    [string] $Domain = "trmx.fun",
    [string] $DeployDir = "/opt/catmap/backend",
    [string] $ServiceName = "catmap-backend",
    [string] $SshKeyPath = (Join-Path $env:USERPROFILE ".ssh\catmap_deploy_ed25519"),
    [string] $EnvFile = "",
    [string] $CertificateFile = "",
    [string] $PrivateKeyFile = "",
    [switch] $SkipLocalChecks
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"
$nginxConfig = Join-Path $repoRoot "deploy\nginx\catmap.conf"
$systemdService = Join-Path $repoRoot "deploy\systemd\catmap-backend.service"
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

if (-not (Test-Path -LiteralPath $backendDir)) {
    throw "Backend directory not found: $backendDir"
}
if (-not (Test-Path -LiteralPath $nginxConfig)) {
    throw "Nginx config not found: $nginxConfig"
}
if (-not (Test-Path -LiteralPath $systemdService)) {
    throw "systemd service not found: $systemdService"
}
if (-not (Test-Path -LiteralPath $SshKeyPath)) {
    throw "SSH key not found: $SshKeyPath. Run scripts/bootstrap-server-ssh-key.ps1 first."
}

if ($EnvFile) {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        throw "Env file not found: $EnvFile"
    }
    $envContent = Get-Content -LiteralPath $EnvFile -Raw -Encoding UTF8
    if ($envContent -notmatch '(?m)^CATMAP_WECHAT_CONTENT_SECURITY_MODE=enforced\s*$') {
        throw "Production image uploads require CATMAP_WECHAT_CONTENT_SECURITY_MODE=enforced."
    }
    $callbackTokenMatch = [regex]::Match(
        $envContent,
        '(?m)^CATMAP_WECHAT_CONTENT_SECURITY_CALLBACK_TOKEN=(?<value>[^\r\n]+)\s*$'
    )
    if (
        -not $callbackTokenMatch.Success -or
        [string]::IsNullOrWhiteSpace($callbackTokenMatch.Groups['value'].Value) -or
        $callbackTokenMatch.Groups['value'].Value.StartsWith('replace-with-')
    ) {
        throw "Production image uploads require a non-placeholder content security callback token."
    }
}

if (-not $SkipLocalChecks) {
    Invoke-Native "py" @("-3.11", "-m", "pytest", "-q") $backendDir
    Invoke-Native "py" @("-3.11", "-m", "ruff", "check", ".") $backendDir
}

$tempDir = Join-Path ([IO.Path]::GetTempPath()) ("catmap-deploy-" + (Get-Date -Format "yyyyMMddHHmmss"))
New-Item -ItemType Directory -Path $tempDir | Out-Null
$archivePath = Join-Path $tempDir "catmap-backend.tar"
$remoteScriptPath = Join-Path $tempDir "remote-deploy.sh"

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

    $remoteScript = @"
#!/usr/bin/env bash
set -euo pipefail

DOMAIN='$Domain'
DEPLOY_DIR='$DeployDir'
SERVICE_NAME='$ServiceName'
ARCHIVE='/tmp/catmap-backend.tar'
ENV_UPLOAD='/tmp/catmap-backend.env'
NGINX_UPLOAD='/tmp/catmap.conf'
SERVICE_UPLOAD='/tmp/catmap-backend.service'
CERT_UPLOAD='/tmp/catmap-origin.pem'
KEY_UPLOAD='/tmp/catmap-origin.key'

export DEBIAN_FRONTEND=noninteractive

if command -v apt-get >/dev/null 2>&1; then
    missing_packages=()
    command -v nginx >/dev/null 2>&1 || missing_packages+=(nginx)
    command -v python3.11 >/dev/null 2>&1 || missing_packages+=(python3.11 python3.11-venv)
    command -v gcc >/dev/null 2>&1 || missing_packages+=(build-essential)
    if [ "`${#missing_packages[@]}" -gt 0 ]; then
        apt-get update
        apt-get install -y "`${missing_packages[@]}"
    fi
elif command -v dnf >/dev/null 2>&1; then
    missing_packages=()
    command -v nginx >/dev/null 2>&1 || missing_packages+=(nginx)
    command -v python3.11 >/dev/null 2>&1 || missing_packages+=(python3)
    command -v gcc >/dev/null 2>&1 || missing_packages+=(gcc)
    if [ "`${#missing_packages[@]}" -gt 0 ]; then
        dnf install -y "`${missing_packages[@]}"
    fi
elif command -v yum >/dev/null 2>&1; then
    missing_packages=()
    command -v nginx >/dev/null 2>&1 || missing_packages+=(nginx)
    command -v python3.11 >/dev/null 2>&1 || missing_packages+=(python3)
    command -v gcc >/dev/null 2>&1 || missing_packages+=(gcc)
    if [ "`${#missing_packages[@]}" -gt 0 ]; then
        yum install -y "`${missing_packages[@]}"
    fi
fi

command -v nginx >/dev/null 2>&1 || { echo 'nginx is not installed.' >&2; exit 1; }
command -v python3.11 >/dev/null 2>&1 || { echo 'python3.11 is not installed.' >&2; exit 1; }

mkdir -p "`$(dirname "`$DEPLOY_DIR")" "`$DEPLOY_DIR" /tmp/catmap-backend-new

if [ -f "`$CERT_UPLOAD" ] && [ -f "`$KEY_UPLOAD" ]; then
    mkdir -p /etc/letsencrypt/live/"`$DOMAIN"
    install -m 644 "`$CERT_UPLOAD" /etc/letsencrypt/live/"`$DOMAIN"/fullchain.pem
    install -m 600 "`$KEY_UPLOAD" /etc/letsencrypt/live/"`$DOMAIN"/privkey.pem
fi

rm -rf /tmp/catmap-backend-new
mkdir -p /tmp/catmap-backend-new
tar -xf "`$ARCHIVE" -C /tmp/catmap-backend-new

mkdir -p "`$DEPLOY_DIR"
find "`$DEPLOY_DIR" -mindepth 1 -maxdepth 1 \
    ! -name '.env' \
    ! -name '.venv' \
    ! -name 'uploads' \
    -exec rm -rf {} +
cp -a /tmp/catmap-backend-new/. "`$DEPLOY_DIR"/

if [ -f "`$ENV_UPLOAD" ]; then
    install -m 600 "`$ENV_UPLOAD" "`$DEPLOY_DIR/.env"
elif [ ! -f "`$DEPLOY_DIR/.env" ]; then
    echo "`$DEPLOY_DIR/.env is missing. Pass -EnvFile on the first deploy." >&2
    exit 1
fi

grep -Eq '^CATMAP_WECHAT_CONTENT_SECURITY_MODE=enforced[[:space:]]*$' "`$DEPLOY_DIR/.env" || {
    echo 'Production image content security must be enforced.' >&2
    exit 1
}
callback_token="`$(sed -n 's/^CATMAP_WECHAT_CONTENT_SECURITY_CALLBACK_TOKEN=//p' "`$DEPLOY_DIR/.env" | tail -n 1)"
if [ -z "`$callback_token" ] || [[ "`$callback_token" == replace-with-* ]]; then
    echo 'A non-placeholder image content security callback token is required.' >&2
    exit 1
fi
unset callback_token

cd "`$DEPLOY_DIR"
python3.11 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/python -m alembic upgrade head

install -m 644 "`$SERVICE_UPLOAD" /etc/systemd/system/"`$SERVICE_NAME".service
systemctl daemon-reload
systemctl enable "`$SERVICE_NAME"
systemctl restart "`$SERVICE_NAME"
systemctl is-active --quiet "`$SERVICE_NAME"

if [ -d /etc/nginx/sites-available ]; then
    install -m 644 "`$NGINX_UPLOAD" /etc/nginx/sites-available/catmap.conf
    ln -sfn /etc/nginx/sites-available/catmap.conf /etc/nginx/sites-enabled/catmap.conf
    rm -f /etc/nginx/sites-enabled/default
elif [ -d /www/server/panel/vhost/nginx ]; then
    install -m 644 "`$NGINX_UPLOAD" /www/server/panel/vhost/nginx/catmap.conf
elif [ -d /www/server/nginx/conf/vhost ]; then
    install -m 644 "`$NGINX_UPLOAD" /www/server/nginx/conf/vhost/catmap.conf
else
    mkdir -p /etc/nginx/conf.d
    install -m 644 "`$NGINX_UPLOAD" /etc/nginx/conf.d/catmap.conf
fi

nginx -t
systemctl enable nginx
if systemctl is-active --quiet nginx; then
    systemctl reload nginx
else
    systemctl restart nginx
fi

rm -f "`$ARCHIVE" "`$ENV_UPLOAD" "`$NGINX_UPLOAD" "`$SERVICE_UPLOAD" "`$CERT_UPLOAD" "`$KEY_UPLOAD"
"@
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($remoteScriptPath, $remoteScript, $utf8NoBom)

    Copy-ToRemote $archivePath "/tmp/catmap-backend.tar"
    Copy-ToRemote $remoteScriptPath "/tmp/catmap-remote-deploy.sh"
    Copy-ToRemote $nginxConfig "/tmp/catmap.conf"
    Copy-ToRemote $systemdService "/tmp/catmap-backend.service"

    if ($EnvFile) {
        Copy-ToRemote $EnvFile "/tmp/catmap-backend.env"
    }

    if ($CertificateFile -or $PrivateKeyFile) {
        if (-not $CertificateFile -or -not $PrivateKeyFile) {
            throw "CertificateFile and PrivateKeyFile must be provided together."
        }
        if (-not (Test-Path -LiteralPath $CertificateFile)) {
            throw "Certificate file not found: $CertificateFile"
        }
        if (-not (Test-Path -LiteralPath $PrivateKeyFile)) {
            throw "Private key file not found: $PrivateKeyFile"
        }
        Copy-ToRemote $CertificateFile "/tmp/catmap-origin.pem"
        Copy-ToRemote $PrivateKeyFile "/tmp/catmap-origin.key"
    }

    Invoke-Remote "bash /tmp/catmap-remote-deploy.sh"

    $healthBody = ""
    $healthStatusCode = ""
    $healthOutput = Join-Path $tempDir "health-response.json"
    for ($attempt = 1; $attempt -le 8; $attempt++) {
        $healthStatusCode = & curl.exe --noproxy "*" --max-time 10 -sS -o $healthOutput -w "%{http_code}" $healthUrl
        $curlExitCode = $LASTEXITCODE
        $healthBody = if (Test-Path -LiteralPath $healthOutput) {
            (Get-Content -LiteralPath $healthOutput -Raw -Encoding UTF8).Trim()
        } else {
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
        throw "Health check failed. HTTP $healthStatusCode. Body: $healthBody"
    }

    Write-Host $healthBody
    Write-Host ""
    Write-Host "Backend deployed and verified: $healthUrl"
}
finally {
    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
