"""Patient CRUD with transparent PHI encryption/decryption."""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_phi, decrypt_phi
from app.core.security import hash_password
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientListItem


def _compute_bmi(weight_kg: Optional[float], height_cm: Optional[float]) -> Optional[float]:
    if weight_kg and height_cm and height_cm > 0:
        height_m = height_cm / 100.0
        return round(weight_kg / (height_m * height_m), 1)
    return None


def _patient_to_response(p: Patient) -> PatientResponse:
    return PatientResponse(
        id=str(p.id),
        user_id=str(p.user_id),
        azoth_alias_id=str(p.azoth_alias_id),
        first_name=decrypt_phi(p.first_name_enc),
        last_name=decrypt_phi(p.last_name_enc),
        dob=decrypt_phi(p.dob_enc),
        demographics=decrypt_phi(p.demographics_enc) if p.demographics_enc else None,
        weight_kg=p.weight_kg,
        height_cm=p.height_cm,
        bmi=_compute_bmi(p.weight_kg, p.height_cm),
    )


async def create_patient(db: AsyncSession, data: PatientCreate) -> PatientResponse:
    """Create user + patient record with encrypted PHI."""
    # Create user account first
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.PATIENT,
    )
    db.add(user)
    await db.flush()

    patient = Patient(
        user_id=user.id,
        first_name_enc=encrypt_phi(data.first_name),
        last_name_enc=encrypt_phi(data.last_name),
        dob_enc=encrypt_phi(data.dob),
        demographics_enc=encrypt_phi(data.demographics) if data.demographics else None,
        weight_kg=data.weight_kg,
        height_cm=data.height_cm,
    )
    db.add(patient)
    await db.flush()

    return _patient_to_response(patient)


async def get_patient(db: AsyncSession, patient_id: uuid.UUID) -> Optional[PatientResponse]:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    p = result.scalar_one_or_none()
    if not p:
        return None
    return _patient_to_response(p)


async def get_patient_by_user(db: AsyncSession, user_id: uuid.UUID) -> Optional[PatientResponse]:
    result = await db.execute(select(Patient).where(Patient.user_id == user_id))
    p = result.scalar_one_or_none()
    if not p:
        return None
    return _patient_to_response(p)


async def list_patients(db: AsyncSession, limit: int = 50, offset: int = 0) -> list[PatientListItem]:
    result = await db.execute(select(Patient).limit(limit).offset(offset))
    patients = result.scalars().all()
    return [
        PatientListItem(
            id=str(p.id),
            azoth_alias_id=str(p.azoth_alias_id),
            first_name=decrypt_phi(p.first_name_enc),
            last_name=decrypt_phi(p.last_name_enc),
            weight_kg=p.weight_kg,
        )
        for p in patients
    ]


async def update_patient(
    db: AsyncSession, patient_id: uuid.UUID, data: PatientUpdate
) -> Optional[PatientResponse]:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    p = result.scalar_one_or_none()
    if not p:
        return None

    if data.first_name is not None:
        p.first_name_enc = encrypt_phi(data.first_name)
    if data.last_name is not None:
        p.last_name_enc = encrypt_phi(data.last_name)
    if data.dob is not None:
        p.dob_enc = encrypt_phi(data.dob)
    if data.demographics is not None:
        p.demographics_enc = encrypt_phi(data.demographics)
    if data.weight_kg is not None:
        p.weight_kg = data.weight_kg
    if data.height_cm is not None:
        p.height_cm = data.height_cm

    await db.flush()
    return _patient_to_response(p)
