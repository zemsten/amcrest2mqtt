from amcrest2mqtt.util import to_gb


def test_to_gb() -> str:
    assert "37.25" == to_gb(40000000000)
