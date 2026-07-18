"""activate president-derived super administrator role

Revision ID: 20260718_0020
Revises: 20260718_0019
Create Date: 2026-07-18
"""

from alembic import op

revision = "20260718_0020"
down_revision = "20260718_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET role = 'admin', token_version = token_version + 1
        WHERE role = 'super_admin'
          AND id NOT IN (
              SELECT user_id FROM user_profiles WHERE title = 'president'
          )
        """
    )
    op.execute(
        """
        UPDATE users
        SET role = 'super_admin', token_version = token_version + 1
        WHERE role <> 'super_admin'
          AND id IN (
              SELECT user_id FROM user_profiles WHERE title = 'president'
          )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET role = 'admin', token_version = token_version + 1
        WHERE role = 'super_admin'
        """
    )
