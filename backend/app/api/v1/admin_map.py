from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_admin
from app.modules.auth.models import User
from app.modules.map import service

router = APIRouter(tags=["Admin Map"])


class AdminMapPointUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area_id: UUID | None = None
    point_type: str | None = None
    point_scope: str | None = None
    name: str | None = Field(default=None, max_length=128)
    subtitle: str | None = Field(default=None, max_length=255)
    description: str | None = None
    location_name: str | None = Field(default=None, max_length=128)
    location_detail: str | None = None
    amap_poi_id: str | None = Field(default=None, max_length=128)
    amap_address: str | None = Field(default=None, max_length=255)
    route_instruction: str | None = None
    landmark_hint: str | None = None
    entrance_hint: str | None = None
    icon_key: str | None = Field(default=None, max_length=64)
    display_level: int | None = None
    label_min_zoom: int | None = None
    preview_enabled: bool | None = None
    preview_min_zoom: int | None = None
    visibility: str | None = None
    status: str | None = None

    def compact_payload(self) -> dict[str, Any]:
        return self.model_dump(exclude_unset=True)


class AdminMapPointLocationUpdateRequest(BaseModel):
    lng: float
    lat: float


@router.get("/points/{point_id}", summary="Get admin map point detail")
def get_admin_map_point(
    point_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.admin_point_detail(db, point_id=point_id)
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/points/{point_id}", summary="Update admin map point")
def update_admin_map_point(
    point_id: UUID,
    payload: AdminMapPointUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_admin_point(
        db,
        point_id=point_id,
        admin=admin,
        payload=payload.compact_payload(),
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.patch("/points/{point_id}/location", summary="Update admin map point location")
def update_admin_map_point_location(
    point_id: UUID,
    payload: AdminMapPointLocationUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    data = service.update_admin_point_location(
        db,
        point_id=point_id,
        admin=admin,
        lng=payload.lng,
        lat=payload.lat,
    )
    return api_success(data=data, trace_id=request.state.trace_id)

