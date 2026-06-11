from __future__ import annotations

import json
import math

from backend.app.database import connect
from backend.app.map_providers import ConfigurableHttpMapProvider, DituMapProvider, MockMapProvider, TiandituMapProvider
from backend.app.repositories.base import get_row
from backend.app.services import admin, orders, pricing


def plan_route(data: dict) -> dict:
    origin = data.get("origin")
    destination = data.get("destination")
    if not origin or not destination:
        raise ValueError("origin and destination are required")
    order_id = data.get("order_id")
    cargo_type = data.get("cargo_type", "鸡苗")
    vehicle_type = data.get("vehicle_type") or "*"
    if order_id:
        order = get_row("transport_orders", int(order_id))
        if order:
            cargo_type = order.get("cargo_type") or cargo_type
            vehicle_type = vehicle_type if vehicle_type != "*" else resolve_order_vehicle_type(order)

    provider = get_provider(data.get("provider"))
    waypoints = data.get("waypoints") or []
    if data.get("optimize_waypoints", True):
        waypoints = optimize_waypoints(origin, destination, waypoints)
    route = provider.plan_driving_route(
        origin=origin,
        destination=destination,
        waypoints=waypoints,
        preference=data.get("preference", "fastest"),
        vehicle_type=vehicle_type,
    )
    route["waypoints_sorted_by"] = "system_nearest_neighbor" if waypoints else ""
    pricing_detail = pricing.estimate(
        {
            "one_way_distance": route["planned_distance"],
            "toll_fee": route.get("toll_fee", 0),
            "vehicle_type": vehicle_type,
            "cargo_type": cargo_type,
            "return_strategy": data.get("return_strategy", "same_route"),
            "return_distance": data.get("return_distance"),
        }
    )
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO route_plans(order_id, provider, preference, planned_distance, planned_duration,
                                    toll_fee, return_distance, billable_distance, freight_fee, polyline, raw_response)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                order_id,
                route["provider"],
                route["preference"],
                route["planned_distance"],
                route["planned_duration"],
                route["toll_fee"],
                pricing_detail["return_distance"],
                pricing_detail["billable_distance"],
                pricing_detail["freight_fee"],
                json.dumps(route["polyline"], ensure_ascii=False),
                json.dumps({"route": route, "pricing": pricing_detail}, ensure_ascii=False),
            ),
        )
        if order_id:
            conn.execute(
                """
                UPDATE transport_orders
                SET planned_distance=?, return_distance=?, billable_distance=?, estimated_fee=?, pricing_detail=?
                WHERE id=?
                """,
                (
                    route["planned_distance"],
                    pricing_detail["return_distance"],
                    pricing_detail["billable_distance"],
                    pricing_detail["freight_fee"],
                    json.dumps(pricing_detail, ensure_ascii=False),
                    order_id,
                ),
            )
            if is_chick_cargo(cargo_type) and route["planned_duration"] > 36 * 60:
                conn.execute(
                    """
                    INSERT INTO alerts(order_id, alert_type, level, title, message)
                    VALUES(?,?,?,?,?)
                    """,
                    (
                        order_id,
                        "duration",
                        "critical",
                        "鸡苗运输时长超限",
                        f"预计运输 {round(route['planned_duration'] / 60, 1)} 小时，超过鸡苗运输最长 36 小时要求",
                    ),
                )
        conn.commit()
    route["id"] = cur.lastrowid
    route["order_id"] = order_id
    route["pricing"] = pricing_detail
    return route


def plan_address_route(data: dict, user: dict | None = None) -> dict:
    provider = get_provider(data.get("provider"))
    settings = admin.get_system_settings()
    origin = geocode_site(settings["default_origin"], provider)
    waypoints = [geocode_site(site, provider) for site in data.get("waypoints", []) if site.get("address")]
    destination_data = data.get("destination") or {}
    destination = geocode_site(destination_data, provider)
    if data.get("optimize_waypoints", True):
        waypoints = optimize_waypoints(origin, destination, waypoints)
    preference = data.get("preference") or ("highway" if settings.get("route_highway_priority") else "fastest")
    vehicle_type = data.get("vehicle_type") or "*"
    cargo_type = data.get("cargo_type", "鸡苗")

    order_id = data.get("order_id")
    if order_id:
        order = get_row("transport_orders", int(order_id))
        if not order:
            raise LookupError("order not found")
        cargo_type = order.get("cargo_type") or cargo_type
        vehicle_type = vehicle_type if vehicle_type != "*" else resolve_order_vehicle_type(order)
        update_order_assignment(int(order_id), data)
    else:
        order = orders.create_order(
            {
                "order_no": data.get("order_no"),
                "customer_id": data.get("customer_id"),
                "vehicle_id": data.get("vehicle_id"),
                "driver_id": data.get("driver_id"),
                "cargo_name": data.get("cargo_name") or "鸡苗",
                "cargo_type": cargo_type,
                "cargo_weight": data.get("cargo_weight", 0),
                "cargo_volume": data.get("cargo_volume", 0),
                "order_description": data.get("order_description", ""),
                "return_strategy": "explicit_return",
            },
            user,
        )
        order_id = order["id"]
        vehicle_type = data.get("vehicle_type") or resolve_order_vehicle_type(order)

    forward_route = provider.plan_driving_route(
        origin=origin,
        destination=destination,
        waypoints=waypoints,
        preference=preference,
        vehicle_type=vehicle_type,
    )
    forward_route["waypoints_sorted_by"] = "system_nearest_neighbor" if waypoints else ""
    return_route = provider.plan_driving_route(
        origin=destination,
        destination=origin,
        waypoints=[],
        preference=preference,
        vehicle_type=vehicle_type,
    )
    pricing_detail = pricing.estimate(
        {
            "one_way_distance": forward_route["planned_distance"],
            "toll_fee": forward_route.get("toll_fee", 0) + return_route.get("toll_fee", 0),
            "vehicle_type": vehicle_type,
            "cargo_type": cargo_type,
            "return_strategy": "explicit_return",
            "return_distance": return_route["planned_distance"],
        }
    )
    stops = [origin] + waypoints + [destination]
    with connect() as conn:
        conn.execute("DELETE FROM order_stops WHERE order_id=?", (order_id,))
        for index, stop in enumerate(stops, start=1):
            stop_type = "origin" if index == 1 else ("destination" if index == len(stops) else "waypoint")
            conn.execute(
                """
                INSERT INTO order_stops(order_id, stop_type, sequence_no, name, address, lng, lat, contact, phone)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    order_id,
                    stop_type,
                    index,
                    stop.get("name") or stop.get("address") or stop_type,
                    full_address(stop),
                    stop.get("lng"),
                    stop.get("lat"),
                    stop.get("contact", ""),
                    stop.get("phone", ""),
                ),
            )
        return_route_id = insert_route_plan(conn, order_id, return_route, pricing_detail, "return_" + preference, {"direction": "return", "route": return_route})
        forward_route_id = insert_route_plan(conn, order_id, forward_route, pricing_detail, preference, {"direction": "forward", "route": forward_route, "return_route_id": return_route_id})
        conn.execute(
            """
            UPDATE transport_orders
            SET vehicle_id=COALESCE(?, vehicle_id), driver_id=COALESCE(?, driver_id),
                cargo_name=COALESCE(?, cargo_name), cargo_type=COALESCE(?, cargo_type),
                cargo_weight=COALESCE(?, cargo_weight), cargo_volume=COALESCE(?, cargo_volume),
                planned_distance=?, return_distance=?, billable_distance=?, estimated_fee=?, pricing_detail=?
            WHERE id=?
            """,
            (
                data.get("vehicle_id"),
                data.get("driver_id"),
                data.get("cargo_name"),
                cargo_type,
                data.get("cargo_weight"),
                data.get("cargo_volume"),
                forward_route["planned_distance"],
                return_route["planned_distance"],
                pricing_detail["billable_distance"],
                pricing_detail["freight_fee"],
                json.dumps(pricing_detail, ensure_ascii=False),
                order_id,
            ),
        )
        if is_chick_cargo(cargo_type) and forward_route["planned_duration"] > 36 * 60:
            conn.execute(
                """
                INSERT INTO alerts(order_id, alert_type, level, title, message)
                VALUES(?,?,?,?,?)
                """,
                (
                    order_id,
                    "duration",
                    "critical",
                    "鸡苗运输时长超限",
                    f"预计运输 {round(forward_route['planned_duration'] / 60, 1)} 小时，超过鸡苗运输最长 36 小时要求",
                ),
            )
        conn.commit()
    forward_route["id"] = forward_route_id
    forward_route["order_id"] = order_id
    forward_route["pricing"] = pricing_detail
    return_route["id"] = return_route_id
    return_route["order_id"] = order_id
    return {
        "order": orders.get_order_detail(int(order_id)),
        "origin": origin,
        "waypoints": waypoints,
        "destination": destination,
        "forward_route": forward_route,
        "return_route": return_route,
        "pricing": pricing_detail,
    }


def geocode_site(site: dict, provider) -> dict:
    province = site.get("province", "")
    city = site.get("city", "")
    address = site.get("address", "")
    name = site.get("name") or address
    if not city or not address:
        raise ValueError("province, city and address are required for route stations")
    query_address = address if province in address or city in address else f"{province}{city}{address}"
    result = provider.geocode(query_address, city)
    if result.get("lng") in (None, "") or result.get("lat") in (None, ""):
        raise ValueError(f"无法解析地址：{province}{city}{address}")
    return {
        "name": name,
        "province": province,
        "city": city,
        "address": address,
        "lng": float(result["lng"]),
        "lat": float(result["lat"]),
        "provider": result.get("provider", ""),
        "fallback": result.get("fallback", False),
    }


def full_address(site: dict) -> str:
    province = site.get("province", "")
    city = site.get("city", "")
    address = site.get("address", "")
    if province and address.startswith(province):
        return address
    if city and address.startswith(city):
        return f"{province}{address}"
    return f"{province}{city}{address}"


def insert_route_plan(conn, order_id: int, route: dict, pricing_detail: dict, preference: str, raw: dict) -> int:
    cur = conn.execute(
        """
        INSERT INTO route_plans(order_id, provider, preference, planned_distance, planned_duration,
                                toll_fee, return_distance, billable_distance, freight_fee, polyline, raw_response)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            order_id,
            route["provider"],
            preference,
            route["planned_distance"],
            route["planned_duration"],
            route.get("toll_fee", 0),
            pricing_detail["return_distance"],
            pricing_detail["billable_distance"],
            pricing_detail["freight_fee"],
            json.dumps(route["polyline"], ensure_ascii=False),
            json.dumps({"route": raw, "pricing": pricing_detail}, ensure_ascii=False),
        ),
    )
    return int(cur.lastrowid)


def update_order_assignment(order_id: int, data: dict) -> None:
    updates = {key: data.get(key) for key in ("vehicle_id", "driver_id") if data.get(key)}
    if not updates:
        return
    keys = list(updates)
    assignments = ", ".join([f"{key}=?" for key in keys])
    with connect() as conn:
        conn.execute(f"UPDATE transport_orders SET {assignments} WHERE id=?", [updates[key] for key in keys] + [order_id])
        conn.commit()


def resolve_order_vehicle_type(order: dict) -> str:
    if not order.get("vehicle_id"):
        return "*"
    vehicle = get_row("vehicles", int(order["vehicle_id"]))
    return vehicle.get("vehicle_type") if vehicle else "*"


def is_chick_cargo(cargo_type: str) -> bool:
    return cargo_type in ("鸡苗", "种蛋", "雏鸡", "鸡苗筐")


def get_provider(provider_name: str | None = None):
    config = get_provider_config(provider_name)
    if not config or config["provider"] == "mock":
        return MockMapProvider()
    if config["provider"] == "tianditu":
        return TiandituMapProvider(config)
    if config["provider"] == "ditu":
        return DituMapProvider(config)
    return ConfigurableHttpMapProvider(config)


def get_provider_config(provider_name: str | None = None) -> dict | None:
    with connect() as conn:
        if provider_name:
            row = conn.execute("SELECT * FROM map_configs WHERE provider=?", (provider_name,)).fetchone()
        else:
            row = conn.execute(
                """
                SELECT * FROM map_configs
                WHERE enabled = 1
                ORDER BY CASE provider WHEN 'tianditu' THEN 0 WHEN 'ditu' THEN 5 WHEN 'mock' THEN 9 ELSE 6 END, id
                LIMIT 1
                """
            ).fetchone()
    return dict(row) if row else None


def search_poi(data: dict) -> dict:
    provider = get_provider(data.get("provider"))
    if not hasattr(provider, "search_poi"):
        raise ValueError("selected map provider does not support poi search")
    keyword = (data.get("keyword") or "").strip()
    city = data.get("city", "")
    limit = int(data.get("limit") or 5)
    if not keyword:
        return {"provider": data.get("provider") or "", "keyword": "", "city": city, "items": []}
    try:
        result = provider.search_poi(keyword, city)
    except Exception:
        result = MockMapProvider().search_poi(keyword, city)
        result["provider"] = getattr(provider, "name", data.get("provider") or "mock")
        result["fallback"] = True
        result["message"] = "天地图查询暂不可用，已显示系统候选"
    if "items" in result:
        result["items"] = result["items"][:limit]
    return result


def optimize_waypoints(origin: dict, destination: dict, waypoints: list[dict]) -> list[dict]:
    remaining = waypoints[:]
    ordered = []
    current = origin
    while remaining:
        best = min(remaining, key=lambda point: distance_km(current, point) + distance_km(point, destination) * 0.15)
        ordered.append(best)
        remaining.remove(best)
        current = best
    return ordered


def distance_km(start: dict, end: dict) -> float:
    radius = 6371.0088
    lng1, lat1 = math.radians(float(start["lng"])), math.radians(float(start["lat"]))
    lng2, lat2 = math.radians(float(end["lng"])), math.radians(float(end["lat"]))
    delta_lng = lng2 - lng1
    delta_lat = lat2 - lat1
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def geocode(data: dict) -> dict:
    provider = get_provider(data.get("provider"))
    if not hasattr(provider, "geocode"):
        raise ValueError("selected map provider does not support geocode")
    return provider.geocode(data.get("address", ""), data.get("city", ""))


def reverse_geocode(data: dict) -> dict:
    provider = get_provider(data.get("provider"))
    if not hasattr(provider, "reverse_geocode"):
        raise ValueError("selected map provider does not support reverse geocode")
    return provider.reverse_geocode(float(data["lng"]), float(data["lat"]))


def get_route(route_id: int) -> dict:
    route = get_row("route_plans", route_id)
    if not route:
        raise LookupError("route not found")
    route["polyline"] = json.loads(route["polyline"])
    return route
