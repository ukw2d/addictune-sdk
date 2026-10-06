from addictune_sdk.models.network import BUILTIN_NETWORKS


def test_builtin_network_display_names():
    assert {n.slug: n.name for n in BUILTIN_NETWORKS} == {
        "di": "DI.FM",
        "radiotunes": "RadioTunes",
        "rockradio": "Rock Radio",
        "jazzradio": "Jazz Radio",
        "classicalradio": "Classical Radio",
        "zenradio": "Zen Radio",
    }
