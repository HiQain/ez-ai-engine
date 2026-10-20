"""create codes and code_sync_state tables

Revision ID: codes_sync_0001
Revises: d7e2a91c4f06
Create Date: 2026-10-20

ez's local mirror of Laravel's price-book codes, kept fresh by polling.
"""

import sqlalchemy as sa
from alembic import op

revision = "codes_sync_0001"
down_revision = "d7e2a91c4f06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "codes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("code_name", sa.String(length=255), nullable=True),
        sa.Column("product_name", sa.String(length=255), nullable=True),
        sa.Column("unit_of_measure", sa.String(length=50), nullable=True),
        sa.Column("labor_cost", sa.Float(), nullable=True),
        sa.Column("material_cost", sa.Float(), nullable=True),
        sa.Column("misc_cost", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("product_group_id", sa.Integer(), nullable=True),
        sa.Column("source_updated_at", sa.DateTime(), nullable=True),
        sa.Column("synced_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_codes_company_id", "codes", ["company_id"])

    op.create_table(
        "code_sync_state",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("last_updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("code_sync_state")
    op.drop_index("ix_codes_company_id", table_name="codes")
    op.drop_table("codes")
