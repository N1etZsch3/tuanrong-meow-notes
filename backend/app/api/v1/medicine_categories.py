from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.dependencies import require_profile_completed
from app.modules.auth.models import User
from app.modules.medicines import service

router = APIRouter(tags=["Medicine Categories"])


@router.get("", summary="List medicine categories")
def list_medicine_categories(
    request: Request,
    include_disabled: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_profile_completed),
):
    data = service.list_categories(
        db,
        user=current_user,
        include_disabled=include_disabled,
    )
    return api_success(data=data, trace_id=request.state.trace_id)
