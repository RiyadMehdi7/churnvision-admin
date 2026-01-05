"""Add users table

Revision ID: 004
Revises: 003
Create Date: 2024-01-05 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table already exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if "users" not in tables:
        # Users table
        op.create_table(
            "users",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("full_name", sa.String(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("is_superuser", sa.Boolean(), default=False),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )

        # Create indexes
        op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()

    if "users" in tables:
        op.drop_index("ix_users_email")
        op.drop_table("users")
