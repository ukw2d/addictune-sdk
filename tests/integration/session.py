"""Shared session cache for integration scripts.

Login once, cache session_key / listen_key / user_id to
.session_cache.json (chmod 600, 12 h TTL).  Consecutive script runs
reuse the cached credentials without hitting the auth endpoint again.

Usage:
    from session import get_session

    async def main():
        s = await get_session()
        async with AddictuneClient(
            session_key=s["session_key"],
            listen_key=s["listen_key"],
        ) as client:
            client._user_id = s["user_id"]
"""
import json
import os
import time
from pathlib import Path

from pydantic import SecretStr

from addictune import AddictuneClient

_CACHE = Path(__file__).parent / ".session_cache.json"
_TTL = 43200  # 12 hours


def _load_cache() -> dict | None:
    if not _CACHE.exists():
        return None
    try:
        data = json.loads(_CACHE.read_text())
        if time.time() - data.get("ts", 0) < _TTL:
            return data
    except Exception:
        pass
    return None


async def get_session() -> dict:
    """Return {session_key, listen_key, user_id} from cache or fresh login."""
    if cached := _load_cache():
        print(f"  [session] reusing cached session (user_id={cached['user_id']})")
        return cached

    email = os.environ.get("ADDICTUNE_EMAIL", "")
    password = os.environ.get("ADDICTUNE_PASSWORD", "")
    if not email or not password:
        raise RuntimeError(
            "Set ADDICTUNE_EMAIL and ADDICTUNE_PASSWORD to run integration tests"
        )

    print("  [session] logging in...")
    async with AddictuneClient() as c:
        auth = await c.login(email, SecretStr(password))
        session = {
            "session_key": auth.api_key.get_secret_value(),
            "listen_key": auth.listen_key.get_secret_value(),
            "user_id": auth.user_id,
            "ts": time.time(),
        }

    _CACHE.write_text(json.dumps(session))
    _CACHE.chmod(0o600)
    print(f"  [session] logged in as user_id={session['user_id']}")
    return session
