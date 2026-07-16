"""Medicines module facade.

Keeps the public surface routes and tests already import (including the row-locked
fetch helpers ``_holding_for_update_or_raise`` / ``_application_or_raise`` that tests
compile-check), while implementation lives in the subdomain services:

- query_service.py        read-only catalog/log/application queries, DB pagination
- catalog_service.py      药品主档 create/edit/archive/delete transactions
- category_service.py     分类 seeding, listing, admin CRUD
- holding_service.py      row-locked holding fetch + mutation primitives + 删除持有
- stock_service.py        采购/使用/报废/校正/分配/转交 (row-locked, one tx each)
- application_service.py  用药申请 create/approve/reject/cancel (row-locked)
- presenters.py           ORM → response payloads, no DB access
- permissions.py          holding permission guards
- common.py               error codes / labels / small pure helpers
"""

from app.modules.medicines.application_service import (
    _application_or_raise,
    approve_application,
    cancel_application,
    create_application,
    reject_application,
)
from app.modules.medicines.catalog_service import (
    archive_catalog,
    create_medicine,
    delete_catalog,
    update_catalog,
)
from app.modules.medicines.category_service import (
    create_category,
    ensure_default_categories,
    list_categories,
    update_category,
    update_category_status,
)
from app.modules.medicines.common import (
    DEFAULT_CATEGORIES,
    DEFAULT_CATEGORY_NAME,
    MEDICINE_ERROR_ALREADY_HELD,
    MEDICINE_ERROR_APPLICATION_CHANGED,
    MEDICINE_ERROR_APPLICATION_EXPIRED,
    MEDICINE_ERROR_APPLICATION_FORBIDDEN,
    MEDICINE_ERROR_APPLICATION_NOT_FOUND,
    MEDICINE_ERROR_APPLY_TO_SELF,
    MEDICINE_ERROR_CATEGORY_INVALID,
    MEDICINE_ERROR_HAS_PENDING_APPLICATION,
    MEDICINE_ERROR_HAS_STOCK,
    MEDICINE_ERROR_HOLDING_DELETE_NON_EMPTY,
    MEDICINE_ERROR_HOLDING_FORBIDDEN,
    MEDICINE_ERROR_NOT_FOUND,
    MEDICINE_ERROR_STOCK_NOT_ENOUGH,
    MEDICINE_PHOTO_LIMIT,
)
from app.modules.medicines.holding_service import (
    _holding_for_update_or_raise,
    delete_holding,
)
from app.modules.medicines.query_service import (
    get_application_detail,
    get_holding_detail,
    get_medicine_detail,
    list_applications,
    list_holding_logs,
    list_medicine_holdings,
    list_medicine_logs,
    list_medicines,
    search_medicines,
)
from app.modules.medicines.stock_service import (
    adjust_holding,
    distribute_holding,
    record_purchase,
    record_scrap,
    record_use,
    transfer_holding,
)

__all__ = [
    "DEFAULT_CATEGORIES",
    "DEFAULT_CATEGORY_NAME",
    "MEDICINE_ERROR_ALREADY_HELD",
    "MEDICINE_ERROR_APPLICATION_CHANGED",
    "MEDICINE_ERROR_APPLICATION_EXPIRED",
    "MEDICINE_ERROR_APPLICATION_FORBIDDEN",
    "MEDICINE_ERROR_APPLICATION_NOT_FOUND",
    "MEDICINE_ERROR_APPLY_TO_SELF",
    "MEDICINE_ERROR_CATEGORY_INVALID",
    "MEDICINE_ERROR_HAS_PENDING_APPLICATION",
    "MEDICINE_ERROR_HAS_STOCK",
    "MEDICINE_ERROR_HOLDING_DELETE_NON_EMPTY",
    "MEDICINE_ERROR_HOLDING_FORBIDDEN",
    "MEDICINE_ERROR_NOT_FOUND",
    "MEDICINE_ERROR_STOCK_NOT_ENOUGH",
    "MEDICINE_PHOTO_LIMIT",
    "_application_or_raise",
    "_holding_for_update_or_raise",
    "adjust_holding",
    "approve_application",
    "archive_catalog",
    "cancel_application",
    "create_application",
    "create_category",
    "create_medicine",
    "delete_catalog",
    "delete_holding",
    "distribute_holding",
    "ensure_default_categories",
    "get_application_detail",
    "get_holding_detail",
    "get_medicine_detail",
    "list_applications",
    "list_categories",
    "list_holding_logs",
    "list_medicine_holdings",
    "list_medicine_logs",
    "list_medicines",
    "record_purchase",
    "record_scrap",
    "record_use",
    "reject_application",
    "search_medicines",
    "transfer_holding",
    "update_catalog",
    "update_category",
    "update_category_status",
]
