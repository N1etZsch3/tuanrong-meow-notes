from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WechatGuest(Base):
    """A visitor whose WeChat OpenID resolved but is not bound to any member account.

    Recorded best-effort on the unbound (40104) startup path so the association can
    measure guest reach and later correlate guests who convert into members by OpenID.
    OpenID is stored as plaintext, consistent with ``users.wechat_openid``.
    """

    __tablename__ = "wechat_guests"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    openid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    visit_count: Mapped[int] = mapped_column(Integer, default=1)
    first_visit_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    last_visit_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
