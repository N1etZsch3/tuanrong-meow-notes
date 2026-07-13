# AGENTS.md

This file is the project-level development handbook for agents working on CatMap / 团绒喵记本.

It defines how to work in this repository. It intentionally does not define the current product feature list, module completion status, or release scope. Those facts change quickly and must be read from the current code, progress notes, plans, and module documents.

## Scope Of This Handbook

- Use this file for development process, safety rules, verification expectations, documentation discipline, and handoff format.
- Do not use this file as the source of truth for concrete module behavior.
- Do not add long module feature lists, release changelogs, or detailed product requirements here.
- When functionality changes, update the relevant module docs, API docs, schema docs, plans, and `docs/开发进度.md` instead.

## Operating Principles

- Treat the current deployed behavior and current repository state as real production context, not as a blank-slate MVP.
- Prefer small, reviewable changes tied to one task.
- Verify before asserting. If a document, branch name, or old plan conflicts with code and progress notes, investigate instead of guessing.
- Preserve data safety, rollback ability, and production stability.
- Do not silently expand scope. If the user asks for a fix, do the fix; move unrelated ideas into notes or future plans.
- Never revert, overwrite, or clean up work you did not create unless the user explicitly asks.
- Keep secrets, credentials, environment values, private keys, and push-sensitive identifiers out of logs, commits, and summaries.

## Current Fact Sources

Before development work, gather current facts in this order:

1. `git status --short --branch` and `git worktree list`.
2. The latest entries in `docs/开发进度.md`.
3. Current code, tests, migrations, routes, pages, scripts, and deployment configuration.
4. Recent commits and tags.
5. Relevant files under `docs/plans/`.
6. Relevant module, API, and database design documents under `docs/模块功能/`, `docs/接口文档/`, and `docs/库表文档/`.
7. Older project overview documents as background only.

If sources conflict:

- Prefer current code plus the latest progress entry for what has actually shipped or been verified.
- Prefer the latest approved plan for work that is in progress.
- Treat older overview documents as historical unless they are confirmed by current code or recent progress.
- Record important conflicts in the handoff or progress entry.

Use explicit UTF-8 reads for Chinese docs when needed. If a Chinese document appears garbled, re-read it with UTF-8 before drawing conclusions.

## Required Start Checklist

At the start of a task:

- Identify whether the request is a feature, fix, documentation update, deployment task, release task, investigation, or review.
- Check branch and worktree state.
- Notice untracked files, ignored local artifacts, and dirty files before editing.
- Identify the affected area and the smallest useful change.
- Read only the relevant current docs and code for that area.
- Decide what is explicitly out of scope.
- Decide how the change will be verified.

For bugs, reproduce the issue or locate concrete evidence before changing behavior whenever practical.

For documentation-only tasks, still inspect current state. Documentation that describes stale behavior is a bug.

## File And Search Practices

- Use `rg` / `rg --files` first for text and file searches.
- Avoid opening ignored prototype images unless the user explicitly asks.
- For frontend visuals, prefer current implementation, approved assets, prototype code, and current docs over old screenshots.
- Do not inspect or print environment file contents unless the user explicitly asks and it is safe to do so.
- Use structured parsers or project APIs when available instead of brittle string manipulation.

## Git And Worktree Workflow

The repository root is the production-facing workspace. Normal development should happen in project-local worktrees under:

```text
D:\Study\Project\CatMap\.worktrees
```

Default branch roles:

- `main`: production-stable branch, release candidate, or explicit hotfix integration.
- `dev`: local integration branch for accepted development work.
- `feature/<topic>`: focused feature work.
- `fix/<topic>`: focused bug fix.
- `docs/<topic>`: documentation-only change.
- `release/<version>`: release stabilization.
- `hotfix/<version-or-topic>`: urgent production fix from `main`.

Before creating a focused worktree:

```powershell
git -C D:\Study\Project\CatMap fetch origin
git -C D:\Study\Project\CatMap\.worktrees\dev status --short --branch
git -C D:\Study\Project\CatMap\.worktrees\dev rev-list --left-right --count origin/dev...dev
```

Use the committed `HEAD` of the local `.worktrees/dev` worktree as the normal baseline. If local `dev` is ahead of `origin/dev`, treat local `dev` as the current accepted development baseline. If `origin/dev` is ahead and local `dev` can be fast-forwarded safely, update it first:

```powershell
git -C D:\Study\Project\CatMap\.worktrees\dev pull --ff-only origin dev
```

Create focused worktrees from local `dev`, for example:

```powershell
git -C D:\Study\Project\CatMap worktree add .worktrees\docs-agents-handbook -b docs/agents-handbook dev
```

Do not create new project worktrees under global fallback directories unless the user explicitly asks.

If a worktree has unrelated uncommitted files, do not touch them. If they block the task, stop and explain the blocker.

## Environment Files And Local Config

Ignored environment and local config files are required for many checks, builds, and deployments.

- Copy required ignored env files from the local `dev` worktree into a new focused worktree using the same relative paths only after confirming they are intended for that runtime environment.
- Do not invent placeholder secrets.
- If required env files are missing from `dev`, ask the user instead of fabricating values.
- Verify copied env files remain ignored with `git status --short --ignored -- <path>`.
- Do not print env contents.
- Do not infer an environment from its worktree or filename. Before a development deployment, check only non-sensitive boolean conditions: the database name is `catmap_dev`, the database role is `catmap_dev_app`, and `CATMAP_TENCENT_COS_ENV_PREFIX` is `dev`.

Mini Program AppIDs and third-party service keys are push-sensitive. Keep local development config aligned with the authorized app, but inspect staged diffs and push ranges before pushing. Do not push real AppIDs, keys, tokens, or private credentials to a remote unless the user explicitly approves that remote state.

## Same-Host Development And Production Isolation

Until separate physical servers are funded, production and development share one host but must remain logically isolated. This is a deployment boundary, not an invitation to treat the environments as interchangeable.

| Concern | Production | Development |
|---|---|---|
| Backend directory | `/opt/catmap/backend` | `/opt/catmap-dev/backend` |
| systemd unit | `catmap-backend` | `catmap-backend-dev` |
| Backend listener | `127.0.0.1:8000` | `127.0.0.1:8001` |
| Database | `catmap` | `catmap_dev` using `catmap_dev_app` |
| Public API domain | production domain | `dev-api.trmx.fun` |
| Mini Program build | `npm run build:mp-weixin:prod` only | `npm run build`, `npm run build:mp-weixin`, or `npm run build:mp-weixin:dev` |

- The production deployment script, production unit, production Nginx vhost, production database, and production service must remain untouched during development deployment work.
- Development deployment must use `scripts/deploy-backend-dev.ps1` with an explicit server host and ignored development environment file. Its fixed deployment directory, service name, domain, database, database role, and COS prefix guards must not be weakened or parameterized to production values.
- The development service must run as the dedicated non-root `catmap-dev` system user, listen only on loopback, and must never add a public firewall/security-group rule for port 8001.
- The development Nginx vhost must not use `default_server`. Obtain the development certificate with the HTTP webroot/bootstrap vhost; never use a standalone ACME mode that stops or occupies production 80/443 listeners.
- One COS bucket may be shared temporarily, but development writes must use the `dev/` prefix. Treat this as naming isolation only: request a CAM policy limited to `dev/*` before considering object storage access fully isolated.
- Do not automatically copy production data into development. Any later refresh must be a separate, approved procedure with backup, masking, restore validation, and rollback notes.
- Deploy only a committed source baseline whose Alembic migrations are compatible with `catmap_dev`. Never deploy uncommitted worktree changes as a development release.
- After a development deployment, verify both production and development health endpoints, both systemd units, the development database/role identity, the development migration version, loopback-only port 8001, and that production resource files and database version did not change.
- The default frontend build is development by design. Production Mini Program validation is a deliberate release action using `npm run build:mp-weixin:prod`; do not use a development artifact for production upload.

## Commit And Push Discipline

- Stage explicit files only. Do not use `git add .`.
- Check `git status` before committing.
- Use concise conventional commit messages.
- Do not commit generated artifacts unless the release process or user explicitly requires them.
- Before pushing, inspect staged diffs and commits being pushed for secrets, private hosts, access keys, map keys, storage credentials, AppIDs, `.env` values, and deployment credentials.
- Push only the intended branch or tag. Never run `git push --all origin`.
- Do not delete or prune old branches or worktrees without user approval.

Recommended commit prefixes:

```text
feat:
fix:
docs:
refactor:
test:
chore:
db:
release:
```

## Version And Release Rules

Use semantic versioning:

```text
MAJOR.MINOR.PATCH
```

Release facts must be discovered from `docs/开发进度.md`, Git tags, recent commits, deployment scripts, and actual deployed health checks. Do not rely on stale text in old overview docs.

Production releases should use annotated tags on the exact deployed commit:

```powershell
git tag -a v<version> -m "release: v<version>"
```

For release and hotfix work:

- Create release branches from `dev`.
- Create hotfix branches from `main`.
- Verify before merging into `main`.
- Record deployment, rollback notes, verification commands, and known exclusions in `docs/开发进度.md`.
- After a hotfix, merge or cherry-pick the fix back to `dev` as appropriate.

## Backend Development Standards

Backend work uses FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL, and PostGIS.

General rules:

- Keep route handlers thin.
- Put business logic in services or clear helper modules.
- Use Pydantic schemas for request and response validation.
- Keep database access transaction-aware.
- Enforce auth and role checks at the API boundary or service boundary as appropriate.
- Return unified API envelopes with trace IDs.
- Use `snake_case` request and response fields.
- Keep API routes under `/api/v1`.
- Use action subpaths for action-like operations.
- Do not store secrets in source files.
- Do not write custom password, token, or crypto logic when project utilities exist.

When adding or changing endpoints:

- Update schemas and tests with the behavior.
- Keep frontend API types aligned.
- Update API docs when the public contract changes.
- Confirm error responses follow the project error format.

## Database And Migration Standards

Schema changes must use SQLAlchemy models and Alembic migrations.

For database work:

- Check current migrations and table docs before editing schema.
- Prefer UUID primary keys unless an existing table pattern differs.
- Use lifecycle timestamps where records need lifecycle tracking.
- Prefer soft deletion or archival for user-facing records where accidental deletion is risky.
- Keep spatial point data separate from business details.
- Avoid destructive migrations in patch-level maintenance unless the user approves a release plan.
- Add downgrade logic where practical.
- Verify upgrade and, when practical, downgrade.
- Record migration names in progress notes.

For production-impacting data changes, include rollback notes or backup expectations in the handoff.

## Frontend Development Standards

Frontend work targets uni-app, Vue 3, TypeScript, Pinia, and WeChat Mini Program first. H5 is useful for local debugging but must not override Mini Program behavior.

General rules:

- Design for phone-sized Mini Program viewports first.
- Every frontend page should be checked against a phone-sized 微信小程序视口 first.
- Keep pages usable, dense enough for mobile, and free of accidental overflow.
- Use existing app components, request services, stores, and assets before creating new abstractions.
- Use the shared page background `frontend/素材/加载页素材/背景.jpg` unless the user explicitly asks for a page-specific exception.
- 中文字体 must use the project Songti-style font stack: `"Songti SC", "STSong", "SimSun", "Noto Serif CJK SC", serif`.
- Keep Chinese UI readable on 手机 viewports; do not override Chinese UI text with unrelated sans-serif fonts unless explicitly requested.
- Prefer current approved assets under `frontend/素材`.
- Do not add random online assets or near-match replacements.
- If a needed asset is missing, use an obvious placeholder and record the gap.
- Handle loading, empty, error, permission-denied, unauthenticated, and image-failed states.
- Keep TypeScript types aligned with backend `snake_case` fields.
- Use Pinia for shared app state.

Prototype and asset rules:

- `frontend/页面原型` is ignored and should not be opened for images unless the user explicitly asks.
- `frontend/页面原型代码` may be used when relevant.
- New frontend-used assets belong under `frontend/素材`, not the repository root.

Before frontend handoff, run the relevant tests and build:

```powershell
cd frontend
npm run test -- --run
npm run type-check
npm run build:mp-weixin
```

Use narrower test commands first when iterating, then run the broader relevant set before handoff.

## External Services And Deployment Config

Third-party services such as map providers, object storage, HTTPS certificates, and deployment hosts must be configured through environment variables, deployment scripts, or approved config files.

- Do not hardcode secrets or private credentials.
- Do not print keys, tokens, certificates, or env values.
- When changing external-service behavior, update `.env.example`, settings, docs, and tests together.
- When changing request domains, CORS, certificates, or deployment scripts, verify both local contract tests and deployed health checks.
- Treat Mini Program request domains, AppID config, map provider keys, and object storage credentials as release-sensitive.

## Verification Standards

Run the smallest meaningful verification while developing, then broaden before handoff.

Backend:

```powershell
cd backend
python -m pytest <targeted-test> -q
python -m pytest -q
python -m ruff check .
python -m alembic upgrade head
```

Frontend:

```powershell
cd frontend
npm run test -- --run <targeted-test>
npm run test -- --run
npm run type-check
npm run build:mp-weixin
```

`npm run build:mp-weixin` is intentionally the development build. For an approved production release validation, additionally run `npm run build:mp-weixin:prod` and confirm the resulting artifact uses only the production API domain.

Deployment-impacting backend work should also run the repository deployment verification path unless the user explicitly scopes the task to local-only work:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy-backend.ps1 -EnvFile backend\.env
```

Then verify the deployed `/api/v1/health` endpoint using the currently configured production or test host from scripts and progress notes.

For an approved development-server deployment, use the isolated path instead:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy-backend-dev.ps1 -ServerHost <server-host> -EnvFile backend\.env
```

Do not run this command until the intended source baseline is committed and the development environment-file guard has passed. The post-deploy checks must cover both environments as defined in `Same-Host Development And Production Isolation`.

If a verification step cannot be run, record exactly why and what risk remains.

Manual Mini Program verification is expected for changes involving navigation, native map behavior, location authorization, image upload/display, AppID config, permissions, or platform-specific UI.

## Documentation And Progress Updates

Update `docs/开发进度.md` before handoff for development, release, deployment, or meaningful documentation work.

Use local `+08:00` timestamps in this format:

```text
YYYY-MM-DD HH:mm:ss +08:00
```

A useful progress entry includes:

- Branch or worktree.
- Affected area.
- Completed work.
- Files changed.
- API or schema changes.
- Migration names.
- Verification commands and results.
- Manual checks not yet done.
- Known blockers or risks.
- Next recommended step.

Plans belong under `docs/plans/` and should be short, actionable, and tied to the current repository state. Do not create large speculative plans unless the user asks.

When a module contract changes, update the relevant module, API, or table document. Do not encode module-specific contract details in this handbook.

## Handoff Format

End coding sessions with a concise handoff in this order:

1. What changed.
2. Files touched.
3. Verification run.
4. What was not verified.
5. Known risks or blockers.
6. Next step.

Keep the handoff factual. Do not claim a module, release, or deployment is complete unless verification supports it.

## Review Mode

When asked for a review, lead with findings.

- Prioritize bugs, regressions, data risks, deployment risks, security issues, and missing tests.
- Include file and line references.
- Keep summaries secondary.
- If no issues are found, say so and mention residual risk or unrun checks.

## Security And Privacy Rules

- Never commit `.env` files, private keys, certificates, tokens, passwords, database dumps, or secret screenshots.
- Do not paste secret values into chat or progress notes.
- Before pushing, inspect diffs and commit ranges for credentials, private domains, service keys, Mini Program AppIDs, and deployment details.
- If a change adds or changes personal-information processing, permissions, image/file upload behavior, location behavior, or third-party sharing, update the relevant privacy/compliance documentation and Mini Program configuration notes.
- Keep user data retention, deletion, and audit implications in mind when changing persistence.

## Completion Checklist

Before handing off:

- Relevant current docs and code were checked.
- Scope stayed focused.
- API/schema changes, if any, have docs and tests.
- Database changes, if any, have migrations.
- Frontend changes handle important states and Mini Program constraints.
- Backend changes preserve auth, response envelopes, and transaction safety.
- Relevant tests, type checks, linters, builds, migrations, or deployment checks were run.
- `docs/开发进度.md` was updated when appropriate.
- Remaining manual checks, risks, and blockers are documented.

## What Not To Put In This File

Do not add:

- Full module feature lists.
- Temporary launch checklists.
- Detailed API examples for one module.
- Table-by-table schema specs.
- Historical progress logs.
- Screenshots or prototype analysis.
- Secrets, env values, AppIDs, private keys, or deployment credentials.

Put those in the appropriate current docs, plans, progress notes, or private environment files instead.
