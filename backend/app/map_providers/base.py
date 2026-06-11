from __future__ import annotations

from typing import Protocol


class MapProvider(Protocol):
    name: str

    def plan_driving_route(
        self,
        origin: dict,
        destination: dict,
        waypoints: list[dict] | None = None,
        preference: str = "fastest",
        vehicle_type: str = "truck",
    ) -> dict:
        ...

    def calculate_distance(self, points: list[dict], preference: str = "fastest") -> float:
        ...
