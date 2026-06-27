from app.core.config import get_settings
from app.modules.files.storage import ObjectStorage, TencentCosObjectStorage


def get_object_storage() -> ObjectStorage:
    return TencentCosObjectStorage(get_settings())
