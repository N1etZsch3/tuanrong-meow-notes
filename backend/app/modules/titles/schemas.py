from uuid import UUID

from pydantic import BaseModel, Field


class TitleHolder(BaseModel):
    user_id: UUID
    meow_no: str
    nickname: str


class TitleCatalogItem(BaseModel):
    key: str
    label: str
    shield: str
    is_available: bool
    holder: TitleHolder | None


class TitleCatalogResponse(BaseModel):
    items: list[TitleCatalogItem]


class SetMemberTitleRequest(BaseModel):
    title: str | None = Field(default=None, max_length=64)
