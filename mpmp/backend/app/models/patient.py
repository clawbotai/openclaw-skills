"""Patient model — PHI fields encrypted at application level (AES-256-GCM)."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    # Anonymized ID for ALL external FHIR payloads — no PHI leaves the system
    azoth_alias_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True
    )
    # PHI — stored as AES-256-GCM encrypted base64 blobs
    first_name_enc: Mapped[str] = mapped_column(Text, nullable=False)
    last_name_enc: Mapped[str] = mapped_column(Text, nullable=False)
    dob_enc: Mapped[str] = mapped_column(Text, nullable=False)  # ISO date string, encrypted
    demographics_enc: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON blob, encrypted

    # Non-PHI biometrics (used by magistral calculator)
    weight_kg: Mapped[float | None] = mapped_column(nullable=True)
    height_cm: Mapped[float | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
