"""add apartment_availability table

Revision ID: d1e9e8b7c3a4
Revises: c445197f0525
Create Date: 2026-01-08 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d1e9e8b7c3a4"
down_revision: Union[str, Sequence[str], None] = "c445197f0525"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add apartment_availability table."""
    # Create apartment_availability table
    op.create_table(
        "apartment_availability",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("apartment_id", sa.Integer(), nullable=False),
        sa.Column("blocked_period", postgresql.DATERANGE(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("is_blocked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("custom_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("min_stay_days", sa.Integer(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(
            ["apartment_id"], ["apartment.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create index on apartment_id
    op.create_index(
        op.f("ix_apartment_availability_apartment_id"),
        "apartment_availability",
        ["apartment_id"],
        unique=False,
    )

    # Create GIST exclusion constraint to prevent overlapping availability rules
    # for the same apartment
    # Using explicit SQL to specify operator classes (int4_ops for integer, range_ops for daterange)
    op.execute(
        """
        CREATE EXTENSION IF NOT EXISTS btree_gist;

        ALTER TABLE apartment_availability
        ADD CONSTRAINT exclude_overlapping_availabilities
        EXCLUDE USING gist (apartment_id WITH =, blocked_period WITH &&);
        """
    )


def downgrade() -> None:
    """Downgrade schema - remove apartment_availability table."""
    op.drop_table("apartment_availability")
