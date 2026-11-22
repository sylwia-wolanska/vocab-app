"""add owner to courses

Revision ID: fcd10c0eb004
Revises: bd063a66a560
Create Date: 2026-11-22 12:04:56.087620

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fcd10c0eb004"
down_revision: str | Sequence[str] | None = "bd063a66a560"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("user_id", sa.Integer(), nullable=True))
    op.execute("UPDATE courses SET user_id = (SELECT min(id) FROM users)")
    op.execute("DELETE FROM courses WHERE user_id IS NULL")
    op.alter_column("courses", "user_id", nullable=False)
    op.create_index(op.f("ix_courses_user_id"), "courses", ["user_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_courses_user_id_users"),
        "courses",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(op.f("uq_courses_name"), "courses", type_="unique")
    op.create_unique_constraint(
        op.f("uq_courses_user_id"), "courses", ["user_id", "name"]
    )


def downgrade() -> None:
    op.drop_constraint(op.f("uq_courses_user_id"), "courses", type_="unique")
    op.create_unique_constraint(op.f("uq_courses_name"), "courses", ["name"])
    op.drop_constraint(op.f("fk_courses_user_id_users"), "courses", type_="foreignkey")
    op.drop_index(op.f("ix_courses_user_id"), table_name="courses")
    op.drop_column("courses", "user_id")
