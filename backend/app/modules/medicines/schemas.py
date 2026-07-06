from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


class MedicineCatalogCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    category_id: UUID | None = None
    specification: str | None = Field(default=None, max_length=128)
    unit: str = Field(min_length=1, max_length=32)
    description: str | None = Field(default=None, max_length=1000)
    usage_notes: str | None = Field(default=None, max_length=1000)
    cover_image_url: str | None = Field(default=None, max_length=512)

    @field_validator(
        "name",
        "specification",
        "unit",
        "description",
        "usage_notes",
        "cover_image_url",
    )
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineCreateRequest(BaseModel):
    medicine_id: UUID | None = None
    catalog: MedicineCatalogCreateRequest | None = None
    holder_id: UUID | None = None
    initial_quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("remark")
    @classmethod
    def strip_remark(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_catalog_mode(self) -> "MedicineCreateRequest":
        if self.medicine_id is None and self.catalog is None:
            raise ValueError("catalog is required when medicine_id is empty")
        return self


class MedicinePurchaseRequest(BaseModel):
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    source: str | None = Field(default=None, max_length=255)
    unit_price: Decimal | None = Field(default=None, ge=0)
    operated_at: str | None = None
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("source", "remark")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineUseRequest(BaseModel):
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reason_type: str | None = Field(default="free_text", max_length=64)
    reason_text: str = Field(min_length=1, max_length=500)
    usage_description: str | None = Field(default=None, max_length=1000)
    related_task_id: UUID | None = None
    operated_at: str | None = None
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("reason_type", "reason_text", "usage_description", "remark")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineScrapRequest(BaseModel):
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reason_type: str = Field(min_length=1, max_length=64)
    reason_text: str = Field(min_length=1, max_length=500)
    operated_at: str | None = None
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("reason_type", "reason_text", "remark")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineAdjustmentRequest(BaseModel):
    quantity: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    reason_text: str = Field(min_length=1, max_length=500)
    operated_at: str | None = None
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("reason_text", "remark")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineDistributeRequest(BaseModel):
    target_user_id: UUID
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    remark: str | None = Field(default=None, max_length=500)
    operated_at: str | None = None

    @field_validator("remark")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineTransferRequest(BaseModel):
    target_user_id: UUID
    reason: str = Field(min_length=1, max_length=500)
    operated_at: str | None = None

    @field_validator("reason")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineApplicationCreateRequest(BaseModel):
    quantity: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reason_type: str | None = Field(default="free_text", max_length=64)
    reason_text: str = Field(min_length=1, max_length=500)
    usage_description: str | None = Field(default=None, max_length=1000)
    requested_use_at: str | None = None
    related_task_id: UUID | None = None
    remark: str | None = Field(default=None, max_length=500)

    @field_validator("reason_type", "reason_text", "usage_description", "remark")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineApplicationReviewRequest(BaseModel):
    review_comment: str | None = Field(default=None, max_length=500)
    operated_at: str | None = None

    @field_validator("review_comment")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineApplicationRejectRequest(BaseModel):
    review_comment: str = Field(min_length=1, max_length=500)

    @field_validator("review_comment")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineApplicationCancelRequest(BaseModel):
    cancel_reason: str | None = Field(default=None, max_length=500)

    @field_validator("cancel_reason")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineCategoryCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    code: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int = 0

    @field_validator("name", "code", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineCategoryUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    code: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=500)
    sort_order: int | None = None

    @field_validator("name", "code", "description")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineCategoryStatusRequest(BaseModel):
    is_enabled: bool


class MedicineCatalogUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    category_id: UUID | None = None
    specification: str | None = Field(default=None, max_length=128)
    unit: str | None = Field(default=None, min_length=1, max_length=32)
    description: str | None = Field(default=None, max_length=1000)
    usage_notes: str | None = Field(default=None, max_length=1000)
    cover_image_url: str | None = Field(default=None, max_length=512)

    @field_validator(
        "name",
        "specification",
        "unit",
        "description",
        "usage_notes",
        "cover_image_url",
    )
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MedicineArchiveRequest(BaseModel):
    archive_reason: str = Field(min_length=1, max_length=500)

    @field_validator("archive_reason")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value
