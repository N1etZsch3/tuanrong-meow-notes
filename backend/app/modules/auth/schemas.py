from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CaptchaResponse(BaseModel):
    captcha_id: UUID
    captcha_image: str
    expires_in: int


class LoginRequest(BaseModel):
    student_no: str | None = Field(default=None, min_length=1, max_length=64)
    meow_no: str | None = Field(default=None, min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=64)
    captcha_id: UUID
    captcha_code: str = Field(min_length=1, max_length=8)
    agree_terms: bool
    wechat_code: str | None = Field(default=None, min_length=1, max_length=256)
    agree_wechat_bind: bool = False

    @model_validator(mode="after")
    def require_account_identifier(self) -> "LoginRequest":
        if not self.student_no and not self.meow_no:
            raise ValueError("meow_no is required")
        if self.student_no and self.meow_no and self.student_no != self.meow_no:
            raise ValueError("student_no and meow_no must match")
        return self

    @property
    def account_no(self) -> str:
        return self.meow_no or self.student_no or ""


class LoginUser(BaseModel):
    id: UUID
    student_no: str
    meow_no: str
    nickname: str
    avatar_url: str | None
    role: str
    status: str
    profile_completed: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    must_change_password: bool
    next_action: str
    user: LoginUser


class RenewAccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class WeChatLoginRequest(BaseModel):
    code: str = Field(min_length=1, max_length=256)


class CurrentUserProfile(BaseModel):
    nickname: str
    avatar_url: str | None = None
    avatar_review_asset_id: UUID | None = None
    avatar_review_status: str = "idle"
    real_name: str | None = None
    department: str | None = None
    grade: str | None = None
    contact_info: str | None = None


class CurrentUserResponse(BaseModel):
    id: UUID
    student_no: str
    meow_no: str
    role: str
    status: str
    must_change_password: bool
    profile_completed: bool
    profile: CurrentUserProfile


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=64)
    new_password: str = Field(min_length=8, max_length=20)
    confirm_password: str = Field(min_length=8, max_length=20)


class ChangePasswordResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    must_change_password: bool
    profile_completed: bool
    token_invalidated: bool
    next_action: str


class AdminUserProfileRequest(BaseModel):
    nickname: str = Field(default="", max_length=64)
    avatar_url: str | None = Field(default=None, max_length=512)
    real_name: str | None = Field(default=None, max_length=64)
    department: str | None = Field(default=None, max_length=128)
    grade: str | None = Field(default=None, max_length=32)
    joined_at: date | None = None
    contact_info: str | None = Field(default=None, max_length=128)


class AdminCreateUserRequest(BaseModel):
    student_no: str | None = Field(default=None, min_length=1, max_length=64)
    meow_no: str | None = Field(default=None, min_length=1, max_length=64)
    initial_password: str | None = Field(default=None, min_length=8, max_length=20)
    role: str = "member"
    profile: AdminUserProfileRequest = Field(default_factory=AdminUserProfileRequest)
    must_change_password: bool = True

    @model_validator(mode="after")
    def match_account_identifiers(self) -> "AdminCreateUserRequest":
        if self.student_no and self.meow_no and self.student_no != self.meow_no:
            raise ValueError("student_no and meow_no must match")
        return self

    @property
    def account_no(self) -> str | None:
        return self.meow_no or self.student_no


class AdminRestoreUserRequest(BaseModel):
    initial_password: str | None = Field(default=None, min_length=8, max_length=20)


class AdminUserItem(BaseModel):
    id: UUID
    student_no: str
    meow_no: str
    role: str
    status: str
    must_change_password: bool
    profile_completed: bool
    last_login_at: datetime | None
    wechat_bound: bool
    profile: CurrentUserProfile

    model_config = ConfigDict(from_attributes=True)


class AdminCreateUserResponse(BaseModel):
    id: UUID
    student_no: str
    meow_no: str
    role: str
    status: str
    must_change_password: bool


class AdminUserListResponse(BaseModel):
    items: list[AdminUserItem]
    page: int
    page_size: int
    total: int
    has_more: bool


class AdminUpdateUserRequest(BaseModel):
    role: str | None = None
    status: str | None = None
    profile: AdminUserProfileRequest | None = None


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=20)
    must_change_password: bool = True


class AdminResetPasswordResponse(BaseModel):
    user_id: UUID
    must_change_password: bool


class AdminClearWeChatBindingResponse(BaseModel):
    user_id: UUID
    wechat_bound: bool
    token_version: int


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
