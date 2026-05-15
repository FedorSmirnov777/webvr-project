from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(80), nullable=False)

    cars = relationship("Car", back_populates="brand", cascade="all, delete-orphan")


class Car(Base):
    __tablename__ = "cars"
    __table_args__ = (UniqueConstraint("brand_id", "model_name", "year", name="uq_car_brand_model_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    body_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    base_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    specs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    published: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    brand = relationship("Brand", back_populates="cars")
    assets = relationship("CarAsset", back_populates="car", cascade="all, delete-orphan")
    trims = relationship("CarTrim", back_populates="car", cascade="all, delete-orphan")


class CarAsset(Base):
    __tablename__ = "car_assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)  # model_3d, image
    storage_key: Mapped[str] = mapped_column(String(400), nullable=False, unique=True)
    public_url: Mapped[str] = mapped_column(String(600), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    car = relationship("Car", back_populates="assets")


class CarTrim(Base):
    __tablename__ = "car_trims"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"), nullable=False, index=True)
    trim_name: Mapped[str] = mapped_column(String(120), nullable=False)
    trim_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    features: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    car = relationship("Car", back_populates="trims")
