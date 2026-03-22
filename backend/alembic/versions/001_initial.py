"""Initial migration - create all tables

Revision ID: 0001
Revises:
Create Date: 2026-03-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users (no FK dependencies)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("phone", sa.String(20), unique=True, nullable=True),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), server_default="client", nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_city", "users", ["city"])

    # 2. refresh_tokens (FK -> users)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), unique=True, nullable=False),
        sa.Column("device_info", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    # 3. categories (no FK dependencies)
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )

    # 4. master_profiles (FK -> users, categories)
    op.create_table(
        "master_profiles",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id"), unique=True, nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", postgresql.UUID(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("rating_avg", sa.Numeric(3, 2), server_default="0", nullable=False),
        sa.Column("rating_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("verification_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("verification_docs", postgresql.JSONB(), nullable=True),
        sa.Column("work_hours", postgresql.JSONB(), nullable=True),
        sa.Column("is_available", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_master_profiles_user_id", "master_profiles", ["user_id"])
    op.create_index("ix_master_profiles_category_id", "master_profiles", ["category_id"])
    op.create_index("ix_master_profiles_verification_status", "master_profiles", ["verification_status"])
    op.create_index("ix_master_profiles_rating_avg", "master_profiles", ["rating_avg"])

    # 5. services (FK -> master_profiles)
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("master_id", postgresql.UUID(), sa.ForeignKey("master_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_services_master_id", "services", ["master_id"])
    op.create_index("ix_services_price", "services", ["price"])

    # 6. portfolio_images (FK -> master_profiles)
    op.create_table(
        "portfolio_images",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("master_id", postgresql.UUID(), sa.ForeignKey("master_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. time_slots (FK -> master_profiles)
    op.create_table(
        "time_slots",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("master_id", postgresql.UUID(), sa.ForeignKey("master_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_booked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("master_id", "date", "start_time", name="uq_time_slots_master_date_start"),
    )
    op.create_index("ix_time_slots_master_id_date", "time_slots", ["master_id", "date"])

    # 8. bookings (FK -> users, master_profiles, services, time_slots)
    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("client_id", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("master_id", postgresql.UUID(), sa.ForeignKey("master_profiles.id"), nullable=False),
        sa.Column("service_id", postgresql.UUID(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("slot_id", postgresql.UUID(), sa.ForeignKey("time_slots.id"), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("is_online", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("cancelled_by", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bookings_client_id", "bookings", ["client_id"])
    op.create_index("ix_bookings_master_id", "bookings", ["master_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_created_at", "bookings", ["created_at"])

    # 9. payments (FK -> bookings)
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("booking_id", postgresql.UUID(), sa.ForeignKey("bookings.id"), unique=True, nullable=False),
        sa.Column("yukassa_payment_id", sa.String(100), unique=True, nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("platform_fee", sa.Numeric(10, 2), nullable=False),
        sa.Column("master_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 10. payouts (FK -> master_profiles)
    op.create_table(
        "payouts",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("master_id", postgresql.UUID(), sa.ForeignKey("master_profiles.id"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("card_last4", sa.String(4), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 11. chat_rooms (FK -> bookings, users)
    op.create_table(
        "chat_rooms",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("booking_id", postgresql.UUID(), sa.ForeignKey("bookings.id"), unique=True, nullable=False),
        sa.Column("client_id", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("master_user_id", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 12. messages (FK -> chat_rooms, users)
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("room_id", postgresql.UUID(), sa.ForeignKey("chat_rooms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(500), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_messages_room_id_created_at", "messages", ["room_id", "created_at"])

    # 13. reviews (FK -> bookings, users, master_profiles)
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("booking_id", postgresql.UUID(), sa.ForeignKey("bookings.id"), unique=True, nullable=False),
        sa.Column("client_id", postgresql.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("master_id", postgresql.UUID(), sa.ForeignKey("master_profiles.id"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("master_reply", sa.Text(), nullable=True),
        sa.Column("is_visible", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )

    # 14. notifications (FK -> users)
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(), nullable=True),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id_is_read", "notifications", ["user_id", "is_read"])

    # 15. fcm_tokens (FK -> users)
    op.create_table(
        "fcm_tokens",
        sa.Column("id", postgresql.UUID(), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", postgresql.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(500), nullable=False),
        sa.Column("device_info", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "token", name="uq_fcm_tokens_user_token"),
    )


def downgrade() -> None:
    op.drop_table("fcm_tokens")
    op.drop_table("notifications")
    op.drop_table("reviews")
    op.drop_table("messages")
    op.drop_table("chat_rooms")
    op.drop_table("payouts")
    op.drop_table("payments")
    op.drop_table("bookings")
    op.drop_table("time_slots")
    op.drop_table("portfolio_images")
    op.drop_table("services")
    op.drop_table("master_profiles")
    op.drop_table("categories")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
