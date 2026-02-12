"""Billing service — Stripe integration for cash-pay and concierge subscriptions.

Workflow gate: optionally holds Azoth MedicationRequest push until Stripe invoice is PAID.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.prescription import Prescription, PrescriptionStatus


async def create_checkout_session(
    db: AsyncSession,
    prescription_id: uuid.UUID,
    success_url: str,
    cancel_url: str,
) -> dict:
    """Create a Stripe Checkout Session for a prescription payment.

    Returns a dict with session_id and url for frontend redirect.
    In dev mode without Stripe key, returns a mock.
    """
    result = await db.execute(
        select(Prescription).where(Prescription.id == prescription_id)
    )
    rx = result.scalar_one_or_none()
    if not rx:
        raise ValueError("Prescription not found")

    if not settings.STRIPE_SECRET_KEY:
        # Dev mock — simulate successful payment
        rx.status = PrescriptionStatus.PENDING_PAYMENT
        await db.flush()
        return {
            "session_id": f"mock_cs_{prescription_id}",
            "url": success_url + "?mock_payment=true",
            "mode": "mock",
        }

    # Production: Stripe API call
    import stripe
    stripe.api_key = settings.STRIPE_SECRET_KEY

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Rx: {rx.compound}",
                    "description": rx.calculated_dosage_string or rx.compound,
                },
                "unit_amount": 0,  # Set by pricing logic
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "prescription_id": str(prescription_id),
        },
    )

    rx.status = PrescriptionStatus.PENDING_PAYMENT
    await db.flush()

    return {
        "session_id": session.id,
        "url": session.url,
        "mode": "live",
    }


async def handle_stripe_webhook(
    db: AsyncSession,
    event_type: str,
    event_data: dict,
) -> Optional[str]:
    """Process Stripe webhook events. Returns prescription_id if payment completed."""
    if event_type == "checkout.session.completed":
        metadata = event_data.get("metadata", {})
        prescription_id = metadata.get("prescription_id")
        if not prescription_id:
            return None

        result = await db.execute(
            select(Prescription).where(Prescription.id == uuid.UUID(prescription_id))
        )
        rx = result.scalar_one_or_none()
        if rx and rx.status == PrescriptionStatus.PENDING_PAYMENT:
            rx.status = PrescriptionStatus.SIGNED  # Ready for Azoth submission
            await db.flush()
            return prescription_id

    return None


async def check_payment_gate(db: AsyncSession, prescription_id: uuid.UUID) -> bool:
    """Check if a prescription has cleared the payment gate.

    Returns True if payment is not required or has been completed.
    """
    result = await db.execute(
        select(Prescription).where(Prescription.id == prescription_id)
    )
    rx = result.scalar_one_or_none()
    if not rx:
        return False

    # If no Stripe key configured, payment gate is disabled
    if not settings.STRIPE_SECRET_KEY:
        return True

    return rx.status != PrescriptionStatus.PENDING_PAYMENT
