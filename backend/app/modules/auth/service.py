from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.errors import APIError, ErrorCode
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.auth.captcha import (
    create_captcha_image_data_url,
    generate_captcha_code,
    hash_captcha_code,
    verify_captcha_code,
)
from app.modules.auth.models import AdminOperationLog, AuthCaptcha, User, UserProfile
from app.modules.auth.schemas import (
    AdminCreateUserRequest,
    AdminResetPasswordRequest,
    AdminUpdateRoleRequest,
    AdminUpdateStatusRequest,
    ChangePasswordRequest,
    LoginRequest,
)

VALID_ROLES = {"member", "admin"}
VALID_STATUSES = {"active", "blocked", "left", "deleted"}


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def create_captcha(
    db: Session,
    *,
    client_ip: str | None = None,
    user_agent: str | None = None,
) -> dict:
    settings = get_settings()
    code = generate_captcha_code()
    captcha = AuthCaptcha(
        code_hash=hash_captcha_code(code),
        expires_at=now_utc() + timedelta(seconds=settings.captcha_expire_seconds),
        client_ip=client_ip,
        user_agent=user_agent,
    )
    db.add(captcha)
    db.commit()
    db.refresh(captcha)
    return {
        "captcha_id": captcha.id,
        "captcha_image": create_captcha_image_data_url(code),
        "expires_in": settings.captcha_expire_seconds,
    }


def profile_payload(profile: UserProfile | None) -> dict:
    if profile is None:
        return {
            "nickname": "",
            "avatar_url": None,
            "real_name": None,
            "department": None,
            "grade": None,
        }
    return {
        "nickname": profile.nickname,
        "avatar_url": profile.avatar_url,
        "real_name": profile.real_name,
        "department": profile.department,
        "grade": profile.grade,
    }


def login_user_payload(user: User) -> dict:
    profile = user.profile
    return {
        "id": user.id,
        "student_no": user.student_no,
        "nickname": profile.nickname if profile else "",
        "avatar_url": profile.avatar_url if profile else None,
        "role": user.role,
        "status": user.status,
    }


def current_user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "student_no": user.student_no,
        "role": user.role,
        "status": user.status,
        "must_change_password": user.must_change_password,
        "profile": profile_payload(user.profile),
    }


def validate_password_strength(password: str) -> None:
    if len(password) < 8 or len(password) > 64:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    if not any(character.isalpha() for character in password) or not any(
        character.isdigit() for character in password
    ):
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)


def get_user_by_student_no(db: Session, student_no: str) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.profile))
        .where(User.student_no == student_no, User.deleted_at.is_(None))
    )


def validate_captcha(db: Session, captcha_id: UUID, captcha_code: str) -> AuthCaptcha:
    captcha = db.get(AuthCaptcha, captcha_id)
    current_time = now_utc()
    if captcha is None or captcha.used_at is not None:
        raise APIError(code=ErrorCode.CAPTCHA_ERROR, message="验证码错误", status_code=400)
    if as_utc(captcha.expires_at) < current_time:
        raise APIError(code=ErrorCode.CAPTCHA_EXPIRED, message="验证码已过期", status_code=400)
    if not verify_captcha_code(captcha_code, captcha.code_hash):
        raise APIError(code=ErrorCode.CAPTCHA_ERROR, message="验证码错误", status_code=400)
    return captcha


def record_login_failure(db: Session, user: User | None) -> None:
    if user is None:
        return
    settings = get_settings()
    user.login_failed_count += 1
    if user.login_failed_count >= settings.auth_lock_failed_attempts:
        user.locked_until = now_utc() + timedelta(minutes=settings.auth_lock_minutes)
    db.commit()


def login(db: Session, payload: LoginRequest) -> dict:
    if not payload.agree_terms:
        raise APIError(code=ErrorCode.AGREEMENT_REQUIRED, message="未勾选协议", status_code=400)

    captcha = validate_captcha(db, payload.captcha_id, payload.captcha_code)
    user = get_user_by_student_no(db, payload.student_no)

    if user is None:
        db.commit()
        raise APIError(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="学号或密码错误",
            status_code=401,
        )
    if user.status != "active":
        db.commit()
        raise APIError(code=ErrorCode.ACCOUNT_DISABLED, message="账号已被禁用", status_code=403)
    if user.locked_until and as_utc(user.locked_until) > now_utc():
        db.commit()
        raise APIError(
            code=ErrorCode.ACCOUNT_LOCKED,
            message="登录失败次数过多，账号临时锁定",
            status_code=423,
        )
    if not verify_password(payload.password, user.password_hash):
        record_login_failure(db, user)
        raise APIError(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="学号或密码错误",
            status_code=401,
        )

    current_time = now_utc()
    captcha.used_at = current_time
    user.last_login_at = current_time
    user.login_failed_count = 0
    user.locked_until = None
    db.commit()
    db.refresh(user)

    settings = get_settings()
    return {
        "access_token": create_access_token(
            user_id=user.id,
            student_no=user.student_no,
            role=user.role,
            token_version=user.token_version,
        ),
        "token_type": "Bearer",
        "expires_in": settings.access_token_expire_seconds,
        "must_change_password": user.must_change_password,
        "user": login_user_payload(user),
    }


def renew_access_token(user: User) -> dict:
    settings = get_settings()
    return {
        "access_token": create_access_token(
            user_id=user.id,
            student_no=user.student_no,
            role=user.role,
            token_version=user.token_version,
        ),
        "token_type": "Bearer",
        "expires_in": settings.access_token_expire_seconds,
    }


def change_password(db: Session, user: User, payload: ChangePasswordRequest) -> None:
    if payload.new_password != payload.confirm_password:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    if not verify_password(payload.old_password, user.password_hash):
        raise APIError(code=ErrorCode.INVALID_CREDENTIALS, message="旧密码错误", status_code=401)
    if verify_password(payload.new_password, user.password_hash):
        raise APIError(
            code=ErrorCode.PASSWORD_REUSED,
            message="新密码不能与旧密码相同",
            status_code=409,
        )
    validate_password_strength(payload.new_password)
    user.password_hash = hash_password(payload.new_password)
    user.password_updated_at = now_utc()
    user.must_change_password = False
    user.token_version += 1
    user.login_failed_count = 0
    user.locked_until = None
    db.commit()


def log_admin_operation(
    db: Session,
    *,
    admin: User,
    operation_type: str,
    target_id: UUID | None,
    summary: str,
    before_data: dict | None = None,
    after_data: dict | None = None,
) -> None:
    db.add(
        AdminOperationLog(
            admin_id=admin.id,
            operation_type=operation_type,
            target_type="user",
            target_id=target_id,
            summary=summary,
            before_data=before_data,
            after_data=after_data,
        )
    )


def create_member_account(db: Session, admin: User, payload: AdminCreateUserRequest) -> User:
    if payload.role not in VALID_ROLES:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    validate_password_strength(payload.initial_password)
    if get_user_by_student_no(db, payload.student_no):
        raise APIError(code=ErrorCode.RESOURCE_EXISTS, message="学号已存在", status_code=409)

    user = User(
        student_no=payload.student_no,
        password_hash=hash_password(payload.initial_password),
        role=payload.role,
        status="active",
        must_change_password=payload.must_change_password,
        token_version=1,
    )
    db.add(user)
    db.flush()
    db.add(
        UserProfile(
            user_id=user.id,
            nickname=payload.profile.nickname,
            real_name=payload.profile.real_name,
            department=payload.profile.department,
            grade=payload.profile.grade,
            joined_at=payload.profile.joined_at,
        )
    )
    log_admin_operation(
        db,
        admin=admin,
        operation_type="user_create",
        target_id=user.id,
        summary=f"创建成员账号 {user.student_no}",
        after_data={"student_no": user.student_no, "role": user.role},
    )
    db.commit()
    db.refresh(user)
    return user


def list_users(
    db: Session,
    *,
    page: int,
    page_size: int,
    keyword: str | None = None,
    role: str | None = None,
    status: str | None = None,
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    statement = select(User).options(selectinload(User.profile)).where(User.deleted_at.is_(None))
    if keyword:
        like = f"%{keyword}%"
        statement = statement.join(UserProfile, isouter=True).where(
            or_(
                User.student_no.ilike(like),
                UserProfile.nickname.ilike(like),
                UserProfile.real_name.ilike(like),
            )
        )
    if role:
        statement = statement.where(User.role == role)
    if status:
        statement = statement.where(User.status == status)

    total = len(db.scalars(statement).all())
    users = db.scalars(
        statement.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": [
            {
                "id": user.id,
                "student_no": user.student_no,
                "role": user.role,
                "status": user.status,
                "must_change_password": user.must_change_password,
                "last_login_at": user.last_login_at,
                "profile": profile_payload(user.profile),
            }
            for user in users
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": page * page_size < total,
    }


def get_target_user(db: Session, user_id: UUID) -> User:
    user = db.get(User, user_id)
    if user is None or user.deleted_at is not None:
        raise APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="用户不存在", status_code=404)
    return user


def reset_user_password(
    db: Session,
    *,
    admin: User,
    user_id: UUID,
    payload: AdminResetPasswordRequest,
) -> User:
    validate_password_strength(payload.new_password)
    user = get_target_user(db, user_id)
    before = {
        "must_change_password": user.must_change_password,
        "token_version": user.token_version,
    }
    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = payload.must_change_password
    user.password_updated_at = now_utc()
    user.login_failed_count = 0
    user.locked_until = None
    user.token_version += 1
    log_admin_operation(
        db,
        admin=admin,
        operation_type="user_reset_password",
        target_id=user.id,
        summary=f"重置成员密码 {user.student_no}",
        before_data=before,
        after_data={"must_change_password": user.must_change_password},
    )
    db.commit()
    db.refresh(user)
    return user


def update_user_status(
    db: Session,
    *,
    admin: User,
    user_id: UUID,
    payload: AdminUpdateStatusRequest,
) -> User:
    if payload.status not in VALID_STATUSES:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    if admin.id == user_id:
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)
    user = get_target_user(db, user_id)
    before = {"status": user.status, "token_version": user.token_version}
    user.status = payload.status
    if payload.status != "active":
        user.token_version += 1
    log_admin_operation(
        db,
        admin=admin,
        operation_type="user_update_status",
        target_id=user.id,
        summary=f"更新成员状态 {user.student_no}",
        before_data=before,
        after_data={"status": user.status, "reason": payload.reason},
    )
    db.commit()
    db.refresh(user)
    return user


def update_user_role(
    db: Session,
    *,
    admin: User,
    user_id: UUID,
    payload: AdminUpdateRoleRequest,
) -> User:
    if payload.role not in VALID_ROLES:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    if admin.id == user_id:
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)
    user = get_target_user(db, user_id)
    before = {"role": user.role, "token_version": user.token_version}
    user.role = payload.role
    user.token_version += 1
    log_admin_operation(
        db,
        admin=admin,
        operation_type="user_update_role",
        target_id=user.id,
        summary=f"更新成员角色 {user.student_no}",
        before_data=before,
        after_data={"role": user.role},
    )
    db.commit()
    db.refresh(user)
    return user
