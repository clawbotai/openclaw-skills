"""Clinical notes (SOAP) endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.audit import log_audit
from app.middleware.rbac import require_roles, get_current_user
from app.models.user import User, UserRole
from app.schemas.clinical import ClinicalNoteCreate, ClinicalNoteUpdate, ClinicalNoteResponse
from app.services import clinical_service

router = APIRouter(prefix="/clinical-notes", tags=["clinical"])


@router.post("/", response_model=ClinicalNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    body: ClinicalNoteCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER)),
):
    result = await clinical_service.create_note(db, current_user.id, body)
    await log_audit(db, current_user.id, "CREATE", "clinical_notes", result.id,
                    ip_address=request.client.host if request.client else None)
    return result


@router.get("/patient/{patient_id}", response_model=list[ClinicalNoteResponse])
async def get_patient_notes(
    patient_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER, UserRole.CLINICAL_STAFF)),
):
    notes = await clinical_service.get_notes_for_patient(db, uuid.UUID(patient_id))
    await log_audit(db, current_user.id, "READ", "clinical_notes", patient_id,
                    detail=f"Listed {len(notes)} notes",
                    ip_address=request.client.host if request.client else None)
    return notes


@router.get("/{note_id}", response_model=ClinicalNoteResponse)
async def get_note(
    note_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER, UserRole.CLINICAL_STAFF)),
):
    result = await clinical_service.get_note(db, uuid.UUID(note_id))
    if not result:
        raise HTTPException(status_code=404, detail="Note not found")
    await log_audit(db, current_user.id, "READ", "clinical_notes", note_id,
                    ip_address=request.client.host if request.client else None)
    return result


@router.patch("/{note_id}", response_model=ClinicalNoteResponse)
async def update_note(
    note_id: str,
    body: ClinicalNoteUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER)),
):
    result = await clinical_service.update_note(db, uuid.UUID(note_id), current_user.id, body)
    if not result:
        raise HTTPException(status_code=404, detail="Note not found or not your note")
    await log_audit(db, current_user.id, "UPDATE", "clinical_notes", result.id,
                    ip_address=request.client.host if request.client else None)
    return result


@router.post("/{note_id}/sign", response_model=ClinicalNoteResponse)
async def sign_note(
    note_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.PROVIDER)),
):
    """Digitally sign a clinical note — makes it immutable."""
    result = await clinical_service.sign_note(db, uuid.UUID(note_id), current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Note not found or not your note")
    await log_audit(db, current_user.id, "SIGN", "clinical_notes", note_id,
                    ip_address=request.client.host if request.client else None)
    return result
