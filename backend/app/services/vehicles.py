from __future__ import annotations

import base64
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

from backend.app.database import connect, rows_to_dicts
from backend.app.repositories.base import get_row, insert_row, list_rows, update_row

UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads" / "vehicles"
PHOTO_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
}

CERT_LABELS = {
    "insurance": "保险",
    "tax": "车船税",
    "license": "行驶证",
    "transport_permit": "道路运输证",
    "inspection": "年检",
}

VEHICLE_FIELDS = {
    "plate_no",
    "vehicle_type",
    "photo_image",
    "brand_model",
    "load_capacity",
    "box_volume",
    "box_type",
    "status",
    "organization",
    "driver_id",
    "gps_device_id",
    "sensor_device_id",
}


def list_vehicles() -> list[dict]:
    vehicles = list_rows("vehicles", "created_at DESC")
    attach_drivers(vehicles)
    return vehicles


def create_vehicle(data: dict) -> dict:
    required = ["plate_no", "vehicle_type"]
    for key in required:
        if not data.get(key):
            raise ValueError(f"{key} is required")
    return insert_row("vehicles", vehicle_payload(data))


def update_vehicle(vehicle_id: int, data: dict) -> dict:
    row = update_row("vehicles", vehicle_id, vehicle_payload(data))
    if not row:
        raise LookupError("vehicle not found")
    return row


def vehicle_payload(data: dict) -> dict:
    payload = {key: value for key, value in data.items() if key in VEHICLE_FIELDS}
    if isinstance(payload.get("photo_image"), str) and payload["photo_image"].startswith("data:image/"):
        payload["photo_image"] = save_vehicle_photo(payload["photo_image"])
    return payload


def save_vehicle_photo(data_url: str) -> str:
    header, _, encoded = data_url.partition(",")
    if not encoded or not header.startswith("data:") or ";base64" not in header:
        raise ValueError("车辆照片格式不正确")
    content_type = header[5:].split(";", 1)[0]
    suffix = PHOTO_TYPES.get(content_type)
    if not suffix:
        raise ValueError("车辆照片只支持 PNG、JPG、WebP 格式")
    try:
        content = base64.b64decode(encoded, validate=True)
    except ValueError as exc:
        raise ValueError("车辆照片内容无法解析") from exc
    if len(content) > 3 * 1024 * 1024:
        raise ValueError("车辆照片不能超过 3MB")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{suffix}"
    target = UPLOAD_DIR / filename
    target.write_bytes(content)
    return f"/uploads/vehicles/{filename}"


def get_vehicle_detail(vehicle_id: int) -> dict:
    vehicle = get_row("vehicles", vehicle_id)
    if not vehicle:
        raise LookupError("vehicle not found")
    with connect() as conn:
        maintenance = rows_to_dicts(conn.execute("SELECT * FROM vehicle_maintenance WHERE vehicle_id=? ORDER BY service_date DESC", (vehicle_id,)).fetchall())
        certificates = rows_to_dicts(conn.execute("SELECT * FROM vehicle_certificates WHERE vehicle_id=? ORDER BY end_date", (vehicle_id,)).fetchall())
        drivers = rows_to_dicts(conn.execute("SELECT * FROM vehicle_drivers WHERE vehicle_id=? ORDER BY is_default DESC, id DESC", (vehicle_id,)).fetchall())
    vehicle["maintenance"] = maintenance
    vehicle["certificates"] = certificates
    vehicle["drivers"] = drivers
    return vehicle


def add_driver(vehicle_id: int, data: dict) -> dict:
    if not get_row("vehicles", vehicle_id):
        raise LookupError("vehicle not found")
    if not data.get("name"):
        raise ValueError("name is required")
    payload = {
        "vehicle_id": vehicle_id,
        "name": data.get("name", ""),
        "phone": data.get("phone", ""),
        "license_no": data.get("license_no", ""),
        "qualification_no": data.get("qualification_no", ""),
        "status": data.get("status", "active"),
        "is_default": 1 if str(data.get("is_default", "0")) in ("1", "true", "on") else 0,
        "remark": data.get("remark", ""),
    }
    with connect() as conn:
        if payload["is_default"]:
            conn.execute("UPDATE vehicle_drivers SET is_default=0 WHERE vehicle_id=?", (vehicle_id,))
        cur = conn.execute(
            """
            INSERT INTO vehicle_drivers(vehicle_id, name, phone, license_no, qualification_no, status, is_default, remark)
            VALUES(?,?,?,?,?,?,?,?)
            """,
            (
                payload["vehicle_id"],
                payload["name"],
                payload["phone"],
                payload["license_no"],
                payload["qualification_no"],
                payload["status"],
                payload["is_default"],
                payload["remark"],
            ),
        )
        driver_id = int(cur.lastrowid)
        if payload["is_default"]:
            conn.execute("UPDATE vehicles SET driver_id=? WHERE id=?", (driver_id, vehicle_id))
        conn.commit()
    return get_driver(driver_id)


def get_driver(driver_id: int) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM vehicle_drivers WHERE id=?", (driver_id,)).fetchone()
    if not row:
        raise LookupError("driver not found")
    return dict(row)


def attach_drivers(vehicles: list[dict]) -> None:
    if not vehicles:
        return
    vehicle_ids = [vehicle["id"] for vehicle in vehicles]
    placeholders = ",".join("?" for _ in vehicle_ids)
    with connect() as conn:
        drivers = rows_to_dicts(
            conn.execute(
                f"SELECT * FROM vehicle_drivers WHERE vehicle_id IN ({placeholders}) ORDER BY is_default DESC, id DESC",
                vehicle_ids,
            ).fetchall()
        )
    grouped: dict[int, list[dict]] = {}
    for driver in drivers:
        grouped.setdefault(driver["vehicle_id"], []).append(driver)
    for vehicle in vehicles:
        vehicle["drivers"] = grouped.get(vehicle["id"], [])
        default_driver = next((driver for driver in vehicle["drivers"] if driver.get("is_default")), None)
        vehicle["default_driver_name"] = (default_driver or {}).get("name", "")


def add_maintenance(vehicle_id: int, data: dict) -> dict:
    if not get_row("vehicles", vehicle_id):
        raise LookupError("vehicle not found")
    payload = {"vehicle_id": vehicle_id, **data}
    return insert_row("vehicle_maintenance", payload)


def list_maintenance(vehicle_id: int) -> list[dict]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM vehicle_maintenance WHERE vehicle_id=? ORDER BY service_date DESC", (vehicle_id,)).fetchall())


def list_certificates(vehicle_id: int) -> list[dict]:
    with connect() as conn:
        return rows_to_dicts(conn.execute("SELECT * FROM vehicle_certificates WHERE vehicle_id=? ORDER BY end_date", (vehicle_id,)).fetchall())


def add_certificate(vehicle_id: int, data: dict) -> dict:
    if not get_row("vehicles", vehicle_id):
        raise LookupError("vehicle not found")
    payload = {"vehicle_id": vehicle_id, **data}
    return insert_row("vehicle_certificates", payload)


def certificate_reminders(days: int = 30) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.*, v.plate_no
            FROM vehicle_certificates c
            JOIN vehicles v ON v.id = c.vehicle_id
            WHERE c.end_date IS NOT NULL
              AND date(c.end_date) <= date('now', ?)
            ORDER BY c.end_date
            """,
            (f"+{days} day",),
        ).fetchall()
    reminders = rows_to_dicts(rows)
    today = date.today()
    for item in reminders:
        end = datetime.strptime(item["end_date"], "%Y-%m-%d").date()
        item["days_left"] = (end - today).days
        item["level"] = "critical" if item["days_left"] < 0 else "warning"
        label = CERT_LABELS.get(item.get("cert_type"), item.get("cert_type", "证照"))
        item["title"] = label
        item["message"] = f"{label} 到期日 {item['end_date']}"
    return reminders


def vehicle_reminders(days: int = 30) -> list[dict]:
    reminders = certificate_reminders(days)
    with connect() as conn:
        maintenance_rows = conn.execute(
            """
            SELECT m.*, v.plate_no
            FROM vehicle_maintenance m
            JOIN vehicles v ON v.id = m.vehicle_id
            WHERE m.next_due_date IS NOT NULL
              AND date(m.next_due_date) <= date('now', ?)
            ORDER BY m.next_due_date
            """,
            (f"+{days} day",),
        ).fetchall()
    today = date.today()
    for row in rows_to_dicts(maintenance_rows):
        due = datetime.strptime(row["next_due_date"], "%Y-%m-%d").date()
        days_left = (due - today).days
        reminders.append(
            {
                "id": row["id"],
                "vehicle_id": row["vehicle_id"],
                "plate_no": row["plate_no"],
                "type": row["type"],
                "title": row["title"],
                "end_date": row["next_due_date"],
                "days_left": days_left,
                "level": "critical" if days_left < 0 else "warning",
                "category": "maintenance",
                "message": f"{row['title']} 到期日 {row['next_due_date']}",
            }
        )
    for item in reminders:
        item.setdefault("category", "certificate")
        item.setdefault("type", item.get("cert_type", "证照"))
        item.setdefault("title", CERT_LABELS.get(item.get("cert_type"), item.get("cert_type", "证照到期")))
        item.setdefault("message", f"{item['title']} 到期日 {item.get('end_date', '-')}")
    return sorted(reminders, key=lambda item: item.get("end_date") or "")
