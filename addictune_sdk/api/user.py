import httpx

from ..exceptions import raise_for_status
from ..models.user import PaymentMethod, Ping, PremiumStatus


class UserAPI:
    """User-level endpoints that don't require a network scope.

    Accessed via ``client.user`` (on the root :class:`~addictune_sdk.client.Client`).
    """

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def ping(self) -> Ping:
        """Ping the API and return server info (version, IP, country).

        Useful as a lightweight health check or to detect the caller's
        geographic location.
        """
        response = await self._client.get("/ping")
        await raise_for_status(response)
        return Ping.model_validate(response.json())

    async def get_payment_method(self, user_id: int, network: str) -> PaymentMethod:
        """Return the payment method on file for a user.

        Args:
            user_id: The authenticated user's ID.
            network: Network slug (e.g. ``"di"``).
        """
        url = f"/{network}/members/{user_id}/payment_method"
        response = await self._client.get(url)
        await raise_for_status(response)
        return PaymentMethod.model_validate(response.json())

    async def check_premium_status(self, network: str) -> PremiumStatus:
        """Check the premium (skip-limit) status for a network.

        Args:
            network: Network slug (e.g. ``"di"``).

        Returns:
            :class:`~addictune_sdk.models.user.PremiumStatus` with skip
            limits, remaining skips, and expiration info.
        """
        url = f"/{network}/skip_rulesets/active"
        response = await self._client.get(url)
        await raise_for_status(response)
        return PremiumStatus.model_validate(response.json())
