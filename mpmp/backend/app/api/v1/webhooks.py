"""Azoth OS inbound webhooks — inventory updates with HMAC verification + idempotency."""
import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.middleware.audit import log_audit
from app.models.inventory import InventoryCache, InventoryStatus

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# In-memory idempotency set (replace with Redis in production)
_processed_events: set[str] = set()


def _verify_hmac(raw_body: bytes, signature: str, secret: str) -> bool:
    """Constant-time HMAC-SHA256 verification."""
    expected = hmac.new(
        secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/inventory-update")
async def inventory_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_azoth_signature: str = Header(None, alias="X-Azoth-Signature"),
):
    """Receive inventory updates from Azoth OS.

    Expected payload:
    {
        "event_id": "uuid",
        "event_type": "inventory.updated",
        "timestamp": "ISO-8601",
        "provider_id": "string",
        "data": {
            "substance": "BPC-157",
            "vial_size_mg": 5.0,
            "status": "in_stock",
            "lot_number": "LOT-2024-001"
        }
    }
    """
    raw_body = await request.body()

    # HMAC verification (skip if webhook secret not configured)
    if settings.AZOTH_WEBHOOK_SECRET:
        if not x_azoth_signature:
            raise HTTPException(status_code=401, detail="Missing signature")
        if not _verify_hmac(raw_body, x_azoth_signature, settings.AZOTH_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_id = payload.get("event_id")
    if not event_id:
        raise HTTPException(status_code=400, detail="Missing event_id")

    # Idempotency check
    # TODO: Replace with Redis SETEX for production
    if event_id in _processed_events:
        return {"status": "already_processed", "event_id": event_id}

    # Parse payload
    data = payload.get("data", {})
    substance = data.get("substance")
    vial_size_mg = data.get("vial_size_mg")
    status_str = data.get("status", "in_stock")

    if not substance or vial_size_mg is None:
        raise HTTPException(status_code=400, detail="Missing substance or vial_size_mg")

    # Map status string to enum
    try:
        inv_status = InventoryStatus(status_str)
    except ValueError:
        inv_status = InventoryStatus.IN_STOCK

    # UPSERT inventory cache
    result = await db.execute(
        select(InventoryCache).where(
            InventoryCache.substance == substance,
            InventoryCache.vial_size_mg == vial_size_mg,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.status = inv_status
        existing.lot_number = data.get("lot_number")
        existing.provider_id = payload.get("provider_id")
        existing.last_webhook_sync = datetime.now(timezone.utc)
    else:
        item = InventoryCache(
            substance=substance,
            vial_size_mg=vial_size_mg,
            status=inv_status,
            lot_number=data.get("lot_number"),
            provider_id=payload.get("provider_id"),
            last_webhook_sync=datetime.now(timezone.utc),
        )
        db.add(item)

    await db.flush()

    # Mark as processed
    _processed_events.add(event_id)

    # Audit
    await log_audit(
        db, None, "WEBHOOK_INVENTORY", "inventory_cache",
        detail=f"{substance} {vial_size_mg}mg → {status_str}",
        ip_address=request.client.host if request.client else None,
    )

    # TODO: Emit WebSocket/SSE event for real-time frontend update
    # await ws_manager.broadcast({"type": "inventory_update", "data": data})

    return {"status": "processed", "event_id": event_id}


@router.get("/inventory")
async def get_inventory(
    db: AsyncSession = Depends(get_db),
):
    """List all cached inventory items (public for calculator UI)."""
    result = await db.execute(
        select(InventoryCache).order_by(InventoryCache.substance)
    )
    items = result.scalars().all()
    return [
        {
            "substance": i.substance,
            "vial_size_mg": i.vial_size_mg,
            "status": i.status.value,
            "lot_number": i.lot_number,
            "last_sync": i.last_webhook_sync.isoformat() if i.last_webhook_sync else None,
        }
        for i in items
    ]
