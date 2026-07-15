import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.public.models import WechatGuest

logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    return datetime.now(tz=UTC)


def _increment_existing_visit(db: Session, openid: str) -> None:
    guest = db.scalar(select(WechatGuest).where(WechatGuest.openid == openid))
    if guest is None:
        return
    guest.visit_count += 1
    guest.last_visit_at = _now_utc()
    db.commit()


def record_guest_visit(db: Session, openid: str) -> None:
    """Best-effort upsert of a guest visit, committed immediately.

    Called on the unbound WeChat login path right before the 40104 response is
    raised. The session is rolled back after that error response, so the guest
    row must be committed here; at this point the session holds no other pending
    writes. Any failure is swallowed — guest recording must never change the
    login response.
    """

    if not openid:
        return

    try:
        guest = db.scalar(select(WechatGuest).where(WechatGuest.openid == openid))
        now = _now_utc()
        if guest is None:
            db.add(
                WechatGuest(
                    openid=openid,
                    visit_count=1,
                    first_visit_at=now,
                    last_visit_at=now,
                )
            )
        else:
            guest.visit_count += 1
            guest.last_visit_at = now
        db.commit()
    except IntegrityError:
        # Two first visits raced on the unique openid; the other insert won.
        db.rollback()
        try:
            _increment_existing_visit(db, openid)
        except Exception:  # noqa: BLE001 - guest recording must not break login
            db.rollback()
            logger.warning("failed to record guest visit after race", exc_info=True)
    except Exception:  # noqa: BLE001 - guest recording must not break login
        db.rollback()
        logger.warning("failed to record guest visit", exc_info=True)
