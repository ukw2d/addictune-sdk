from pydantic import BaseModel


class ChannelArtist(BaseModel):
    id: int
    name: str
    asset_url: str | None = None


class SimilarChannel(BaseModel):
    id: int
    similar_channel_id: int


class Channel(BaseModel):
    id: int
    key: str
    name: str
    description: str | None = None
    description_short: str | None = None
    description_long: str | None = None
    network_id: int
    premium_id: int | None = None
    asset_url: str | None = None
    banner_url: str | None = None
    channel_director: str | None = None
    artists: list[ChannelArtist] = []
    similar_channels: list[SimilarChannel] = []
    channel_filter_ids: list[int] = []

    model_config = {"extra": "ignore"}
