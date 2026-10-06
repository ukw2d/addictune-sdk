# SDK trim → 0.4.0

Beads: epic `addictune-sdk` trim (see `bd list`). Baseline: HEAD `97adbb4`, 3416 production LOC, 177 unit tests passing.

## Evidence

- Only consumer is `addictune-cli` (pins `addictune-sdk>=0.3.1`). Grep of its code shows it uses:
  `Client`, `AddictuneConfig(network=)`, `client.network/listen_key/ensure_session/close/assets`,
  `auth.login(email, password)`, `channels.get_all/get_filter/get_track_history/get_currently_playing/get_routine/get_favorites/add_favorite/remove_favorite/get_stream_url/resolve_stream_url`,
  `tracks.get_by_id/get_liked_track/get_liked_tracks/iter_liked_tracks/vote/skip_track`,
  `playlists.iter_playlists/get_content/iter_followed/add_listen_history`,
  `mixshows.get_by_id/iter_shows/iter_popular/iter_episodes/get_upcoming/iter_followed/follow/unfollow`,
  `search.query`, `assets.get_bytes`. It also imports `AddictuneClient` for type hints and mutates
  `client._session_keys/_credentials/_listen_key` in `handlers/auth.py`.
- Unused by any consumer: `load_config`/JSON config, `api/user.py`, `channels.add_listen_history/get_listen_history/get_favorite`,
  `playlists.get_featured/get_by_id/get_listen_history`, `tracks.get_qualities/get_preferred_quality/set_preferred_quality`,
  `AuthAPI.login(mode="direct")`, `ChannelsAPI(stream_qualities=)`, `CircuitConfig.name`, cache item index.
- `tests/integration/*` are live scripts (need creds, `sys.path` hack), not collected by pytest.

## Scope

1. Internals: `headers.py` via field aliases; `Network.listen_host` without `object.__setattr__`; one ETag helper in `_helpers.py`.
2. Cache: remove `index_list/get_indexed`, `set_default_ttl/resolve_ttl`; TTL fallback is a module constant; drop `AddictuneConfig.default_cache_ttl`.
3. Transport: drop `_send` request rebuild and `CircuitConfig.name`; keep `RetryConfig`/`CircuitConfig` semantics.
4. Public session API (additive): `Client.login(email, password, network=None)`, `Client.set_session(slug, session_key, listen_key=None)`, `Client.has_session(slug)`; `AuthAPI.login` raises `AddictuneAuthError` on 422 (bad credentials).
5. Remove JSON config (`from_json/to_json/to_dict/_from_dict/_default_config_paths/load_config`) and its README sections.
6. Remove `AddictuneClient` alias.
7. Remove unused API methods, their models/fixtures/tests, `login(mode=)`, `stream_qualities` param.
8. Remove `api/user.py`, `models/user.py`, exports, fixtures, tests.
9. Delete `tests/integration/`.
10. README/CONTRIBUTING accuracy; dedupe model re-exports in `__init__.py`.
11. Stream URL helper that uses `Client.listen_key` so callers never inject the key themselves (CLI `_with_listen_key`, `url.replace("listen_key", ...)`).
12. `Network.name` uses display form (`Rock Radio`, `Jazz Radio`, ...) so the CLI drops `STATION_NAMES`.
13. Type `ShowEpisode.tracks`, `PlaylistTracks.tracks/last_tracks`, `MixShow.artists` (breaking for dict readers; fits 0.4.0).
14. Bump 0.4.0, `uv lock`, `uv build`, `uv publish`, tag `v0.4.0`; README gets a one-line versioning policy.

Aligned with `addictune-cli/docs/rewrite/06-sdk.md`: Phase A and Phase B ship together in 0.4.0.

## Non-goals

`hishel` (needs `shared=False` because `/shows` is `private`; no gain over current ETag path), `httpx retries=` replacing the transport (only covers connect errors and drops the breaker), a feature-availability API (CLI probes `AddictuneNotFoundError`), CLI changes (follow-up in CLI repo: switch to `Client`, use new session API, drop `STATION_NAMES`, typed track access, pin `>=0.4,<0.5`).

## Acceptance

- `uv run pytest -q` green after every task; `uv run ruff check` clean if ruff available.
- Every method the CLI calls (list above) still exists with the same signature.
- No module-global mutation from `Client.__init__`.
- Public exports in `addictune_sdk.__all__` match what exists.
- 0.4.0 wheel/sdist built and published.

## Failure / rollback

Each task is one commit; revert per commit. Publishing is irreversible per version — only publish after the epic review `APPROVE`.
