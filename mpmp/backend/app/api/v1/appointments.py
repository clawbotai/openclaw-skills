"""Scheduling & appointment endpoints."""
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.middleware.audit import log_audit
from app.middleware.rbac import require_roles, get_current_user
from app.models.user import User, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse
from app.services import scheduling_service

router = APIRouter(prefix="/appointments", tags=["scheduling"])


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: AppointmentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER, UserRole.CLINICAL_STAFF)),
):
    result = await scheduling_service.create_appointment(db, body)
    await log_audit(db, current_user.id, "CREATE", "appointments", result.id,
                    ip_address=request.client.host if request.client else None)
    return result


@router.get("/", response_model=list[AppointmentResponse])
async def list_appointments(
    provider_id: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Patients can only see their own appointments
    if current_user.role == UserRole.PATIENT:
        from app.services.patient_service import get_patient_by_user
        patient = await get_patient_by_user(db, current_user.id)
        if not patient:
            return []
        patient_id = patient.id

    return await scheduling_service.list_appointments(
        db,
        provider_id=uuid.UUID(provider_id) if provider_id else None,
        patient_id=uuid.UUID(patient_id) if patient_id else None,
        status_filter=status_filter,
        from_date=datetime.fromisoformat(from_date) if from_date else None,
        to_date=datetime.fromisoformat(to_date) if to_date else None,
        limit=limit,
    )


@router.get("/{apt_id}", response_model=AppointmentResponse)
async def get_appointment(
    apt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await scheduling_service.get_appointment(db, uuid.UUID(apt_id))
    if not result:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return result


@router.patch("/{apt_id}", response_model=AppointmentResponse)
async def update_appointment(
    apt_id: str,
    body: AppointmentUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER, UserRole.CLINICAL_STAFF)),
):
    result = await scheduling_service.update_appointment(db, uuid.UUID(apt_id), body)
    if not result:
        raise HTTPException(status_code=404, detail="Appointment not found")
    await log_audit(db, current_user.id, "UPDATE", "appointments", apt_id,
                    ip_address=request.client.host if request.client else None)
    return result


@router.delete("/{apt_id}", response_model=AppointmentResponse)
async def cancel_appointment(
    apt_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN, UserRole.PROVIDER, UserRole.CLINICAL_STAFF)),
):
    result = await scheduling_service.cancel_appointment(db, uuid.UUID(apt_id))
    if not result:
        raise HTTPException(status_code=404, detail="Appointment not found")
    await log_audit(db, current_user.id, "CANCEL", "appointments", apt_id,
                    ip_address=request.client.host if request.client else None)
    return result
