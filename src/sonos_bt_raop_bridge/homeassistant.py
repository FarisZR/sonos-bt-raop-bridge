from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib import error, request
import json


@dataclass(frozen=True)
class HomeAssistantEntity:
    entity_id: str
    state: str
    friendly_name: str | None
    attributes: dict[str, Any]

    @classmethod
    def from_state(cls, payload: dict[str, Any]) -> "HomeAssistantEntity":
        attributes = dict(payload.get("attributes") or {})
        return cls(
            entity_id=payload["entity_id"],
            state=str(payload.get("state", "unknown")),
            friendly_name=attributes.get("friendly_name"),
            attributes=attributes,
        )


class HomeAssistantClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        data = None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers=headers, method=method)
        with request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))

    def api_health(self) -> Any:
        return self._request("GET", "/api/")

    def get_states(self) -> list[HomeAssistantEntity]:
        payload = self._request("GET", "/api/states")
        return [HomeAssistantEntity.from_state(item) for item in payload]

    def call_service(self, domain: str, service: str, service_data: dict[str, Any]) -> Any:
        return self._request("POST", f"/api/services/{domain}/{service}", service_data)


def select_target_entity(
    entities: Iterable[HomeAssistantEntity],
    override_entity_id: str | None = None,
    preferred_names: Iterable[str] = (),
) -> HomeAssistantEntity | None:
    entity_list = [entity for entity in entities if entity.entity_id.startswith("media_player.")]
    if override_entity_id:
        for entity in entity_list:
            if entity.entity_id == override_entity_id:
                return entity
        return None

    preferred = tuple(preferred_names)
    exact_name_matches = []
    fallback_matches = []
    for entity in entity_list:
        name = entity.friendly_name or ""
        if name in preferred:
            exact_name_matches.append(entity)
            continue
        lowered_name = name.casefold()
        lowered_id = entity.entity_id.casefold()
        if any(candidate.casefold() in lowered_name for candidate in preferred):
            fallback_matches.append(entity)
            continue
        if any(candidate.casefold() in lowered_id for candidate in preferred):
            fallback_matches.append(entity)

    if exact_name_matches:
        return sorted(exact_name_matches, key=lambda entity: entity.entity_id)[0]
    if fallback_matches:
        return sorted(fallback_matches, key=lambda entity: entity.entity_id)[0]
    return None
