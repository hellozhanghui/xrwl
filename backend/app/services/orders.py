from __future__ import annotations

import secrets
import json
import math
from datetime import datetime

from backend.app.database import connect, rows_to_dicts
from backend.app.repositories.base import get_row, insert_row
from backend.app.services import pricing, workflows


def create_order(data: dict, user: dict | None = None) -> dict:
    cargo_name = data.get("cargo_name")
    if not cargo_name:
        raise ValueError("cargo_name is required")
    order_no = data.get("order_no") or "XR" + datetime.now().strftime("%Y%m%d%H%M%S")
    stops = data.pop("stops", [])
    vehicle_id = data.get("vehicle_id")
    if vehicle_id:
        ensure_vehicle_available(int(vehicle_id))
    vehicle_type = data.get("vehicle_type") or resolve_vehicle_type(data.get("vehicle_id"))
    pricing_detail = pricing.estimate(
        {
            "one_way_distance": data.get("planned_distance", 0),
            "toll_fee": data.get("toll_fee", 0),
            "vehicle_type": vehicle_type,
            "cargo_type": data.get("cargo_type", "鸡苗"),
            "return_strategy": data.get("return_strategy", "same_route"),
            "return_distance": data.get("return_distance"),
        }
    )
    payload = {
        "order_no": order_no,
        "customer_id": data.get("customer_id"),
        "vehicle_id": data.get("vehicle_id"),
        "driver_id": data.get("driver_id"),
        "cargo_name": cargo_name,
        "cargo_type": data.get("cargo_type", "鸡苗"),
        "cargo_weight": data.get("cargo_weight", 0),
        "cargo_volume": data.get("cargo_volume", 0),
        "planned_distance": data.get("planned_distance", 0),
        "return_distance": pricing_detail["return_distance"],
        "billable_distance": pricing_detail["billable_distance"],
        "estimated_fee": data.get("estimated_fee") or pricing_detail["freight_fee"],
        "pricing_detail": json.dumps(pricing_detail, ensure_ascii=False),
        "order_description": data.get("order_description", ""),
        "status": "pending",
        "confirmation_token": secrets.token_urlsafe(16),
    }
    order = insert_row("transport_orders", payload)
    with connect() as conn:
        if vehicle_id:
            conn.execute("UPDATE vehicles SET status='assigned' WHERE id=?", (vehicle_id,))
        for index, stop in enumerate(stops, start=1):
            conn.execute(
                """
                INSERT INTO order_stops(order_id, stop_type, sequence_no, name, address, lng, lat, contact, phone)
                VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    order["id"],
                    stop.get("stop_type", "waypoint"),
                    stop.get("sequence_no", index),
                    stop.get("name", ""),
                    stop.get("address", ""),
                    stop.get("lng"),
                    stop.get("lat"),
                    stop.get("contact", ""),
                    stop.get("phone", ""),
                ),
            )
        conn.commit()
    detail = get_order_detail(order["id"])
    workflows.start_instance("transport_order", "order", order["id"], f"运输订单 {order_no}", user)
    return detail


def resolve_vehicle_type(vehicle_id: object) -> str:
    if not vehicle_id:
        return "*"
    vehicle = get_row("vehicles", int(vehicle_id))
    return vehicle.get("vehicle_type") if vehicle else "*"


def list_orders(status: str | None = None) -> list[dict]:
    with connect() as conn:
        if status:
            rows = conn.execute("SELECT * FROM transport_orders WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM transport_orders ORDER BY created_at DESC").fetchall()
        return rows_to_dicts(rows)


def get_order_detail(order_id: int) -> dict:
    order = get_row("transport_orders", order_id)
    if not order:
        raise LookupError("order not found")
    with connect() as conn:
        order["stops"] = rows_to_dicts(conn.execute("SELECT * FROM order_stops WHERE order_id=? ORDER BY sequence_no", (order_id,)).fetchall())
        order["routes"] = rows_to_dicts(
            conn.execute(
                """
                SELECT id, order_id, provider, preference, planned_distance, planned_duration,
                       toll_fee, return_distance, billable_distance, freight_fee, polyline, created_at
                FROM route_plans
                WHERE order_id=?
                ORDER BY id DESC
                """,
                (order_id,),
            ).fetchall()
        )
    for route in order["routes"]:
        route["polyline"] = slim_polyline(route.get("polyline", ""))
    return order


def ensure_vehicle_available(vehicle_id: int) -> None:
    vehicle = get_row("vehicles", vehicle_id)
    if not vehicle:
        raise LookupError("vehicle not found")
    if vehicle.get("status") not in ("idle", "available"):
        raise ValueError(f"车辆 {vehicle.get('plate_no')} 当前状态为 {vehicle.get('status')}，不能创建新订单")


def slim_polyline(value: str, max_points: int = 400) -> str:
    if not value:
        return "[]"
    try:
        points = json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value
    if not isinstance(points, list) or len(points) <= max_points:
        return value
    step = max(1, math.ceil((len(points) - 2) / max(max_points - 2, 1)))
    slimmed = [points[0], *points[1:-1:step], points[-1]]
    return json.dumps(slimmed[:max_points], ensure_ascii=False)


def add_stop(order_id: int, data: dict) -> dict:
    if not get_row("transport_orders", order_id):
        raise LookupError("order not found")
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO order_stops(order_id, stop_type, sequence_no, name, address, lng, lat, contact, phone,
                                    planned_arrival, actual_arrival)
            VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                order_id,
                data.get("stop_type", "waypoint"),
                data.get("sequence_no", 1),
                data.get("name", ""),
                data.get("address", ""),
                data.get("lng"),
                data.get("lat"),
                data.get("contact", ""),
                data.get("phone", ""),
                data.get("planned_arrival"),
                data.get("actual_arrival"),
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM order_stops WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(row)


def list_change_logs(order_id: int) -> list[dict]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM order_change_logs WHERE order_id=? ORDER BY created_at DESC", (order_id,)).fetchall())


def transition_order(order_id: int, action: str, data: dict | None = None, client_ip: str = "", user: dict | None = None) -> dict:
    data = data or {}
    order = get_row("transport_orders", order_id)
    if not order:
        raise LookupError("order not found")
    now = datetime.now().isoformat(timespec="seconds")
    updates: dict[str, object]
    if action == "confirm":
        updates = {"status": "confirmed", "confirmed_at": now, "confirmed_by": data.get("confirmed_by", ""), "confirmed_ip": client_ip}
    elif action == "assign":
        updates = {"vehicle_id": data.get("vehicle_id"), "driver_id": data.get("driver_id"), "status": "assigned"}
    elif action == "start":
        updates = {"status": "in_transit", "started_at": now}
    elif action == "complete":
        if not data.get("completed_confirmed_by"):
            raise ValueError("completed_confirmed_by is required")
        updates = {
            "status": "completed",
            "completed_at": now,
            "completed_confirmed_by": data.get("completed_confirmed_by"),
            "actual_fee": data.get("actual_fee"),
            "actual_distance": data.get("actual_distance"),
            "ticket_exception": "",
        }
    else:
        raise ValueError("unsupported action")
    keys = [key for key, value in updates.items() if value is not None]
    values = [updates[key] for key in keys]
    assignments = ", ".join([f"{key}=?" for key in keys])
    with connect() as conn:
        conn.execute(f"UPDATE transport_orders SET {assignments} WHERE id=?", values + [order_id])
        if action == "assign" and data.get("vehicle_id"):
            conn.execute("UPDATE vehicles SET status='assigned' WHERE id=?", (data["vehicle_id"],))
        if action == "start" and order.get("vehicle_id"):
            conn.execute("UPDATE vehicles SET status='in_transit' WHERE id=?", (order["vehicle_id"],))
        if action == "complete" and order.get("vehicle_id"):
            conn.execute("UPDATE vehicles SET status='idle' WHERE id=?", (order["vehicle_id"],))
        changed = conn.execute("SELECT status FROM transport_orders WHERE id=?", (order_id,)).fetchone()
        conn.execute(
            """
            INSERT INTO order_change_logs(order_id, action, before_status, after_status, changed_by,
                                          changed_by_name, remark)
            VALUES(?,?,?,?,?,?,?)
            """,
            (
                order_id,
                action,
                order.get("status", ""),
                changed["status"] if changed else "",
                user.get("id") if user else None,
                user.get("real_name", "") if user else data.get("confirmed_by", ""),
                data.get("remark", ""),
            ),
        )
        conn.commit()
    workflows.advance_by_biz("order", order_id, action, user, data.get("remark", ""))
    return get_order_detail(order_id)
