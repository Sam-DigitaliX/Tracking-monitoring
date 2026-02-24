"""Add monitoring_batches table and ingest_key to sites

Revision ID: 002
Revises: 001
Create Date: 2026-02-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add ingest_key to sites
    op.add_column("sites", sa.Column("ingest_key", sa.String(64), unique=True))

    # Create monitoring_batches table
    op.create_table(
        "monitoring_batches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("container_id", sa.String(50), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_seconds", sa.Integer(), server_default=sa.text("60")),
        sa.Column("total_events", sa.Integer(), server_default=sa.text("0")),
        sa.Column("event_counts", JSON, server_default=sa.text("'{}'")),
        sa.Column("tag_metrics", JSON, server_default=sa.text("'{}'")),
        sa.Column("user_data_quality", JSON, server_default=sa.text("'{}'")),
        sa.Column("ecommerce_quality", JSON, server_default=sa.text("'{}'")),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes for efficient querying
    op.create_index("ix_monitoring_batches_site_id", "monitoring_batches", ["site_id"])
    op.create_index("ix_monitoring_batches_window_start", "monitoring_batches", ["window_start"])
    op.create_index(
        "ix_monitoring_batches_site_window",
        "monitoring_batches",
        ["site_id", "container_id", "window_start"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_table("monitoring_batches")
    op.drop_column("sites", "ingest_key")
