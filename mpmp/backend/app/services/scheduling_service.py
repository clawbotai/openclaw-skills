"""Scheduling service — appointments with telehealth link generation."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AppointmentResponse


def _apt_to_response(a: Appointment) -> AppointmentResponse:
    return AppointmentResponse(
        id=str(a.id),
        patient_id=str(a.patient_id),
        provider_id=str(a.provider_id),
        start_time=a.start_time.isoformat(),
        duration_minutes=a.duration_minutes,
        status=a.status.value,
        telehealth_link=a.telehealth_link,
        notes=a.notes,
        created_at=a.created_at.isoformat(),
    )


def _generate_telehealth_link(appointment_id: uuid.UUID) -> str:
    """Generate a placeholder telehealth link. Replace with Daily.co/Zoom API in production."""
    return f"https://meet.mpmp.local/session/{appointment_id}"


async def create_appointment(db: AsyncSession, data: AppointmentCreate) -> AppointmentResponse:
    apt = Appointment(
        patient_id=uuid.UUID(data.patient_id),
        provider_id=uuid.UUID(data.provider_id),
        start_time=datetime.fromisoformat(data.start_time),
        duration_minutes=data.duration_minutes,
        notes=data.notes,
    )
    if data.telehealth:
        apt.telehealth_link = _generate_telehealth_link(apt.id)

    db.add(apt)
    await db.flush()
    return _apt_to_response(apt)


async def get_appointment(db: AsyncSession, apt_id: uuid.UUID) -> Optional[AppointmentResponse]:
    result = await db.execute(select(Appointment).where(Appointment.id == apt_id))
    a = result.scalar_one_or_none()
    return _apt_to_response(a) if a else None


async def list_appointments(
    db: AsyncSession,
    provider_id: Optional[uuid.UUID] = None,
    patient_id: Optional[uuid.UUID] = None,
    status_filter: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    limit: int = 50,
) -> list[AppointmentResponse]:
    query = select(Appointment)
    conditions = []
    if provider_id:
        conditions.append(Appointment.provider_id == provider_id)
    if patient_id:
        conditions.append(Appointment.patient_id == patient_id)
    if status_filter:
        conditions.append(Appointment.status == AppointmentStatus(status_filter))
    if from_date:
        conditions.append(Appointment.start_time >= from_date)
    if to_date:
        conditions.append(Appointment.start_time <= to_date)
    if conditions:
        query = query.where(and_(*conditions))
    query = query.order_by(Appointment.start_time.asc()).limit(limit)

    result = await db.execute(query)
    return [_apt_to_response(a) for a in result.scalars().all()]


async def update_appointment(
    db: AsyncSession, apt_id: uuid.UUID, data: AppointmentUpdate
) -> Optional[AppointmentResponse]:
    result = await db.execute(select(Appointment).where(Appointment.id == apt_id))
    a = result.scalar_one_or_none()
    if not a:
        return None

    if data.start_time is not None:
        a.start_time = datetime.fromisoformat(data.start_time)
    if data.duration_minutes is not None:
        a.duration_minutes = data.duration_minutes
    if data.status is not None:
        a.status = AppointmentStatus(data.status)
    if data.notes is not None:
        a.notes = data.notes

    await db.flush()
    return _apt_to_response(a)


async def cancel_appointment(db: AsyncSession, apt_id: uuid.UUID) -> Optional[AppointmentResponse]:
    result = await db.execute(select(Appointment).where(Appointment.id == apt_id))
    a = result.scalar_one_or_none()
    if not a:
        return None
    a.status = AppointmentStatus.CANCELLED
    await db.flush()
    return _apt_to_response(a)
