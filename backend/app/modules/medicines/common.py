"""Medicines module shared constants and small pure helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

MEDICINE_ERROR_NOT_FOUND = 66003
MEDICINE_ERROR_CATEGORY_INVALID = 66002
MEDICINE_ERROR_ALREADY_HELD = 66009
MEDICINE_ERROR_STOCK_NOT_ENOUGH = 66005
MEDICINE_ERROR_HOLDING_FORBIDDEN = 66006
MEDICINE_ERROR_APPLICATION_NOT_FOUND = 66015
MEDICINE_ERROR_APPLICATION_FORBIDDEN = 66016
MEDICINE_ERROR_APPLICATION_CHANGED = 66017
MEDICINE_ERROR_APPLICATION_EXPIRED = 66018
MEDICINE_ERROR_APPLY_TO_SELF = 66020
MEDICINE_ERROR_HAS_STOCK = 66013
MEDICINE_ERROR_HAS_PENDING_APPLICATION = 66014
MEDICINE_ERROR_HOLDING_DELETE_NON_EMPTY = 66022
DEFAULT_CATEGORY_NAME = "其他"

DEFAULT_CATEGORIES = [
    ("抗生素", "antibiotic"),
    ("消炎药", "anti_inflammatory"),
    ("止疼药", "painkiller"),
    ("驱虫药", "deworming"),
    ("外用消毒", "external_disinfection"),
    ("眼耳用药", "eye_ear"),
    ("营养补充", "nutrition"),
    ("其他", "other"),
]
MEDICINE_PHOTO_LIMIT = 5

OPERATION_LABELS = {
    "initial_in": "初始入库",
    "purchase": "购入",
    "use_self": "使用",
    "scrap": "报废",
    "distribute_out": "分配转出",
    "distribute_in": "分配转入",
    "transfer_out": "转交转出",
    "transfer_in": "转交转入",
    "application_use": "申请使用",
    "adjustment": "库存校正",
    "archive": "归档记录",
    "delete_holding": "删除持有库存记录",
}


def _now() -> datetime:
    return datetime.now(UTC)


def _parse_operated_at(value: str | None) -> datetime:
    if not value:
        return _now()
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _as_aware(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _quantity(value: Decimal | int | float | None) -> int | float:
    if value is None:
        return 0
    decimal_value = Decimal(str(value))
    if decimal_value == decimal_value.to_integral_value():
        return int(decimal_value)
    return float(decimal_value)


def _operation_label(operation_type: str) -> str:
    return OPERATION_LABELS.get(operation_type, operation_type)
