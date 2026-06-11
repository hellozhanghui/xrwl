from __future__ import annotations

from backend.app.database import connect, rows_to_dicts
from backend.app.repositories.base import get_row, insert_row, list_rows, update_row
from backend.app.security import hash_password
from backend.app.services.auth import public_user
from backend.app.services import workflows


def list_users() -> list[dict]:
    return [public_user(row) for row in list_rows("users", "created_at DESC")]


def create_user(data: dict) -> dict:
    if not data.get("username") or not data.get("real_name") or not data.get("role"):
        raise ValueError("username, real_name and role are required")
    payload = {
        "username": data["username"],
        "password_hash": hash_password(data.get("password", "123456")),
        "real_name": data["real_name"],
        "phone": data.get("phone", ""),
        "role": data["role"],
        "status": data.get("status", "active"),
    }
    return public_user(insert_row("users", payload))


def update_user(user_id: int, data: dict) -> dict:
    payload = {key: data.get(key) for key in ("real_name", "phone", "role", "status") if key in data}
    if data.get("password"):
        payload["password_hash"] = hash_password(data["password"])
    row = update_row("users", user_id, payload)
    if not row:
        raise LookupError("user not found")
    return public_user(row)


def list_devices() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT d.*, v.plate_no
            FROM devices d
            LEFT JOIN vehicles v ON v.id = d.vehicle_id
            ORDER BY d.last_seen_at DESC, d.id DESC
            """
        ).fetchall()
        return rows_to_dicts(rows)


def create_device(data: dict) -> dict:
    if not data.get("device_no") or not data.get("device_type"):
        raise ValueError("device_no and device_type are required")
    return insert_row("devices", data)


def update_device(device_id: int, data: dict) -> dict:
    row = update_row("devices", device_id, data)
    if not row:
        raise LookupError("device not found")
    return row


def list_tickets(query: dict | None = None) -> list[dict]:
    query = query or {}
    where = ["o.status='completed'"]
    args: list[object] = []
    if query.get("plate_no"):
        where.append("v.plate_no LIKE ?")
        args.append(f"%{query['plate_no']}%")
    if query.get("driver"):
        where.append("d.name LIKE ?")
        args.append(f"%{query['driver']}%")
    if query.get("ticket_type"):
        where.append("(t.ticket_type=? OR (?='未提交' AND t.id IS NULL))")
        args.extend([query["ticket_type"], query["ticket_type"]])
    if query.get("start"):
        where.append("date(COALESCE(t.issued_at, o.completed_at, o.created_at)) >= date(?)")
        args.append(query["start"])
    if query.get("end"):
        where.append("date(COALESCE(t.issued_at, o.completed_at, o.created_at)) <= date(?)")
        args.append(query["end"])
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT t.id, o.id AS order_id, COALESCE(t.vehicle_id, o.vehicle_id) AS vehicle_id,
                   COALESCE(t.ticket_type, '未提交') AS ticket_type,
                   COALESCE(t.amount, o.estimated_fee, 0) AS amount,
                   COALESCE(t.ticket_no, '') AS ticket_no,
                   COALESCE(t.issued_at, date(o.completed_at), date(o.created_at)) AS issued_at,
                   COALESCE(t.status, 'not_submitted') AS status,
                   COALESCE(t.rejection_reason, '') AS rejection_reason,
                   t.reviewed_at, o.order_no, o.completed_at, o.created_at AS order_created_at,
                   o.billable_distance, o.estimated_fee, o.ticket_exception,
                   v.plate_no, d.name AS driver_name
            FROM transport_orders o
            LEFT JOIN tickets t ON t.order_id = o.id
            LEFT JOIN vehicles v ON v.id = o.vehicle_id
            LEFT JOIN vehicle_drivers d ON d.id = o.driver_id
            WHERE {" AND ".join(where)}
            ORDER BY COALESCE(t.created_at, o.completed_at, o.created_at) DESC
            """,
            args,
        ).fetchall()
        return rows_to_dicts(rows)


def create_ticket(data: dict, user: dict | None = None) -> dict:
    if not data.get("ticket_type"):
        raise ValueError("ticket_type is required")
    if data.get("order_id") and not data.get("vehicle_id"):
        order = get_row("transport_orders", int(data["order_id"]))
        if order:
            data["vehicle_id"] = order.get("vehicle_id")
    ticket = insert_row("tickets", data)
    workflows.start_instance("ticket_review", "ticket", ticket["id"], f"票据审核 {ticket.get('ticket_no') or ticket['id']}", user)
    workflows.advance_by_biz("ticket", ticket["id"], "submit", user, "票据提交")
    return ticket


def approve_ticket(ticket_id: int, status: str, user: dict | None = None, reason: str = "") -> dict:
    if status not in ("approved", "rejected", "pending"):
        raise ValueError("invalid ticket status")
    row = update_row("tickets", ticket_id, {"status": status})
    if not row:
        raise LookupError("ticket not found")
    with connect() as conn:
        conn.execute(
            "UPDATE tickets SET reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP WHERE id=?",
            (user.get("id") if user else None, ticket_id),
        )
        if status == "rejected" and row.get("order_id"):
            reason = reason or "票据审核驳回，异常请核实"
            conn.execute(
                "UPDATE tickets SET rejection_reason=?, reviewed_by=?, reviewed_at=CURRENT_TIMESTAMP WHERE id=?",
                (reason, user.get("id") if user else None, ticket_id),
            )
            conn.execute(
                "UPDATE transport_orders SET status='in_transit', ticket_exception=? WHERE id=?",
                (reason, row["order_id"]),
            )
            conn.execute(
                """
                INSERT INTO order_change_logs(order_id, action, before_status, after_status, changed_by, changed_by_name, remark)
                VALUES(?,?,?,?,?,?,?)
                """,
                (row["order_id"], "ticket_rejected", "completed", "in_transit", user.get("id") if user else None, user.get("real_name", "") if user else "", reason),
            )
        if status == "approved" and row.get("order_id"):
            conn.execute("UPDATE transport_orders SET ticket_exception='' WHERE id=?", (row["order_id"],))
        conn.commit()
    workflows.advance_by_biz("ticket", ticket_id, "reject" if status == "rejected" else "review", user, f"票据状态 {status}")
    return get_row("tickets", ticket_id)


def list_map_configs() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM map_configs
            WHERE provider != 'ditu'
            ORDER BY CASE provider WHEN 'tianditu' THEN 0 WHEN 'mock' THEN 9 ELSE 5 END, id DESC
            """
        ).fetchall()
        return rows_to_dicts(rows)


def save_map_config(data: dict) -> dict:
    if not data.get("provider"):
        raise ValueError("provider is required")
    existing = get_config_by_provider(data["provider"])
    payload = {
        "provider": data["provider"],
        "api_key": data.get("api_key", ""),
        "secret": data.get("secret", ""),
        "base_url": data.get("base_url", ""),
        "route_path": data.get("route_path", ""),
        "geocode_path": data.get("geocode_path", ""),
        "reverse_geocode_path": data.get("reverse_geocode_path", ""),
        "poi_path": data.get("poi_path", ""),
        "static_map_path": data.get("static_map_path", ""),
        "enabled": 1 if data.get("enabled", True) else 0,
        "quota_limit": data.get("quota_limit", 0),
    }
    if existing:
        return update_row("map_configs", existing["id"], payload) or existing
    return insert_row("map_configs", payload)


def get_config_by_provider(provider: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM map_configs WHERE provider=?", (provider,)).fetchone()
        return dict(row) if row else None


def list_vendor_adapters() -> list[dict]:
    return list_rows("device_vendor_adapters", "id DESC")


def save_vendor_adapter(data: dict) -> dict:
    required = ["vendor_name", "protocol"]
    for key in required:
        if not data.get(key):
            raise ValueError(f"{key} is required")
    return insert_row("device_vendor_adapters", data)


def get_system_settings() -> dict:
    with connect() as conn:
        rows = conn.execute("SELECT key, value FROM system_settings ORDER BY key").fetchall()
    settings = {row["key"]: parse_setting_value(row["value"]) for row in rows}
    settings["default_origin"] = {
        "name": settings.get("default_origin_name", ""),
        "province": settings.get("default_origin_province", ""),
        "city": settings.get("default_origin_city", ""),
        "address": settings.get("default_origin_address", ""),
    }
    settings["route_highway_priority"] = bool_value(settings.get("route_highway_priority", True))
    return settings


def save_system_settings(data: dict) -> dict:
    allowed = {
        "default_origin_name",
        "default_origin_province",
        "default_origin_city",
        "default_origin_address",
        "route_highway_priority",
        "seal_image",
        "seal_name",
    }
    with connect() as conn:
        for key in allowed:
            if key not in data:
                continue
            conn.execute(
                """
                INSERT INTO system_settings(key, value, updated_at)
                VALUES(?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
                """,
                (key, serialize_setting_value(data[key])),
            )
        conn.commit()
    return get_system_settings()


def parse_setting_value(value: object) -> object:
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def serialize_setting_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value or "")


def bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("1", "true", "yes", "on", "启用")
