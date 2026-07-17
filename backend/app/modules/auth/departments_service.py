"""成员多部门读写 helper（按功能拆分，供 profile 自助与管理员路径复用）。"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.auth.models import User, UserDepartment


def _clean_departments(departments: list[str] | None) -> list[str]:
    """清洗部门列表：去空白、去重、保持顺序。"""
    if not departments:
        return []
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in departments:
        value = (raw or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        cleaned.append(value)
    return cleaned


def user_department_names(user: User) -> list[str]:
    """按 sort_order 返回用户当前部门名列表。"""
    return [item.department for item in sorted(user.departments, key=lambda d: d.sort_order)]


def primary_department(user: User) -> str | None:
    names = user_department_names(user)
    return names[0] if names else None


def set_user_departments(db: Session, user: User, departments: list[str]) -> list[str]:
    """将用户部门整体设置为给定列表（增删对齐），并回写主部门到 profile.department。

    - 幂等：已存在的部门保留，缺失的删除，新增的插入。
    - sort_order 按传入顺序赋值，第 0 个即主部门。
    - profile.department 双写主部门，兼容仍读单值字段的旧客户端。
    """
    cleaned = _clean_departments(departments)
    existing = {item.department: item for item in user.departments}

    # 删除不再保留的部门
    for name, item in list(existing.items()):
        if name not in cleaned:
            db.delete(item)

    # 新增/更新顺序
    for index, name in enumerate(cleaned):
        item = existing.get(name)
        if item is None:
            db.add(UserDepartment(user_id=user.id, department=name, sort_order=index))
        else:
            item.sort_order = index

    # 回写主部门（兼容旧单值字段）
    if user.profile is not None:
        user.profile.department = cleaned[0] if cleaned else None

    return cleaned
