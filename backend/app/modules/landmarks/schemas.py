from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UploadedFileRef(BaseModel):
    file_id: UUID | None = None
    file_url: str = Field(min_length=1, max_length=1024)
    thumbnail_url: str | None = Field(default=None, max_length=1024)
    cos_object_key: str | None = Field(default=None, max_length=512)


class LandmarkMapPointCreateRequest(BaseModel):
    campus_id: UUID | None = None
    area_id: UUID | None = None
    lng: float
    lat: float
    location_name: str = Field(min_length=1, max_length=128)
    location_detail: str = Field(min_length=1, max_length=255)
    route_instruction: str | None = None
    landmark_hint: str | None = None
    entrance_hint: str | None = None
    amap_poi_id: str | None = Field(default=None, max_length=128)
    amap_address: str | None = Field(default=None, max_length=255)
    tencent_poi_id: str | None = Field(default=None, max_length=128)
    tencent_poi_name: str | None = Field(default=None, max_length=128)
    tencent_poi_address: str | None = Field(default=None, max_length=255)
    tencent_poi_category: str | None = Field(default=None, max_length=128)
    tencent_poi_lng: float | None = None
    tencent_poi_lat: float | None = None
    tencent_poi_distance_meters: int | None = None
    tencent_poi_match_method: str | None = Field(default=None, max_length=32)


class LandmarkMapPointUpdateRequest(BaseModel):
    area_id: UUID | None = None
    lng: float | None = None
    lat: float | None = None
    location_name: str | None = Field(default=None, max_length=128)
    location_detail: str | None = Field(default=None, max_length=255)
    route_instruction: str | None = None
    landmark_hint: str | None = None
    entrance_hint: str | None = None
    amap_poi_id: str | None = Field(default=None, max_length=128)
    amap_address: str | None = Field(default=None, max_length=255)
    tencent_poi_id: str | None = Field(default=None, max_length=128)
    tencent_poi_name: str | None = Field(default=None, max_length=128)
    tencent_poi_address: str | None = Field(default=None, max_length=255)
    tencent_poi_category: str | None = Field(default=None, max_length=128)
    tencent_poi_lng: float | None = None
    tencent_poi_lat: float | None = None
    tencent_poi_distance_meters: int | None = None
    tencent_poi_match_method: str | None = Field(default=None, max_length=32)


class LandmarkPhotoRequest(UploadedFileRef):
    photo_type: str = Field(default="scene", max_length=32)
    caption: str | None = Field(default=None, max_length=255)
    sort_order: int = 0
    is_cover: bool = False


class LandmarkCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    map_point: LandmarkMapPointCreateRequest
    photos: list[LandmarkPhotoRequest] = Field(default_factory=list)
    is_public: bool = True

    @field_validator("name", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class LandmarkUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    map_point: LandmarkMapPointUpdateRequest | None = None
    photos: list[LandmarkPhotoRequest] | None = None
    is_public: bool | None = None

    @field_validator("name", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value
