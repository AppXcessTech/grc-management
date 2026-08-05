"""add_category_to_permissions

Revision ID: efe87bddac51
Revises: 9a7b6c5d4e3f
Create Date: 2026-06-30 18:50:53.037301

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efe87bddac51'
down_revision: Union[str, None] = '9a7b6c5d4e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('permissions', sa.Column('category', sa.String(length=128), nullable=True))
    op.alter_column('permissions', 'action',
        existing_type=sa.Enum('view', 'create', 'edit', 'delete', 'approve', name='permission_action', native_enum=False),
        type_=sa.String(length=64),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column('permissions', 'action',
        existing_type=sa.String(length=64),
        type_=sa.Enum('view', 'create', 'edit', 'delete', 'approve', name='permission_action', native_enum=False),
        existing_nullable=False,
    )
    op.drop_column('permissions', 'category')
