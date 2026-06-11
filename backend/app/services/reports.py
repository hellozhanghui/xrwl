from __future__ import annotations

from backend.app.database import connect, rows_to_dicts


def summary() -> dict:
    with connect() as conn:
        vehicle_total = conn.execute("SELECT COUNT(*) AS total FROM vehicles").fetchone()["total"]
        order_total = conn.execute("SELECT COUNT(*) AS total FROM transport_orders").fetchone()["total"]
        active_orders = conn.execute("SELECT COUNT(*) AS total FROM transport_orders WHERE status IN ('assigned','confirmed','in_transit')").fetchone()["total"]
        alert_total = conn.execute("SELECT COUNT(*) AS total FROM alerts WHERE status='open'").fetchone()["total"]
        revenue = conn.execute("SELECT COALESCE(SUM(CASE WHEN actual_fee > 0 THEN actual_fee ELSE estimated_fee END), 0) AS total FROM transport_orders").fetchone()["total"] or 0
    return {
        "vehicles": vehicle_total,
        "orders": order_total,
        "active_orders": active_orders,
        "open_alerts": alert_total,
        "revenue": revenue,
    }


def vehicle_utilization() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT v.id, v.plate_no,
                   COUNT(o.id) AS order_count,
                   SUM(CASE WHEN o.status IN ('assigned','confirmed','in_transit','completed') THEN 1 ELSE 0 END) AS used_count,
                   COALESCE(SUM(o.actual_distance), SUM(o.planned_distance), 0) AS distance
            FROM vehicles v
            LEFT JOIN transport_orders o ON o.vehicle_id = v.id
            GROUP BY v.id
            ORDER BY order_count DESC
            """
        ).fetchall()
    data = rows_to_dicts(rows)
    for item in data:
        item["utilization"] = 0 if item["order_count"] == 0 else round(item["used_count"] / item["order_count"], 2)
    return data


def order_distance() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT order_no, cargo_name, planned_distance, actual_distance,
                   ROUND(COALESCE(actual_distance, 0) - COALESCE(planned_distance, 0), 2) AS distance_delta
            FROM transport_orders
            ORDER BY created_at DESC
            """
        ).fetchall()
        return rows_to_dicts(rows)


def costs() -> dict:
    with connect() as conn:
        tickets = rows_to_dicts(conn.execute("SELECT ticket_type, SUM(amount) AS amount FROM tickets GROUP BY ticket_type").fetchall())
        maintenance = conn.execute("SELECT COALESCE(SUM(cost), 0) AS amount FROM vehicle_maintenance").fetchone()["amount"]
    return {"tickets": tickets, "maintenance": maintenance}


def sensor_alerts() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE alert_type IN ('temperature','humidity') ORDER BY created_at DESC"
        ).fetchall()
        return rows_to_dicts(rows)
