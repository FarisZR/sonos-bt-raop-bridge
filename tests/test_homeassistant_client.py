from sonos_bt_raop_bridge.homeassistant import HomeAssistantEntity, select_target_entity


def make_entity(entity_id: str, friendly_name: str) -> HomeAssistantEntity:
    return HomeAssistantEntity(
        entity_id=entity_id,
        state="idle",
        friendly_name=friendly_name,
        attributes={"friendly_name": friendly_name},
    )


def test_select_target_entity_prefers_exact_friendly_name() -> None:
    entities = [
        make_entity("media_player.office", "Office"),
        make_entity("media_player.kitchen", "Kitchen"),
        make_entity("media_player.kitchen_group", "Kitchen Stereo"),
    ]
    selected = select_target_entity(entities, preferred_names=("Kitchen", "Kuche", "Kueche"))
    assert selected is not None
    assert selected.entity_id == "media_player.kitchen"


def test_select_target_entity_honors_override_entity_id() -> None:
    entities = [
        make_entity("media_player.office", "Office"),
        make_entity("media_player.kitchen", "Kitchen"),
    ]
    selected = select_target_entity(entities, override_entity_id="media_player.kitchen")
    assert selected is not None
    assert selected.entity_id == "media_player.kitchen"


def test_select_target_entity_does_not_pick_other_rooms() -> None:
    entities = [make_entity("media_player.office", "Office")]
    selected = select_target_entity(entities, preferred_names=("Kitchen", "Kuche", "Kueche"))
    assert selected is None
