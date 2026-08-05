"""Encrypt sensitive columns in asset_import_requests table

Adds _encrypted columns, migrates existing plaintext data using AES-256-GCM,
then drops the old plaintext columns.

Revision ID: f8g9h0i1j2k3
Revises: f7c8d9e0a1b2
Create Date: 2026-07-26 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f8g9h0i1j2k3"
down_revision: Union[str, None] = "f7c8d9e0a1b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add new encrypted columns (nullable initially so we can populate them)
    op.add_column("asset_import_requests", sa.Column("role_arn_encrypted", sa.String(2048), nullable=True))
    op.add_column("asset_import_requests", sa.Column("region_encrypted", sa.String(64), nullable=True))
    op.add_column("asset_import_requests", sa.Column("account_name_encrypted", sa.String(255), nullable=True))

    # Step 2: Encrypt existing data using Python crypto utilities
    import os
    import base64
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key_b64 = os.environ.get("AWS_CREDENTIALS_ENCRYPTION_KEY", "")
    if not key_b64:
        raise ValueError(
            "AWS_CREDENTIALS_ENCRYPTION_KEY must be set to run this migration. "
            "Generate a key with: python -c \"import os,base64; print(base64.b64encode(os.urandom(32)).decode())\""
        )

    key = base64.b64decode(key_b64)
    if len(key) != 32:
        raise ValueError("Encryption key must be 32 bytes for AES-256")

    aesgcm = AESGCM(key)

    def encrypt_value(value):
        if value is None:
            return None
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, str(value).encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("ascii")

    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, role_arn, region, account_name FROM asset_import_requests")
    ).fetchall()

    for row in rows:
        conn.execute(
            sa.text(
                "UPDATE asset_import_requests SET "
                "role_arn_encrypted = :role_arn_encrypted, "
                "region_encrypted = :region_encrypted, "
                "account_name_encrypted = :account_name_encrypted "
                "WHERE id = :id"
            ),
            {
                "id": row[0],
                "role_arn_encrypted": encrypt_value(row[1]),
                "region_encrypted": encrypt_value(row[2]),
                "account_name_encrypted": encrypt_value(row[3]),
            },
        )

    # Step 3: Make encrypted columns NOT NULL (role_arn and region are required)
    op.alter_column("asset_import_requests", "role_arn_encrypted", nullable=False)
    op.alter_column("asset_import_requests", "region_encrypted", nullable=False)

    # Step 4: Drop old plaintext columns
    op.drop_column("asset_import_requests", "role_arn")
    op.drop_column("asset_import_requests", "account_name")
    op.drop_column("asset_import_requests", "region")


def downgrade() -> None:
    # Reverse: add back plaintext columns, decrypt data, drop encrypted columns
    op.add_column("asset_import_requests", sa.Column("role_arn", sa.String(2048), nullable=True))
    op.add_column("asset_import_requests", sa.Column("region", sa.String(64), nullable=True))
    op.add_column("asset_import_requests", sa.Column("account_name", sa.String(255), nullable=True))

    import os
    import base64
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    key_b64 = os.environ.get("AWS_CREDENTIALS_ENCRYPTION_KEY", "")
    if not key_b64:
        raise ValueError("AWS_CREDENTIALS_ENCRYPTION_KEY must be set to run this migration")
    key = base64.b64decode(key_b64)
    aesgcm = AESGCM(key)

    def decrypt_value(value):
        if value is None:
            return None
        encrypted_bytes = base64.b64decode(value)
        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]
        return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, role_arn_encrypted, region_encrypted, account_name_encrypted "
            "FROM asset_import_requests"
        )
    ).fetchall()

    for row in rows:
        conn.execute(
            sa.text(
                "UPDATE asset_import_requests SET "
                "role_arn = :role_arn, "
                "region = :region, "
                "account_name = :account_name "
                "WHERE id = :id"
            ),
            {
                "id": row[0],
                "role_arn": decrypt_value(row[1]),
                "region": decrypt_value(row[2]),
                "account_name": decrypt_value(row[3]),
            },
        )

    op.alter_column("asset_import_requests", "role_arn", nullable=False)
    op.alter_column("asset_import_requests", "region", nullable=False)

    op.drop_column("asset_import_requests", "role_arn_encrypted")
    op.drop_column("asset_import_requests", "region_encrypted")
    op.drop_column("asset_import_requests", "account_name_encrypted")
