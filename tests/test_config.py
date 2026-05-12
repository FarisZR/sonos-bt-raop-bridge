from pathlib import Path

from sonos_bt_raop_bridge.config import load_config


def test_env_aliases_are_normalized(tmp_path: Path) -> None:
    env = {
        "HASS_SERVER": "http://ha.local:8123",
        "HASS_TOKEN": "secret",
    }
    config = load_config(env=env, dotenv_paths=(tmp_path / ".env",))
    assert config.ha_url == "http://ha.local:8123"
    assert config.ha_token == "secret"


def test_environment_overrides_dotenv_file(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text("HA_URL=http://file.example\nBRIDGE_BT_ALIAS=FileAlias\n", encoding="utf-8")
    config = load_config(
        env={"HA_URL": "http://env.example"},
        dotenv_paths=(dotenv,),
    )
    assert config.ha_url == "http://env.example"
    assert config.bridge_bt_alias == "FileAlias"


def test_default_friendly_names_are_applied(tmp_path: Path) -> None:
    config = load_config(env={}, dotenv_paths=(tmp_path / ".env",))
    assert "Kitchen" in config.ha_target_friendly_names
    assert "Küche" in config.ha_target_friendly_names
    assert "Kueche" in config.ha_target_friendly_names
