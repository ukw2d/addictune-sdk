"""Models for the User API domain."""

from __future__ import annotations

from pydantic import BaseModel


class Ping(BaseModel):
    api_version: float
    ip: str
    country: str
    country_code: str | None = None
    time: str | None = None

    model_config = {"extra": "ignore"}


class PaymentType(BaseModel):
    id: int
    billable: bool
    key: str | None = None
    label: str | None = None
    name: str | None = None
    indirect_billing: bool = False
    require_address: bool = False

    model_config = {"extra": "ignore"}


class PaymentMethod(BaseModel):
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
    listener_type: str
    territories: list = []
    window_unit: str | None = None
    window_duration: int | None = None
    limit: int | None = None
    skips_remaining: int | None = None
    expires_at: str | None = None

    model_config = {"extra": "ignore"}
