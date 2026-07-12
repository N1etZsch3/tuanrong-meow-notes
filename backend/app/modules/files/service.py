from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.errors import APIError, ErrorCode
from app.modules.auth.models import User, UserProfile
from app.modules.auth.wechat import exchange_wechat_code_for_openid
from app.modules.files.content_security import ContentSecurityClient
from app.modules.files.image_processor import ProcessedImage, process_image
from app.modules.files.models import FileAsset, FileAssetVariant
from app.modules.files.presets import (
    CONTENT_SECURITY_SCENES,
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
    "medicine_catalog",
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
    wechat_code: str | None,
    current_user: User,
    storage: ObjectStorage,
    content_security: ContentSecurityClient,
    settings: Settings,
    security_openid: str | None = None,
) -> dict:
    usage = _validate_upload_request(
        usage_type=usage_type,
        owner_type=owner_type,
        visibility=visibility,
        current_user=current_user,
    )
    final_owner_type, final_owner_id = _resolve_upload_owner(
        usage_type=usage_type,
        owner_type=owner_type,
        owner_id=owner_id,
        current_user=current_user,
    )
    security_enabled = _requires_content_security_review(usage_type, settings)
    if security_enabled:
        if security_openid is None:
            if not wechat_code:
                raise APIError(
                    code=ErrorCode.FILE_SECURITY_CODE_REQUIRED,
                    message="请重新进入小程序后再上传图片",
                    status_code=400,
                )
            security_openid = exchange_wechat_code_for_openid(wechat_code, settings=settings)
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
    uploaded_keys: list[str] = []
    uploaded_urls: dict[str, str] = {}
    try:
        for variant in processed.variants:
            object_key = build_object_key(
                env=settings.tencent_cos_env_prefix,
                owner_type=final_owner_type,
                owner_id=final_owner_id,
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
        owner_id=final_owner_id,
        visibility=visibility or "internal",
        source_filename=file.filename,
        current_user=current_user,
        settings=settings,
        uploaded_urls=uploaded_urls,
        uploaded_keys=uploaded_keys,
        security_status="pending" if security_enabled else "legacy",
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

    if security_enabled:
        default_object_key = next(
            variant.object_key
            for variant in asset.variants
            if variant.variant_key == asset.default_variant_key
        )
        try:
            submission = content_security.submit_image(
                media_url=storage.presign_get_object(default_object_key, expires=3600),
                openid=security_openid or "",
                scene=CONTENT_SECURITY_SCENES[usage_type],
            )
        except APIError:
            asset.security_status = "failed"
            asset.security_error_code = int(ErrorCode.FILE_SECURITY_UNAVAILABLE)
            asset.security_checked_at = now_utc()
            db.commit()
            _cleanup_uploaded_objects(storage, uploaded_keys)
            raise

        asset.security_provider = "wechat"
        asset.security_trace_id = submission.trace_id
        asset.security_submitted_at = now_utc()
        if usage_type == "user_avatar" and final_owner_id is not None:
            _set_avatar_review_pending(db, final_owner_id, asset)
        db.commit()
        db.refresh(asset)
    elif usage_type == "user_avatar" and final_owner_id is not None:
        _set_avatar_review_pending(db, final_owner_id, asset)
        _apply_passed_user_avatar(db, asset)
        db.commit()
        db.refresh(asset)

    return asset_payload(asset)


def batch_upload_images(
    *,
    db: Session,
    files: list[UploadFile],
    usage_type: str,
    owner_type: str | None,
    owner_id: UUID | None,
    visibility: str | None,
    wechat_code: str | None,
    current_user: User,
    storage: ObjectStorage,
    content_security: ContentSecurityClient,
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
    security_openid: str | None = None
    if _requires_content_security_review(usage_type, settings):
        if not wechat_code:
            raise APIError(
                code=ErrorCode.FILE_SECURITY_CODE_REQUIRED,
                message="请重新进入小程序后再上传图片",
                status_code=400,
            )
        security_openid = exchange_wechat_code_for_openid(wechat_code, settings=settings)
    items = [
        upload_image(
            db=db,
            file=file,
            usage_type=usage_type,
            owner_type=owner_type,
            owner_id=owner_id,
            visibility=visibility,
            wechat_code=None,
            current_user=current_user,
            storage=storage,
            content_security=content_security,
            settings=settings,
            security_openid=security_openid,
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
    _ensure_security_ready(asset)
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
    _ensure_security_ready(asset)
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
    _ensure_security_ready(asset)
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
    target_usage_type = usage_type or asset.usage_type
    if target_usage_type in CONTENT_SECURITY_SCENES and (
        asset.usage_type != target_usage_type or asset.security_status != "passed"
    ):
        raise APIError(
            code=ErrorCode.FILE_SECURITY_REJECTED,
            message="头像必须通过专用上传流程完成安全审核",
            status_code=422,
        )
    _ensure_security_ready(asset)
    if asset.owner_type not in {None, "temporary", owner_type} and asset.owner_id != owner_id:
        raise APIError(
            code=ErrorCode.FILE_ALREADY_BOUND,
            message="图片已经绑定到其他业务对象",
            status_code=409,
        )
    asset.owner_type = owner_type
    asset.owner_id = owner_id
    if usage_type:
        asset.usage_type = target_usage_type
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


def resolve_business_image(
    *,
    db: Session,
    current_user: User,
    file_id: UUID | None,
    file_url: str | None,
    thumbnail_url: str | None,
    allowed_usage_types: set[str],
) -> tuple[UUID | None, str | None, str | None]:
    """Resolve a client image reference to a canonical, publishable file asset."""
    settings = get_settings()
    asset: FileAsset | None = None
    if file_id is not None:
        asset = db.get(FileAsset, file_id)
    elif file_url:
        asset = (
            db.query(FileAsset)
            .filter(
                or_(
                    FileAsset.default_url == file_url,
                    FileAsset.default_thumb_url == file_url,
                    FileAsset.variants.any(FileAssetVariant.url == file_url),
                )
            )
            .order_by(FileAsset.created_at.desc(), FileAsset.id.desc())
            .first()
        )

    if settings.wechat_content_security_mode != "enforced":
        if asset is None or asset.deleted_at is not None:
            return file_id, file_url, thumbnail_url
        return asset.id, asset.default_url or file_url, asset.default_thumb_url or thumbnail_url

    if asset is None or asset.deleted_at is not None:
        raise APIError(
            code=ErrorCode.FILE_SECURITY_REJECTED,
            message="图片未经安全审核，请重新上传",
            status_code=422,
        )
    if asset.process_status != "completed":
        raise APIError(
            code=ErrorCode.FILE_PROCESSING,
            message="文件正在处理中",
            status_code=409,
        )
    if asset.usage_type not in allowed_usage_types:
        raise APIError(
            code=ErrorCode.FILE_SECURITY_REJECTED,
            message="图片用途与当前业务不匹配",
            status_code=422,
        )
    if current_user.role not in {"admin", "super_admin"} and asset.uploaded_by != current_user.id:
        raise APIError(
            code=ErrorCode.FILE_FORBIDDEN,
            message="无权使用该图片",
            status_code=403,
        )
    if _asset_requires_content_security_review(asset):
        _ensure_security_ready(asset)
    if not asset.default_url:
        raise APIError(
            code=ErrorCode.FILE_PROCESSING,
            message="文件正在处理中",
            status_code=409,
        )
    return asset.id, asset.default_url, asset.default_thumb_url


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
    security_ready = _is_security_ready(asset)
    security_status = _public_security_status(asset)
    variants = {
        variant.variant_key: variant_payload(variant, include_url=security_ready)
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
        "default_url": asset.default_url if security_ready else None,
        "default_thumb_url": asset.default_thumb_url if security_ready else None,
        "security_status": security_status,
        "review_message": security_review_message(security_status),
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
    security_ready = _is_security_ready(asset)
    return {
        "asset_id": asset.id,
        "usage_type": asset.usage_type,
        "owner_type": asset.owner_type,
        "owner_id": asset.owner_id,
        "process_status": asset.process_status,
        "default_url": asset.default_url if security_ready else None,
        "default_thumb_url": asset.default_thumb_url if security_ready else None,
        "security_status": _public_security_status(asset),
        "created_at": asset.created_at,
    }


def variant_payload(variant: FileAssetVariant, *, include_url: bool = True) -> dict:
    return {
        "variant_key": variant.variant_key,
        "url": variant.url if include_url else None,
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


def security_review_message(status: str) -> str:
    if status == "pending":
        return "图片已上传，审核通过后自动生效"
    if status in {"rejected", "failed"}:
        return "图片包含违规内容，请更换后重试"
    return ""


def handle_security_callback(db: Session, payload: dict) -> dict:
    trace_id = str(payload.get("trace_id") or "").strip()
    if not trace_id:
        raise APIError(
            code=ErrorCode.FILE_SECURITY_CALLBACK_INVALID,
            message="图片审核回调无效",
            status_code=400,
        )
    asset = db.query(FileAsset).filter(FileAsset.security_trace_id == trace_id).one_or_none()
    if asset is None:
        return {"matched": False, "trace_id": trace_id}

    if not _asset_requires_content_security_review(asset):
        asset.security_status = "legacy"
        db.commit()
        return {
            "matched": True,
            "asset_id": asset.id,
            "security_status": "legacy",
        }

    if asset.security_status in {"passed", "rejected"}:
        return {
            "matched": True,
            "asset_id": asset.id,
            "security_status": asset.security_status,
        }

    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    errcode = int(payload.get("errcode") or 0)
    suggest = str(result.get("suggest") or "").strip().lower()
    label_value = result.get("label")
    label = (
        int(label_value)
        if isinstance(label_value, int | str) and str(label_value).isdigit()
        else None
    )

    asset.security_error_code = errcode
    asset.security_suggest = suggest or None
    asset.security_label = label
    asset.security_checked_at = now_utc()
    if errcode == 0 and suggest == "pass":
        asset.security_status = "passed"
        _apply_passed_user_avatar(db, asset)
    elif errcode == 0 and suggest in {"risky", "review"}:
        asset.security_status = "rejected"
        _record_avatar_review_result(db, asset, "rejected")
    else:
        asset.security_status = "failed"
        _record_avatar_review_result(db, asset, "failed")
    db.commit()
    db.refresh(asset)
    return {
        "matched": True,
        "asset_id": asset.id,
        "security_status": asset.security_status,
    }


def _set_avatar_review_pending(db: Session, user_id: UUID, asset: FileAsset) -> None:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).one_or_none()
    if profile is None:
        raise APIError(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message="用户资料不存在",
            status_code=404,
        )
    profile.avatar_review_asset_id = asset.id
    profile.avatar_review_status = "pending"
    profile.avatar_review_updated_at = now_utc()


def _apply_passed_user_avatar(db: Session, asset: FileAsset) -> None:
    if asset.usage_type != "user_avatar" or asset.owner_type != "user" or asset.owner_id is None:
        return
    profile = db.query(UserProfile).filter(UserProfile.user_id == asset.owner_id).one_or_none()
    if profile is None or profile.avatar_review_asset_id != asset.id:
        return
    profile.avatar_asset_id = asset.id
    profile.avatar_url = f"/api/v1/files/assets/{asset.id}/content?scene=avatar_profile"
    profile.avatar_thumb_url = f"/api/v1/files/assets/{asset.id}/content?scene=avatar_in_list"
    profile.avatar_review_status = "passed"
    profile.avatar_review_updated_at = now_utc()


def _record_avatar_review_result(db: Session, asset: FileAsset, status: str) -> None:
    if asset.usage_type != "user_avatar" or asset.owner_type != "user" or asset.owner_id is None:
        return
    profile = db.query(UserProfile).filter(UserProfile.user_id == asset.owner_id).one_or_none()
    if profile is None or profile.avatar_review_asset_id != asset.id:
        return
    profile.avatar_review_status = status
    profile.avatar_review_updated_at = now_utc()


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


def _resolve_upload_owner(
    *,
    usage_type: str,
    owner_type: str | None,
    owner_id: UUID | None,
    current_user: User,
) -> tuple[str, UUID | None]:
    if usage_type != "user_avatar":
        return owner_type or "temporary", owner_id
    if owner_type not in {None, "user"}:
        raise APIError(
            code=ErrorCode.FILE_OWNER_UNSUPPORTED,
            message="头像归属类型不支持",
            status_code=400,
        )
    target_user_id = owner_id or current_user.id
    if current_user.role not in {"admin", "super_admin"} and target_user_id != current_user.id:
        raise APIError(code=ErrorCode.FILE_FORBIDDEN, message="无权修改该头像", status_code=403)
    return "user", target_user_id


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
    security_status: str,
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
        security_status=security_status,
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


def _ensure_security_ready(asset: FileAsset) -> None:
    if _is_security_ready(asset):
        return
    if asset.security_status == "pending":
        raise APIError(
            code=ErrorCode.FILE_SECURITY_PENDING,
            message="图片正在进行安全审核",
            status_code=409,
        )
    raise APIError(
        code=ErrorCode.FILE_SECURITY_REJECTED,
        message="图片包含违规内容，请更换后重试",
        status_code=422,
    )


def _requires_content_security_review(usage_type: str, settings: Settings) -> bool:
    return (
        settings.wechat_content_security_mode == "enforced"
        and usage_type in CONTENT_SECURITY_SCENES
    )


def _asset_requires_content_security_review(asset: FileAsset) -> bool:
    return asset.usage_type in CONTENT_SECURITY_SCENES


def _is_security_ready(asset: FileAsset) -> bool:
    return not _asset_requires_content_security_review(asset) or asset.security_status in {
        "legacy",
        "passed",
    }


def _public_security_status(asset: FileAsset) -> str:
    return asset.security_status if _asset_requires_content_security_review(asset) else "legacy"


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
