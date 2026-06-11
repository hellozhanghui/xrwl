from __future__ import annotations

import math


class MockMapProvider:
    name = "mock"

    def search_poi(self, keyword: str, city: str = "") -> dict:
        return {
            "provider": self.name,
            "keyword": keyword,
            "city": city,
            "items": [
                {"name": f"{city or '保定'}{keyword}", "address": f"{city or '保定市'}示例路1号", "lng": 115.5001, "lat": 38.8571},
                {"name": f"{keyword}配送点", "address": f"{city or '保定市'}物流园", "lng": 115.4801, "lat": 38.8739},
            ],
            "fallback": True,
        }

    def geocode(self, address: str, city: str = "") -> dict:
        return {"provider": self.name, "address": address, "city": city, "lng": 115.5001, "lat": 38.8571, "fallback": True}

    def reverse_geocode(self, lng: float, lat: float) -> dict:
        return {"provider": self.name, "lng": lng, "lat": lat, "address": f"模拟地址({lng},{lat})", "fallback": True}

    def plan_driving_route(
        self,
        origin: dict,
        destination: dict,
        waypoints: list[dict] | None = None,
        preference: str = "fastest",
        vehicle_type: str = "truck",
    ) -> dict:
        points = [origin] + (waypoints or []) + [destination]
        distance = self.calculate_distance(points, preference)
        duration = int(max(distance / 55 * 60, 10))
        toll_factor = 0.58 if preference in ("highway", "fastest") else 0.36
        return {
            "provider": self.name,
            "preference": preference,
            "vehicle_type": vehicle_type,
            "planned_distance": round(distance, 2),
            "planned_duration": duration,
            "toll_fee": round(distance * toll_factor, 2),
            "polyline": points,
            "waypoint_count": max(len(points) - 2, 0),
        }

    def calculate_distance(self, points: list[dict], preference: str = "fastest") -> float:
        if len(points) < 2:
            return 0.0
        total = 0.0
        for start, end in zip(points, points[1:]):
            total += haversine_km(float(start["lng"]), float(start["lat"]), float(end["lng"]), float(end["lat"]))
        road_factor = 1.22 if preference == "shortest" else 1.32
        if preference == "highway":
            road_factor = 1.38
        return total * road_factor


def haversine_km(lng1: float, lat1: float, lng2: float, lat2: float) -> float:
    radius = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
