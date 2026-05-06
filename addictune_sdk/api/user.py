import httpx

from ..exceptions import raise_for_status
from ..models.user import PaymentMethod, Ping, PremiumStatus


class UserAPI:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def ping(self) -> Ping:
        response = await self._client.get("/ping")
        await raise_for_status(response)
        return Ping.model_validate(response.json())

    async def get_payment_method(self, user_id: int, network: str) -> PaymentMethod:
        url = f"/{network}/members/{user_id}/payment_method"
        response = await self._client.get(url)
        await raise_for_status(response)
        return PaymentMethod.model_validate(response.json())

    async def check_premium_status(self, network: str) -> PremiumStatus:
        url = f"/{network}/skip_rulesets/active"
        response = await self._client.get(url)
        await raise_for_status(response)
        return PremiumStatus.model_validate(response.json())
