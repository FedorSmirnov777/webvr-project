"""init schema

Revision ID: 20260301_0001
Revises:
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa


revision = "20260301_0001"
down_revision = None
branch_labels = None
depends_on = None


role_enum = sa.Enum("admin", "manager", "viewer", name="user_role")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        role_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "brands",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False),
    )
    op.create_index("ix_brands_slug", "brands", ["slug"], unique=True)

    op.create_table(
        "cars",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("body_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("specs", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("brand_id", "model_name", "year", name="uq_car_brand_model_year"),
    )

    op.create_table(
        "car_assets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("car_id", sa.Integer(), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("storage_key", sa.String(length=400), nullable=False, unique=True),
        sa.Column("public_url", sa.String(length=600), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_car_assets_car_id", "car_assets", ["car_id"], unique=False)

    op.create_table(
        "car_trims",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("car_id", sa.Integer(), sa.ForeignKey("cars.id", ondelete="CASCADE"), nullable=False),
        sa.Column("trim_name", sa.String(length=120), nullable=False),
        sa.Column("trim_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("features", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_car_trims_car_id", "car_trims", ["car_id"], unique=False)

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("car_id", sa.Integer(), sa.ForeignKey("cars.id", ondelete="SET NULL"), nullable=True),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("lead_type", sa.String(length=40), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_name", sa.String(length=120), nullable=False),
        sa.Column("car_id", sa.Integer(), sa.ForeignKey("cars.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(length=120), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_events_event_name", "events", ["event_name"], unique=False)
    op.create_index("ix_events_session_id", "events", ["session_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_events_session_id", table_name="events")
    op.drop_index("ix_events_event_name", table_name="events")
    op.drop_table("events")
    op.drop_table("leads")
    op.drop_index("ix_car_trims_car_id", table_name="car_trims")
    op.drop_table("car_trims")
    op.drop_index("ix_car_assets_car_id", table_name="car_assets")
    op.drop_table("car_assets")
    op.drop_table("cars")
    op.drop_index("ix_brands_slug", table_name="brands")
    op.drop_table("brands")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
