from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user, require_password_changed
from app.modules.auth.models import User
from app.modules.auth.schemas import ChangePasswordRequest, LoginRequest

router = APIRouter(tags=["Auth"])


@router.get("/captcha", summary="Get login captcha")
def get_captcha(request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else None
    data = service.create_captcha(
        db,
        client_ip=client_ip,
        user_agent=request.headers.get("user-agent"),
    )
    return api_success(data=data, trace_id=request.state.trace_id)


@router.post("/login", summary="Student number login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    data = service.login(db, payload)
    return api_success(data=data, trace_id=request.state.trace_id, message="login success")


@router.get("/me", summary="Get current user")
def me(request: Request, current_user: User = Depends(get_current_user)):
    return api_success(
        data=service.current_user_payload(current_user),
        trace_id=request.state.trace_id,
    )


@router.post("/renew", summary="Renew current access token")
def renew_access_token(
    request: Request,
    current_user: User = Depends(require_password_changed),
):
    return api_success(
        data=service.renew_access_token(current_user),
        trace_id=request.state.trace_id,
    )


@router.patch("/password", summary="Change current user's password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = service.change_password(db, current_user, payload)
    return api_success(
        data=data,
        trace_id=request.state.trace_id,
        message="密码修改成功",
    )


@router.post("/logout", summary="Logout")
def logout(request: Request, current_user: User = Depends(get_current_user)):
    return api_success(data=None, trace_id=request.state.trace_id, message="logout success")
