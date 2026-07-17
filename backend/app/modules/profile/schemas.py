from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

Department = Literal["生存保障部", "活动部", "宣传部", "秘书部", "养护部"]


class ProfileResponse(BaseModel):
    user_id: UUID
    student_no: str
    meow_no: str
    role: str
    nickname: str
    avatar_url: str | None
    avatar_review_asset_id: UUID | None = None
    avatar_review_status: str = "idle"
    department: str | None
    departments: list[str] = Field(default_factory=list)
    contact_info: str | None
    profile_completed: bool
    profile_completed_at: datetime | None


class CompleteProfileRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=512)
    department: Department | None = None
    departments: list[Department] = Field(default_factory=list, max_length=5)
    contact_info: str = Field(pattern=r"^1[3-9]\d{9}$")

    def resolved_departments(self) -> list[Department]:
        """兼容旧客户端：只传 department 单值时视为单元素列表。"""
        if self.departments:
            return self.departments
        return [self.department] if self.department else []

    @model_validator(mode="after")
    def _require_at_least_one_department(self) -> "CompleteProfileRequest":
        if not self.resolved_departments():
            raise ValueError("至少选择一个部门")
        return self


class UpdateProfileRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=512)
    department: Department | None = None
    departments: list[Department] | None = Field(default=None, max_length=5)
    contact_info: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")


class CompleteProfileResponse(BaseModel):
    profile_completed: bool
    next_action: str
