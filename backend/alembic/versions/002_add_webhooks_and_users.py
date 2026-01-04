"""Add webhooks and users tables

Revision ID: 002
Revises: 001
Create Date: 2024-01-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('secret', sa.String(), nullable=True),
        sa.Column('events', postgresql.JSON(), default=[]),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Webhook Deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('webhook_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('webhooks.id'), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('payload', postgresql.JSON(), nullable=False),
        sa.Column('response_status', sa.String(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), default=False),
        sa.Column('delivered_at', sa.DateTime(), default=sa.func.now()),
    )

    # Create indexes for faster queries
    op.create_index('ix_webhooks_is_active', 'webhooks', ['is_active'])
    op.create_index('ix_webhooks_tenant_id', 'webhooks', ['tenant_id'])
    op.create_index('ix_webhook_deliveries_webhook_id', 'webhook_deliveries', ['webhook_id'])
    op.create_index('ix_webhook_deliveries_delivered_at', 'webhook_deliveries', ['delivered_at'])


def downgrade() -> None:
    op.drop_index('ix_webhook_deliveries_delivered_at')
    op.drop_index('ix_webhook_deliveries_webhook_id')
    op.drop_index('ix_webhooks_tenant_id')
    op.drop_index('ix_webhooks_is_active')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')
