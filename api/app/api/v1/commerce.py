import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.commerce import Event, Lead
from app.models.user import UserRole
from app.schemas.commerce import EventCreate, LeadCreate
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
