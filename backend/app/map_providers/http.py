from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from backend.app.map_providers.mock import MockMapProvider


class ConfigurableHttpMapProvider:
    def __init__(self, config: dict, timeout: float = 8.0) -> None:
        self.config = config
        self.name = config["provider"]
        self.timeout = timeout
        self.fallback = MockMapProvider()

    def search_poi(self, keyword: str, city: str = "") -> dict:
        payload = self._get(
            self.config.get("poi_path") or "/poi/search",
            {"keyword": keyword, "keywords": keyword, "city": city},
        )
        return {"provider": self.name, "keyword": keyword, "city": city, "raw_response": payload}

    def geocode(self, address: str, city: str = "") -> dict:
        payload = self._get(
            self.config.get("geocode_path") or "/geocode",
            {"address": address, "city": city},
        )
        point = find_first_point(payload) or {}
        return {"provider": self.name, "address": address, "city": city, "lng": point.get("lng"), "lat": point.get("lat"), "raw_response": payload}

    def reverse_geocode(self, lng: float, lat: float) -> dict:
        payload = self._get(
            self.config.get("reverse_geocode_path") or "/reverse-geocode",
            {"lng": lng, "lat": lat, "location": f"{lng},{lat}"},
        )
        return {"provider": self.name, "lng": lng, "lat": lat, "raw_response": payload}

    def plan_driving_route(
        self,
        origin: dict,
        destination: dict,
        waypoints: list[dict] | None = None,
        preference: str = "fastest",
        vehicle_type: str = "truck",
    ) -> dict:
        waypoints = waypoints or []
        params = {
            "origin": point_param(origin),
            "destination": point_param(destination),
            "waypoints": "|".join(point_param(point) for point in waypoints),
            "preference": preference,
            "strategy": preference,
            "vehicle_type": vehicle_type,
        }
        try:
            payload = self._get(self.config.get("route_path") or "/route/driving", params)
            normalized = normalize_route_response(payload, [origin] + waypoints + [destination], preference, vehicle_type, self.name)
            normalized["raw_response"] = payload
            normalized["fallback"] = False
            return normalized
        except Exception as exc:
            fallback = self.fallback.plan_driving_route(origin, destination, waypoints, preference, vehicle_type)
            fallback["provider"] = self.name
            fallback["fallback"] = True
            fallback["raw_response"] = {"error": str(exc), "message": "map api failed; mock route used"}
            return fallback

    def calculate_distance(self, points: list[dict], preference: str = "fastest") -> float:
        route = self.plan_driving_route(points[0], points[-1], points[1:-1], preference)
        return float(route["planned_distance"])

    def render_static_map(self, route: dict) -> dict:
        payload = self._get(
            self.config.get("static_map_path") or "/static-map",
            {"polyline": json.dumps(route.get("polyline", []), ensure_ascii=False)},
        )
        return {"provider": self.name, "raw_response": payload}

    def _get(self, path: str, params: dict[str, Any]) -> dict:
        if not self.config.get("base_url") or self.config.get("base_url", "").startswith("internal://"):
            raise ValueError("map provider base_url is not configured")
        query = {key: value for key, value in params.items() if value not in ("", None)}
        if self.config.get("api_key"):
            query.setdefault("key", self.config["api_key"])
            query.setdefault("api_key", self.config["api_key"])
        if self.config.get("secret"):
            query.setdefault("secret", self.config["secret"])
        url = build_url(self.config["base_url"], path, query)
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"map api http {exc.code}: {raw[:300]}") from exc
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            if raw.lstrip().startswith("<"):
                return xml_to_dict(raw)
            raise RuntimeError(f"map api returned non-json: {raw[:300]}") from exc


class DituMapProvider(ConfigurableHttpMapProvider):
    pass


class TiandituMapProvider(ConfigurableHttpMapProvider):
    def search_poi(self, keyword: str, city: str = "") -> dict:
        search_keyword = f"{city}{keyword}" if city and city not in keyword else keyword
        payload = self._get(
            self.config.get("poi_path") or "/v2/search",
            {
                "postStr": json.dumps(
                    {
                        "keyWord": search_keyword,
                        "queryType": 1,
                        "mapBound": "73.66,3.86,135.05,53.55",
                        "level": 12,
                        "start": 0,
                        "count": 10,
                    },
                    ensure_ascii=False,
                ),
                "type": "query",
            },
        )
        error_code = find_first_value(payload, ("infocode", "errorCode"))
        if error_code and str(error_code) not in ("0", "1000"):
            message = find_first_value(payload, ("message", "msg")) or f"tianditu infocode {error_code}"
            raise RuntimeError(str(message))
        return {"provider": self.name, "keyword": keyword, "city": city, "items": normalize_tianditu_search(payload), "raw_response": payload}

    def geocode(self, address: str, city: str = "") -> dict:
        keyword = f"{city}{address}" if city and city not in address else address
        payload = self._get(
            self.config.get("geocode_path") or "/geocoder",
            {"ds": json.dumps({"keyWord": keyword}, ensure_ascii=False)},
        )
        point = find_first_point(payload) or {}
        return {"provider": self.name, "address": address, "city": city, "lng": point.get("lng"), "lat": point.get("lat"), "raw_response": payload}

    def reverse_geocode(self, lng: float, lat: float) -> dict:
        payload = self._get(
            self.config.get("reverse_geocode_path") or "/geocoder",
            {"postStr": json.dumps({"lon": lng, "lat": lat, "ver": 1}, ensure_ascii=False), "type": "geocode"},
        )
        return {"provider": self.name, "lng": lng, "lat": lat, "address": find_address(payload), "raw_response": payload}

    def plan_driving_route(
        self,
        origin: dict,
        destination: dict,
        waypoints: list[dict] | None = None,
        preference: str = "fastest",
        vehicle_type: str = "truck",
    ) -> dict:
        waypoints = waypoints or []
        post_str = {
            "orig": point_param(origin),
            "dest": point_param(destination),
            "style": tianditu_route_style(preference),
        }
        if waypoints:
            post_str["mid"] = ";".join(point_param(point) for point in waypoints)
        try:
            payload = self._get(
                self.config.get("route_path") or "/drive",
                {"postStr": json.dumps(post_str, ensure_ascii=False), "type": "search"},
            )
            normalized = normalize_route_response(payload, [origin] + waypoints + [destination], preference, vehicle_type, self.name)
            normalized["raw_response"] = {"source": "tianditu", "parsed": True}
            normalized["fallback"] = False
            return normalized
        except Exception as exc:
            fallback = self.fallback.plan_driving_route(origin, destination, waypoints, preference, vehicle_type)
            fallback["provider"] = self.name
            fallback["fallback"] = True
            fallback["raw_response"] = {"error": str(exc), "message": "tianditu api failed; mock route used"}
            return fallback

    def _get(self, path: str, params: dict[str, Any]) -> dict:
        if not self.config.get("api_key"):
            raise ValueError("tianditu tk is not configured")
        params = {**params, "tk": self.config["api_key"]}
        return super()._get(path, params)


def build_url(base_url: str, path: str, query: dict[str, Any]) -> str:
    base = base_url.rstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        url = path
    else:
        url = f"{base}/{path.lstrip('/')}"
    separator = "&" if "?" in url else "?"
    return url + separator + urllib.parse.urlencode(query, doseq=True)


def point_param(point: dict) -> str:
    return f"{point['lng']},{point['lat']}"


def tianditu_route_style(preference: str) -> str:
    return {
        "fastest": "0",
        "highway": "2",
        "shortest": "1",
        "cost": "3",
    }.get(preference, "0")


def normalize_route_response(payload: dict, fallback_points: list[dict], preference: str, vehicle_type: str, provider: str) -> dict:
    distance = find_number(payload, ["distance", "dist", "meters", "total_distance"])
    duration = find_number(payload, ["duration", "time", "seconds", "total_duration"])
    toll = find_number(payload, ["toll_fee", "tolls", "toll", "fee"])
    polyline = find_polyline(payload) or fallback_points
    mock = MockMapProvider().plan_driving_route(fallback_points[0], fallback_points[-1], fallback_points[1:-1], preference, vehicle_type)
    planned_distance = round((distance / 1000 if distance and distance > 1000 else distance) or mock["planned_distance"], 2)
    planned_duration = int((duration / 60 if duration and duration > 1000 else duration) or mock["planned_duration"])
    return {
        "provider": provider,
        "preference": preference,
        "vehicle_type": vehicle_type,
        "planned_distance": planned_distance,
        "planned_duration": planned_duration,
        "toll_fee": round(float(toll or mock["toll_fee"]), 2),
        "polyline": polyline,
        "waypoint_count": max(len(fallback_points) - 2, 0),
    }


def find_number(data: Any, keys: list[str]) -> float | None:
    for key in keys:
        found = find_number_for_key(data, key)
        if found is not None:
            return found
    return None


def find_number_for_key(data: Any, target_key: str) -> float | None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                converted = to_number(value)
                if converted is not None:
                    return converted
            found = find_number_for_key(value, target_key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_number_for_key(item, target_key)
            if found is not None:
                return found
    return None


def find_first_value(data: Any, keys: tuple[str, ...]) -> Any:
    if isinstance(data, dict):
        for key in keys:
            if key in data:
                return data[key]
        for value in data.values():
            found = find_first_value(value, keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_first_value(item, keys)
            if found is not None:
                return found
    return None


def to_number(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        try:
            return float(text)
        except ValueError:
            return None
    if isinstance(value, dict) and "text" in value:
        return to_number(value["text"])
    return None


def find_polyline(data: Any) -> list[dict] | None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key in ("polyline", "points", "path") and isinstance(value, list):
                return normalize_points(value)
            if key == "routelatlon":
                route_text = value.get("text") if isinstance(value, dict) else value
                if isinstance(route_text, str):
                    return normalize_semicolon_points(route_text)
            found = find_polyline(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_polyline(item)
            if found:
                return found
    return None


def normalize_semicolon_points(value: str) -> list[dict]:
    points = []
    for item in value.split(";"):
        if not item or "," not in item:
            continue
        lng, lat = item.split(",", 1)
        try:
            points.append({"lng": float(lng), "lat": float(lat)})
        except ValueError:
            continue
    return points


def normalize_points(points: list[Any]) -> list[dict]:
    normalized = []
    for point in points:
        if isinstance(point, dict) and "lng" in point and "lat" in point:
            normalized.append({"lng": point["lng"], "lat": point["lat"], "name": point.get("name", "")})
        elif isinstance(point, str) and "," in point:
            lng, lat = point.split(",", 1)
            normalized.append({"lng": float(lng), "lat": float(lat)})
    return normalized


def find_first_point(data: Any) -> dict | None:
    if isinstance(data, dict):
        if "lng" in data and "lat" in data:
            return {"lng": data["lng"], "lat": data["lat"]}
        if "lon" in data and "lat" in data:
            return {"lng": data["lon"], "lat": data["lat"]}
        if "lonlat" in data and isinstance(data["lonlat"], str) and "," in data["lonlat"]:
            lng, lat = data["lonlat"].split(",", 1)
            return {"lng": float(lng), "lat": float(lat)}
        if "location" in data and isinstance(data["location"], str) and "," in data["location"]:
            lng, lat = data["location"].split(",", 1)
            return {"lng": float(lng), "lat": float(lat)}
        for value in data.values():
            found = find_first_point(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_first_point(item)
            if found:
                return found
    return None


def find_address(data: Any) -> str:
    if isinstance(data, dict):
        for key in ("formatted_address", "address", "addressComponent"):
            value = data.get(key)
            if isinstance(value, str):
                return value
        for value in data.values():
            found = find_address(value)
            if found:
                return found
    elif isinstance(data, list):
        for item in data:
            found = find_address(item)
            if found:
                return found
    return ""


def normalize_tianditu_search(payload: dict) -> list[dict]:
    items = payload.get("pois") or payload.get("results") or payload.get("result", {}).get("pois") or []
    normalized = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            point = find_first_point(item) or {}
            normalized.append(
                {
                    "name": item.get("name") or item.get("hotPointName") or "",
                    "address": item.get("address") or item.get("addressDetail") or "",
                    "lng": point.get("lng"),
                    "lat": point.get("lat"),
                }
            )
    return normalized


def xml_to_dict(raw: str) -> dict:
    root = ET.fromstring(raw)
    return {root.tag: element_to_dict(root)}


def element_to_dict(element: ET.Element) -> dict:
    data: dict[str, Any] = dict(element.attrib)
    text = (element.text or "").strip()
    if text:
        data["text"] = text
    for child in element:
        child_data = element_to_dict(child)
        existing = data.get(child.tag)
        if existing is None:
            data[child.tag] = child_data
        elif isinstance(existing, list):
            existing.append(child_data)
        else:
            data[child.tag] = [existing, child_data]
    return data
