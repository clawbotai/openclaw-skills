"""Clinical notes service — SOAP with encryption, versioning, and digital signing."""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_phi, decrypt_phi
from app.models.clinical_note import ClinicalNote
from app.schemas.clinical import SOAPData, ClinicalNoteCreate, ClinicalNoteUpdate, ClinicalNoteResponse


def _note_to_response(n: ClinicalNote) -> ClinicalNoteResponse:
    soap_json = decrypt_phi(n.soap_data_enc)
    soap = SOAPData(**json.loads(soap_json)) if soap_json else SOAPData()
    return ClinicalNoteResponse(
        id=str(n.id),
        patient_id=str(n.patient_id),
        provider_id=str(n.provider_id),
        version=n.version,
        soap=soap,
        signed_at=n.signed_at.isoformat() if n.signed_at else None,
        created_at=n.created_at.isoformat(),
        updated_at=n.updated_at.isoformat(),
    )


async def create_note(
    db: AsyncSession, provider_id: uuid.UUID, data: ClinicalNoteCreate
) -> ClinicalNoteResponse:
    soap_json = data.soap.model_dump_json()
    note = ClinicalNote(
        patient_id=uuid.UUID(data.patient_id),
        provider_id=provider_id,
        soap_data_enc=encrypt_phi(soap_json),
        version=1,
    )
    db.add(note)
    await db.flush()
    return _note_to_response(note)


async def update_note(
    db: AsyncSession, note_id: uuid.UUID, provider_id: uuid.UUID, data: ClinicalNoteUpdate
) -> Optional[ClinicalNoteResponse]:
    result = await db.execute(
        select(ClinicalNote).where(ClinicalNote.id == note_id, ClinicalNote.provider_id == provider_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        return None
    if note.signed_at:
        # Signed notes are immutable — create a new version
        soap_json = data.soap.model_dump_json()
        new_note = ClinicalNote(
            patient_id=note.patient_id,
            provider_id=provider_id,
            soap_data_enc=encrypt_phi(soap_json),
            version=note.version + 1,
        )
        db.add(new_note)
        await db.flush()
        return _note_to_response(new_note)

    note.soap_data_enc = encrypt_phi(data.soap.model_dump_json())
    await db.flush()
    return _note_to_response(note)


async def sign_note(
    db: AsyncSession, note_id: uuid.UUID, provider_id: uuid.UUID
) -> Optional[ClinicalNoteResponse]:
    """Digitally sign a note — makes it immutable."""
    result = await db.execute(
        select(ClinicalNote).where(ClinicalNote.id == note_id, ClinicalNote.provider_id == provider_id)
    )
    note = result.scalar_one_or_none()
    if not note:
        return None
    if note.signed_at:
        return _note_to_response(note)  # Already signed

    # SHA-256 of encrypted content + provider + timestamp for tamper detection
    sign_time = datetime.now(timezone.utc)
    sig_input = f"{note.soap_data_enc}:{provider_id}:{sign_time.isoformat()}"
    note.signature_hash = hashlib.sha256(sig_input.encode()).hexdigest()
    note.signed_at = sign_time
    await db.flush()
    return _note_to_response(note)


async def get_notes_for_patient(
    db: AsyncSession, patient_id: uuid.UUID, limit: int = 50
) -> list[ClinicalNoteResponse]:
    result = await db.execute(
        select(ClinicalNote)
        .where(ClinicalNote.patient_id == patient_id)
        .order_by(ClinicalNote.created_at.desc())
        .limit(limit)
    )
    return [_note_to_response(n) for n in result.scalars().all()]


async def get_note(db: AsyncSession, note_id: uuid.UUID) -> Optional[ClinicalNoteResponse]:
    result = await db.execute(select(ClinicalNote).where(ClinicalNote.id == note_id))
    note = result.scalar_one_or_none()
    if not note:
        return None
    return _note_to_response(note)
