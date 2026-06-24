from uuid import UUID

from pydantic import BaseModel


class LngLat(BaseModel):
    lng: float
    lat: float


class LngLatBounds(BaseModel):
    south_west: LngLat
    north_east: LngLat


class CardAction(BaseModel):
    key: str
    label: str
    enabled: bool = True
    disabled_reason: str | None = None
    method: str | None = None
    path: str | None = None
    target_type: str


class MapPointReference(BaseModel):
    point_id: UUID
    point_type: str
    business_type: str | None = None
