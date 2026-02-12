"""Azoth OS outbound routing — FHIR MedicationRequest via SMART on FHIR OAuth2.

Handles:
1. OAuth2 Client Credentials flow for machine-to-machine auth
2. FHIR MedicationRequest payload construction
3. Submission to Azoth REST API
4. Fallback PDF+SMTP dispatch when AZOTH_OS_SYNC=FALSE
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.core.config import settings
from app.services.magistral_calculator import DosageCalculation


# SNOMED CT route codes
ROUTE_CODES = {
    "subcutaneous": {"code": "34206005", "display": "Subcutaneous route"},
    "intramuscular": {"code": "78421000", "display": "Intramuscular route"},
    "intravenous": {"code": "47625008", "display": "Intravenous route"},
    "oral": {"code": "26643006", "display": "Oral route"},
}


class AzothTokenCache:
    """Simple in-memory OAuth2 token cache."""
    _token: Optional[str] = None
    _expires_at: Optional[datetime] = None

    @classmethod
    async def get_token(cls) -> str:
        now = datetime.now(timezone.utc)
        if cls._token and cls._expires_at and cls._expires_at > now:
            return cls._token

        if not settings.AZOTH_CLIENT_ID or not settings.AZOTH_CLIENT_SECRET:
            raise RuntimeError("Azoth OAuth2 credentials not configured")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.AZOTH_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.AZOTH_CLIENT_ID,
                    "client_secret": settings.AZOTH_CLIENT_SECRET,
                    "scope": settings.AZOTH_FHIR_SCOPE,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        cls._token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        cls._expires_at = now.replace(second=0) + __import__("datetime").timedelta(seconds=expires_in - 60)
        return cls._token


def build_medication_request(
    prescription_id: uuid.UUID,
    azoth_alias_id: uuid.UUID,
    calculation: DosageCalculation,
    route: str = "subcutaneous",
) -> dict:
    """Construct a FHIR MedicationRequest payload per Azoth spec."""
    route_info = ROUTE_CODES.get(route.lower(), ROUTE_CODES["subcutaneous"])

    return {
        "resourceType": "MedicationRequest",
        "identifier": [
            {"system": "urn:uuid", "value": str(prescription_id)}
        ],
        "status": "active",
        "intent": "order",
        "subject": {
            "reference": f"Patient/{azoth_alias_id}"
        },
        "medicationCodeableConcept": {
            "coding": [{
                "system": "http://azoth-os.com/fhir/peptides",
                "code": calculation.compound,
            }]
        },
        "dosageInstruction": [{
            "text": calculation.fhir_dosage_text,
            "route": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": route_info["code"],
                    "display": route_info["display"],
                }]
            },
        }],
        "dispenseRequest": {
            "quantity": {"value": 1, "unit": "vial"}
        },
    }


async def submit_medication_request(fhir_payload: dict) -> dict:
    """POST MedicationRequest to Azoth OS FHIR endpoint.

    Returns {"order_tracking_id": "...", "status": "accepted"} on success.
    Raises on failure.
    """
    token = await AzothTokenCache.get_token()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.AZOTH_API_BASE}/MedicationRequest",
            json=fhir_payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/fhir+json",
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return resp.json()


async def route_prescription(
    prescription_id: uuid.UUID,
    azoth_alias_id: uuid.UUID,
    calculation: DosageCalculation,
    route: str = "subcutaneous",
) -> dict:
    """High-level routing decision based on AZOTH_OS_SYNC state.

    Returns routing result with tracking info.
    """
    if settings.AZOTH_OS_SYNC:
        # STATE B: Connected Mode — push FHIR to Azoth
        payload = build_medication_request(
            prescription_id, azoth_alias_id, calculation, route
        )
        result = await submit_medication_request(payload)
        return {
            "mode": "azoth",
            "tracking_id": result.get("id") or result.get("order_tracking_id"),
            "fhir_payload": payload,
            "response": result,
        }
    else:
        # STATE A: Standalone Mode — generate PDF for SMTP
        from app.services.pdf_generator import generate_prescription_pdf
        pdf_bytes, pdf_hash = generate_prescription_pdf(
            calculation=calculation,
            provider_name="Provider",  # Resolved by caller
            patient_alias=str(azoth_alias_id),
            prescription_id=str(prescription_id),
        )
        # TODO: Enqueue SMTP job via Celery/Redis
        return {
            "mode": "standalone",
            "pdf_hash": pdf_hash,
            "pdf_size_bytes": len(pdf_bytes),
            "smtp_queued": False,  # Will be True after Celery integration
        }
