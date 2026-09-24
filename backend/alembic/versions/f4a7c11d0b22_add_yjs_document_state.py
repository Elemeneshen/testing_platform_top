"""add yjs document state

Revision ID: f4a7c11d0b22
Revises: d21f7a93bc42
Create Date: 2026-09-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a7c11d0b22"
down_revision: Union[str, None] = "d21f7a93bc42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("student_code_sessions", sa.Column("ydoc_state", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    op.drop_column("student_code_sessions", "ydoc_state")
