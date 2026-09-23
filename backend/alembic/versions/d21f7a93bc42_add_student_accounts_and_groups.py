"""add student accounts and teacher-managed groups

Revision ID: d21f7a93bc42
Revises: c8b24f610e31
Create Date: 2026-09-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d21f7a93bc42"
down_revision: Union[str, Sequence[str], None] = "c8b24f610e31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("teacher_id", "name", name="uq_teacher_group_name"),
    )
    op.create_index(op.f("ix_student_groups_id"), "student_groups", ["id"], unique=False)
    op.add_column("students", sa.Column("username", sa.String(), nullable=True))
    op.add_column("students", sa.Column("password_hash", sa.String(), nullable=True))
    op.add_column("students", sa.Column("group_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_students_username"), "students", ["username"], unique=True)
    op.create_foreign_key("fk_students_group_id", "students", "student_groups", ["group_id"], ["id"], ondelete="SET NULL")


def downgrade() -> None:
    op.drop_constraint("fk_students_group_id", "students", type_="foreignkey")
    op.drop_index(op.f("ix_students_username"), table_name="students")
    op.drop_column("students", "group_id")
    op.drop_column("students", "password_hash")
    op.drop_column("students", "username")
    op.drop_index(op.f("ix_student_groups_id"), table_name="student_groups")
    op.drop_table("student_groups")
