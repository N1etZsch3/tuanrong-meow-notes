# Medicine Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the V1 medicine management module from the imported docs, with backend data/API support and reusable mobile frontend pages.

**Architecture:** Add a new backend `medicines` module with SQLAlchemy models, Alembic migration, transaction-aware service functions, and member/admin routes under `/api/v1`. Add a frontend `medicines` API module plus list, create, catalog detail, and holding detail pages that reuse existing task and supply page visual patterns.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy 2.0, Alembic, PostgreSQL numeric quantities, uni-app, Vue 3, TypeScript, Pinia, Vitest.

---

### Task 1: Document Import Baseline

**Files:**
- Create: `docs/模块功能/药品管理模块_功能说明文档.md`
- Create: `docs/库表文档/药品管理模块_库表设计文档.md`
- Create: `docs/接口文档/药品管理模块_接口设计文档.md`
- Create: `docs/plans/2026-07-06-medicine-management-design.md`
- Create: `docs/plans/2026-07-06-medicine-management.md`

**Step 1: Verify docs are on the feature branch**

Run: `git status --short --branch`

Expected: the five docs appear as untracked or staged files on `feature/medicine-management`.

**Step 2: Commit the design and imported docs**

Run:

```bash
git add docs/模块功能/药品管理模块_功能说明文档.md docs/库表文档/药品管理模块_库表设计文档.md docs/接口文档/药品管理模块_接口设计文档.md docs/plans/2026-07-06-medicine-management-design.md docs/plans/2026-07-06-medicine-management.md
git commit -m "docs(medicines): add medicine management design"
```

Expected: commit succeeds without staging unrelated files.

---

### Task 2: Backend Models And Migration

**Files:**
- Create: `backend/app/modules/medicines/__init__.py`
- Create: `backend/app/modules/medicines/models.py`
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/20260706_0012_create_medicine_tables.py`
- Test: `backend/tests/test_medicines_api.py`

**Step 1: Write failing schema/import test**

Add tests that import the medicine models and assert the expected table names are present in `Base.metadata`.

Run: `python -m pytest backend/tests/test_medicines_api.py -q`

Expected: fail because `app.modules.medicines` does not exist.

**Step 2: Implement models and migration**

Create SQLAlchemy models for categories, catalogs, aliases, photos, holdings, logs, and applications. Add the Alembic migration with constraints/indexes from the table doc, including numeric non-negative checks and the active `(medicine_id, holder_id)` uniqueness rule.

**Step 3: Verify schema tests and migration**

Run:

```bash
python -m pytest backend/tests/test_medicines_api.py -q
python -m alembic upgrade head
python -m alembic downgrade 20260703_0011
python -m alembic upgrade head
```

Expected: tests pass and migration upgrades/downgrades cleanly.

---

### Task 3: Backend Member Medicine APIs

**Files:**
- Create: `backend/app/modules/medicines/schemas.py`
- Create: `backend/app/modules/medicines/service.py`
- Create: `backend/app/api/v1/medicine_categories.py`
- Create: `backend/app/api/v1/medicines.py`
- Create: `backend/app/api/v1/medicine_holdings.py`
- Create: `backend/app/api/v1/medicine_applications.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_medicines_api.py`

**Step 1: Write failing API tests**

Cover:

- `GET /api/v1/medicine-categories`
- `POST /api/v1/medicines` creates a new catalog, holding, and `initial_in` log.
- `GET /api/v1/medicines` returns catalog-level summary with holder tags.
- `GET /api/v1/medicines/{medicine_id}` returns aggregate stock and recent logs.
- `GET /api/v1/medicine-holdings/{holding_id}` returns holder-specific permissions.

Run: `python -m pytest backend/tests/test_medicines_api.py -q`

Expected: fail with missing routes.

**Step 2: Implement minimal read/create flows**

Implement Pydantic request schemas, query helpers, stock status calculation, holder DTOs, and route registration. Keep route handlers thin and put behavior in service functions.

**Step 3: Verify**

Run: `python -m pytest backend/tests/test_medicines_api.py -q`

Expected: new tests pass.

---

### Task 4: Backend Stock Operations And Applications

**Files:**
- Modify: `backend/app/modules/medicines/schemas.py`
- Modify: `backend/app/modules/medicines/service.py`
- Modify: `backend/app/api/v1/medicine_holdings.py`
- Modify: `backend/app/api/v1/medicine_applications.py`
- Test: `backend/tests/test_medicines_api.py`

**Step 1: Write failing operation tests**

Cover purchase, use, scrap, distribute, transfer, submit application, approve, reject, cancel, and 24-hour expiry guard.

Run: `python -m pytest backend/tests/test_medicines_api.py -q`

Expected: fail because operation endpoints do not exist or are incomplete.

**Step 2: Implement transaction-aware operations**

Use row-level locks where supported, validate holder/admin permissions, update holding quantities/status, write stock logs, and keep application status transitions guarded.

**Step 3: Verify**

Run:

```bash
python -m pytest backend/tests/test_medicines_api.py -q
python -m pytest backend/tests -q
python -m ruff check backend/app backend/tests
```

Expected: all pass.

---

### Task 5: Backend Admin Medicine APIs

**Files:**
- Create: `backend/app/api/v1/admin_medicines.py`
- Modify: `backend/app/modules/medicines/schemas.py`
- Modify: `backend/app/modules/medicines/service.py`
- Modify: `backend/app/api/v1/router.py`
- Test: `backend/tests/test_medicines_api.py`

**Step 1: Write failing admin tests**

Cover category create/edit/status, catalog edit, archive no-stock catalog, reject archive with stock, soft-delete no-stock catalog, and reject deleting non-empty holding.

Run: `python -m pytest backend/tests/test_medicines_api.py -q`

Expected: fail with missing admin routes.

**Step 2: Implement admin routes**

Use existing `require_admin`, preserve logs for archive and delete-holding actions, and keep delete operations soft.

**Step 3: Verify**

Run: `python -m pytest backend/tests/test_medicines_api.py -q`

Expected: pass.

---

### Task 6: Frontend API And Routes

**Files:**
- Create: `frontend/src/api/medicines.ts`
- Modify: `frontend/src/api/routes.ts`
- Modify: `frontend/src/pages.json`
- Test: `frontend/tests/api/medicines.test.ts`
- Test: `frontend/tests/api/routes.test.ts`

**Step 1: Write failing frontend API tests**

Assert medicine endpoint builders, DTO request functions, and route entries exist.

Run: `npm run test -- --run tests/api/medicines.test.ts tests/api/routes.test.ts`

Expected: fail because module/routes do not exist.

**Step 2: Implement API client and route config**

Add typed request wrappers for categories, list, search, create, detail, holdings, logs, operations, applications, and admin calls used by V1 pages.

**Step 3: Verify**

Run: `npm run test -- --run tests/api/medicines.test.ts tests/api/routes.test.ts`

Expected: pass.

---

### Task 7: Frontend Medicine List And Add Entry

**Files:**
- Create: `frontend/src/pages/medicines/index.vue`
- Create: `frontend/src/pages/medicines/create.vue`
- Modify: `frontend/src/pages/profile/index.vue`
- Test: `frontend/tests/pages/medicines-page.test.ts`
- Test: `frontend/tests/pages/profile-page.test.ts`

**Step 1: Write failing page tests**

Assert:

- `我的` page links to `/pages/medicines/index`.
- Medicine list loads categories and medicines.
- List page has a visible add-medicine entry.
- Cards render holder chips and navigate to catalog/holding details.
- Create page searches existing catalogs and can submit existing/new catalog payloads.

Run: `npm run test -- --run tests/pages/medicines-page.test.ts tests/pages/profile-page.test.ts`

Expected: fail because pages and entry do not exist.

**Step 2: Implement pages reusing existing UI**

Reuse task list page structure for title/search/filter/cards, shared background image, Songti font stack, and horizontal holder chip strip. Use the add entry on the list page, not admin home.

**Step 3: Verify**

Run: `npm run test -- --run tests/pages/medicines-page.test.ts tests/pages/profile-page.test.ts`

Expected: pass.

---

### Task 8: Frontend Detail, Holding Actions, And Applications

**Files:**
- Create: `frontend/src/pages/medicines/detail.vue`
- Create: `frontend/src/pages/medicines/holding.vue`
- Modify: `frontend/src/pages/medicines/index.vue`
- Test: `frontend/tests/pages/medicines-page.test.ts`

**Step 1: Write failing detail tests**

Assert catalog detail renders summary, holder list, recent logs, and admin permissions. Assert holding detail shows record modal actions for holder and application modal for non-holder.

Run: `npm run test -- --run tests/pages/medicines-page.test.ts`

Expected: fail because detail pages are missing.

**Step 2: Implement reusable detail pages**

Reuse task-detail layout density and supply-detail dynamic/record modal interaction patterns. Keep operation forms compact and mobile-first.

**Step 3: Verify frontend**

Run:

```bash
npm run test -- --run tests/pages/medicines-page.test.ts
npm run type-check
npm run build:mp-weixin
```

Expected: all pass.

---

### Task 9: Progress Notes And Final Verification

**Files:**
- Modify: `docs/开发进度.md`

**Step 1: Update progress**

Add a 2026-07-06 entry for `feature/medicine-management` with docs read, files changed, API/table changes, migration name, verification commands, known gaps, and next step.

**Step 2: Full verification**

Run:

```bash
python -m pytest backend/tests -q
python -m ruff check backend/app backend/tests
npm run test -- --run
npm run type-check
npm run build:mp-weixin
git diff --check
```

Expected: all pass, or any failure is documented with exact output and blocker notes.

**Step 3: Final commit**

Stage explicit medicine files, route/page files, tests, migration, and progress doc. Commit with:

```bash
git commit -m "feat(medicines): add medicine management module"
```

Expected: commit succeeds with only intended files.
