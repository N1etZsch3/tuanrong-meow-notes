from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UploadedFileRef(BaseModel):
    file_id: UUID | None = None
    file_url: str = Field(min_length=1, max_length=1024)
    thumbnail_url: str | None = Field(default=None, max_length=1024)
    cos_object_key: str | None = Field(default=None, max_length=512)


class SupplyPointMapPointRequest(BaseModel):
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


class SupplyPointItemRequest(BaseModel):
    item_name: str = Field(min_length=1, max_length=64)
    item_type: str = Field(default="custom", max_length=32)
    quantity: int = Field(default=1, ge=0)
    unit: str | None = Field(default=None, max_length=32)
    icon_key: str | None = Field(default=None, max_length=64)
    color_key: str | None = Field(default=None, max_length=32)
    is_custom: bool = False
    sort_order: int | None = None

    @field_validator("item_name", "item_type", "unit", "icon_key", "color_key")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class SupplyPointPhotoRequest(UploadedFileRef):
    photo_type: str = Field(default="scene", max_length=32)
    caption: str | None = Field(default=None, max_length=255)
    sort_order: int = 0
    is_cover: bool = False


class SupplyPointCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    usage_instruction: str | None = Field(default=None, max_length=500)
    access_instruction: str | None = Field(default=None, max_length=500)
    map_point_id: UUID | None = None
    map_point: SupplyPointMapPointRequest | None = None
    items: list[SupplyPointItemRequest] = Field(min_length=1)
    photos: list[SupplyPointPhotoRequest] = Field(default_factory=list)
    is_public: bool = True

    @field_validator("name", "description", "usage_instruction", "access_instruction")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class SupplyPointUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)
    usage_instruction: str | None = Field(default=None, max_length=500)
    access_instruction: str | None = Field(default=None, max_length=500)
    map_point: SupplyPointMapPointRequest | None = None
    items: list[SupplyPointItemRequest] | None = None
    photos: list[SupplyPointPhotoRequest] | None = None
    is_public: bool | None = None

    @field_validator("name", "description", "usage_instruction", "access_instruction")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class SupplyRecordItemRequest(BaseModel):
    item_id: UUID
    quantity: int = Field(default=1, ge=0)


class SupplyRecordCreateRequest(BaseModel):
    items: list[SupplyRecordItemRequest] = Field(min_length=1)
    photo: UploadedFileRef
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("remark")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value
