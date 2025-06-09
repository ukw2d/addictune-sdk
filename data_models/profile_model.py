from pydantic import BaseModel
from typing import List
from pydantic import Field
from pydantic import SecretStr

class FavoriteChannel(BaseModel):
    channel_id: int
    position: int


class Profile(BaseModel):
    id: int
    activated: bool
    active: bool
    banned: bool
    email: str
    first_name: str
    last_name: str
    locale: str = Field(pattern=r"^[a-z]{2}_[A-Z]{2}$")  # e.g., 'en_US', 'de_DE'
    network_favorite_channels: List[FavoriteChannel]
    user_type: str


class SecretProfile(Profile):
    api_key: SecretStr
    listen_key: SecretStr
    timezone: str
    has_set_password: bool