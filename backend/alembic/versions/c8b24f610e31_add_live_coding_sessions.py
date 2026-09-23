"""add live coding mode and per-student code sessions

Revision ID: c8b24f610e31
Revises: f5ddf1a7ed08
Create Date: 2026-09-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c8b24f610e31"
down_revision: Union[str, Sequence[str], None] = "f5ddf1a7ed08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("code_review_tasks", sa.Column("student_mode", sa.String(), nullable=False, server_default="review"))
    op.create_table(
        "student_code_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", "student_id", name="uq_student_code_session"),
    )
    op.create_index(op.f("ix_student_code_sessions_id"), "student_code_sessions", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_student_code_sessions_id"), table_name="student_code_sessions")
    op.drop_table("student_code_sessions")
    op.drop_column("code_review_tasks", "student_mode")
