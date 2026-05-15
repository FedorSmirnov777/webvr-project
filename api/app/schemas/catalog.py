from datetime import datetime

from pydantic import BaseModel, Field


class BrandCreate(BaseModel):
    name: str
    slug: str
    country: str


class BrandOut(BaseModel):
    id: int
    name: str
    slug: str
    country: str

    class Config:
        from_attributes = True


class CarCreate(BaseModel):
    brand_id: int | None = None
    brand_slug: str | None = None
    model_name: str
    year: int = Field(ge=1980, le=2100)
    body_type: str
    description: str
    base_price: float | None = None
    specs: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)
    published: bool = False


class CarUpdate(BaseModel):
    body_type: str | None = None
    description: str | None = None
    base_price: float | None = None
    specs: dict | None = None
    config: dict | None = None
    published: bool | None = None


class CarOut(BaseModel):
    id: int
    brand_id: int
    model_name: str
    year: int
    body_type: str
    description: str
    base_price: float | None
    specs: dict
    config: dict
    published: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssetOut(BaseModel):
    id: int
    car_id: int
    kind: str
    storage_key: str
    public_url: str
    version: int

    class Config:
        from_attributes = True


class TrimCreate(BaseModel):
    trim_name: str
    trim_price: float | None = None
    features: dict = Field(default_factory=dict)


class TrimOut(BaseModel):
    id: int
    car_id: int
    trim_name: str
    trim_price: float | None
    features: dict
    created_at: datetime

    class Config:
        from_attributes = True
