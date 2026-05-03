import asyncio

from addictune import AddictuneClient
from addictune.config import AddictuneSettings


async def main():
    settings = AddictuneSettings()
    print(f"Network: {settings.network_name} ({settings.network})")

    async with AddictuneClient(settings=settings) as client:
        print("Logging in...")
        auth = await client.login("kromerx@gmail.com", "ukw2dDIFM")
        print("Login successful")

        print("\nFetching channels...")
        channels = await client.channels.get_all()
        print(f"Got {len(channels)} channels")
        for ch in channels[:5]:
            print(f"  - {ch.get('name')}")


if __name__ == "__main__":
    asyncio.run(main())
