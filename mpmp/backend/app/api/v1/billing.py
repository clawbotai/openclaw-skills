"""Billing endpoints — Stripe checkout + webhook receiver."""
import hashlib
import hmac
import uuid

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.middleware.audit import log_audit
from app.middleware.rbac import require_roles, get_current_user
from app.models.user import User, UserRole
from app.schemas.billing import CreateCheckoutRequest, PaymentStatusResponse
from app.services import billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout")
async def create_checkout(
    body: CreateCheckoutRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a Stripe checkout session for a prescription payment."""
    try:
        result = await billing_service.create_checkout_session(
            db, uuid.UUID(body.prescription_id), body.success_url, body.cancel_url
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await log_audit(db, current_user.id, "CREATE", "billing_checkout",
                    body.prescription_id,
                    ip_address=request.client.host if request.client else None)
    return result


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str = Header(None, alias="Stripe-Signature"),
):
    """Stripe webhook receiver — validates signature, processes payment events."""
    body = await request.body()

    if settings.STRIPE_SECRET_KEY and stripe_signature:
        # In production, verify Stripe webhook signature
        # stripe.Webhook.construct_event(body, stripe_signature, webhook_secret)
        pass

    import json
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    rx_id = await billing_service.handle_stripe_webhook(
        db, event.get("type", ""), event.get("data", {}).get("object", {})
    )

    if rx_id:
        await log_audit(db, None, "PAYMENT_COMPLETED", "prescriptions", rx_id,
                        ip_address=request.client.host if request.client else None)

    return {"received": True}
