from enum import IntEnum
from typing import Any


class ErrorCode(IntEnum):
    PARAM_ERROR = 40001
    MISSING_REQUIRED_PARAM = 40002
    CAPTCHA_ERROR = 40003
    CAPTCHA_EXPIRED = 40004
    AGREEMENT_REQUIRED = 40005
    UNAUTHENTICATED = 40101
    TOKEN_INVALID = 40102
    INVALID_CREDENTIALS = 40103
    MUST_CHANGE_PASSWORD = 40301
    FORBIDDEN = 40302
    ACCOUNT_DISABLED = 40303
    RESOURCE_NOT_FOUND = 40401
    RESOURCE_EXISTS = 40901
    ACCOUNT_LOCKED = 42301
    SERVER_ERROR = 50001


class APIError(Exception):
    def __init__(
        self,
        *,
        code: int | ErrorCode,
        message: str,
        status_code: int = 400,
        data: Any = None,
    ) -> None:
        self.code = int(code)
        self.message = message
        self.status_code = status_code
        self.data = data
        super().__init__(message)
