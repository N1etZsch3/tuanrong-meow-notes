from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_password_changed
from app.modules.auth.models import User
from app.modules.files import service
from app.modules.files.dependencies import get_object_storage
from app.modules.files.presets import upload_config_payload
from app.modules.files.storage import ObjectStorage

router = APIRouter(tags=["Files"])


class BindAssetOwnerRequest(BaseModel):
    owner_type: str
    owner_id: UUID
    usage_type: str | None = None


@router.get("/config", summary="Get image upload config")
def get_file_upload_config(
    request: Request,
    current_user: User = Depends(require_password_changed),
):
    return api_success(data=upload_config_payload(), trace_id=request.state.trace_id)


@router.post("/images", summary="Upload one image")
def upload_image(
    request: Request,
    file: UploadFile = File(...),
    usage_type: str = Form(...),
    owner_type: str | None = Form(default=None),
    owner_id: UUID | None = Form(default=None),
    visibility: str | None = Form(default="internal"),
    caption: str | None = Form(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    storage: ObjectStorage = Depends(get_object_storage),
    current_user: User = Depends(require_password_changed),
):
    data = service.upload_image(
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
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/images/batch", summary="Upload multiple images")
def batch_upload_images(
    request: Request,
    files: list[UploadFile] = File(...),
    usage_type: str = Form(...),
    owner_type: str | None = Form(default=None),
    owner_id: UUID | None = Form(default=None),
    visibility: str | None = Form(default="internal"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    storage: ObjectStorage = Depends(get_object_storage),
    current_user: User = Depends(require_password_changed),
):
    data = service.batch_upload_images(
        db=db,
        files=files,
        usage_type=usage_type,
        owner_type=owner_type,
        owner_id=owner_id,
        visibility=visibility,
        current_user=current_user,
        storage=storage,
        settings=settings,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/assets", summary="List image assets")
def list_assets(
    request: Request,
    owner_type: str | None = None,
    owner_id: UUID | None = None,
    usage_type: str | None = None,
    process_status: str = "completed",
    uploaded_by: UUID | None = None,
    include_deleted: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    data = service.list_assets(
        db=db,
        current_user=current_user,
        owner_type=owner_type,
        owner_id=owner_id,
        usage_type=usage_type,
        process_status=process_status,
        uploaded_by=uploaded_by,
        include_deleted=include_deleted,
        page=page,
        page_size=page_size,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/assets/{asset_id}", summary="Get image asset detail")
def get_asset(
    asset_id: UUID,
    request: Request,
    include_variants: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    return api_success(
        data=service.get_asset(db, asset_id, current_user),
        trace_id=request.state.trace_id,
    )


@router.get("/assets/{asset_id}/variant", summary="Get image variant URL")
def get_asset_variant(
    asset_id: UUID,
    request: Request,
    scene: str | None = None,
    variant_key: str | None = None,
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
    current_user: User = Depends(require_password_changed),
):
    data = service.get_asset_variant(
        db=db,
        asset_id=asset_id,
        current_user=current_user,
        scene=scene,
        variant_key=variant_key,
        storage=storage,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.get("/assets/{asset_id}/content", summary="Redirect to displayable image content URL")
def get_asset_content(
    asset_id: UUID,
    scene: str | None = None,
    variant_key: str | None = None,
    db: Session = Depends(get_db),
    storage: ObjectStorage = Depends(get_object_storage),
):
    data = service.get_asset_content_url(
        db=db,
        asset_id=asset_id,
        scene=scene,
        variant_key=variant_key,
        storage=storage,
    )
    return RedirectResponse(data["url"])


@router.patch("/assets/{asset_id}/owner", summary="Bind image asset owner")
def bind_asset_owner(
    asset_id: UUID,
    payload: BindAssetOwnerRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    data = service.bind_asset_owner(
        db=db,
        asset_id=asset_id,
        owner_type=payload.owner_type,
        owner_id=payload.owner_id,
        usage_type=payload.usage_type,
        current_user=current_user,
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.delete("/assets/{asset_id}", summary="Delete image asset")
def delete_asset(
    asset_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_password_changed),
):
    data = service.delete_asset(db, asset_id, current_user)
    return api_success(data=data, trace_id=request.state.trace_id)
