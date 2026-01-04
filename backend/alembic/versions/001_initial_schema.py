"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_superuser', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('status', sa.Enum('TRIAL', 'ACTIVE', 'SUSPENDED', 'CHURNED', name='tenantstatus'), nullable=False, default='TRIAL'),
        sa.Column('tier', sa.Enum('STARTER', 'PROFESSIONAL', 'ENTERPRISE', name='pricingtier'), nullable=False, default='STARTER'),
        sa.Column('max_employees', sa.Integer(), nullable=True),
        sa.Column('max_users', sa.Integer(), default=5),
        sa.Column('features_enabled', postgresql.JSON(), default=[]),
        sa.Column('trial_started_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('trial_ends_at', sa.DateTime(), nullable=True),
        sa.Column('contract_start', sa.Date(), nullable=True),
        sa.Column('contract_end', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('industry', sa.String(), nullable=True),
        sa.Column('employee_count_range', sa.String(), nullable=True),
        sa.Column('region', sa.String(), nullable=True),
    )

    # Tenant Contacts table
    op.create_table(
        'tenant_contacts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
    )

    # Tenant Configs table
    op.create_table(
        'tenant_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
    )

    # Releases table
    op.create_table(
        'releases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('version', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('track', sa.Enum('STABLE', 'BETA', 'LTS', name='releasetrack'), nullable=False, default='STABLE'),
        sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'DEPRECATED', name='releasestatus'), nullable=False, default='DRAFT'),
        sa.Column('docker_images', postgresql.JSON(), default=[]),
        sa.Column('requires_downtime', sa.Boolean(), default=False),
        sa.Column('breaking_changes', postgresql.JSON(), default=[]),
        sa.Column('release_notes', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )

    # Tenant Deployments table
    op.create_table(
        'tenant_deployments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('current_version', sa.String(), nullable=False),
        sa.Column('deployed_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('deployed_by', sa.String(), nullable=True),
        sa.Column('environment', sa.String(), default='production'),
        sa.Column('last_health_check', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(), default='UNKNOWN'),
    )

    # Licenses table
    op.create_table(
        'licenses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('key_string', sa.Text(), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('revoked', sa.Boolean(), default=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revocation_reason', sa.String(), nullable=True),
        sa.Column('max_employees', sa.Integer(), nullable=True),
        sa.Column('max_users', sa.Integer(), nullable=True),
        sa.Column('features', postgresql.JSON(), default=[]),
    )

    # License Audit Logs table
    op.create_table(
        'license_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('license_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('licenses.id'), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('performed_by', sa.String(), nullable=True),
        sa.Column('performed_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('details', postgresql.JSON(), nullable=True),
    )

    # Subscriptions table
    op.create_table(
        'subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('plan', sa.Enum('MONTHLY', 'ANNUAL', 'MULTI_YEAR', name='pricingplan'), nullable=False, default='MONTHLY'),
        sa.Column('status', sa.Enum('ACTIVE', 'PAST_DUE', 'CANCELLED', name='subscriptionstatus'), nullable=False, default='ACTIVE'),
        sa.Column('base_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(), default='USD'),
        sa.Column('billing_cycle_start', sa.Date(), nullable=False),
        sa.Column('next_invoice_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(), default='invoice'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )

    # Invoices table
    op.create_table(
        'invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('subscription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subscriptions.id'), nullable=True),
        sa.Column('invoice_number', sa.String(), nullable=False, unique=True),
        sa.Column('subtotal', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('tax', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(), default='USD'),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'SENT', 'PAID', 'OVERDUE', 'VOID', name='invoicestatus'), nullable=False, default='DRAFT'),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('pdf_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )

    # Invoice Line Items table
    op.create_table(
        'invoice_line_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('quantity', sa.Integer(), default=1),
    )

    # Contracts table
    op.create_table(
        'contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('contract_type', sa.String(), default='subscription'),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('auto_renew', sa.Boolean(), default=True),
        sa.Column('notice_period_days', sa.Integer(), default=30),
        sa.Column('total_contract_value', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_terms', sa.String(), default='net30'),
        sa.Column('document_url', sa.String(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'PENDING_RENEWAL', 'EXPIRED', name='contractstatus'), nullable=False, default='ACTIVE'),
        sa.Column('renewal_reminder_sent', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )

    # Assets table
    op.create_table(
        'assets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('contract_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('contracts.id'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('asset_type', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
    )

    # Telemetry Pings table
    op.create_table(
        'telemetry_pings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(), default=sa.func.now()),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('status', sa.String(), default='HEALTHY'),
        sa.Column('cpu_percent', sa.Float(), nullable=True),
        sa.Column('memory_percent', sa.Float(), nullable=True),
        sa.Column('disk_percent', sa.Float(), nullable=True),
        sa.Column('active_users', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
    )

    # Usage Metrics table
    op.create_table(
        'usage_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('metric_name', sa.String(), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), default=sa.func.now()),
        sa.Column('dimensions', postgresql.JSON(), nullable=True),
    )

    # Support Tickets table
    op.create_table(
        'tickets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('priority', sa.String(), default='NORMAL'),
        sa.Column('status', sa.String(), default='OPEN'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Announcements table
    op.create_table(
        'announcements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('announcements')
    op.drop_table('tickets')
    op.drop_table('usage_metrics')
    op.drop_table('telemetry_pings')
    op.drop_table('assets')
    op.drop_table('contracts')
    op.drop_table('invoice_line_items')
    op.drop_table('invoices')
    op.drop_table('subscriptions')
    op.drop_table('license_audit_logs')
    op.drop_table('licenses')
    op.drop_table('tenant_deployments')
    op.drop_table('releases')
    op.drop_table('tenant_configs')
    op.drop_table('tenant_contacts')
    op.drop_table('tenants')
    op.drop_table('users')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS tenantstatus")
    op.execute("DROP TYPE IF EXISTS pricingtier")
    op.execute("DROP TYPE IF EXISTS releasetrack")
    op.execute("DROP TYPE IF EXISTS releasestatus")
    op.execute("DROP TYPE IF EXISTS pricingplan")
    op.execute("DROP TYPE IF EXISTS subscriptionstatus")
    op.execute("DROP TYPE IF EXISTS invoicestatus")
    op.execute("DROP TYPE IF EXISTS contractstatus")
