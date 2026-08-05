"""Rename AuthenticationPolicy canonical category to Policy

The AuthenticationPolicy canonical type (password policies, MFA, sign-on
settings, etc.) is merged into the existing Policy category, which also
holds IAM policies. Existing canonical_assets rows are folded to 'Policy'.

Revision ID: g3h4i5j6k7l8
Revises: f8g9h0i1j2k3
Create Date: 2026-08-04 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "g3h4i5j6k7l8"
down_revision: Union[str, None] = "f8g9h0i1j2k3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fold existing AuthenticationPolicy assets into the Policy category.
    op.execute(
        sa.text(
            "UPDATE canonical_assets SET canonical_type = 'Policy' "
            "WHERE canonical_type = 'AuthenticationPolicy'"
        )
    )


def downgrade() -> None:
    # The fold is not reversible — after merging we cannot tell which rows
    # were originally AuthenticationPolicy.
    pass
