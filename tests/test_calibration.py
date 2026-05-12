from sonos_bt_raop_bridge.calibration import median_offset_ms


def test_median_offset_ms_uses_median_not_mean() -> None:
    assert median_offset_ms([10, 20, 1000]) == 20.0
