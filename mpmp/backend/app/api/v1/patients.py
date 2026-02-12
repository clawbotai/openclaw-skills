"""Patient management endpoints."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.audit import log_audit
from app.middleware.rbac import require_roles, get_current_user
from app.models.user import User, UserRole
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientListItem
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    body: PatientCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER, UserRole.CLINICAL_STAFF)),
):
    result = await patient_service.create_patient(db, body)
    await log_audit(
        db, current_user.id, "CREATE", "patients", result.id,
        ip_address=request.client.host if request.client else None,
    )
    return result


@router.get("/", response_model=list[PatientListItem])
async def list_patients(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER, UserRole.CLINICAL_STAFF)),
):
    return await patient_service.list_patients(db, limit, offset)


@router.get("/me", response_model=PatientResponse)
async def get_my_profile(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Patient views their own profile."""
    result = await patient_service.get_patient_by_user(db, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="Patient profile not found")
    await log_audit(db, current_user.id, "READ", "patients", result.id,
                    ip_address=request.client.host if request.client else None)
    return result


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER, UserRole.CLINICAL_STAFF)),
):
    result = await patient_service.get_patient(db, uuid.UUID(patient_id))
    if not result:
        raise HTTPException(status_code=404, detail="Patient not found")
    await log_audit(db, current_user.id, "READ", "patients", patient_id,
                    ip_address=request.client.host if request.client else None)
    return result


@router.patch("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    body: PatientUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER)),
):
    result = await patient_service.update_patient(db, uuid.UUID(patient_id), body)
    if not result:
        raise HTTPException(status_code=404, detail="Patient not found")
    await log_audit(db, current_user.id, "UPDATE", "patients", patient_id,
                    ip_address=request.client.host if request.client else None)
    return result
