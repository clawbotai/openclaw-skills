"""Prescription model — links to Azoth tracking when AZOTH_OS_SYNC is TRUE."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PrescriptionStatus(str, enum.Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    PENDING_PAYMENT = "pending_payment"
    SUBMITTED = "submitted"  # Sent to Azoth or SMTP
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class Prescription(Base):
    __tablename__ = "prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)
    provider_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[PrescriptionStatus] = mapped_column(Enum(PrescriptionStatus, name="prescription_status"), default=PrescriptionStatus.DRAFT)
    # Azoth integration
    azoth_tracking_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    # Magistral calculator output
    compound: Mapped[str] = mapped_column(String(255), nullable=False)
    vial_size_mg: Mapped[float | None] = mapped_column(nullable=True)
    diluent_ml: Mapped[float | None] = mapped_column(nullable=True)
    target_dose_mcg: Mapped[float | None] = mapped_column(nullable=True)
    calculated_dosage_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    # FHIR payload (stored for audit)
    fhir_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
