from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.catalog import Brand, Car, CarAsset, CarTrim
from app.models.user import User, UserRole
from app.schemas.catalog import AssetOut, CarCreate, CarOut, CarUpdate, TrimCreate, TrimOut
from app.scripts.bootstrap import main as bootstrap_main
from app.services.auth import get_optional_user, require_roles
from app.services.storage import StorageService
from app.utils.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=list[CarOut])
def list_cars(
    brand_id: int | None = None,
    published_only: bool = True,
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> list[Car]:
    try:
        query = db.query(Car)
    except OperationalError:
        db.rollback()
        try:
            bootstrap_main()
            query = db.query(Car)
        except Exception:
            logger.exception("Bootstrap failed while loading cars")
            return []
    if brand_id:
        query = query.filter(Car.brand_id == brand_id)

    if published_only:
        query = query.filter(Car.published.is_(True))
    elif not user or user.role not in {UserRole.admin, UserRole.manager}:
        raise HTTPException(status_code=403, detail="Only admin/manager can view drafts")

    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Car.model_name.ilike(pattern), Car.body_type.ilike(pattern)))

    try:
        return query.order_by(Car.updated_at.desc()).all()
    except OperationalError:
        db.rollback()
        try:
            bootstrap_main()
            query = db.query(Car)
        except Exception:
            logger.exception("Bootstrap failed on retry while loading cars")
            return []
        if brand_id:
            query = query.filter(Car.brand_id == brand_id)
        if published_only:
            query = query.filter(Car.published.is_(True))
        if search:
            pattern = f"%{search}%"
            query = query.filter(or_(Car.model_name.ilike(pattern), Car.body_type.ilike(pattern)))
        return query.order_by(Car.updated_at.desc()).all()


@router.post("", response_model=CarOut)
def create_car(
    payload: CarCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.admin, UserRole.manager)),
) -> Car:
    brand_id = payload.brand_id
    if brand_id is None and payload.brand_slug:
        brand = db.query(Brand).filter(Brand.slug == payload.brand_slug).first()
        if not brand:
            raise HTTPException(status_code=400, detail=f"Brand slug not found: {payload.brand_slug}")
        brand_id = brand.id

    if brand_id is None:
        raise HTTPException(status_code=400, detail="brand_id or brand_slug is required")

    car = Car(
        brand_id=brand_id,
        model_name=payload.model_name,
        year=payload.year,
        body_type=payload.body_type,
        description=payload.description,
        base_price=payload.base_price,
        specs=payload.specs,
        config=payload.config,
        published=payload.published,
    )
    db.add(car)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Car with same brand/model/year already exists")
    db.refresh(car)
    return car


@router.get("/compare", response_model=list[CarOut])
def compare_cars(ids: list[int] = Query(..., min_length=2, max_length=2), db: Session = Depends(get_db)) -> list[Car]:
    cars = db.query(Car).filter(Car.id.in_(ids), Car.published.is_(True)).all()
    if len(cars) != 2:
        raise HTTPException(status_code=400, detail="Exactly two published car IDs are required")
    return cars


@router.get("/compare/items", response_model=list[CarOut])
def compare_cars_legacy(ids: list[int] = Query(..., min_length=2, max_length=2), db: Session = Depends(get_db)) -> list[Car]:
    cars = db.query(Car).filter(Car.id.in_(ids), Car.published.is_(True)).all()
    if len(cars) != 2:
        raise HTTPException(status_code=400, detail="Exactly two published car IDs are required")
    return cars


@router.post("/{car_id}/publish", response_model=CarOut)
def publish_car(
    car_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.admin, UserRole.manager)),
) -> Car:
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    car.published = True
    car.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(car)
    return car


@router.patch("/{car_id}", response_model=CarOut)
def update_car(
    car_id: int,
    payload: CarUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.admin, UserRole.manager)),
) -> Car:
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(car, key, value)

    car.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(car)
    return car


@router.post("/{car_id}/assets", response_model=AssetOut)
@limiter.limit("30/minute")
def upload_asset(
    car_id: int,
    request: Request,
    kind: str = Query(default="model_3d"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.admin, UserRole.manager)),
) -> CarAsset:
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if kind not in {"model_3d", "image"}:
        raise HTTPException(status_code=400, detail="kind must be model_3d or image")

    storage = StorageService()
    storage_key, public_url = storage.upload_local(file=file, prefix=f"car_{car_id}_{kind}_{int(datetime.now().timestamp())}")

    version = db.query(CarAsset).filter(CarAsset.car_id == car_id, CarAsset.kind == kind).count() + 1
    asset = CarAsset(car_id=car_id, kind=kind, storage_key=storage_key, public_url=public_url, version=version)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{car_id}/assets", response_model=list[AssetOut])
def list_assets(car_id: int, db: Session = Depends(get_db)) -> list[CarAsset]:
    return db.query(CarAsset).filter(CarAsset.car_id == car_id).order_by(CarAsset.created_at.desc()).all()


@router.post("/{car_id}/trims", response_model=TrimOut)
def add_trim(
    car_id: int,
    payload: TrimCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.admin, UserRole.manager)),
) -> CarTrim:
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    trim = CarTrim(car_id=car_id, trim_name=payload.trim_name, trim_price=payload.trim_price, features=payload.features)
    db.add(trim)
    db.commit()
    db.refresh(trim)
    return trim


@router.get("/{car_id}/trims", response_model=list[TrimOut])
def list_trims(car_id: int, db: Session = Depends(get_db)) -> list[CarTrim]:
    return db.query(CarTrim).filter(CarTrim.car_id == car_id).order_by(CarTrim.trim_price.asc().nulls_last()).all()


@router.get("/{car_id}")
def get_car(car_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)) -> dict:
    try:
        car = db.query(Car).filter(Car.id == car_id).first()
    except OperationalError:
        db.rollback()
        bootstrap_main()
        car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if not car.published and (not user or user.role not in {UserRole.admin, UserRole.manager}):
        raise HTTPException(status_code=404, detail="Car not found")

    trims = (
        db.query(CarTrim)
        .filter(CarTrim.car_id == car.id)
        .order_by(CarTrim.trim_price.asc().nulls_last())
        .all()
    )
    assets = db.query(CarAsset).filter(CarAsset.car_id == car.id).order_by(CarAsset.created_at.desc()).all()

    image_assets   = sorted([a for a in assets if a.kind == "image"], key=lambda a: a.version or 0)
    hero_image_url = image_assets[0].public_url if image_assets else None
    extra_images   = [a.public_url for a in image_assets[1:]]
    model_url      = next((a.public_url for a in assets if a.kind == "model_3d"), None)

    return {
        "id": car.id,
        "brand_id": car.brand_id,
        "model_name": car.model_name,
        "year": car.year,
        "body_type": car.body_type,
        "description": car.description,
        "base_price": float(car.base_price) if car.base_price is not None else None,
        "specs": car.specs or {},
        "config": {
            **(car.config or {}),
            "hero_image_url": hero_image_url,
            "model_url": model_url,
        },
        "extra_images": extra_images,
        "published": car.published,
        "created_at": car.created_at,
        "updated_at": car.updated_at,
        "trims": [
            {
                "trim_name": trim.trim_name,
                "trim_price": float(trim.trim_price) if trim.trim_price is not None else None,
                "features": trim.features or {},
            }
            for trim in trims
        ],
    }
