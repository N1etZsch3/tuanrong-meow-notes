from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import APIError, ErrorCode
from app.core.security import decode_access_token, is_invalid_token_error
from app.db.session import get_db
from app.modules.auth.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise APIError(code=ErrorCode.UNAUTHENTICATED, message="未登录", status_code=401)

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(str(payload.get("sub")))
    except Exception as exc:
        if is_invalid_token_error(exc) or isinstance(exc, ValueError | TypeError):
            raise APIError(
                code=ErrorCode.TOKEN_INVALID,
                message="Token 无效或已过期",
                status_code=401,
            ) from exc
        raise

    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise APIError(code=ErrorCode.TOKEN_INVALID, message="Token 无效或已过期", status_code=401)
    if user.status != "active":
        raise APIError(code=ErrorCode.ACCOUNT_DISABLED, message="账号已被禁用", status_code=403)
    if int(payload.get("token_version", -1)) != user.token_version:
        raise APIError(code=ErrorCode.TOKEN_INVALID, message="Token 无效或已过期", status_code=401)
    return user


def require_password_changed(user: User = Depends(get_current_user)) -> User:
    if user.must_change_password:
        raise APIError(
            code=ErrorCode.MUST_CHANGE_PASSWORD,
            message="请先修改初始密码",
            status_code=403,
        )
    return user


def require_profile_completed(user: User = Depends(require_password_changed)) -> User:
    if not user.profile or not user.profile.profile_completed:
        raise APIError(
            code=ErrorCode.PROFILE_INCOMPLETE,
            message="请先完成个人资料初始化",
            status_code=403,
        )
    return user


def require_admin(user: User = Depends(require_password_changed)) -> User:
    if user.role not in {"admin", "super_admin"}:
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)
    return user
