from app.core.config import get_settings
from app.core.errors import APIError, ErrorCode
from app.modules.files.storage import ObjectStorage, TencentCosObjectStorage


def get_object_storage() -> ObjectStorage:
    return TencentCosObjectStorage(get_settings())


def get_optional_object_storage() -> ObjectStorage | None:
    try:
        return get_object_storage()
    except APIError as exc:
        if exc.code == int(ErrorCode.FILE_COS_UPLOAD_FAILED):
            return None
        raise
