"""Add status column to requirements

Revision ID: b0c1d2e3f4a5
Revises: a7b8c9d0e1f2
Create Date: 2026-06-15 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("requirements", sa.Column("status", sa.String(32), nullable=True))
