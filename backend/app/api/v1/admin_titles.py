from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.responses import api_success
from app.db.session import get_db
from app.modules.auth.models import User
from app.modules.titles import service
from app.modules.titles.dependencies import require_president

router = APIRouter(tags=["Admin Titles"])


@router.get("", summary="List title slots and current holders")
def list_titles(
    request: Request,
    db: Session = Depends(get_db),
    president: User = Depends(require_president),
):
    del president
    return api_success(data=service.title_catalog(db), trace_id=request.state.trace_id)
