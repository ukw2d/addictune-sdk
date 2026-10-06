from addictune_sdk import cache


def test_set_and_get_etag_roundtrip(tmp_path):
    cache.configure(cache_dir=tmp_path)
    cache.set_etag("/u", '"e1"', {"a": 1}, ttl=60)
    assert cache.get_etag("/u") == ('"e1"', {"a": 1})


def test_missing_server_ttl_falls_back_to_default(tmp_path, mocker):
    cache.configure(cache_dir=tmp_path)
    clock = mocker.patch("addictune_sdk.cache.time.time", return_value=1000.0)
    cache.set_etag("/u", '"e1"', {"a": 1}, ttl=None)
    clock.return_value = 1000.0 + cache.DEFAULT_TTL - 1
    assert cache.get_etag("/u") == ('"e1"', {"a": 1})
    clock.return_value = 1000.0 + cache.DEFAULT_TTL + 1
    assert cache.get_etag("/u") == (None, None)
