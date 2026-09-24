"""add teacher registration codes

Revision ID: a91e86c42f10
Revises: f4a7c11d0b22
Create Date: 2026-09-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a91e86c42f10"
down_revision: Union[str, None] = "f4a7c11d0b22"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("teachers", sa.Column("registration_code", sa.String(length=12), nullable=True))
    op.execute("UPDATE teachers SET registration_code = upper(substr(md5(random()::text || id::text), 1, 8))")
    op.alter_column("teachers", "registration_code", nullable=False)
    op.create_index(op.f("ix_teachers_registration_code"), "teachers", ["registration_code"], unique=True)
    op.add_column("students", sa.Column("registration_teacher_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_students_registration_teacher_id",
        "students",
        "teachers",
        ["registration_teacher_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.execute(
        """UPDATE students s
              SET registration_teacher_id = g.teacher_id
             FROM student_groups g
            WHERE s.group_id = g.id"""
    )


def downgrade() -> None:
    op.drop_constraint("fk_students_registration_teacher_id", "students", type_="foreignkey")
    op.drop_column("students", "registration_teacher_id")
    op.drop_index(op.f("ix_teachers_registration_code"), table_name="teachers")
    op.drop_column("teachers", "registration_code")
