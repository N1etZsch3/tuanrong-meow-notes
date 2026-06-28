# Cat Library List Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the V1 cat archive list page and the member-facing list/stat/filter backend APIs.

**Architecture:** Add the initial cats module on the backend with SQLAlchemy models, Alembic migration, thin FastAPI routes, and service-layer query logic. Add frontend API bindings and replace the tab placeholder with a mobile-first uni-app list page that loads stats, filter options, and cat cards from `/api/v1/cats`.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic-compatible dict responses, uni-app, Vue 3, TypeScript, Pinia.

---

## Module Start Checklist

- Module changed: 猫咪库模块.
- Docs read: project overview, database overview, API conventions, cat module function/API/table docs, `frontend/页面原型/猫咪库.png`.
- APIs affected: `GET /api/v1/cats/stats`, `GET /api/v1/cats/filter-options`, `GET /api/v1/cats`.
- Tables affected: `cats`, `cat_aliases`, `cat_photos`, `cat_map_points`, `cat_observation_records`, `cat_health_records`, `cat_favorites`.
- Prototype/assets: `frontend/页面原型/猫咪库.png`; used only `frontend/素材/icon/猫咪.png`; cat photos fall back to explicit placeholders when API images are missing.
- Upstream modules: auth/profile completion, file upload URL fields, map point tables for nullable point references.
- Smallest useful slice: authenticated cat stats, filter options, paginated/searchable/filterable cat list, and the frontend list page.
- Out of scope: cat detail page, admin create/edit flow, observations, favorites mutation, real photo upload binding.
- Verification: focused backend tests, focused frontend API/page tests, full test/type/build checks, ruff, Alembic upgrade where available.

## Tasks

### Task 1: Backend Contract

- Add failing tests for empty cat stats/filter/list responses.
- Implement initial cats models, migration, routes, and service functions.
- Verify `tests/test_cats_api.py::test_cats_empty_list_contract`.

### Task 2: Backend Query Behavior

- Add tests for seeded cats, stats aggregation, alias search, filters, sorting, favorites, and profile completion enforcement.
- Implement query filtering and list DTO shaping.
- Verify `tests/test_cats_api.py`.

### Task 3: Frontend API

- Add failing tests for `getCatStats`, `getCatFilterOptions`, and `getCats`.
- Implement `frontend/src/api/cats.ts`.
- Verify `tests/api/cats.test.ts`.

### Task 4: Frontend Page

- Add page helper/source tests for query building, time formatting, tag tones, loading/error/empty states, and backend API usage.
- Implement `frontend/src/pages/cats/cats-page.ts`.
- Replace `frontend/src/pages/cats/index.vue` with the list page based on the prototype.
- Verify `tests/pages/cats-page.test.ts`.

### Task 5: Handoff

- Run backend tests, ruff, Alembic migration check, frontend tests, type check, and uni-app builds.
- Update `docs/开发进度.md`.
- Commit only files for this slice.
