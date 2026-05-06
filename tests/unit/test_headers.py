import pytest

from addictune_sdk.headers import ResponseHeaders


def test_etag_parsed():
    rh = ResponseHeaders.model_validate(
        {"etag": '"v1"', "cache-control": None, "age": 0}
    )
    assert rh.etag == '"v1"'


def test_ttl_computed_from_max_age():
    rh = ResponseHeaders.model_validate({"cache-control": "max-age=300", "age": "0"})
    assert rh.ttl == 300


def test_ttl_subtracts_age():
    rh = ResponseHeaders.model_validate({"cache-control": "max-age=300", "age": "60"})
    assert rh.ttl == 240


def test_ttl_returns_none_when_expired():
    rh = ResponseHeaders.model_validate({"cache-control": "max-age=60", "age": "120"})
    assert rh.ttl is None


def test_ttl_returns_none_without_cache_control():
    rh = ResponseHeaders.model_validate({"etag": '"abc"'})
    assert rh.ttl is None


def test_ttl_returns_none_for_no_max_age_directive():
    rh = ResponseHeaders.model_validate({"cache-control": "no-cache, no-store"})
    assert rh.ttl is None


def test_ttl_ignores_invalid_max_age_value():
    rh = ResponseHeaders.model_validate({"cache-control": "max-age=notanumber"})
    assert rh.ttl is None


def test_missing_headers_default_gracefully():
    rh = ResponseHeaders.model_validate({})
    assert rh.etag is None
    assert rh.cache_control is None
    assert rh.age == 0
    assert rh.ttl is None
