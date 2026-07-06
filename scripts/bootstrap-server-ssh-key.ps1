param(
    [string] $ServerHost = "49.235.238.143",
    [string] $ServerUser = "root",
    [int] $SshPort = 22,
    [string] $KeyPath = (Join-Path $env:USERPROFILE ".ssh\catmap_deploy_ed25519"),
    [string] $PasswordFile = (Join-Path (Split-Path -Parent $PSScriptRoot) "ssl_key\server_key.txt")
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$defaultPasswordFile = Join-Path $repoRoot "ssl_key\server_key.txt"
if (-not (Test-Path -LiteralPath $PasswordFile) -and (Test-Path -LiteralPath $defaultPasswordFile)) {
    $PasswordFile = $defaultPasswordFile
}

if (-not (Test-Path -LiteralPath $PasswordFile)) {
    throw "Password file not found: $PasswordFile"
}

$sshDir = Split-Path -Parent $KeyPath
if (-not (Test-Path -LiteralPath $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir | Out-Null
}

if (-not (Test-Path -LiteralPath $KeyPath)) {
    $sshKeygenCommand = 'ssh-keygen -t ed25519 -f "' + $KeyPath + '" -N "" -C catmap-deploy@' + $ServerHost
    & cmd.exe /c $sshKeygenCommand
    if ($LASTEXITCODE -ne 0) {
        throw "ssh-keygen failed with exit code $LASTEXITCODE"
    }
}

$publicKeyPath = "$KeyPath.pub"
if (-not (Test-Path -LiteralPath $publicKeyPath)) {
    throw "Public key not found: $publicKeyPath"
}

$password = (Get-Content -LiteralPath $PasswordFile -Raw -Encoding UTF8).Trim()
$publicKey = (Get-Content -LiteralPath $publicKeyPath -Raw -Encoding ASCII).Trim()

$venvDir = Join-Path ([IO.Path]::GetTempPath()) "catmap-bootstrap-paramiko"
$pythonExe = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonExe)) {
    & py -3 -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create temporary Python environment for SSH bootstrap."
    }
    & $pythonExe -m pip install --upgrade pip paramiko
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install paramiko for SSH bootstrap."
    }
}

$bootstrapPython = @'
import os
import socket
import sys

import paramiko


def run(client, command):
    stdin, stdout, stderr = client.exec_command(command)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if exit_code != 0:
        raise RuntimeError(f"Command failed ({exit_code}): {command}\nSTDOUT:\n{out}\nSTDERR:\n{err}")
    return out


host = os.environ["CATMAP_BOOTSTRAP_HOST"]
port = int(os.environ["CATMAP_BOOTSTRAP_PORT"])
user = os.environ["CATMAP_BOOTSTRAP_USER"]
password = os.environ["CATMAP_BOOTSTRAP_PASSWORD"]
public_key = os.environ["CATMAP_BOOTSTRAP_PUBLIC_KEY"].strip()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(
        hostname=host,
        port=port,
        username=user,
        password=password,
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
        auth_timeout=20,
        banner_timeout=20,
    )
except (socket.error, paramiko.SSHException) as exc:
    raise SystemExit(f"SSH password login failed: {exc}") from exc

run(client, "umask 077 && mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys")

sftp = client.open_sftp()
try:
    with sftp.open(".ssh/authorized_keys", "r") as remote_file:
        authorized_keys = remote_file.read().decode("utf-8", errors="replace")
except FileNotFoundError:
    authorized_keys = ""

if public_key not in authorized_keys.splitlines():
    with sftp.open(".ssh/authorized_keys", "a") as remote_file:
        if authorized_keys and not authorized_keys.endswith("\n"):
            remote_file.write("\n")
        remote_file.write(public_key + "\n")

dropin = """PubkeyAuthentication yes
PasswordAuthentication yes
PermitRootLogin yes
AuthorizedKeysFile .ssh/authorized_keys .ssh/authorized_keys2
"""

run(client, "mkdir -p /etc/ssh/sshd_config.d")
with sftp.open("/etc/ssh/sshd_config.d/99-catmap-auth.conf", "w") as remote_file:
    remote_file.write(dropin)

run(client, "sshd -t")
run(client, "systemctl reload sshd || systemctl reload ssh || service sshd reload || service ssh reload")

sftp.close()
client.close()
print("SSH public key installed and password login remains enabled.")
'@

$bootstrapScriptPath = Join-Path ([IO.Path]::GetTempPath()) "catmap-bootstrap-ssh.py"
Set-Content -LiteralPath $bootstrapScriptPath -Value $bootstrapPython -Encoding UTF8

$env:CATMAP_BOOTSTRAP_HOST = $ServerHost
$env:CATMAP_BOOTSTRAP_PORT = [string] $SshPort
$env:CATMAP_BOOTSTRAP_USER = $ServerUser
$env:CATMAP_BOOTSTRAP_PASSWORD = $password
$env:CATMAP_BOOTSTRAP_PUBLIC_KEY = $publicKey
try {
    & $pythonExe $bootstrapScriptPath
    if ($LASTEXITCODE -ne 0) {
        throw "SSH bootstrap failed with exit code $LASTEXITCODE"
    }
}
finally {
    Remove-Item Env:\CATMAP_BOOTSTRAP_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:\CATMAP_BOOTSTRAP_PUBLIC_KEY -ErrorAction SilentlyContinue
}

& ssh -i $KeyPath -p $SshPort -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new "$ServerUser@$ServerHost" "printf catmap-key-ok"
if ($LASTEXITCODE -ne 0) {
    throw "Public-key SSH verification failed."
}

Write-Host ""
Write-Host "SSH key bootstrap complete: $KeyPath"
