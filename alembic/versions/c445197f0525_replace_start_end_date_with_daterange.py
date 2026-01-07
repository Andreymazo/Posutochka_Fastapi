"""replace_start_end_date_with_daterange

Revision ID: c445197f0525
Revises: adc25bdc87d9
Create Date: 2026-01-07 21:25:04.381356

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c445197f0525"
down_revision: Union[str, Sequence[str], None] = "adc25bdc87d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - replace start_date/end_date with booking_period DATERANGE."""
    # Enable btree_gist extension for GIST index on DATERANGE
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    # Add new booking_period column as DATERANGE
    op.add_column("booking", sa.Column("booking_period", postgresql.DATERANGE(), nullable=True))

    # Migrate existing data: create Range from start_date and end_date
    # [) means start_date is included, end_date is excluded
    op.execute("""
        UPDATE booking
        SET booking_period = daterange(start_date::date, end_date::date, '[)')
        WHERE start_date IS NOT NULL AND end_date IS NOT NULL
    """)

    # Drop the GIST index that will be created by the model (if it exists from a previous run)
    op.execute("DROP INDEX IF EXISTS ix_booking_no_overlap")

    # Make booking_period NOT NULL after data migration
    op.alter_column("booking", "booking_period", nullable=False)

    # Drop old columns
    op.drop_column("booking", "start_date")
    op.drop_column("booking", "end_date")

    # Create GIST index to prevent overlapping bookings for the same apartment
    # Using explicit SQL to specify operator classes (int4_ops for integer, range_ops for daterange)
    op.execute(
        """
        CREATE INDEX ix_booking_no_overlap
        ON booking
        USING gist (apartment_id int4_ops, booking_period range_ops)
        """
    )


def downgrade() -> None:
    """Downgrade schema - restore start_date/end_date from booking_period."""
    # Drop the GIST index
    op.drop_index("ix_booking_no_overlap", table_name="booking", postgresql_using="gist")

    # Add back the old columns
    op.add_column("booking", sa.Column("start_date", sa.DateTime(), nullable=True))
    op.add_column("booking", sa.Column("end_date", sa.DateTime(), nullable=True))

    # Migrate data back: extract dates from Range
    op.execute("""
        UPDATE booking
        SET start_date = lower(booking_period)::timestamp,
            end_date = upper(booking_period)::timestamp
        WHERE booking_period IS NOT NULL
    """)

    # Make old columns NOT NULL
    op.alter_column("booking", "start_date", nullable=False)
    op.alter_column("booking", "end_date", nullable=False)

    # Drop booking_period column
    op.drop_column("booking", "booking_period")
