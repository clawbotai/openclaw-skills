"""Inventory cache — read-only mirror of Azoth OS when connected, local when standalone."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Enum, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class InventoryStatus(str, enum.Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class InventoryCache(Base):
    __tablename__ = "inventory_cache"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    substance: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    vial_size_mg: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[InventoryStatus] = mapped_column(Enum(InventoryStatus, name="inventory_status"), default=InventoryStatus.IN_STOCK)
    lot_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Azoth provider reference
    last_webhook_sync: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
