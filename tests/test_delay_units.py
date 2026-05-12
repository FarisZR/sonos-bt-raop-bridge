from sonos_bt_raop_bridge.bluez import clamp_delay_units, delay_units_to_ms, ms_to_delay_units


def test_ms_to_delay_units_uses_tenth_millisecond_units() -> None:
    assert ms_to_delay_units(1800) == 18000


def test_clamp_delay_units_caps_uint16_range() -> None:
    assert clamp_delay_units(-5) == 0
    assert clamp_delay_units(70000) == 65535


def test_delay_units_to_ms_round_trip() -> None:
    assert delay_units_to_ms(1234) == 123.4
