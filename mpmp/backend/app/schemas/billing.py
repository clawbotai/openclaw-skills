"""Billing & subscription schemas."""
from typing import Optional
from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    prescription_id: str
    success_url: str
    cancel_url: str


class SubscriptionCreate(BaseModel):
    patient_id: str
    price_id: str  # Stripe price ID
    success_url: str
    cancel_url: str


class PaymentStatusResponse(BaseModel):
    prescription_id: str
    status: str  # pending, paid, failed
    stripe_payment_intent_id: Optional[str] = None
    amount_cents: Optional[int] = None
    currency: str = "usd"


class WebhookEvent(BaseModel):
    """Stripe webhook event (partial — full validation done via signature)."""
    id: str
    type: str
