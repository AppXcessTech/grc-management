"""add_raw_api_responses_table

Revision ID: f7c8d9e0a1b2
Revises: ea09b672d65d
Create Date: 2026-07-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7c8d9e0a1b2'
down_revision: Union[str, None] = 'ea09b672d65d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('raw_api_responses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('discovery_run_id', sa.String(length=36), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('account_id', sa.String(length=255), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('service', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('provider_resource_id', sa.String(length=1024), nullable=False),
        sa.Column('api_call', sa.String(length=100), nullable=False),
        sa.Column('api_response', sa.JSON(), nullable=False),
        sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_raw_api_responses_discovery_run_id'), 'raw_api_responses', ['discovery_run_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_raw_api_responses_discovery_run_id'), table_name='raw_api_responses')
    op.drop_table('raw_api_responses')
