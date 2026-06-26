from app.modules.auth.models import User
from app.modules.auth.service import clean_initial_display_text, clean_initial_text


def dashboard_payload(user: User) -> dict:
    profile = user.profile
    return {
        "profile": {
            "user_id": user.id,
            "student_no": user.student_no,
            "meow_no": user.student_no,
            "nickname": clean_initial_display_text(profile.nickname if profile else None),
            "avatar_url": profile.avatar_url if profile else None,
            "department": clean_initial_text(profile.department if profile else None),
            "role": user.role,
            "show_admin_entry": user.role in {"admin", "super_admin"},
        },
        "stats": {
            "total_completed_tasks": 0,
            "monthly_completed_tasks": 0,
            "current_in_progress_tasks": 0,
            "total_observation_records": 0,
            "favorite_cats": 0,
        },
        "todo": {
            "unread_notifications": 0,
            "pending_assignments": 0,
            "today_duty_count": 0,
            "in_progress_task_count": 0,
        },
        "recent_tasks": [],
        "recent_notifications": [],
    }


def empty_page_payload(*, page: int, page_size: int) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return {
        "items": [],
        "page": page,
        "page_size": page_size,
        "total": 0,
        "has_more": False,
    }
