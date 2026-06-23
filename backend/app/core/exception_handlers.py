from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import APIError, ErrorCode
from app.core.responses import api_error_response

HTTP_ERROR_CODE_MAP = {
    400: ErrorCode.PARAM_ERROR,
    401: ErrorCode.UNAUTHENTICATED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.RESOURCE_NOT_FOUND,
    409: ErrorCode.RESOURCE_EXISTS,
    423: ErrorCode.ACCOUNT_LOCKED,
}

HTTP_ERROR_MESSAGE_MAP = {
    400: "参数错误",
    401: "未登录",
    403: "权限不足",
    404: "资源不存在",
    409: "资源已存在",
    423: "登录失败次数过多，账号临时锁定",
}


def get_trace_id(request: Request) -> str:
    return getattr(request.state, "trace_id", "")


async def api_error_handler(request: Request, exc: APIError):
    return api_error_response(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        data=exc.data,
        trace_id=get_trace_id(request),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError):
    return api_error_response(
        status_code=422,
        code=ErrorCode.PARAM_ERROR,
        message="参数错误",
        data={"errors": jsonable_encoder(exc.errors())},
        trace_id=get_trace_id(request),
    )


async def http_error_handler(request: Request, exc: StarletteHTTPException):
    code = int(HTTP_ERROR_CODE_MAP.get(exc.status_code, ErrorCode.SERVER_ERROR))
    message = HTTP_ERROR_MESSAGE_MAP.get(exc.status_code, str(exc.detail) or "服务端异常")
    return api_error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
        trace_id=get_trace_id(request),
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    return api_error_response(
        status_code=500,
        code=ErrorCode.SERVER_ERROR,
        message="服务端异常",
        trace_id=get_trace_id(request),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
