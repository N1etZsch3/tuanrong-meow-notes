"""Medicine holding permission guards."""

from __future__ import annotations

from app.core.errors import APIError
from app.modules.auth.models import User
from app.modules.medicines.common import MEDICINE_ERROR_HOLDING_FORBIDDEN
from app.modules.medicines.models import MedicineHolding


def _require_active_holding(holding: MedicineHolding) -> None:
    if holding.status not in {"active", "empty"}:
        raise APIError(
            code=MEDICINE_ERROR_HOLDING_FORBIDDEN,
            message="无权操作该库存",
            status_code=403,
        )


def _require_holder_or_admin(holding: MedicineHolding, user: User) -> None:
    if holding.holder_id == user.id or user.role in {"admin", "super_admin"}:
        return
    raise APIError(
        code=MEDICINE_ERROR_HOLDING_FORBIDDEN,
        message="无权操作该库存",
        status_code=403,
    )
