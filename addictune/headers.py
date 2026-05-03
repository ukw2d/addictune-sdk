from pydantic import BaseModel, model_validator


class ResponseHeaders(BaseModel):
    etag: str | None = None
    cache_control: str | None = None
    age: int = 0

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data):
        if hasattr(data, "get"):
            return {
                "etag": data.get("etag"),
                "cache_control": data.get("cache-control"),
                "age": data.get("age", 0),
            }
        return data

    @property
    def ttl(self) -> int | None:
        if not self.cache_control:
            return None
        for part in self.cache_control.split(","):
            part = part.strip()
            if part.startswith("max-age="):
                try:
                    remaining = int(part[len("max-age=") :]) - self.age
                    return remaining if remaining > 0 else None
                except ValueError:
                    pass
        return None
