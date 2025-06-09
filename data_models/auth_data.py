from pydantic import BaseModel, SecretStr, field_serializer

class AuthData(BaseModel):
    username: str
    password: SecretStr

    @field_serializer('password')
    def serialize_password(self, password: SecretStr):
        return password.get_secret_value()