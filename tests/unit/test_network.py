import pytest
from pydantic import ValidationError

from addictune_sdk.models.network import BUILTIN_NETWORKS, Network


def test_builtin_network_display_names():
    assert {n.slug: n.name for n in BUILTIN_NETWORKS} == {
        "di": "DI.FM",
        "radiotunes": "RadioTunes",
        "rockradio": "Rock Radio",
        "jazzradio": "Jazz Radio",
        "classicalradio": "Classical Radio",
        "zenradio": "Zen Radio",
    }


def test_missing_listen_domain_is_a_validation_error():
    with pytest.raises(ValidationError):
        Network(slug="x", name="X")
