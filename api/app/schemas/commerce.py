from pydantic import BaseModel, EmailStr, Field


class LeadCreate(BaseModel):
    car_id: int | None = None
    full_name: str
    email: EmailStr
    phone: str | None = None
    lead_type: str = Field(pattern="^(test_drive|quote)$")
    note: str | None = None
    payload: dict = Field(default_factory=dict)


class EventCreate(BaseModel):
    event_name: str
    car_id: int | None = None
    session_id: str | None = None
    payload: dict = Field(default_factory=dict)
