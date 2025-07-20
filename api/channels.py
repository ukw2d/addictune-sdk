from src.api.api_base import APIBase


class ChannelsAPI:
    def __init__(self, api_base: APIBase):
        self.api_base = api_base
    
    async def get_all_channels(self):
        path = self.api_base._build_request_path("/channels")
        response = await self.api_base.api_client.get(path)
        response.raise_for_status()
        return response.json()