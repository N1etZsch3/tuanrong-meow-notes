from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings
from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import User
from app.modules.files.image_processor import ProcessedImage, process_image
from app.modules.files.models import FileAsset, FileAssetVariant
from app.modules.files.presets import (
    DEFAULT_MAX_BATCH_COUNT,
    IMAGE_PRESETS,
    SCENE_VARIANT_MAP,
    USAGE_TYPE_CONFIGS,
)
from app.modules.files.storage import ObjectStorage

OWNER_TYPES = {
    "user",
    "cat",
    "map_point",
    "task",
    "task_checkin",
    "observation",
    "supply_point",
    "supply_point_record",
    "temporary",
}
VISIBILITIES = {"private", "internal", "public"}


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def upload_image(
    *,
    db: Session,
    file: UploadFile,
    usage_type: str,
    owner_type: str | None,
    owner_id: UUID | None,
    visibility: str | None,
    current_user: User,
    storage: ObjectStorage,
    settings: Settings,
) -> dict:
    usage = _validate_upload_request(
        usage_type=usage_type,
        owner_type=owner_type,
        visibility=visibility,
        current_user=current_user,
    )
    max_size = min(usage.max_file_size_bytes, settings.file_upload_max_bytes)
    file_bytes = file.file.read()
    if not file_bytes:
        raise APIError(code=ErrorCode.FILE_EMPTY, message="文件不能为空", status_code=400)
    if len(file_bytes) > max_size:
        raise APIError(code=ErrorCode.FILE_TOO_LARGE, message="文件大小超过限制", status_code=400)

    preset = IMAGE_PRESETS.get(usage.process_preset)
    if preset is None:
        raise APIError(
            code=ErrorCode.FILE_PRESET_UNSUPPORTED,
            message="图片处理预设不支持",
            status_code=400,
        )
    processed = process_image(
        file_bytes=file_bytes,
        preset=preset,
        max_pixels=settings.file_image_max_pixels,
    )
    asset_id = uuid4()
    final_owner_type = owner_type or "temporary"
    uploaded_keys: list[str] = []
    uploaded_urls: dict[str, str] = {}
    try:
        for variant in processed.variants:
            object_key = build_object_key(
                env=settings.tencent_cos_env_prefix,
                owner_type=final_owner_type,
                owner_id=owner_id,
                uploaded_by=current_user.id,
                asset_id=asset_id,
                variant_key=variant.variant_key,
            )
            uploaded_urls[variant.variant_key] = storage.put_object(
                object_key=object_key,
                body=variant.body,
                content_type=variant.mime_type,
            )
            uploaded_keys.append(object_key)
    except APIError:
        _cleanup_uploaded_objects(storage, uploaded_keys)
        raise
    except Exception as exc:
        _cleanup_uploaded_objects(storage, uploaded_keys)
        raise APIError(
            code=ErrorCode.FILE_COS_UPLOAD_FAILED,
            message="上传 COS 失败",
            status_code=500,
        ) from exc

    asset = _asset_from_processed(
        asset_id=asset_id,
        processed=processed,
        usage_type=usage_type,
        owner_type=final_owner_type,
        owner_id=owner_id,
        visibility=visibility or "internal",
        source_filename=file.filename,
        current_user=current_user,
        settings=settings,
        uploaded_urls=uploaded_urls,
        uploaded_keys=uploaded_keys,
    )
    try:
        db.add(asset)
        db.commit()
        db.refresh(asset)
    except SQLAlchemyError as exc:
        db.rollback()
        _cleanup_uploaded_objects(storage, uploaded_keys)
        raise APIError(
            code=ErrorCode.FILE_METADATA_WRITE_FAILED,
            message="文件元数据写入失败",
            status_code=500,
        ) from exc

    return asset_payload(asset)


def batch_upload_images(
    *,
    db: Session,
    files: list[UploadFile],
    usage_type: str,
    owner_type: str | None,
    owner_id: UUID | None,
    visibility: str | None,
    current_user: User,
    storage: ObjectStorage,
    settings: Settings,
) -> dict:
    usage = USAGE_TYPE_CONFIGS.get(usage_type)
    max_count = usage.max_batch_count if usage else DEFAULT_MAX_BATCH_COUNT
    if not files:
        raise APIError(code=ErrorCode.FILE_EMPTY, message="文件不能为空", status_code=400)
    if len(files) > max_count:
        raise APIError(
            code=ErrorCode.FILE_COUNT_EXCEEDED,
            message="文件数量超过限制",
            status_code=400,
        )
    items = [
        upload_image(
            db=db,
            file=file,
            usage_type=usage_type,
            owner_type=owner_type,
            owner_id=owner_id,
            visibility=visibility,
            current_user=current_user,
            storage=storage,
            settings=settings,
        )
        for file in files
    ]
    return {"items": items, "total": len(items)}


def get_asset(db: Session, asset_id: UUID, current_user: User) -> dict:
    asset = _load_asset(db, asset_id)
    _ensure_asset_access(asset, current_user)
    return asset_payload(asset)


def get_asset_variant(
    *,
    db: Session,
    asset_id: UUID,
    current_user: User,
    scene: str | None,
    variant_key: str | None,
    storage: ObjectStorage | None,
) -> dict:
    asset = _load_asset(db, asset_id)
    _ensure_asset_access(asset, current_user)
    variant = _select_variant(asset=asset, scene=scene, variant_key=variant_key)
    return selected_variant_payload(asset, variant, storage=storage)


def get_asset_content_url(
    *,
    db: Session,
    asset_id: UUID,
    scene: str | None,
    variant_key: str | None,
    storage: ObjectStorage | None,
) -> dict:
    asset = _load_asset(db, asset_id)
    if asset.visibility not in {"internal", "public"}:
        raise APIError(
            code=ErrorCode.FILE_FORBIDDEN,
            message="无权访问该文件",
            status_code=403,
        )
    variant = _select_variant(asset=asset, scene=scene, variant_key=variant_key)
    return selected_variant_payload(asset, variant, storage=storage)


def get_asset_content_bytes(
    *,
    db: Session,
    asset_id: UUID,
    scene: str | None,
    variant_key: str | None,
    storage: ObjectStorage,
) -> dict:
    asset = _load_asset(db, asset_id)
    if asset.visibility not in {"internal", "public"}:
        raise APIError(
            code=ErrorCode.FILE_FORBIDDEN,
            message="无权访问该文件",
            status_code=403,
        )
    variant = _select_variant(asset=asset, scene=scene, variant_key=variant_key)
    return {
        "asset_id": asset.id,
        "variant_key": variant.variant_key,
        "body": storage.get_object(variant.object_key),
        "mime_type": variant.mime_type,
        "size_bytes": variant.size_bytes,
    }


def list_assets(
    *,
    db: Session,
    current_user: User,
    owner_type: str | None,
    owner_id: UUID | None,
    usage_type: str | None,
    process_status: str,
    uploaded_by: UUID | None,
    include_deleted: bool,
    page: int,
    page_size: int,
) -> dict:
    query = db.query(FileAsset).options(selectinload(FileAsset.variants))
    if owner_type:
        _validate_owner_type(owner_type)
        query = query.filter(FileAsset.owner_type == owner_type)
    if owner_id:
        query = query.filter(FileAsset.owner_id == owner_id)
    if usage_type:
        _validate_usage_type(usage_type)
        query = query.filter(FileAsset.usage_type == usage_type)
    if process_status:
        query = query.filter(FileAsset.process_status == process_status)
    if not include_deleted:
        query = query.filter(FileAsset.deleted_at.is_(None))
    if current_user.role not in {"admin", "super_admin"}:
        query = query.filter(FileAsset.uploaded_by == current_user.id)
    elif uploaded_by:
        query = query.filter(FileAsset.uploaded_by == uploaded_by)

    total = query.count()
    safe_page_size = min(max(page_size, 1), 100)
    safe_page = max(page, 1)
    items = (
        query.order_by(FileAsset.created_at.desc())
        .offset((safe_page - 1) * safe_page_size)
        .limit(safe_page_size)
        .all()
    )
    return {
        "items": [asset_summary_payload(asset) for asset in items],
        "page": safe_page,
        "page_size": safe_page_size,
        "total": total,
        "has_more": safe_page * safe_page_size < total,
    }


def bind_asset_owner(
    *,
    db: Session,
    asset_id: UUID,
    owner_type: str,
    owner_id: UUID,
    usage_type: str | None,
    current_user: User,
) -> dict:
    _validate_owner_type(owner_type)
    if usage_type:
        _validate_usage_type(usage_type)
    asset = _load_asset(db, asset_id)
    _ensure_asset_access(asset, current_user)
    if asset.owner_type not in {None, "temporary", owner_type} and asset.owner_id != owner_id:
        raise APIError(
            code=ErrorCode.FILE_ALREADY_BOUND,
            message="图片已经绑定到其他业务对象",
            status_code=409,
        )
    asset.owner_type = owner_type
    asset.owner_id = owner_id
    if usage_type:
        asset.usage_type = usage_type
    db.commit()
    db.refresh(asset)
    return {
        "asset_id": asset.id,
        "owner_type": asset.owner_type,
        "owner_id": asset.owner_id,
        "usage_type": asset.usage_type,
    }


def delete_asset(db: Session, asset_id: UUID, current_user: User) -> dict:
    asset = _load_asset(db, asset_id, allow_deleted=True)
    if asset.deleted_at is not None:
        raise APIError(code=ErrorCode.FILE_DELETED, message="文件已被删除", status_code=409)
    _ensure_asset_owner_or_admin(asset, current_user)
    deleted_at = now_utc()
    asset.process_status = "deleted"
    asset.deleted_at = deleted_at
    for variant in asset.variants:
        variant.deleted_at = deleted_at
    db.commit()
    db.refresh(asset)
    return {"asset_id": asset.id, "deleted": True, "deleted_at": deleted_at}


def build_object_key(
    *,
    env: str,
    owner_type: str,
    owner_id: UUID | None,
    uploaded_by: UUID,
    asset_id: UUID,
    variant_key: str,
) -> str:
    owner_segment = str(owner_id or uploaded_by)
    return f"catmap/{env}/{owner_type}/{owner_segment}/{asset_id}/{variant_key}.jpg"


def asset_payload(asset: FileAsset) -> dict:
    variants = {
        variant.variant_key: variant_payload(variant)
        for variant in asset.variants
        if variant.deleted_at is None
    }
    return {
        "asset_id": asset.id,
        "usage_type": asset.usage_type,
        "owner_type": asset.owner_type,
        "owner_id": asset.owner_id,
        "process_preset": asset.process_preset,
        "process_status": asset.process_status,
        "default_variant_key": asset.default_variant_key,
        "default_thumb_variant_key": asset.default_thumb_variant_key,
        "default_url": asset.default_url,
        "default_thumb_url": asset.default_thumb_url,
        "variants": variants,
        "source": {
            "source_filename": asset.source_filename,
            "source_mime_type": asset.source_mime_type,
            "source_size_bytes": asset.source_size_bytes,
            "source_width": asset.source_width,
            "source_height": asset.source_height,
        },
        "created_at": asset.created_at,
    }


def asset_summary_payload(asset: FileAsset) -> dict:
    return {
        "asset_id": asset.id,
        "usage_type": asset.usage_type,
        "owner_type": asset.owner_type,
        "owner_id": asset.owner_id,
        "process_status": asset.process_status,
        "default_url": asset.default_url,
        "default_thumb_url": asset.default_thumb_url,
        "created_at": asset.created_at,
    }


def variant_payload(variant: FileAssetVariant) -> dict:
    return {
        "variant_key": variant.variant_key,
        "url": variant.url,
        "width": variant.width,
        "height": variant.height,
        "size_bytes": variant.size_bytes,
        "mime_type": variant.mime_type,
    }


def selected_variant_payload(
    asset: FileAsset,
    variant: FileAssetVariant,
    *,
    storage: ObjectStorage | None = None,
) -> dict:
    return {
        "asset_id": asset.id,
        "variant_key": variant.variant_key,
        "url": storage.presign_get_object(variant.object_key) if storage else variant.url,
        "width": variant.width,
        "height": variant.height,
    }


def _validate_upload_request(
    *,
    usage_type: str,
    owner_type: str | None,
    visibility: str | None,
    current_user: User,
) -> object:
    usage = _validate_usage_type(usage_type)
    _validate_owner_type(owner_type or "temporary")
    if visibility and visibility not in VISIBILITIES:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    if current_user.role not in usage.allowed_roles:
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)
    if (
        usage_type != "user_avatar"
        and current_user.role not in {"admin", "super_admin"}
        and (not current_user.profile or not current_user.profile.profile_completed)
    ):
        raise APIError(
            code=ErrorCode.PROFILE_INCOMPLETE,
            message="请先完成个人资料初始化",
            status_code=403,
        )
    return usage


def _validate_usage_type(usage_type: str):
    usage = USAGE_TYPE_CONFIGS.get(usage_type)
    if usage is None:
        raise APIError(
            code=ErrorCode.FILE_USAGE_UNSUPPORTED,
            message="图片用途类型不支持",
            status_code=400,
        )
    return usage


def _validate_owner_type(owner_type: str) -> None:
    if owner_type not in OWNER_TYPES:
        raise APIError(
            code=ErrorCode.FILE_OWNER_UNSUPPORTED,
            message="图片归属类型不支持",
            status_code=400,
        )


def _asset_from_processed(
    *,
    asset_id: UUID,
    processed: ProcessedImage,
    usage_type: str,
    owner_type: str,
    owner_id: UUID | None,
    visibility: str,
    source_filename: str | None,
    current_user: User,
    settings: Settings,
    uploaded_urls: dict[str, str],
    uploaded_keys: list[str],
) -> FileAsset:
    usage = USAGE_TYPE_CONFIGS[usage_type]
    preset = IMAGE_PRESETS[usage.process_preset]
    asset = FileAsset(
        id=asset_id,
        storage_provider="tencent_cos",
        bucket=settings.tencent_cos_bucket or "test-bucket",
        region=settings.tencent_cos_region,
        env=settings.tencent_cos_env_prefix,
        usage_type=usage_type,
        owner_type=owner_type,
        owner_id=owner_id,
        source_filename=source_filename,
        source_mime_type=processed.source_mime_type,
        source_size_bytes=processed.source_size_bytes,
        source_width=processed.source_width,
        source_height=processed.source_height,
        source_checksum_sha256=processed.source_checksum_sha256,
        default_variant_key=preset.default_variant_key,
        default_url=uploaded_urls.get(preset.default_variant_key),
        default_thumb_variant_key=preset.default_thumb_variant_key,
        default_thumb_url=uploaded_urls.get(preset.default_thumb_variant_key),
        process_preset=usage.process_preset,
        process_status="completed",
        visibility=visibility,
        uploaded_by=current_user.id,
    )
    object_key_by_variant = {
        key.rsplit("/", 1)[-1].removesuffix(".jpg"): key for key in uploaded_keys
    }
    for sort_order, variant in enumerate(processed.variants):
        asset.variants.append(
            FileAssetVariant(
                variant_key=variant.variant_key,
                object_key=object_key_by_variant[variant.variant_key],
                url=uploaded_urls[variant.variant_key],
                mime_type=variant.mime_type,
                file_ext=variant.file_ext,
                width=variant.width,
                height=variant.height,
                size_bytes=variant.size_bytes,
                quality=variant.quality,
                resize_mode=variant.resize_mode,
                checksum_sha256=variant.checksum_sha256,
                sort_order=sort_order,
            )
        )
    return asset


def _load_asset(db: Session, asset_id: UUID, allow_deleted: bool = False) -> FileAsset:
    asset = (
        db.query(FileAsset)
        .options(selectinload(FileAsset.variants))
        .filter(FileAsset.id == asset_id)
        .one_or_none()
    )
    if asset is None:
        raise APIError(
            code=ErrorCode.FILE_ASSET_NOT_FOUND,
            message="文件资产不存在",
            status_code=404,
        )
    if not allow_deleted and asset.deleted_at is not None:
        raise APIError(code=ErrorCode.FILE_DELETED, message="文件已被删除", status_code=409)
    if asset.process_status == "processing":
        raise APIError(code=ErrorCode.FILE_PROCESSING, message="文件正在处理中", status_code=409)
    return asset


def _ensure_asset_access(asset: FileAsset, current_user: User) -> None:
    if current_user.role in {"admin", "super_admin"}:
        return
    if asset.uploaded_by == current_user.id:
        return
    if asset.visibility in {"internal", "public"}:
        return
    raise APIError(code=ErrorCode.FILE_FORBIDDEN, message="无权访问该文件", status_code=403)


def _ensure_asset_owner_or_admin(asset: FileAsset, current_user: User) -> None:
    if current_user.role in {"admin", "super_admin"} or asset.uploaded_by == current_user.id:
        return
    raise APIError(code=ErrorCode.FILE_FORBIDDEN, message="无权访问该文件", status_code=403)


def _find_variant(asset: FileAsset, variant_key: str) -> FileAssetVariant | None:
    return next(
        (
            variant
            for variant in asset.variants
            if variant.variant_key == variant_key and variant.deleted_at is None
        ),
        None,
    )


def _select_variant(
    *,
    asset: FileAsset,
    scene: str | None,
    variant_key: str | None,
) -> FileAssetVariant:
    if not scene and not variant_key:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    if scene and scene not in SCENE_VARIANT_MAP and not variant_key:
        raise APIError(
            code=ErrorCode.FILE_SCENE_UNSUPPORTED,
            message="图片访问场景不支持",
            status_code=400,
        )

    selected_key = variant_key or SCENE_VARIANT_MAP[scene or ""]
    variant = _find_variant(asset, selected_key)
    if variant is None and variant_key is None:
        variant = _find_variant(asset, asset.default_thumb_variant_key)
    if variant is None:
        variant = _find_variant(asset, asset.default_variant_key)
    if variant is None:
        variant = next((item for item in asset.variants if item.deleted_at is None), None)
    if variant is None:
        raise APIError(
            code=ErrorCode.FILE_VARIANT_NOT_FOUND,
            message="图片变体不存在",
            status_code=400,
        )
    return variant


def _cleanup_uploaded_objects(storage: ObjectStorage, object_keys: list[str]) -> None:
    for object_key in object_keys:
        storage.delete_object(object_key)
