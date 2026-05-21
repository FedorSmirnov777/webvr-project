import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.commerce import Event, Lead, Rating
from app.models.user import UserRole
from app.schemas.commerce import EventCreate, LeadCreate, RatingCreate, RatingOut
from app.services.lead_notify import send_lead_to_telegram
from app.services.auth import require_roles
from app.utils.rate_limit import limiter

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/leads")
@limiter.limit("20/minute")
def create_lead(payload: LeadCreate, request: Request, db: Session = Depends(get_db)) -> dict[str, int]:
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)

    try:
        send_lead_to_telegram(lead)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Telegram lead notification failed: %s", exc)

    return {"id": lead.id}


@router.post("/events")
@limiter.limit("120/minute")
def track_event(payload: EventCreate, request: Request, db: Session = Depends(get_db)) -> dict[str, int]:
    event = Event(**payload.model_dump())
    db.add(event)
    db.commit()
    return {"id": event.id}


@router.get("/analytics/funnel")
def get_funnel(
    db: Session = Depends(get_db),
    _=Depends(require_roles(UserRole.admin, UserRole.manager)),
) -> dict[str, int]:
    views = db.query(func.count(Event.id)).filter(Event.event_name == "car_view").scalar() or 0
    configs = db.query(func.count(Event.id)).filter(Event.event_name == "car_configured").scalar() or 0
    leads = db.query(func.count(Lead.id)).scalar() or 0

    return {
        "views": views,
        "configured": configs,
        "leads": leads,
    }


@router.get("/ratings/{car_id}", response_model=RatingOut)
def get_rating(car_id: int, db: Session = Depends(get_db)) -> dict:
    result = db.query(func.avg(Rating.score), func.count(Rating.id)).filter(Rating.car_id == car_id).one()
    avg = round(float(result[0]), 1) if result[0] is not None else 0.0
    return {"average": avg, "count": result[1] or 0}


@router.post("/ratings/{car_id}", response_model=RatingOut)
@limiter.limit("10/minute")
def submit_rating(car_id: int, payload: RatingCreate, request: Request, db: Session = Depends(get_db)) -> dict:
    db.add(Rating(car_id=car_id, score=payload.score))
    db.commit()
    result = db.query(func.avg(Rating.score), func.count(Rating.id)).filter(Rating.car_id == car_id).one()
    avg = round(float(result[0]), 1) if result[0] is not None else 0.0
    return {"average": avg, "count": result[1] or 0}
