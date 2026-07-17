from datetime import UTC, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.auth.departments_service import user_department_names
from app.modules.auth.models import User
from app.modules.auth.service import clean_initial_display_text, clean_initial_text
from app.modules.tasks.models import Task, TaskCheckin, TaskCheckinPhoto


def dashboard_payload(db: Session, user: User) -> dict:
    profile = user.profile
    departments = user_department_names(user)
    now = datetime.now(tz=UTC)
    month_start = datetime.combine(now.date().replace(day=1), time.min, tzinfo=UTC)
    total_completed_tasks = db.scalar(
        select(func.count(TaskCheckin.id)).where(
            TaskCheckin.submitter_id == user.id,
            TaskCheckin.deleted_at.is_(None),
            TaskCheckin.is_completed.is_(True),
        )
    ) or 0
    monthly_completed_tasks = db.scalar(
        select(func.count(TaskCheckin.id)).where(
            TaskCheckin.submitter_id == user.id,
            TaskCheckin.deleted_at.is_(None),
            TaskCheckin.is_completed.is_(True),
            TaskCheckin.submitted_at >= month_start,
        )
    ) or 0
    return {
        "profile": {
            "user_id": user.id,
            "student_no": user.student_no,
            "meow_no": user.student_no,
            "nickname": clean_initial_display_text(profile.nickname if profile else None),
            "avatar_url": profile.avatar_url if profile else None,
            "department": departments[0]
            if departments
            else clean_initial_text(profile.department if profile else None),
            "departments": departments,
            "role": user.role,
            "show_admin_entry": user.role in {"admin", "super_admin"},
        },
        "stats": {
            "total_completed_tasks": total_completed_tasks,
            "monthly_completed_tasks": monthly_completed_tasks,
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


def _checkin_photo_payload(photo: TaskCheckinPhoto) -> dict:
    return {
        "photo_id": photo.id,
        "file_url": photo.file_url,
        "thumbnail_url": photo.thumbnail_url,
        "caption": photo.caption,
        "sort_order": photo.sort_order,
    }


def checkins_page_payload(
    db: Session,
    user: User,
    *,
    page: int,
    page_size: int,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    statement = (
        select(TaskCheckin)
        .options(
            selectinload(TaskCheckin.task).selectinload(Task.map_point),
            selectinload(TaskCheckin.photos),
        )
        .where(
            TaskCheckin.submitter_id == user.id,
            TaskCheckin.deleted_at.is_(None),
            TaskCheckin.is_completed.is_(True),
        )
        .order_by(TaskCheckin.submitted_at.desc())
    )
    total = db.scalar(
        select(func.count(TaskCheckin.id)).where(
            TaskCheckin.submitter_id == user.id,
            TaskCheckin.deleted_at.is_(None),
            TaskCheckin.is_completed.is_(True),
        )
    ) or 0
    start = (page - 1) * page_size
    checkins = db.scalars(statement.offset(start).limit(page_size)).all()
    return {
        "items": [
            {
                "checkin_id": checkin.id,
                "task_id": checkin.task_id,
                "execution_date_id": checkin.task_execution_date_id,
                "task_title": checkin.task.title if checkin.task else "",
                "task_type": checkin.task.task_type if checkin.task else "feeding",
                "execute_date": checkin.execute_date.isoformat()
                if checkin.execute_date
                else None,
                "submitted_at": checkin.submitted_at,
                "process_result": checkin.process_result,
                "remark": checkin.remark,
                "map_point": (
                    {
                        "map_point_id": checkin.task.map_point.id,
                        "location_name": checkin.task.map_point.location_name,
                    }
                    if checkin.task and checkin.task.map_point
                    else None
                ),
                "photos": [
                    _checkin_photo_payload(photo)
                    for photo in sorted(checkin.photos, key=lambda item: item.sort_order)
                    if photo.deleted_at is None
                ],
            }
            for checkin in checkins
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": start + page_size < total,
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
