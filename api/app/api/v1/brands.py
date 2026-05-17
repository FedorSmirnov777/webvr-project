import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.catalog import Brand
from app.models.user import UserRole
from app.schemas.catalog import BrandCreate, BrandOut
from app.scripts.bootstrap import main as bootstrap_main
from app.services.auth import require_roles

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("", response_model=list[BrandOut])
def list_brands(db: Session = Depends(get_db)) -> list[Brand]:
    try:
        return db.query(Brand).order_by(Brand.name.asc()).all()
    except OperationalError:
        db.rollback()
        try:
            bootstrap_main()
            return db.query(Brand).order_by(Brand.name.asc()).all()
        except Exception:
            logger.exception("Bootstrap failed while loading brands")
            return []


@router.post("", response_model=BrandOut)
def create_brand(
    payload: BrandCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.admin, UserRole.manager)),
) -> Brand:
    brand = Brand(name=payload.name.strip(), slug=payload.slug.strip(), country=payload.country.strip())
    db.add(brand)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Brand already exists")
    db.refresh(brand)
    return brand
