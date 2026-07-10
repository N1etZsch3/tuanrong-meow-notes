import re
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
    AdminUpdateUserRequest,
    ChangePasswordRequest,
    LoginRequest,
    WeChatLoginRequest,
)
from app.modules.auth.wechat import exchange_wechat_code_for_openid

VALID_ROLES = {"member", "summer_volunteer", "admin"}
VALID_STATUSES = {"active", "blocked", "left", "deleted"}
ADMIN_ROLES = {"admin", "super_admin"}
MEOW_NO_PREFIX = "trmx"
MEOW_NO_WIDTH = 4
PASSWORD_ALLOWED_PATTERN = re.compile(r"^[A-Za-z0-9@_!]+$")


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def clean_initial_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if stripped and set(stripped) == {"?"}:
        return None
    return value


def clean_initial_display_text(value: str | None) -> str:
    return clean_initial_text(value) or ""


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
        "contact_info": None,
        }
    return {
        "nickname": clean_initial_display_text(profile.nickname),
        "avatar_url": profile.avatar_url,
        "real_name": clean_initial_text(profile.real_name),
        "department": clean_initial_text(profile.department),
        "grade": clean_initial_text(profile.grade),
        "contact_info": clean_initial_text(profile.contact_info),
    }


def is_profile_completed(profile: UserProfile | None) -> bool:
    return bool(profile and profile.profile_completed)


def next_action_for(user: User) -> str:
    if user.must_change_password:
        return "change_password"
    if not is_profile_completed(user.profile):
        return "complete_profile"
    return "enter_app"


def login_user_payload(user: User) -> dict:
    profile = user.profile
    return {
        "id": user.id,
        "student_no": user.student_no,
        "meow_no": user.student_no,
        "nickname": clean_initial_display_text(profile.nickname if profile else None),
        "avatar_url": profile.avatar_url if profile else None,
        "role": user.role,
        "status": user.status,
        "profile_completed": is_profile_completed(profile),
    }


def current_user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "student_no": user.student_no,
        "meow_no": user.student_no,
        "role": user.role,
        "status": user.status,
        "must_change_password": user.must_change_password,
        "profile_completed": is_profile_completed(user.profile),
        "profile": profile_payload(user.profile),
    }


def validate_password_strength(password: str) -> None:
    if len(password) < 8 or len(password) > 20:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    if PASSWORD_ALLOWED_PATTERN.fullmatch(password) is None:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    if not any(character.isalpha() for character in password) or not any(
        character.isdigit() for character in password
    ):
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)


def generate_next_meow_no(db: Session) -> str:
    values = db.scalars(
        select(User.student_no).where(User.student_no.like(f"{MEOW_NO_PREFIX}%"))
    ).all()
    max_sequence = 0
    for value in values:
        suffix = value.removeprefix(MEOW_NO_PREFIX)
        if suffix.isdigit():
            max_sequence = max(max_sequence, int(suffix))
    return f"{MEOW_NO_PREFIX}{max_sequence + 1:0{MEOW_NO_WIDTH}d}"


def get_user_by_student_no(db: Session, student_no: str) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.profile))
        .where(User.student_no == student_no, User.deleted_at.is_(None))
    )


def get_user_by_wechat_openid(db: Session, openid: str) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.profile))
        .where(User.wechat_openid == openid, User.deleted_at.is_(None))
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


def issue_login_response(user: User) -> dict:
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
        "next_action": next_action_for(user),
        "user": login_user_payload(user),
    }


def apply_wechat_binding(
    db: Session,
    *,
    user: User,
    openid: str,
    agree_wechat_bind: bool,
    current_time: datetime,
) -> None:
    existing_user = get_user_by_wechat_openid(db, openid)
    if existing_user is not None and existing_user.id != user.id:
        raise APIError(
            code=ErrorCode.WECHAT_OPENID_ALREADY_BOUND,
            message="当前微信已绑定其他账号",
            status_code=409,
        )

    if user.wechat_openid:
        if user.wechat_openid != openid:
            raise APIError(
                code=ErrorCode.WECHAT_BINDING_MISMATCH,
                message="当前微信与喵喵号绑定不一致，请联系管理员",
                status_code=403,
            )
        user.last_wechat_login_at = current_time
        return

    if not agree_wechat_bind:
        raise APIError(
            code=ErrorCode.WECHAT_BINDING_CONFIRMATION_REQUIRED,
            message="请确认微信绑定后再登录",
            status_code=400,
        )

    user.wechat_openid = openid
    user.wechat_bound_at = current_time
    user.last_wechat_login_at = current_time


def login(db: Session, payload: LoginRequest) -> dict:
    captcha = validate_captcha(db, payload.captcha_id, payload.captcha_code)
    user = get_user_by_student_no(db, payload.account_no)

    if user is None:
        db.commit()
        raise APIError(
            code=ErrorCode.INVALID_CREDENTIALS,
            message="喵喵号或密码错误",
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
            message="喵喵号或密码错误",
            status_code=401,
        )
    if user.must_change_password and not payload.agree_terms:
        db.commit()
        raise APIError(code=ErrorCode.AGREEMENT_REQUIRED, message="未勾选协议", status_code=400)

    current_time = now_utc()
    settings = get_settings()
    if (
        settings.wechat_auth_mode == "enforced"
        and user.wechat_openid
        and not payload.wechat_code
    ):
        db.commit()
        raise APIError(
            code=ErrorCode.WECHAT_BINDING_MISMATCH,
            message="请使用已绑定微信登录",
            status_code=403,
        )

    if payload.wechat_code and settings.wechat_auth_mode != "off":
        openid = exchange_wechat_code_for_openid(payload.wechat_code)
        apply_wechat_binding(
            db,
            user=user,
            openid=openid,
            agree_wechat_bind=payload.agree_wechat_bind,
            current_time=current_time,
        )

    captcha.used_at = current_time
    user.last_login_at = current_time
    user.login_failed_count = 0
    user.locked_until = None
    db.commit()
    db.refresh(user)

    return issue_login_response(user)


def login_with_wechat(db: Session, payload: WeChatLoginRequest) -> dict:
    settings = get_settings()
    if settings.wechat_auth_mode == "off":
        raise APIError(
            code=ErrorCode.SERVER_ERROR,
            message="微信登录暂未启用",
            status_code=503,
        )

    openid = exchange_wechat_code_for_openid(payload.code)
    user = get_user_by_wechat_openid(db, openid)
    if user is None:
        raise APIError(
            code=ErrorCode.WECHAT_OPENID_UNBOUND,
            message="当前微信尚未绑定喵喵号",
            status_code=401,
        )
    if user.status != "active":
        raise APIError(code=ErrorCode.ACCOUNT_DISABLED, message="账号已被禁用", status_code=403)

    current_time = now_utc()
    user.last_login_at = current_time
    user.last_wechat_login_at = current_time
    db.commit()
    db.refresh(user)
    return issue_login_response(user)


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


def clear_current_user_wechat_binding(db: Session, user: User) -> dict:
    if not user.wechat_openid:
        raise APIError(
            code=ErrorCode.PARAM_ERROR,
            message="当前账号尚未绑定微信",
            status_code=400,
        )

    user.wechat_openid = None
    user.wechat_bound_at = None
    user.last_wechat_login_at = None
    user.token_version += 1
    db.commit()
    db.refresh(user)
    return {
        "user_id": user.id,
        "wechat_bound": False,
        "token_version": user.token_version,
        "token_invalidated": True,
    }


def change_password(db: Session, user: User, payload: ChangePasswordRequest) -> dict:
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
        "profile_completed": is_profile_completed(user.profile),
        "token_invalidated": True,
        "next_action": next_action_for(user),
    }


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


def is_admin_account(user: User) -> bool:
    return user.role in ADMIN_ROLES


def admin_user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "student_no": user.student_no,
        "meow_no": user.student_no,
        "role": user.role,
        "status": user.status,
        "must_change_password": user.must_change_password,
        "profile_completed": is_profile_completed(user.profile),
        "last_login_at": user.last_login_at,
        "wechat_bound": bool(user.wechat_openid),
        "profile": profile_payload(user.profile),
        "editable": not is_admin_account(user),
        "can_reset_password": not is_admin_account(user),
    }


def admin_user_log_payload(user: User) -> dict:
    payload = admin_user_payload(user)
    payload["id"] = str(payload["id"])
    if payload["last_login_at"] is not None:
        payload["last_login_at"] = payload["last_login_at"].isoformat()
    return payload


def create_member_account(db: Session, admin: User, payload: AdminCreateUserRequest) -> User:
    if payload.role not in VALID_ROLES:
        raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
    account_no = payload.account_no or generate_next_meow_no(db)
    initial_password = payload.initial_password or account_no
    validate_password_strength(initial_password)
    if get_user_by_student_no(db, account_no):
        raise APIError(code=ErrorCode.RESOURCE_EXISTS, message="喵喵号已存在", status_code=409)

    user = User(
        student_no=account_no,
        password_hash=hash_password(initial_password),
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
            nickname=clean_initial_display_text(payload.profile.nickname),
            real_name=clean_initial_text(payload.profile.real_name),
            department=clean_initial_text(payload.profile.department),
            grade=clean_initial_text(payload.profile.grade),
            joined_at=payload.profile.joined_at,
            profile_completed=False,
        )
    )
    log_admin_operation(
        db,
        admin=admin,
        operation_type="user_create",
        target_id=user.id,
        summary=f"创建成员账号 {user.student_no}",
        after_data={"meow_no": user.student_no, "role": user.role},
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
    department: str | None = None,
    sort_by: str | None = None,
    sort_order: str = "desc",
) -> dict:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    statement = select(User).options(selectinload(User.profile)).where(User.deleted_at.is_(None))
    if keyword or department:
        statement = statement.join(UserProfile, isouter=True)
    if keyword:
        like = f"%{keyword}%"
        statement = statement.where(
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
    if department:
        statement = statement.where(UserProfile.department == department)

    total = len(db.scalars(statement).all())
    if sort_by == "meow_no":
        order_clause = User.student_no.asc() if sort_order == "asc" else User.student_no.desc()
    else:
        order_clause = User.created_at.desc()
    users = db.scalars(
        statement.order_by(order_clause).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return {
        "items": [admin_user_payload(user) for user in users],
        "page": page,
        "page_size": page_size,
        "total": total,
        "has_more": page * page_size < total,
    }


def get_target_user(db: Session, user_id: UUID) -> User:
    user = db.scalar(
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == user_id, User.deleted_at.is_(None))
    )
    if user is None or user.deleted_at is not None:
        raise APIError(code=ErrorCode.RESOURCE_NOT_FOUND, message="用户不存在", status_code=404)
    return user


def get_user_detail(db: Session, *, user_id: UUID) -> dict:
    return admin_user_payload(get_target_user(db, user_id))


def ensure_target_is_editable(user: User) -> None:
    if is_admin_account(user):
        raise APIError(code=ErrorCode.FORBIDDEN, message="不能修改管理员账号", status_code=403)


def update_user_detail(
    db: Session,
    *,
    admin: User,
    user_id: UUID,
    payload: AdminUpdateUserRequest,
) -> dict:
    if admin.id == user_id:
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)
    user = get_target_user(db, user_id)
    ensure_target_is_editable(user)
    before = admin_user_log_payload(user)

    if payload.role is not None:
        if payload.role not in VALID_ROLES:
            raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
        user.role = payload.role
        user.token_version += 1
    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise APIError(code=ErrorCode.PARAM_ERROR, message="参数错误", status_code=400)
        user.status = payload.status
        if payload.status != "active":
            user.token_version += 1
    if payload.profile is not None:
        if user.profile is None:
            user.profile = UserProfile(user_id=user.id, nickname="")
        profile = user.profile
        profile.nickname = clean_initial_display_text(payload.profile.nickname)
        profile.avatar_url = clean_initial_text(payload.profile.avatar_url)
        profile.real_name = clean_initial_text(payload.profile.real_name)
        profile.department = clean_initial_text(payload.profile.department)
        profile.grade = clean_initial_text(payload.profile.grade)
        profile.joined_at = payload.profile.joined_at
        profile.contact_info = clean_initial_text(payload.profile.contact_info)

    log_admin_operation(
        db,
        admin=admin,
        operation_type="user_update_detail",
        target_id=user.id,
        summary=f"更新成员资料 {user.student_no}",
        before_data=before,
        after_data=admin_user_log_payload(user),
    )
    db.commit()
    db.refresh(user)
    return admin_user_payload(user)


def reset_user_password(
    db: Session,
    *,
    admin: User,
    user_id: UUID,
    payload: AdminResetPasswordRequest,
) -> User:
    validate_password_strength(payload.new_password)
    user = get_target_user(db, user_id)
    ensure_target_is_editable(user)
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
    ensure_target_is_editable(user)
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


def soft_delete_user(
    db: Session,
    *,
    admin: User,
    user_id: UUID,
) -> User:
    if admin.id == user_id:
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)
    user = get_target_user(db, user_id)
    ensure_target_is_editable(user)
    before = {
        "status": user.status,
        "token_version": user.token_version,
        "deleted_at": None,
    }
    user.status = "left"
    user.deleted_at = now_utc()
    user.token_version += 1
    log_admin_operation(
        db,
        admin=admin,
        operation_type="user_soft_delete",
        target_id=user.id,
        summary=f"成员退出 {user.student_no}",
        before_data=before,
        after_data={
            "status": user.status,
            "deleted_at": user.deleted_at.isoformat(),
        },
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
    ensure_target_is_editable(user)
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


def clear_user_wechat_binding(
    db: Session,
    *,
    admin: User,
    user_id: UUID,
) -> User:
    if admin.id == user_id:
        raise APIError(code=ErrorCode.FORBIDDEN, message="权限不足", status_code=403)
    user = get_target_user(db, user_id)
    ensure_target_is_editable(user)
    before = {
        "wechat_bound": bool(user.wechat_openid),
        "token_version": user.token_version,
    }
    user.wechat_openid = None
    user.wechat_bound_at = None
    user.last_wechat_login_at = None
    user.token_version += 1
    log_admin_operation(
        db,
        admin=admin,
        operation_type="user_clear_wechat_binding",
        target_id=user.id,
        summary=f"清除成员微信绑定 {user.student_no}",
        before_data=before,
        after_data={"wechat_bound": False, "token_version": user.token_version},
    )
    db.commit()
    db.refresh(user)
    return user
