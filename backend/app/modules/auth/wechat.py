import json
from typing import Any
from urllib import parse, request
from urllib.error import URLError

from app.core.config import Settings, get_settings
from app.core.errors import APIError, ErrorCode

WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


def _fetch_json(url: str, timeout: float) -> dict[str, Any]:
    with request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def exchange_wechat_code_for_openid(
    code: str,
    *,
    settings: Settings | None = None,
) -> str:
    settings = settings or get_settings()
    if not settings.wechat_miniapp_appid or not settings.wechat_miniapp_secret:
        raise APIError(
            code=ErrorCode.SERVER_ERROR,
            message="微信登录服务未配置",
            status_code=500,
        )

    query = parse.urlencode(
        {
            "appid": settings.wechat_miniapp_appid,
            "secret": settings.wechat_miniapp_secret,
            "js_code": code,
            "grant_type": "authorization_code",
        }
    )
    url = f"{WECHAT_CODE2SESSION_URL}?{query}"

    try:
        payload = _fetch_json(url, settings.wechat_code2session_timeout_seconds)
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise APIError(
            code=ErrorCode.SERVER_ERROR,
            message="微信登录服务暂不可用",
            status_code=502,
        ) from exc

    if payload.get("errcode") or not payload.get("openid"):
        raise APIError(
            code=ErrorCode.PARAM_ERROR,
            message="微信登录凭证无效",
            status_code=400,
        )

    return str(payload["openid"])
