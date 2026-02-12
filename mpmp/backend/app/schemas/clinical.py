"""Clinical note (SOAP) schemas."""
from typing import Optional
from pydantic import BaseModel


class SOAPData(BaseModel):
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""


class ClinicalNoteCreate(BaseModel):
    patient_id: str
    soap: SOAPData


class ClinicalNoteUpdate(BaseModel):
    soap: SOAPData


class ClinicalNoteSign(BaseModel):
    """Empty body — signing uses the authenticated provider's identity."""
    pass


class ClinicalNoteResponse(BaseModel):
    id: str
    patient_id: str
    provider_id: str
    version: int
    soap: SOAPData
    signed_at: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
