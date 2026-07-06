# Medicine Management Design

## Goal

Build a V1 medicine management module for the campus cat association so members can see what medicine exists, who holds it, how much remains, how stock changed, and who requested use.

## Scope

The module follows the imported medicine documents:

- Medicine does not enter `map_points` and stores no coordinates.
- The list is grouped by medicine catalog, with holder inventory shown as child entries.
- The add-medicine entry lives on the medicine list page.
- Members can create their own holdings, record purchase/use/scrap, distribute stock, transfer stock, and apply to use another holder's stock.
- Holders can approve or reject applications sent to their own holdings.
- Admins can create categories, edit catalogs, archive or soft-delete no-stock catalogs, and soft-delete empty holdings.

Out of scope for this branch:

- WebSocket or real-time notifications.
- Batch and expiry-date management.
- Finance/statistics.
- Task creation-time planned medicine requirements.
- Full task search linkage; `related_task_id` fields stay nullable and reserved.

## Architecture

Backend adds `backend/app/modules/medicines` with SQLAlchemy models, Pydantic request schemas, service-layer transactions, and API routes under `/api/v1`. Inventory mutation flows lock the holding row, update derived quantity fields, and append `medicine_stock_logs` in the same transaction.

Frontend adds `frontend/src/api/medicines.ts` and `frontend/src/pages/medicines/*`. Pages reuse existing task-list structure for the catalog list, task-detail style for catalog/holding details, and supply-detail record modal patterns for stock operations and applications. The entry is surfaced from `我的` and the list page contains the add button.

## Data Model

V1 tables:

- `medicine_categories`
- `medicine_catalogs`
- `medicine_aliases`
- `medicine_photos`
- `medicine_holdings`
- `medicine_stock_logs`
- `medicine_use_applications`

The implementation will not create database views initially. Summary payloads will be assembled with SQLAlchemy aggregate queries to keep the migration small and easier to verify. Views can be added later if query cost warrants it.

## Permission Model

Logged-in, profile-completed members can read medicine lists, details, holdings, logs, and related applications. A user can mutate a holding only when they are the current holder, except admin exceptional operations. A non-holder can submit applications against a specific active holding with available stock. Admin endpoints use existing `require_admin`.

## Testing

Backend starts with `backend/tests/test_medicines_api.py`, covering create/list/detail, stock mutation, distribution/transfer, applications, and admin archive/delete guardrails. Frontend starts with API route tests and page tests for the list add entry and role-dependent holding actions.
