"""Models for the User API domain."""

from __future__ import annotations

from pydantic import BaseModel


class Ping(BaseModel):
    """Response from the ``/ping`` health-check endpoint.

    Attributes:
        api_version: The API version number.
        ip: The caller's IP address as seen by the server.
        country: The caller's country name.
        country_code: ISO country code.
    """

    api_version: float
    ip: str
    country: str
    country_code: str | None = None
    time: str | None = None

    model_config = {"extra": "ignore"}


class PaymentType(BaseModel):
    """A type of payment method (e.g. credit card, PayPal).

    Attributes:
        id: Payment type identifier.
        billable: Whether this type incurs charges.
        key: Machine-readable key.
        label: Short label for display.
        name: Human-readable name.
    """

    id: int
    billable: bool
    key: str | None = None
    label: str | None = None
    name: str | None = None
    indirect_billing: bool = False
    require_address: bool = False

    model_config = {"extra": "ignore"}


class PaymentMethod(BaseModel):
    """The payment method on file for a user.

    Attributes:
        id: Payment method identifier.
        active: Whether the payment method is currently active.
        description: Masked description (e.g. ``"Visa ending in 4242"``).
        first_name: Cardholder first name.
        last_name: Cardholder last name.
        expires_at: Expiration date.
        payment_type: The type of payment method.
    """

    id: int
    active: bool
    description: str | None = None
    country: str | None = None
    archived_at: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    expires_at: str | None = None
    member_id: int | None = None
    payment_type: PaymentType | None = None

    model_config = {"extra": "ignore"}


class PremiumStatus(BaseModel):
    """Premium subscription status including skip-limit info.

    Attributes:
        listener_type: ``"premium"`` or ``"free"``.
        territories: Geographic territories where the subscription applies.
        limit: Maximum number of skips allowed per window.
        skips_remaining: Skips remaining in the current window.
        expires_at: When the premium subscription expires.
    """

    listener_type: str
    territories: list = []
    window_unit: str | None = None
    window_duration: int | None = None
    limit: int | None = None
    skips_remaining: int | None = None
    expires_at: str | None = None

    model_config = {"extra": "ignore"}
