from typing import Protocol

from app.core.config import Settings
from app.core.errors import APIError, ErrorCode


class ObjectStorage(Protocol):
    def put_object(self, *, object_key: str, body: bytes, content_type: str) -> str:
        ...

    def presign_get_object(self, object_key: str, *, expires: int = 3600) -> str:
        ...

    def delete_object(self, object_key: str) -> None:
        ...


class TencentCosObjectStorage:
    def __init__(self, settings: Settings) -> None:
        if not settings.tencent_cos_secret_id or not settings.tencent_cos_secret_key:
            raise APIError(
                code=ErrorCode.FILE_COS_UPLOAD_FAILED,
                message="腾讯云 COS 配置未完成",
                status_code=500,
            )
        if not settings.tencent_cos_bucket or not settings.tencent_cos_region:
            raise APIError(
                code=ErrorCode.FILE_COS_UPLOAD_FAILED,
                message="腾讯云 COS 存储桶配置未完成",
                status_code=500,
            )

        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError as exc:
            raise APIError(
                code=ErrorCode.FILE_COS_UPLOAD_FAILED,
                message="腾讯云 COS SDK 未安装",
                status_code=500,
            ) from exc

        config = CosConfig(
            Region=settings.tencent_cos_region,
            SecretId=settings.tencent_cos_secret_id,
            SecretKey=settings.tencent_cos_secret_key,
            Scheme=settings.tencent_cos_scheme,
        )
        self._client = CosS3Client(config)
        self._bucket = settings.tencent_cos_bucket
        self._base_url = (
            settings.tencent_cos_cdn_domain
            or settings.tencent_cos_domain
            or (
                f"{settings.tencent_cos_scheme}://"
                f"{settings.tencent_cos_bucket}.cos.{settings.tencent_cos_region}.myqcloud.com"
            )
        ).rstrip("/")

    def put_object(self, *, object_key: str, body: bytes, content_type: str) -> str:
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=object_key,
                Body=body,
                ContentType=content_type,
            )
        except Exception as exc:
            raise APIError(
                code=ErrorCode.FILE_COS_UPLOAD_FAILED,
                message="上传 COS 失败",
                status_code=500,
            ) from exc
        return f"{self._base_url}/{object_key}"

    def delete_object(self, object_key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=object_key)
        except Exception:
            return

    def presign_get_object(self, object_key: str, *, expires: int = 3600) -> str:
        try:
            return self._client.get_presigned_url(
                Method="GET",
                Bucket=self._bucket,
                Key=object_key,
                Expired=expires,
            )
        except Exception as exc:
            raise APIError(
                code=ErrorCode.FILE_COS_UPLOAD_FAILED,
                message="生成图片访问地址失败",
                status_code=500,
            ) from exc
