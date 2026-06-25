"""clear profile question mark placeholders

Revision ID: 20260625_0006
Revises: 20260625_0005
Create Date: 2026-06-25
"""

import sqlalchemy as sa

from alembic import op

revision = "20260625_0006"
down_revision = "20260625_0005"
branch_labels = None
depends_on = None


def _is_question_placeholder(value: str | None) -> bool:
    if value is None:
        return False
    stripped = value.strip()
    return bool(stripped) and set(stripped) == {"?"}


def upgrade() -> None:
    profiles = sa.table(
        "user_profiles",
        sa.column("id"),
        sa.column("nickname"),
        sa.column("real_name"),
        sa.column("department"),
        sa.column("grade"),
        sa.column("contact_info"),
    )
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(
            profiles.c.id,
            profiles.c.nickname,
            profiles.c.real_name,
            profiles.c.department,
            profiles.c.grade,
            profiles.c.contact_info,
        )
    ).mappings()

    for row in rows:
        values: dict[str, str | None] = {}
        if _is_question_placeholder(row["nickname"]):
            values["nickname"] = ""
        for field in ("real_name", "department", "grade", "contact_info"):
            if _is_question_placeholder(row[field]):
                values[field] = None
        if values:
            connection.execute(
                sa.update(profiles).where(profiles.c.id == row["id"]).values(**values)
            )


def downgrade() -> None:
    pass
