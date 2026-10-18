"""The login payload says whether the account can play premium streams.

Both auth endpoints return the member object -- nested under ``member`` for
``/member_sessions``, top level for ``/members/authenticate`` -- and it carries
``subscriptions``; a free account has none that is active.
"""

import pytest

from addictune_sdk.models.auth import AuthResponse

_ACTIVE = {"status": "active", "expires_on": "2027-08-28"}
_EXPIRED = {"status": "expired", "expires_on": "2020-01-01"}


def _session_payload(member_extra: dict) -> dict:
    return {
        "key": "k",
        "member_id": 1,
        "member": {"id": 1, "listen_key": "lk", **member_extra},
    }


def _authenticate_payload(extra: dict) -> dict:
    return {"id": 1, "api_key": "k", "listen_key": "lk", **extra}


@pytest.mark.parametrize("payload", [_session_payload, _authenticate_payload])
class TestPremium:
    def test_an_active_subscription_is_premium(self, payload) -> None:
        auth = AuthResponse.model_validate(
            payload({"subscriptions": [_EXPIRED, _ACTIVE]})
        )
        assert auth.premium is True

    def test_no_active_subscription_is_free(self, payload) -> None:
        assert (
            AuthResponse.model_validate(payload({"subscriptions": [_EXPIRED]})).premium
            is False
        )
        assert (
            AuthResponse.model_validate(payload({"subscriptions": []})).premium is False
        )

    def test_missing_subscriptions_is_unknown(self, payload) -> None:
        assert AuthResponse.model_validate(payload({})).premium is None
