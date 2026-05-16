"""Inspect raw API response for GET /di/channels/11 to check for favorite data."""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from addictune_sdk import Client

EMAIL = "kromerx@gmail.com"
PASSWORD = "ukw2dDIFM"


async def main():
    async with Client() as client:
        auth = await client.login(EMAIL, PASSWORD)
        print(f"Logged in: user_id={auth.user_id}")

        # Use the underlying httpx client to make a raw request
        http = client._http_client
        resp = await http.get("/di/channels/11")
        print(f"\nStatus: {resp.status_code}")
        print(f"Headers: {dict(resp.headers)}\n")

        data = resp.json()
        print("Raw JSON response:")
        print(json.dumps(data, indent=2))

        # Check for any favorite-related keys
        print("\n--- Favorite-related key search ---")
        _search_for_favorite_keys(data)


def _search_for_favorite_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            current = f"{path}.{k}" if path else k
            lower = k.lower()
            if any(word in lower for word in ("fav", "liked", "like", "heart", "bookm")):
                print(f"  FOUND: {current} = {v!r}")
            _search_for_favorite_keys(v, current)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            _search_for_favorite_keys(item, f"{path}[{i}]")


if __name__ == "__main__":
    asyncio.run(main())
