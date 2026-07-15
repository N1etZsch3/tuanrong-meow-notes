param(
    [Parameter(Mandatory = $true)]
    [string] $ServerHost,
    [string] $ServerUser = "root",
    [int] $SshPort = 22,
    [string] $SshKeyPath = (Join-Path $env:USERPROFILE ".ssh\catmap_deploy_ed25519"),
    [Parameter(Mandatory = $true)]
    [ValidateSet("clone-catmap-to-catmap_dev")]
    [string] $ConfirmationToken
)

$ErrorActionPreference = "Stop"

$ProductionDatabase = "catmap"
$DevelopmentDatabase = "catmap_dev"
$ProductionDatabaseRole = "catmap_app"
$DevelopmentDatabaseRole = "catmap_dev_app"
$DatabaseContainer = "catmap-postgis"
$ProductionService = "catmap-backend"
$DevelopmentService = "catmap-backend-dev"

$repoRoot = Split-Path -Parent $PSScriptRoot
$scriptPath = Join-Path $repoRoot "scripts\refresh-dev-database.ps1"

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FilePath exited with code $LASTEXITCODE"
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

if (
    $ProductionDatabase -ne "catmap" -or
    $DevelopmentDatabase -ne "catmap_dev" -or
    $ProductionDatabaseRole -ne "catmap_app" -or
    $DevelopmentDatabaseRole -ne "catmap_dev_app" -or
    $DatabaseContainer -ne "catmap-postgis" -or
    $ProductionService -ne "catmap-backend" -or
    $DevelopmentService -ne "catmap-backend-dev"
) {
    throw "Database refresh targets are immutable."
}
if ($ProductionDatabase -eq $DevelopmentDatabase) {
    throw "Production and development database targets must be different."
}
if (-not (Test-Path -LiteralPath $SshKeyPath)) {
    throw "SSH key not found: $SshKeyPath"
}

$sourceStatus = & git -C $repoRoot status --porcelain=v1 -- $scriptPath
if ($LASTEXITCODE -ne 0 -or $sourceStatus) {
    throw "Development database refresh requires a committed refresh script."
}

$refreshId = [Guid]::NewGuid().ToString("N").Substring(0, 12)
$backupStamp = Get-Date -Format "yyyyMMddHHmmss"
$tempDir = Join-Path ([IO.Path]::GetTempPath()) "catmap-dev-db-refresh-$refreshId"
$remoteScriptPath = Join-Path $tempDir "refresh-dev-database.sh"
$remoteTempDir = "/opt/catmap-dev/.db-refresh-$refreshId"

New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    $remoteScript = @'
#!/usr/bin/env bash
set -euo pipefail

PRODUCTION_DATABASE='__PRODUCTION_DATABASE__'
DEVELOPMENT_DATABASE='__DEVELOPMENT_DATABASE__'
PRODUCTION_DATABASE_ROLE='__PRODUCTION_DATABASE_ROLE__'
DEVELOPMENT_DATABASE_ROLE='__DEVELOPMENT_DATABASE_ROLE__'
DATABASE_CONTAINER='__DATABASE_CONTAINER__'
PRODUCTION_SERVICE='__PRODUCTION_SERVICE__'
DEVELOPMENT_SERVICE='__DEVELOPMENT_SERVICE__'
REFRESH_ID='__REFRESH_ID__'
BACKUP_STAMP='__BACKUP_STAMP__'
WORK_DIR='__REMOTE_TEMP_DIR__'
STAGING_DATABASE="catmap_dev_stage_${REFRESH_ID}"
BACKUP_DATABASE="catmap_dev_bak_${BACKUP_STAMP}"
BACKUP_DIR='/opt/catmap-dev/backups'
CONTAINER_PRODUCTION_DUMP="/tmp/catmap-prod-${REFRESH_ID}.dump"
CONTAINER_DEVELOPMENT_DUMP="/tmp/catmap-dev-${REFRESH_ID}.dump"
HOST_DEVELOPMENT_DUMP="$BACKUP_DIR/catmap_dev_before_${BACKUP_STAMP}.dump"
SWITCHED=0

if [ "$PRODUCTION_DATABASE" != 'catmap' ] || \
   [ "$DEVELOPMENT_DATABASE" != 'catmap_dev' ] || \
   [ "$PRODUCTION_DATABASE_ROLE" != 'catmap_app' ] || \
   [ "$DEVELOPMENT_DATABASE_ROLE" != 'catmap_dev_app' ] || \
   [ "$DATABASE_CONTAINER" != 'catmap-postgis' ] || \
   [ "$PRODUCTION_SERVICE" != 'catmap-backend' ] || \
   [ "$DEVELOPMENT_SERVICE" != 'catmap-backend-dev' ]; then
    echo 'Refusing unexpected database refresh targets.' >&2
    exit 1
fi

admin_psql() {
    docker exec "$DATABASE_CONTAINER" psql \
        -v ON_ERROR_STOP=1 \
        -U "$PRODUCTION_DATABASE_ROLE" \
        "$@"
}

database_exists() {
    admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
        "select 1 from pg_database where datname='$1'" | grep -qx '1'
}

terminate_database_connections() {
    admin_psql -d "$PRODUCTION_DATABASE" -qc \
        "select pg_terminate_backend(pid) from pg_stat_activity where datname='$1' and pid <> pg_backend_pid()" \
        >/dev/null
}

cleanup() {
    exit_code=$?
    set +e

    if [ "$exit_code" -ne 0 ] && [ "$SWITCHED" -eq 1 ]; then
        echo 'Development database validation failed after the switch; restoring the previous development database.' >&2
        systemctl stop "$DEVELOPMENT_SERVICE" >/dev/null 2>&1 || true
        terminate_database_connections "$DEVELOPMENT_DATABASE" || true
        terminate_database_connections "$BACKUP_DATABASE" || true
        failed_database="catmap_dev_failed_${REFRESH_ID}"
        admin_psql -d "$PRODUCTION_DATABASE" -qc \
            "ALTER DATABASE \"$DEVELOPMENT_DATABASE\" RENAME TO \"$failed_database\"" || true
        admin_psql -d "$PRODUCTION_DATABASE" -qc \
            "ALTER DATABASE \"$BACKUP_DATABASE\" RENAME TO \"$DEVELOPMENT_DATABASE\"" || true
    elif [ "$exit_code" -ne 0 ] && database_exists "$STAGING_DATABASE"; then
        terminate_database_connections "$STAGING_DATABASE" || true
        docker exec "$DATABASE_CONTAINER" dropdb \
            -U "$PRODUCTION_DATABASE_ROLE" "$STAGING_DATABASE" || true
    fi

    docker exec "$DATABASE_CONTAINER" rm -f \
        "$CONTAINER_PRODUCTION_DUMP" "$CONTAINER_DEVELOPMENT_DUMP" >/dev/null 2>&1 || true
    rm -rf "$WORK_DIR"
    exit "$exit_code"
}
trap cleanup EXIT

install -d -m 700 "$WORK_DIR" "$BACKUP_DIR"
docker inspect "$DATABASE_CONTAINER" >/dev/null
systemctl is-active --quiet "$PRODUCTION_SERVICE"
curl --noproxy '*' --max-time 10 -fsS 'https://trmx.fun/api/v1/health' >/dev/null

production_owner="$(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
    "select pg_get_userbyid(datdba) from pg_database where datname='$PRODUCTION_DATABASE'")"
development_owner="$(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
    "select pg_get_userbyid(datdba) from pg_database where datname='$DEVELOPMENT_DATABASE'")"
development_role_flags="$(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
    "select rolsuper::text || '|' || rolcreatedb::text || '|' || rolcreaterole::text from pg_roles where rolname='$DEVELOPMENT_DATABASE_ROLE'")"

if [ "$production_owner" != "$PRODUCTION_DATABASE_ROLE" ] || \
   [ "$development_owner" != "$DEVELOPMENT_DATABASE_ROLE" ] || \
   [ "$development_role_flags" != 'false|false|false' ]; then
    echo 'Database ownership or development role isolation does not match the approved contract.' >&2
    exit 1
fi
if database_exists "$STAGING_DATABASE" || database_exists "$BACKUP_DATABASE"; then
    echo 'A staging or backup database already uses the generated refresh name.' >&2
    exit 1
fi

docker exec "$DATABASE_CONTAINER" pg_dump \
    -U "$PRODUCTION_DATABASE_ROLE" -Fc --no-owner --no-acl \
    -d "$DEVELOPMENT_DATABASE" -f "$CONTAINER_DEVELOPMENT_DUMP"
docker cp "$DATABASE_CONTAINER:$CONTAINER_DEVELOPMENT_DUMP" "$HOST_DEVELOPMENT_DUMP"
chmod 600 "$HOST_DEVELOPMENT_DUMP"

docker exec "$DATABASE_CONTAINER" pg_dump \
    -U "$PRODUCTION_DATABASE_ROLE" -Fc --no-owner --no-acl \
    --exclude-schema=tiger \
    --exclude-schema=tiger_data \
    --exclude-schema=topology \
    --exclude-table-data=spatial_ref_sys \
    -d "$PRODUCTION_DATABASE" -f "$CONTAINER_PRODUCTION_DUMP"

docker exec "$DATABASE_CONTAINER" createdb \
    -U "$PRODUCTION_DATABASE_ROLE" -O "$DEVELOPMENT_DATABASE_ROLE" "$STAGING_DATABASE"

while IFS= read -r extension_name; do
    if [[ ! "$extension_name" =~ ^[a-zA-Z0-9_]+$ ]]; then
        echo 'Production database contains an unexpected extension name.' >&2
        exit 1
    fi
    admin_psql -d "$STAGING_DATABASE" -qc \
        "CREATE EXTENSION IF NOT EXISTS \"$extension_name\""
done < <(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
    "select extname from pg_extension where extname <> 'plpgsql' order by extname")

docker exec "$DATABASE_CONTAINER" pg_restore \
    -U "$DEVELOPMENT_DATABASE_ROLE" \
    -d "$STAGING_DATABASE" \
    --no-owner --no-acl --no-comments --exit-on-error \
    "$CONTAINER_PRODUCTION_DUMP"

production_version="$(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
    'select version_num from alembic_version')"
staging_version="$(admin_psql -d "$STAGING_DATABASE" -Atqc \
    'select version_num from alembic_version')"
production_tables="$(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
    "select count(*) from pg_tables where schemaname='public'")"
staging_tables="$(admin_psql -d "$STAGING_DATABASE" -Atqc \
    "select count(*) from pg_tables where schemaname='public'")"

if [ "$production_version" != '20260712_0014' ] || \
   [ "$staging_version" != "$production_version" ] || \
   [ "$staging_tables" != "$production_tables" ]; then
    echo 'Restored development staging database does not match the production snapshot.' >&2
    exit 1
fi

for table_name in users tasks cats file_assets; do
    production_count="$(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
        "select count(*) from \"$table_name\"")"
    staging_count="$(admin_psql -d "$STAGING_DATABASE" -Atqc \
        "select count(*) from \"$table_name\"")"
    if [ "$production_count" != "$staging_count" ]; then
        echo "Restored row count differs for $table_name." >&2
        exit 1
    fi
done

systemctl stop "$DEVELOPMENT_SERVICE" >/dev/null 2>&1 || true
terminate_database_connections "$DEVELOPMENT_DATABASE"
terminate_database_connections "$STAGING_DATABASE"
admin_psql -d "$PRODUCTION_DATABASE" -qc \
    "ALTER DATABASE \"$DEVELOPMENT_DATABASE\" RENAME TO \"$BACKUP_DATABASE\""
admin_psql -d "$PRODUCTION_DATABASE" -qc \
    "ALTER DATABASE \"$STAGING_DATABASE\" RENAME TO \"$DEVELOPMENT_DATABASE\""
SWITCHED=1

new_development_owner="$(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
    "select pg_get_userbyid(datdba) from pg_database where datname='$DEVELOPMENT_DATABASE'")"
new_development_version="$(docker exec "$DATABASE_CONTAINER" psql \
    -U "$DEVELOPMENT_DATABASE_ROLE" -d "$DEVELOPMENT_DATABASE" -Atqc \
    'select version_num from alembic_version')"
production_version_after="$(admin_psql -d "$PRODUCTION_DATABASE" -Atqc \
    'select version_num from alembic_version')"

if [ "$new_development_owner" != "$DEVELOPMENT_DATABASE_ROLE" ] || \
   [ "$new_development_version" != '20260712_0014' ] || \
   [ "$production_version_after" != '20260712_0014' ]; then
    echo 'Database isolation validation failed after the development switch.' >&2
    exit 1
fi

echo "Development database refreshed from a production read-only snapshot."
echo "Rollback database retained: $BACKUP_DATABASE"
echo "Rollback dump retained: $HOST_DEVELOPMENT_DUMP"
'@

    $remoteScript = $remoteScript.
        Replace('__PRODUCTION_DATABASE__', $ProductionDatabase).
        Replace('__DEVELOPMENT_DATABASE__', $DevelopmentDatabase).
        Replace('__PRODUCTION_DATABASE_ROLE__', $ProductionDatabaseRole).
        Replace('__DEVELOPMENT_DATABASE_ROLE__', $DevelopmentDatabaseRole).
        Replace('__DATABASE_CONTAINER__', $DatabaseContainer).
        Replace('__PRODUCTION_SERVICE__', $ProductionService).
        Replace('__DEVELOPMENT_SERVICE__', $DevelopmentService).
        Replace('__REFRESH_ID__', $refreshId).
        Replace('__BACKUP_STAMP__', $backupStamp).
        Replace('__REMOTE_TEMP_DIR__', $remoteTempDir)

    $utf8NoBom = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($remoteScriptPath, $remoteScript, $utf8NoBom)

    Invoke-Remote "install -d -m 700 '$remoteTempDir'"
    Copy-ToRemote $remoteScriptPath "$remoteTempDir/refresh-dev-database.sh"
    Invoke-Remote "bash '$remoteTempDir/refresh-dev-database.sh'"
}
finally {
    try {
        Invoke-Remote "rm -rf '$remoteTempDir'"
    }
    catch {
        Write-Warning "Could not remove the protected database refresh temporary directory."
    }
    Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
}
