"""Task-module permission predicates."""

from __future__ import annotations

from app.modules.auth.models import User
from app.modules.tasks.models import TaskCheckinPhoto


def is_admin(user: User | None) -> bool:
    return user is not None and user.role in {"admin", "super_admin"}


def can_delete_checkin_photo(photo: TaskCheckinPhoto, viewer: User | None) -> bool:
    return bool(is_admin(viewer) or (viewer is not None and photo.uploaded_by == viewer.id))
