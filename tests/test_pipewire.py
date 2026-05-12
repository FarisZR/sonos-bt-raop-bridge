from sonos_bt_raop_bridge.pipewire import list_sinks, select_target_sink, set_default_sink


def test_list_sinks_filters_audio_sink_nodes() -> None:
    payload = [
        {
            "id": 41,
            "type": "PipeWire:Interface:Node",
            "info": {
                "props": {
                    "node.name": "raop_sink.living_room",
                    "node.description": "Wohnzimmer",
                    "media.class": "Audio/Sink",
                    "sess.media": "raop",
                }
            },
        },
        {
            "id": 42,
            "type": "PipeWire:Interface:Node",
            "info": {
                "props": {
                    "node.name": "bluez_input.phone",
                    "media.class": "Audio/Source",
                    "sess.media": "bluetooth",
                }
            },
        },
    ]

    sinks = list_sinks(payload)

    assert len(sinks) == 1
    assert sinks[0].id == 41
    assert sinks[0].description == "Wohnzimmer"
    assert sinks[0].session_media == "raop"


def test_select_target_sink_prefers_exact_description_match() -> None:
    sinks = list_sinks(
        [
            {
                "id": 57,
                "type": "PipeWire:Interface:Node",
                "info": {
                    "props": {
                        "node.name": "raop_sink.kitchen",
                        "node.description": "Küche",
                        "media.class": "Audio/Sink",
                        "sess.media": "raop",
                    }
                },
            },
            {
                "id": 58,
                "type": "PipeWire:Interface:Node",
                "info": {
                    "props": {
                        "node.name": "raop_sink.kitchen.stereo",
                        "node.description": "Kitchen speakers",
                        "media.class": "Audio/Sink",
                        "sess.media": "raop",
                    }
                },
            },
        ]
    )

    selected = select_target_sink(sinks, "Kitchen|Küche|Kueche")

    assert selected is not None
    assert selected.id == 57


def test_select_target_sink_ignores_non_raop_sinks() -> None:
    sinks = list_sinks(
        [
            {
                "id": 60,
                "type": "PipeWire:Interface:Node",
                "info": {
                    "props": {
                        "node.name": "alsa_output.pci-0000_00_1f.3",
                        "node.description": "Kitchen desk speaker",
                        "media.class": "Audio/Sink",
                        "sess.media": "alsa",
                    }
                },
            }
        ]
    )

    assert select_target_sink(sinks, "Kitchen|Küche|Kueche") is None


def test_set_default_sink_uses_wpctl(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], check: bool) -> None:
        captured["command"] = command
        captured["check"] = check

    monkeypatch.setattr("sonos_bt_raop_bridge.pipewire.subprocess.run", fake_run)

    set_default_sink(56)

    assert captured == {
        "command": ["wpctl", "set-default", "56"],
        "check": True,
    }
