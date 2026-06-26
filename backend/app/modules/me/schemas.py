from uuid import UUID

from pydantic import BaseModel


class MeProfile(BaseModel):
    user_id: UUID
    student_no: str
    meow_no: str
    nickname: str
    avatar_url: str | None
    department: str | None
    role: str
    show_admin_entry: bool


class MeStats(BaseModel):
    total_completed_tasks: int
    monthly_completed_tasks: int
    current_in_progress_tasks: int
    total_observation_records: int
    favorite_cats: int


class MeTodo(BaseModel):
    unread_notifications: int
    pending_assignments: int
    today_duty_count: int
    in_progress_task_count: int


class MeDashboard(BaseModel):
    profile: MeProfile
    stats: MeStats
    todo: MeTodo
    recent_tasks: list[dict]
    recent_notifications: list[dict]


class EmptyPage(BaseModel):
    items: list[dict]
    page: int
    page_size: int
    total: int
    has_more: bool
