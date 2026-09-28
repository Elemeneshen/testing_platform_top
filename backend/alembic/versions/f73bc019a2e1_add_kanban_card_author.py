"""add kanban card author

Revision ID: f73bc019a2e1
Revises: e62a91c8d4f0
Create Date: 2026-09-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f73bc019a2e1"
down_revision: Union[str, None] = "e62a91c8d4f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("kanban_cards", sa.Column("created_by_student_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_kanban_cards_created_by_student",
        "kanban_cards",
        "students",
        ["created_by_student_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_kanban_cards_created_by_student", "kanban_cards", type_="foreignkey")
    op.drop_column("kanban_cards", "created_by_student_id")
