"""align task assignment schema with current models

Revision ID: b37d4a8e912c
Revises: a91e86c42f10
Create Date: 2026-09-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b37d4a8e912c"
down_revision: Union[str, Sequence[str], None] = "a91e86c42f10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("created_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_tasks_created_by",
        "tasks",
        "teachers",
        ["created_by"],
        ["id"],
    )
    op.execute(
        """UPDATE tasks
           SET created_by = tests.created_by
          FROM tests
         WHERE tasks.test_id = tests.id
           AND tasks.created_by IS NULL"""
    )
    op.alter_column("tasks", "created_by", nullable=False)

    op.add_column(
        "tasks",
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("tasks", "test_id", existing_type=sa.Integer(), nullable=True)

    op.create_table(
        "task_group_assignment",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["student_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "group_id"),
    )
    op.create_table(
        "task_student_assignment",
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("task_id", "student_id"),
    )


def downgrade() -> None:
    op.drop_table("task_student_assignment")
    op.drop_table("task_group_assignment")
    op.alter_column("tasks", "test_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("tasks", "is_visible")
    op.drop_constraint("fk_tasks_created_by", "tasks", type_="foreignkey")
    op.drop_column("tasks", "created_by")
