from pydantic import BaseModel


class PublicStats(BaseModel):
    in_campus_cats: int
    neuter_rate: float
    adopted_cats: int
    watching_cats: int
    total_cats: int


class PublicCatListItem(BaseModel):
    cat_id: str
    name: str
    avatar_url: str | None = None
    coat_color: str
    sex: str
    neuter_status: str
    status: str
    personality_tags: list[str] = []
    alias_summary: str | None = None


class PublicCatPhoto(BaseModel):
    file_url: str
    caption: str | None = None


class PublicCatDetail(BaseModel):
    cat_id: str
    name: str
    aliases: list[str] = []
    avatar_url: str | None = None
    photos: list[PublicCatPhoto] = []
    coat_color: str
    sex: str
    neuter_status: str
    status: str
    personality_tags: list[str] = []
    story: str | None = None


class PublicCatList(BaseModel):
    items: list[PublicCatListItem]
    page: int
    page_size: int
    total: int
    has_more: bool


class PublicPostCard(BaseModel):
    post_id: str
    post_type: str
    title: str
    summary: str | None = None
    cover_url: str | None = None
    published_at: str | None = None


class PublicPostBlock(BaseModel):
    block_type: str
    text: str | None = None
    image_url: str | None = None


class PublicPostDetail(BaseModel):
    post_id: str
    post_type: str
    title: str
    summary: str | None = None
    cover_url: str | None = None
    published_at: str | None = None
    blocks: list[PublicPostBlock] = []


class PublicPostList(BaseModel):
    items: list[PublicPostCard]
    page: int
    page_size: int
    total: int
    has_more: bool
