# Backend Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy the FastAPI backend to the server behind Cloudflare HTTPS and add a local one-command backend deployment script.

**Architecture:** Nginx terminates HTTPS with the Cloudflare Origin Certificate and proxies backend paths to a systemd-managed Uvicorn service on `127.0.0.1:8000`. A local PowerShell script syncs backend source to `/opt/catmap/backend`, updates the Python environment, runs Alembic, restarts the service, and verifies the public HTTPS health endpoint.

**Tech Stack:** FastAPI, Uvicorn, Python 3.11 venv, Alembic, Nginx, systemd, OpenSSH, PowerShell.

---

### Task 1: Create Deployment Artifacts

**Files:**
- Create: `deploy/nginx/catmap.conf`
- Create: `deploy/systemd/catmap-backend.service`
- Create: `scripts/deploy-backend.ps1`
- Create: `scripts/bootstrap-server-ssh-key.ps1`
- Modify: `frontend/src/config/app-env.ts`
- Modify: `frontend/.env.example`
- Modify: `docs/开发进度.md`

**Step 1: Add script contract tests**

Add focused tests or static checks that verify:

- `deploy-backend.ps1` does not contain `server_key.txt`.
- `deploy-backend.ps1` contains the production health URL.
- `catmap.conf` redirects HTTP to HTTPS.
- `catmap.conf` proxies `/api/v1/` to `127.0.0.1:8000`.
- Frontend default API URL is `https://catmap.example.com/api/v1`.

**Step 2: Run checks to verify failure**

Run the new checks before creating implementation files. Expected: fail because files or target values do not exist yet.

**Step 3: Add deployment templates and scripts**

Create Nginx, systemd, SSH bootstrap, and deployment scripts with safe defaults:

- server host `203.0.113.10`
- domain `catmap.example.com`
- deployment directory `/opt/catmap/backend`
- service name `catmap-backend`
- deployment SSH key `~/.ssh/catmap_deploy_ed25519`

**Step 4: Run checks to verify pass**

Run the same checks. Expected: pass.

### Task 2: Bootstrap Server Access

**Files:**
- Use local secret input: `ssl_key/server_key.txt`
- Use generated SSH key: `~/.ssh/catmap_deploy_ed25519`

**Step 1: Generate deployment SSH key if absent**

Run the bootstrap script. It must create the key only if it does not already exist.

**Step 2: Install the public key on the server**

Use the password from `ssl_key/server_key.txt` for the first login and append the deployment public key to `root/.ssh/authorized_keys`.

**Step 3: Verify public-key SSH**

Run:

```powershell
ssh -i "$env:USERPROFILE\.ssh\catmap_deploy_ed25519" root@203.0.113.10 "printf catmap-key-ok"
```

Expected: `catmap-key-ok`.

### Task 3: Configure Server HTTPS And Backend Service

**Files:**
- Upload: `ssl_key/Origin _Certificate.txt`
- Upload: `ssl_key/Private_Key.txt`
- Upload: `deploy/nginx/catmap.conf`
- Upload: `deploy/systemd/catmap-backend.service`

**Step 1: Prepare server directories**

Create:

- `/opt/catmap/backend`
- `/etc/nginx/ssl/catmap`

**Step 2: Upload SSL files with restricted permissions**

Install certificate and key as:

- `/etc/nginx/ssl/catmap/origin.pem`
- `/etc/nginx/ssl/catmap/origin.key`

Set private key permission to `600`.

**Step 3: Install Nginx and systemd templates**

Copy templates into place and run:

```bash
nginx -t
systemctl daemon-reload
systemctl reload nginx
```

Expected: Nginx config test succeeds and reload succeeds.

### Task 4: Deploy Backend

**Files:**
- Sync: `backend/**`
- Preserve server runtime file: `/opt/catmap/backend/.env`

**Step 1: Run backend local verification**

Run:

```powershell
cd backend
py -3.11 -m pytest -q
py -3.11 -m ruff check .
```

Expected: both pass.

**Step 2: Run one-command deploy script**

Run:

```powershell
.\scripts\deploy-backend.ps1
```

Expected: sync, dependency install, migration, service restart, and health check succeed.

**Step 3: Verify public HTTPS endpoint**

Run:

```powershell
curl.exe -fsS https://catmap.example.com/api/v1/health
```

Expected: unified response envelope with `code: 0`.

### Task 5: Frontend API Address And Handoff

**Files:**
- Modify: `frontend/src/config/app-env.ts`
- Modify: `frontend/.env.example`
- Modify: `docs/开发进度.md`

**Step 1: Update frontend API default**

Set the default API base URL to:

```text
https://catmap.example.com/api/v1
```

**Step 2: Verify frontend**

Run:

```powershell
cd frontend
npm run type-check
npm run build:mp-weixin
```

Expected: both pass.

**Step 3: Final verification**

Run:

```powershell
git diff --check
git status --short
```

Expected: no whitespace errors; only deployment-related files changed.
