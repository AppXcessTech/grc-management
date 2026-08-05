"""Add evidence management tables.

Revision ID: 0006_add_evidence_management
Revises: 0005_add_password_reset_tokens
Create Date: 2026-06-09 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_add_evidence_management"
down_revision = "0005_add_password_reset_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old evidence table (simple model replaced by new design)
    op.drop_table("evidence")

    # Evidence Sources - extensible for future automated collectors
    op.create_table(
        "evidence_sources",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(128), nullable=False, unique=True, index=True),
        sa.Column(
            "source_type",
            sa.Enum(
                "manual", "aws", "azure", "gcp", "github", "gitlab", "jira", "okta", "google_workspace",
                name="evidence_source_type", native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("TRUE")),
        sa.Column("config_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Seed the Manual Upload source
    op.execute(
        sa.text(
            "INSERT INTO evidence_sources (name, source_type, description, is_active) "
            "VALUES ('Manual Upload', 'manual', 'Manually uploaded evidence by users', TRUE)"
        )
    )

    # Evidence - main table
    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "evidence_type",
            sa.Enum(
                "screenshot", "log", "configuration", "report", "api_snapshot", "document",
                name="evidence_type", native_enum=False,
            ),
            nullable=False,
            server_default="document",
        ),
        sa.Column("collected_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("collected_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Evidence Files
    op.create_table(
        "evidence_files",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Evidence Reviews
    op.create_table(
        "evidence_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="evidence_review_status", native_enum=False),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # Junction: Evidence <-> Controls
    op.create_table(
        "evidence_control_links",
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
        sa.Column("control_id", sa.Integer(), sa.ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
    )

    # Junction: Evidence <-> Requirements
    op.create_table(
        "evidence_requirement_links",
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
        sa.Column("requirement_id", sa.Integer(), sa.ForeignKey("requirements.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True),
    )


def downgrade() -> None:
    op.drop_table("evidence_requirement_links")
    op.drop_table("evidence_control_links")
    op.drop_table("evidence_reviews")
    op.drop_table("evidence_files")
    op.drop_table("evidence")
    op.drop_table("evidence_sources")
    op.execute("DROP TYPE IF EXISTS evidence_source_type")
    op.execute("DROP TYPE IF EXISTS evidence_type")
    op.execute("DROP TYPE IF EXISTS evidence_review_status")

    # Recreate old simple evidence table
    op.create_table(
        "evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("control_id", sa.Integer(), sa.ForeignKey("controls.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(512), nullable=True),
        sa.Column("url", sa.String(512), nullable=True),
    )
