from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class UploadedFileRef(BaseModel):
    file_id: UUID | None = None
    file_url: str = Field(min_length=1, max_length=1024)
    thumbnail_url: str | None = Field(default=None, max_length=1024)
    cos_object_key: str | None = Field(default=None, max_length=512)


class TaskPhotoRequest(UploadedFileRef):
    photo_type: str = Field(default="scene", max_length=32)
    caption: str | None = Field(default=None, max_length=255)
    sort_order: int = 0
    is_cover: bool = False


class TaskMapPointRequest(BaseModel):
    campus_id: UUID | None = None
    area_id: UUID | None = None
    lng: float
    lat: float
    location_name: str = Field(min_length=1, max_length=128)
    location_detail: str | None = None
    route_instruction: str | None = None
    landmark_hint: str | None = None
    entrance_hint: str | None = None
    amap_poi_id: str | None = Field(default=None, max_length=128)
    amap_address: str | None = Field(default=None, max_length=255)


class SummerFeedingTaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default="暑假投喂", max_length=500)
    required_items: str | None = Field(default="猫粮、水", max_length=255)
    map_point_id: UUID | None = None
    map_point: TaskMapPointRequest | None = None
    execute_dates: list[date] = Field(min_length=1)
    photos: list[TaskPhotoRequest] = Field(default_factory=list)
    is_public: bool = True

    @field_validator("title", "description", "required_items")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class SummerFeedingTaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    required_items: str | None = Field(default=None, max_length=255)
    map_point: TaskMapPointRequest | None = None
    execute_dates: list[date] | None = None
    photos: list[TaskPhotoRequest] | None = None

    @field_validator("title", "description", "required_items")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class TaskStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(in_progress|completed|cancelled|archived)$")
    reason: str | None = Field(default=None, max_length=500)


class TaskCheckinRequest(BaseModel):
    execute_date: date | None = None
    is_completed: bool = True
    process_result: str | None = Field(default=None, max_length=500)
    remark: str | None = Field(default=None, max_length=500)
    photos: list[UploadedFileRef] = Field(default_factory=list)
    checkin_lng: float | None = None
    checkin_lat: float | None = None

    @field_validator("process_result", "remark")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value
