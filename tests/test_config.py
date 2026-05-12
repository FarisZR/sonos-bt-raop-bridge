from pathlib import Path

from sonos_bt_raop_bridge.config import load_config
from sonos_bt_raop_bridge.config import _parse_env_file


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


def test_unreadable_env_file_is_ignored(monkeypatch, tmp_path: Path) -> None:
    protected = tmp_path / "protected.env"
    protected.write_text("HA_URL=http://hidden.example\n", encoding="utf-8")

    original_read_text = Path.read_text

    def fake_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self == protected:
            raise PermissionError("denied")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fake_read_text)

    assert _parse_env_file(protected) == {}
    config = load_config(env={}, dotenv_paths=(protected,))
    assert config.ha_url is None
