"""Add extended health and telemetry fields for ChurnVision integration

Revision ID: 003
Revises: 002
Create Date: 2024-01-04 00:00:00.000000

This migration adds extended fields to support the ChurnVision integration specification:
- TenantDeployment: Extended health monitoring fields
- Creates health_pings table (used by telemetry model)
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

    # Create health_pings table (the model uses health_pings, not telemetry_pings)
    op.create_table(
        "health_pings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(), default=sa.func.now()),
        sa.Column("api_status", sa.String(), nullable=True),
        sa.Column("db_status", sa.String(), nullable=True),
        sa.Column("ollama_status", sa.String(), nullable=True),
        sa.Column("active_users_count", sa.Integer(), nullable=True),
        sa.Column("predictions_this_period", sa.Integer(), nullable=True),
        sa.Column("api_calls_this_period", sa.Integer(), nullable=True),
        sa.Column("deployed_version", sa.String(), nullable=True),
        sa.Column("python_version", sa.String(), nullable=True),
        sa.Column("recent_errors", postgresql.JSON(), default=[]),
        sa.Column("installation_id", sa.String(), nullable=True),
        sa.Column("error_count_24h", sa.Integer(), default=0, nullable=True),
        sa.Column("collection_timestamp", sa.DateTime(), nullable=True),
    )

    # Create indexes
    op.create_index(
        "ix_tenant_deployments_installation_id",
        "tenant_deployments",
        ["installation_id"],
    )
    op.create_index(
        "ix_health_pings_installation_id", "health_pings", ["installation_id"]
    )
    op.create_index("ix_health_pings_tenant_id", "health_pings", ["tenant_id"])


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_health_pings_tenant_id")
    op.drop_index("ix_health_pings_installation_id")
    op.drop_index("ix_tenant_deployments_installation_id")

    # Drop health_pings table
    op.drop_table("health_pings")

    # Remove columns from tenant_deployments
    op.drop_column("tenant_deployments", "last_reported_at")
    op.drop_column("tenant_deployments", "installation_id")
    op.drop_column("tenant_deployments", "python_version")
    op.drop_column("tenant_deployments", "platform")
    op.drop_column("tenant_deployments", "uptime_seconds")
    op.drop_column("tenant_deployments", "cache_healthy")
    op.drop_column("tenant_deployments", "database_healthy")
