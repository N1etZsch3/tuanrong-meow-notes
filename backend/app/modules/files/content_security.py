import hashlib
import json
import threading
import time
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import parse, request
from urllib.error import URLError

from app.core.config import Settings, get_settings
from app.core.errors import APIError, ErrorCode

WECHAT_STABLE_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/stable_token"
WECHAT_MEDIA_CHECK_URL = "https://api.weixin.qq.com/wxa/media_check_async"


@dataclass(frozen=True)
class MediaCheckSubmission:
    trace_id: str


class ContentSecurityClient(Protocol):
    def submit_image(
        self,
        *,
        media_url: str,
        openid: str,
        scene: int,
    ) -> MediaCheckSubmission:
        ...


_token_lock = threading.Lock()
_token_cache: dict[str, tuple[str, float]] = {}


def _post_json(url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(http_request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class WeChatContentSecurityClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def submit_image(
        self,
        *,
        media_url: str,
        openid: str,
        scene: int,
    ) -> MediaCheckSubmission:
        access_token = self._get_access_token()
        url = f"{WECHAT_MEDIA_CHECK_URL}?{parse.urlencode({'access_token': access_token})}"
        try:
            payload = _post_json(
                url,
                {
                    "media_url": media_url,
                    "media_type": 2,
                    "version": 2,
                    "scene": scene,
                    "openid": openid,
                },
                self.settings.wechat_content_security_timeout_seconds,
            )
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise APIError(
                code=ErrorCode.FILE_SECURITY_UNAVAILABLE,
                message="图片安全审核服务暂不可用，请稍后重试",
                status_code=502,
            ) from exc

        trace_id = str(payload.get("trace_id") or "").strip()
        if payload.get("errcode") or not trace_id:
            raise APIError(
                code=ErrorCode.FILE_SECURITY_UNAVAILABLE,
                message="图片安全审核服务暂不可用，请稍后重试",
                status_code=502,
            )
        return MediaCheckSubmission(trace_id=trace_id)

    def _get_access_token(self) -> str:
        appid = self.settings.wechat_miniapp_appid
        secret = self.settings.wechat_miniapp_secret
        if not appid or not secret:
            raise APIError(
                code=ErrorCode.FILE_SECURITY_UNAVAILABLE,
                message="图片安全审核服务未配置",
                status_code=500,
            )

        now = time.monotonic()
        cached = _token_cache.get(appid)
        if cached and cached[1] > now:
            return cached[0]

        with _token_lock:
            now = time.monotonic()
            cached = _token_cache.get(appid)
            if cached and cached[1] > now:
                return cached[0]
            try:
                payload = _post_json(
                    WECHAT_STABLE_TOKEN_URL,
                    {
                        "grant_type": "client_credential",
                        "appid": appid,
                        "secret": secret,
                        "force_refresh": False,
                    },
                    self.settings.wechat_content_security_timeout_seconds,
                )
            except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
                raise APIError(
                    code=ErrorCode.FILE_SECURITY_UNAVAILABLE,
                    message="图片安全审核服务暂不可用，请稍后重试",
                    status_code=502,
                ) from exc

            access_token = str(payload.get("access_token") or "").strip()
            if payload.get("errcode") or not access_token:
                raise APIError(
                    code=ErrorCode.FILE_SECURITY_UNAVAILABLE,
                    message="图片安全审核服务暂不可用，请稍后重试",
                    status_code=502,
                )
            expires_in = max(int(payload.get("expires_in") or 7200), 300)
            _token_cache[appid] = (access_token, now + expires_in - 120)
            return access_token


def get_content_security_client() -> ContentSecurityClient:
    return WeChatContentSecurityClient()


def verify_callback_signature(
    *,
    token: str,
    signature: str,
    timestamp: str,
    nonce: str,
) -> bool:
    if not token or not signature or not timestamp or not nonce:
        return False
    source = "".join(sorted((token, timestamp, nonce)))
    expected = hashlib.sha1(source.encode("utf-8")).hexdigest()
    return expected == signature
