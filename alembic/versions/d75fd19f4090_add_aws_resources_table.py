"""add aws_resources table

Revision ID: d75fd19f4090
Revises: b0c1d2e3f4a5
Create Date: 2026-06-17 15:58:56.723592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd75fd19f4090'
down_revision: Union[str, None] = 'b0c1d2e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('aws_resources',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.Integer(), nullable=False),
    sa.Column('resource_type', sa.String(length=50), nullable=False),
    sa.Column('resource_id', sa.String(length=1024), nullable=False),
    sa.Column('region', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('details', sa.JSON(), nullable=True),
    sa.Column('account_id', sa.String(length=64), nullable=True),
    sa.Column('account_name', sa.String(length=255), nullable=True),
    sa.Column('discovered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aws_resources_organization_id'), 'aws_resources', ['organization_id'], unique=False)
    op.create_index(op.f('ix_aws_resources_resource_type'), 'aws_resources', ['resource_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_aws_resources_resource_type'), table_name='aws_resources')
    op.drop_index(op.f('ix_aws_resources_organization_id'), table_name='aws_resources')
    op.drop_table('aws_resources')
