"""User API integration tests against the live AudioAddict API.

Run:
    ADDICTUNE_EMAIL=kromerx@gmail.com ADDICTUNE_PASSWORD=ukw2dDIFM \
      uv run python tests/integration/user.py
"""

import asyncio
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from session import get_session

from addictune_sdk import Client

PAUSE = 1.5

_results: list[tuple[str, bool]] = []


async def _run(name: str, fn, *args) -> bool:
    try:
        await fn(*args)
        print(f"  PASS  {name}")
        _results.append((name, True))
        return True
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        traceback.print_exc()
        _results.append((name, False))
        return False


async def ping(client) -> None:
    result = await client.user.ping()
    assert result.api_version > 0
    assert result.ip
    assert result.country


async def get_payment_method(client, user_id) -> None:
    result = await client.user.get_payment_method(user_id=user_id, network="di")
    assert result.id
    assert result.active is True
    assert result.payment_type is not None
    assert result.payment_type.billable is True
    print(f"    method: {result.description}, type: {result.payment_type.label}")


async def check_premium_status(client) -> None:
    result = await client.user.check_premium_status(network="di")
    assert result.listener_type
    assert result.window_unit
    print(
        f"    listener_type: {result.listener_type}, skips: {result.limit}/{result.window_duration}{result.window_unit}"
    )


async def main() -> None:
    session = await get_session()

    async with Client(
        session_key=session["session_key"],
        listen_key=session["listen_key"],
    ) as client:
        user_id = session["user_id"]

        print("\nUser")
        print("─" * 40)

        tests = [
            ("ping", ping, client),
            ("get_payment_method", get_payment_method, client, user_id),
            ("check_premium_status", check_premium_status, client),
        ]

        for name, fn, *args in tests:
            await _run(name, fn, *args)
            await asyncio.sleep(PAUSE)

    total = len(_results)
    passed = sum(1 for _, ok in _results if ok)
    failed = total - passed
    print("─" * 40)
    print(f"  {passed}/{total} passed" + (f"  ({failed} failed)" if failed else ""))

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
