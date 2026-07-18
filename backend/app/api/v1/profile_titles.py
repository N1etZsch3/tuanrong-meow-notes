from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.titles import service

router = APIRouter(tags=["Profile Titles"])


@router.post("/title/resign", summary="Resign the current non-president title")
def resign_my_title(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.resign_title(db, user=current_user)
    return api_success(data=data, trace_id=request.state.trace_id)
