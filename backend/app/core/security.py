from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import get_settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(
    *,
    user_id: UUID,
    student_no: str,
    role: str,
    token_version: int,
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(tz=UTC)
    expires_at = now + (
        expires_delta or timedelta(seconds=settings.access_token_expire_seconds)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "student_no": student_no,
        "role": role,
        "token_version": token_version,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def is_invalid_token_error(exc: Exception) -> bool:
    return isinstance(exc, InvalidTokenError)
