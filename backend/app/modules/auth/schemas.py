from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CaptchaResponse(BaseModel):
    captcha_id: UUID
    captcha_image: str
    expires_in: int


class LoginRequest(BaseModel):
    student_no: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=64)
    captcha_id: UUID
    captcha_code: str = Field(min_length=1, max_length=8)
    agree_terms: bool


class LoginUser(BaseModel):
    id: UUID
    student_no: str
    nickname: str
    avatar_url: str | None
    role: str
    status: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    must_change_password: bool
    user: LoginUser


class CurrentUserProfile(BaseModel):
    nickname: str
    avatar_url: str | None = None
    real_name: str | None = None
    department: str | None = None
    grade: str | None = None


class CurrentUserResponse(BaseModel):
    id: UUID
    student_no: str
    role: str
    status: str
    must_change_password: bool
    profile: CurrentUserProfile


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=64)
    new_password: str = Field(min_length=8, max_length=64)
    confirm_password: str = Field(min_length=8, max_length=64)


class AdminUserProfileRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=64)
    real_name: str | None = Field(default=None, max_length=64)
    department: str | None = Field(default=None, max_length=128)
    grade: str | None = Field(default=None, max_length=32)
    joined_at: date | None = None


class AdminCreateUserRequest(BaseModel):
    student_no: str = Field(min_length=1, max_length=64)
    initial_password: str = Field(min_length=8, max_length=64)
    role: str = "member"
    profile: AdminUserProfileRequest
    must_change_password: bool = True


class AdminUserItem(BaseModel):
    id: UUID
    student_no: str
    role: str
    status: str
    must_change_password: bool
    last_login_at: datetime | None
    profile: CurrentUserProfile

    model_config = ConfigDict(from_attributes=True)


class AdminCreateUserResponse(BaseModel):
    id: UUID
    student_no: str
    role: str
    status: str
    must_change_password: bool


class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem]
    page: int
    page_size: int
    total: int
    has_more: bool


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=64)
    must_change_password: bool = True


class AdminResetPasswordResponse(BaseModel):
    user_id: UUID
    must_change_password: bool


class AdminUpdateStatusRequest(BaseModel):
    status: str
    reason: str | None = None


class AdminUpdateStatusResponse(BaseModel):
    user_id: UUID
    status: str


class AdminUpdateRoleRequest(BaseModel):
    role: str


class AdminUpdateRoleResponse(BaseModel):
    user_id: UUID
    role: str
