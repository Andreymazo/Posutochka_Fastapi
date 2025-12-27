"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2024-12-27

Creates all initial tables for the Posutochka application:
- user (with user_role enum)
- landlord
- client
- apartment
- photo
- booking (with booking_status enum)
- payment (with payment_status enum)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create enums explicitly with checkfirst=True to handle cases
    # where the types may already exist in the database
    user_role_enum = sa.Enum("landlord", "client", name="user_role", create_type=False)
    booking_status_enum = sa.Enum(
        "pending", "confirmed", "cancelled", name="booking_status", create_type=False
    )
    payment_status_enum = sa.Enum(
        "paid", "pending", "failed", name="payment_status", create_type=False
    )

    # Create enum types in PostgreSQL before creating tables
    user_role_enum.create(op.get_bind(), checkfirst=True)
    booking_status_enum.create(op.get_bind(), checkfirst=True)
    payment_status_enum.create(op.get_bind(), checkfirst=True)

    # Create user table
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("phone_number", sa.String(15), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("registration_date", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("telegram_username", sa.String(32), nullable=True),
    )

    # Create landlord table
    op.create_table(
        "landlord",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), unique=True, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
    )

    # Create client table
    op.create_table(
        "client",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), unique=True, nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
    )

    # Create apartment table
    op.create_table(
        "apartment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("price_per_night", sa.Float(), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
    )

    # Create photo table
    op.create_table(
        "photo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("apartment_id", sa.Integer(), sa.ForeignKey("apartment.id"), nullable=False),
        sa.Column("url", sa.String(255), nullable=False),
    )

    # Create booking table
    op.create_table(
        "booking",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("cost", sa.Float(), nullable=False),
        sa.Column("booking_status", booking_status_enum, nullable=False),
        sa.Column("landlord_id", sa.Integer(), sa.ForeignKey("landlord.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("client.id"), nullable=False),
        sa.Column("apartment_id", sa.Integer(), sa.ForeignKey("apartment.id"), nullable=False),
    )

    # Create payment table
    op.create_table(
        "payment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("booking.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("payment_date", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("payment_status", payment_status_enum, nullable=False),
    )


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table("payment")
    op.drop_table("booking")
    op.drop_table("photo")
    op.drop_table("apartment")
    op.drop_table("client")
    op.drop_table("landlord")
    op.drop_table("user")

    # Drop enums
    sa.Enum(name="payment_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="booking_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
