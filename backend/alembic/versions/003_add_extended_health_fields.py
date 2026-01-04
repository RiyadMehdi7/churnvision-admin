"""Add extended health and telemetry fields for ChurnVision integration

Revision ID: 003
Revises: 002
Create Date: 2024-01-04 00:00:00.000000

This migration adds extended fields to support the ChurnVision integration specification:
- TenantDeployment: Extended health monitoring fields
- TelemetryPing: Installation tracking and error count fields
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add extended fields to tenant_deployments table
    op.add_column(
        "tenant_deployments",
        sa.Column("database_healthy", sa.Boolean(), default=True, nullable=True),
    )
    op.add_column(
        "tenant_deployments",
        sa.Column("cache_healthy", sa.Boolean(), default=True, nullable=True),
    )
    op.add_column(
        "tenant_deployments",
        sa.Column("uptime_seconds", sa.Integer(), default=0, nullable=True),
    )
    op.add_column(
        "tenant_deployments", sa.Column("platform", sa.String(), nullable=True)
    )
    op.add_column(
        "tenant_deployments", sa.Column("python_version", sa.String(), nullable=True)
    )
    op.add_column(
        "tenant_deployments", sa.Column("installation_id", sa.String(), nullable=True)
    )
    op.add_column(
        "tenant_deployments",
        sa.Column("last_reported_at", sa.DateTime(), nullable=True),
    )

    # Add extended fields to health_pings (telemetry) table
    op.add_column(
        "health_pings", sa.Column("installation_id", sa.String(), nullable=True)
    )
    op.add_column(
        "health_pings",
        sa.Column("error_count_24h", sa.Integer(), default=0, nullable=True),
    )
    op.add_column(
        "health_pings", sa.Column("collection_timestamp", sa.DateTime(), nullable=True)
    )

    # Create index for installation_id lookups
    op.create_index(
        "ix_tenant_deployments_installation_id",
        "tenant_deployments",
        ["installation_id"],
    )
    op.create_index(
        "ix_health_pings_installation_id", "health_pings", ["installation_id"]
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_health_pings_installation_id")
    op.drop_index("ix_tenant_deployments_installation_id")

    # Remove columns from health_pings
    op.drop_column("health_pings", "collection_timestamp")
    op.drop_column("health_pings", "error_count_24h")
    op.drop_column("health_pings", "installation_id")

    # Remove columns from tenant_deployments
    op.drop_column("tenant_deployments", "last_reported_at")
    op.drop_column("tenant_deployments", "installation_id")
    op.drop_column("tenant_deployments", "python_version")
    op.drop_column("tenant_deployments", "platform")
    op.drop_column("tenant_deployments", "uptime_seconds")
    op.drop_column("tenant_deployments", "cache_healthy")
    op.drop_column("tenant_deployments", "database_healthy")
