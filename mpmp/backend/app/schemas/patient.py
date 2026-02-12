"""Patient request/response schemas — PHI handled transparently."""
from typing import Optional
from pydantic import BaseModel


class PatientCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    dob: str  # ISO date YYYY-MM-DD
    demographics: Optional[str] = None  # JSON string
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[str] = None
    demographics: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None


class PatientResponse(BaseModel):
    id: str
    user_id: str
    azoth_alias_id: str
    first_name: str
    last_name: str
    dob: str
    demographics: Optional[str] = None
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    bmi: Optional[float] = None

    class Config:
        from_attributes = True


class PatientListItem(BaseModel):
    id: str
    azoth_alias_id: str
    first_name: str
    last_name: str
    weight_kg: Optional[float] = None
