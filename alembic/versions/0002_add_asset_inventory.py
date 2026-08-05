"""Add asset inventory tables and integrations.

Revision ID: 0002_add_asset_inventory
Revises: 0001_initial_schema
Create Date: 2026-06-04 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_add_asset_inventory"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False, index=True),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column("contact_phone", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "asset_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "asset_tags",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "asset_owners",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("asset_owners.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("department_id", sa.Integer(), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("asset_categories.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column(
            "asset_type",
            sa.Enum(
                "employee",
                "device",
                "server",
                "application",
                "database",
                "cloud_resource",
                "vendor",
                name="asset_type",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("identifier", sa.String(length=255), nullable=True, unique=True),
        sa.Column("description", sa.String(length=2048), nullable=True),
        sa.Column(
            "criticality",
            sa.Enum("low", "medium", "high", "critical", name="asset_criticality", native_enum=False),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "risk_level",
            sa.Enum("low", "medium", "high", "critical", name="asset_risk_level", native_enum=False),
            nullable=False,
            server_default="medium",
        ),
        sa.Column("compliance_scope", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )

    op.create_table(
        "asset_integrations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column(
            "provider",
            sa.Enum(
                "Azure AD",
                "Google Workspace",
                "Microsoft 365",
                "AWS",
                "GCP",
                "Azure",
                name="integration_provider",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "asset_tag_assignments",
        sa.Column("asset_id", sa.Integer(), sa.ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("asset_tags.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("asset_tag_assignments")
    op.drop_table("asset_integrations")
    op.drop_table("assets")
    op.drop_table("asset_owners")
    op.drop_table("asset_tags")
    op.drop_table("asset_categories")
    op.drop_table("vendors")
