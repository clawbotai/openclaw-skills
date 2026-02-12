"""Appointment/scheduling schemas."""
from typing import Optional
from pydantic import BaseModel


class AppointmentCreate(BaseModel):
    patient_id: str
    provider_id: str
    start_time: str  # ISO datetime
    duration_minutes: int = 30
    notes: Optional[str] = None
    telehealth: bool = False


class AppointmentUpdate(BaseModel):
    start_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    patient_id: str
    provider_id: str
    start_time: str
    duration_minutes: int
    status: str
    telehealth_link: Optional[str] = None
    notes: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
