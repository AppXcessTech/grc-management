"""Add mdm_device_id and mdm_payload to endpoint_devices

Revision ID: 9a7b6c5d4e3f
Revises: 8e63a8c21c5b
Create Date: 2026-06-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a7b6c5d4e3f'
down_revision: Union[str, None] = '8e63a8c21c5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('endpoint_devices', sa.Column('mdm_device_id', sa.String(255), nullable=True, index=True))
    op.add_column('endpoint_devices', sa.Column('mdm_payload', sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column('endpoint_devices', 'mdm_payload')
    op.drop_column('endpoint_devices', 'mdm_device_id')
