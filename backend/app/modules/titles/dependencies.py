from fastapi import Depends

from app.core.errors import APIError, ErrorCode
from app.modules.auth.dependencies import require_password_changed
from app.modules.auth.models import User
from app.modules.titles.constants import PRESIDENT


def require_president(user: User = Depends(require_password_changed)) -> User:
    if (
        user.role != "super_admin"
        or user.profile is None
        or user.profile.title != PRESIDENT
    ):
        raise APIError(
            code=ErrorCode.TITLE_PRESIDENT_REQUIRED,
            message="仅会长可执行此操作",
            status_code=403,
        )
    return user
