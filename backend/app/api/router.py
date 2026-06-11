from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from backend.app.repositories.base import insert_row, list_rows
from backend.app.services import admin, auth, devices, dispatch, orders, pricing, reports, routes, vehicles, workflows


def dispatch_request(
    method: str,
    raw_path: str,
    body: dict | None,
    client_ip: str = "",
    headers: dict[str, str] | None = None,
) -> tuple[int, object]:
    body = body or {}
    headers = headers or {}
    parsed = urlparse(raw_path)
    path = parsed.path
    query = {key: values[0] for key, values in parse_qs(parsed.query).items()}

    if method == "GET" and path == "/api/health":
        return 200, {"status": "ok"}
    if method == "POST" and path == "/api/auth/login":
        return 200, auth.login(body.get("username", ""), body.get("password", ""))

    user = auth.authenticate(headers, path)
    if method == "GET" and path == "/api/auth/me":
        return 200, user
    if method == "POST" and path == "/api/auth/logout":
        auth.logout(auth.extract_token(headers))
        return 200, {"status": "ok"}

    area = area_for_path(path)
    auth.authorize(user, area)

    if method == "GET" and path == "/api/summary":
        return 200, reports.summary()

    if method == "GET" and path == "/api/users":
        return 200, admin.list_users()
    if method == "POST" and path == "/api/users":
        return 201, admin.create_user(body)
    if method == "PUT" and path.startswith("/api/users/"):
        return 200, admin.update_user(int(path.rsplit("/", 1)[-1]), body)

    if method == "GET" and path == "/api/vehicles":
        return 200, vehicles.list_vehicles()
    if method == "POST" and path == "/api/vehicles":
        return 201, vehicles.create_vehicle(body)
    if method == "GET" and path.startswith("/api/vehicles/"):
        parts = path.strip("/").split("/")
        if len(parts) == 3:
            return 200, vehicles.get_vehicle_detail(int(parts[2]))
        if len(parts) == 4 and parts[3] == "maintenance":
            return 200, vehicles.list_maintenance(int(parts[2]))
        if len(parts) == 4 and parts[3] == "certificates":
            return 200, vehicles.list_certificates(int(parts[2]))
    if method == "PUT" and path.startswith("/api/vehicles/"):
        return 200, vehicles.update_vehicle(int(path.rsplit("/", 1)[-1]), body)
    if method == "POST" and path.startswith("/api/vehicles/") and path.endswith("/maintenance"):
        return 201, vehicles.add_maintenance(int(path.split("/")[3]), body)
    if method == "POST" and path.startswith("/api/vehicles/") and path.endswith("/certificates"):
        return 201, vehicles.add_certificate(int(path.split("/")[3]), body)
    if method == "POST" and path.startswith("/api/vehicles/") and path.endswith("/drivers"):
        return 201, vehicles.add_driver(int(path.split("/")[3]), body)
    if method == "GET" and path == "/api/reminders/certificates":
        return 200, vehicles.certificate_reminders(int(query.get("days", "30")))
    if method == "GET" and path == "/api/reminders/vehicles":
        return 200, vehicles.vehicle_reminders(int(query.get("days", "30")))

    if method == "POST" and path in ("/api/routes/plan", "/api/routes/multi-stop", "/api/routes/return"):
        if path == "/api/routes/return":
            body["preference"] = "highway"
        return 201, routes.plan_route(body)
    if method == "POST" and path == "/api/routes/address-plan":
        return 201, routes.plan_address_route(body, user)
    if method == "GET" and path.startswith("/api/routes/"):
        return 200, routes.get_route(int(path.rsplit("/", 1)[-1]))
    if method == "POST" and path == "/api/maps/search-poi":
        return 200, routes.search_poi(body)
    if method == "POST" and path == "/api/maps/geocode":
        return 200, routes.geocode(body)
    if method == "POST" and path == "/api/maps/reverse-geocode":
        return 200, routes.reverse_geocode(body)

    if method == "POST" and path == "/api/orders":
        return 201, orders.create_order(body, user)
    if method == "GET" and path == "/api/orders":
        return 200, orders.list_orders(query.get("status"))
    if method == "POST" and path.startswith("/api/orders/") and path.endswith("/stops"):
        return 201, orders.add_stop(int(path.split("/")[3]), body)
    if method == "GET" and path.startswith("/api/orders/") and path.endswith("/logs"):
        return 200, orders.list_change_logs(int(path.split("/")[3]))
    if method == "GET" and path.startswith("/api/orders/"):
        return 200, orders.get_order_detail(int(path.rsplit("/", 1)[-1]))
    for action in ("confirm", "assign", "start", "complete"):
        suffix = f"/{action}"
        if method == "POST" and path.startswith("/api/orders/") and path.endswith(suffix):
            order_id = int(path.split("/")[3])
            return 200, orders.transition_order(order_id, action, body, client_ip, user)

    if method == "POST" and path == "/api/device/gps/report":
        return 201, devices.report_gps(body)
    if method == "POST" and path == "/api/device/sensor/report":
        return 201, devices.report_sensor(body)
    if method == "POST" and path == "/api/device/status":
        return 200, devices.update_device_status(body)

    if method == "GET" and path == "/api/tracking/live":
        return 200, devices.live_positions()
    if method == "GET" and path.startswith("/api/tracking/vehicles/") and path.endswith("/history"):
        vehicle_id = int(path.split("/")[4])
        return 200, devices.history(vehicle_id, query.get("start"), query.get("end"))
    if method == "GET" and path.startswith("/api/tracking/orders/"):
        order_id = int(path.split("/")[4])
        if path.endswith("/path"):
            return 200, list_rows("gps_points", "received_at")
        if path.endswith("/distance"):
            detail = orders.get_order_detail(order_id)
            return 200, {"order_id": order_id, "actual_distance": detail.get("actual_distance", 0)}

    if method == "GET" and path == "/api/dispatch/available-vehicles":
        return 200, dispatch.available_vehicles()
    if method == "POST" and path == "/api/dispatch/match-vehicles":
        return 200, dispatch.match_vehicles(body)
    if method == "POST" and path == "/api/dispatch/assign":
        return 200, dispatch.assign(body)

    if method == "GET" and path == "/api/reports/vehicle-utilization":
        return 200, reports.vehicle_utilization()
    if method == "GET" and path == "/api/reports/order-distance":
        return 200, reports.order_distance()
    if method == "GET" and path == "/api/reports/costs":
        return 200, reports.costs()
    if method == "GET" and path == "/api/reports/sensor-alerts":
        return 200, reports.sensor_alerts()
    if method == "GET" and path == "/api/pricing/rates":
        return 200, pricing.list_rate_configs()
    if method == "POST" and path == "/api/pricing/rates":
        return 201, pricing.save_rate_config(body)
    if method == "POST" and path == "/api/pricing/estimate":
        return 200, pricing.estimate(body)

    if method == "GET" and path == "/api/devices":
        return 200, admin.list_devices()
    if method == "POST" and path == "/api/devices":
        return 201, admin.create_device(body)
    if method == "PUT" and path.startswith("/api/devices/"):
        return 200, admin.update_device(int(path.rsplit("/", 1)[-1]), body)

    if method == "POST" and path == "/api/tickets":
        return 201, admin.create_ticket(body, user)
    if method == "GET" and path == "/api/tickets":
        return 200, admin.list_tickets(query)
    if method == "POST" and path.startswith("/api/tickets/") and path.endswith("/review"):
        return 200, admin.approve_ticket(int(path.split("/")[3]), body.get("status", "approved"), user, body.get("reason", ""))

    if method == "GET" and path == "/api/workflows/definitions":
        return 200, workflows.list_definitions()
    if method == "POST" and path.startswith("/api/workflows/definitions/") and path.endswith("/steps"):
        return 200, workflows.save_definition_steps(path.split("/")[4], body.get("steps", []))
    if method == "GET" and path == "/api/workflows/instances":
        return 200, workflows.list_instances(query.get("biz_type"), int(query["biz_id"]) if query.get("biz_id") else None)
    if method == "GET" and path.startswith("/api/workflows/instances/"):
        return 200, workflows.get_instance_detail(int(path.rsplit("/", 1)[-1]))
    if method == "GET" and path == "/api/workflows/tasks":
        return 200, workflows.list_tasks(user, query.get("status", "pending"))
    if method == "POST" and path.startswith("/api/workflows/tasks/") and path.endswith("/complete"):
        return 200, workflows.complete_task(int(path.split("/")[3]), body.get("action", "complete"), user, body.get("comment", ""))

    if method == "GET" and path == "/api/map-configs":
        return 200, admin.list_map_configs()
    if method == "POST" and path == "/api/map-configs":
        return 201, admin.save_map_config(body)
    if method == "GET" and path == "/api/system-settings":
        return 200, admin.get_system_settings()
    if method == "POST" and path == "/api/system-settings":
        return 200, admin.save_system_settings(body)
    if method == "GET" and path == "/api/device-vendor-adapters":
        return 200, admin.list_vendor_adapters()
    if method == "POST" and path == "/api/device-vendor-adapters":
        return 201, admin.save_vendor_adapter(body)

    if method == "GET" and path == "/api/alerts":
        return 200, list_rows("alerts", "created_at DESC")

    return 404, {"error": "not_found", "message": f"{method} {path} is not implemented"}


def area_for_path(path: str) -> str:
    if path.startswith("/api/users") or path.startswith("/api/map-configs") or path.startswith("/api/system-settings") or path.startswith("/api/device-vendor-adapters"):
        return "admin"
    if path.startswith("/api/vehicles") or path.startswith("/api/reminders"):
        return "vehicles"
    if path.startswith("/api/orders"):
        return "orders"
    if path.startswith("/api/routes"):
        return "routes"
    if path.startswith("/api/maps"):
        return "routes"
    if path.startswith("/api/dispatch"):
        return "dispatch"
    if path.startswith("/api/tracking"):
        return "tracking"
    if path.startswith("/api/reports") or path == "/api/summary":
        return "reports"
    if path.startswith("/api/pricing"):
        return "reports"
    if path.startswith("/api/devices"):
        return "devices"
    if path.startswith("/api/tickets"):
        return "tickets"
    if path.startswith("/api/workflows"):
        return "orders"
    if path.startswith("/api/alerts"):
        return "alerts"
    return "admin"
