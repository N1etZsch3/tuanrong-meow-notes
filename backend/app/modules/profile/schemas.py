from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

Department = Literal["生存保障部", "活动部", "宣传部", "秘书部", "养护部"]


class ProfileResponse(BaseModel):
    user_id: UUID
    student_no: str
    meow_no: str
    role: str
    nickname: str
    avatar_url: str | None
    department: str | None
    contact_info: str | None
    profile_completed: bool
    profile_completed_at: datetime | None


class CompleteProfileRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=512)
    department: Department
    contact_info: str = Field(pattern=r"^1[3-9]\d{9}$")


class UpdateProfileRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=512)
    department: Department | None = None
    contact_info: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")


class CompleteProfileResponse(BaseModel):
    profile_completed: bool
    next_action: str
