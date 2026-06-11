from __future__ import annotations

from backend.app.database import connect, rows_to_dicts


def find_vehicle(vehicle_plate: str | None = None, vehicle_id: int | None = None) -> dict:
    with connect() as conn:
        if vehicle_id:
            row = conn.execute("SELECT * FROM vehicles WHERE id=?", (vehicle_id,)).fetchone()
        else:
            row = conn.execute("SELECT * FROM vehicles WHERE plate_no=?", (vehicle_plate,)).fetchone()
    if not row:
        raise LookupError("vehicle not found")
    return dict(row)


def report_gps(data: dict) -> dict:
    vehicle = find_vehicle(data.get("vehicle_plate"), data.get("vehicle_id"))
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO gps_points(vehicle_id, order_id, device_no, lng, lat, speed, heading, odometer, acc, device_time)
            VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                vehicle["id"],
                data.get("order_id"),
                data["device_no"],
                data["lng"],
                data["lat"],
                data.get("speed", 0),
                data.get("heading", 0),
                data.get("odometer", 0),
                1 if data.get("acc") else 0,
                data.get("device_time"),
            ),
        )
        conn.execute(
            """
            INSERT INTO devices(device_no, device_type, protocol, vehicle_id, status, last_seen_at)
            VALUES(?, 'gps', 'http', ?, 'online', CURRENT_TIMESTAMP)
            ON CONFLICT(device_no) DO UPDATE SET status='online', vehicle_id=excluded.vehicle_id, last_seen_at=CURRENT_TIMESTAMP
            """,
            (data["device_no"], vehicle["id"]),
        )
        if data.get("speed", 0) > 100:
            conn.execute(
                "INSERT INTO alerts(vehicle_id, order_id, alert_type, level, title, message) VALUES(?,?,?,?,?,?)",
                (vehicle["id"], data.get("order_id"), "overspeed", "warning", "车辆超速", f"{vehicle['plate_no']} 当前速度 {data.get('speed')} km/h"),
            )
        conn.commit()
        point = conn.execute("SELECT * FROM gps_points WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(point)


def report_sensor(data: dict) -> dict:
    vehicle = find_vehicle(data.get("vehicle_plate"), data.get("vehicle_id"))
    profile = sensor_profile(data.get("order_id"))
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO cargo_sensor_records(vehicle_id, order_id, device_no, box_no, temperature, humidity,
                                             battery, signal, device_time)
            VALUES(?,?,?,?,?,?,?,?,?)
            """,
            (
                vehicle["id"],
                data.get("order_id"),
                data["device_no"],
                data.get("box_no", ""),
                data["temperature"],
                data["humidity"],
                data.get("battery"),
                data.get("signal"),
                data.get("device_time"),
            ),
        )
        conn.execute(
            """
            INSERT INTO devices(device_no, device_type, protocol, vehicle_id, status, battery, last_seen_at)
            VALUES(?, 'temperature', 'http', ?, 'online', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(device_no) DO UPDATE SET status='online', vehicle_id=excluded.vehicle_id,
                                                battery=excluded.battery, last_seen_at=CURRENT_TIMESTAMP
            """,
            (data["device_no"], vehicle["id"], data.get("battery")),
        )
        temperature = float(data["temperature"])
        humidity = float(data["humidity"])
        if temperature > profile["max_temperature"] or temperature < profile["min_temperature"]:
            conn.execute(
                "INSERT INTO alerts(vehicle_id, order_id, alert_type, level, title, message) VALUES(?,?,?,?,?,?)",
                (
                    vehicle["id"],
                    data.get("order_id"),
                    "temperature",
                    "warning",
                    "鸡苗舱温异常" if profile["cargo_type"] == "鸡苗" else "温度异常",
                    f"{vehicle['plate_no']} 当前温度 {temperature} C，要求 {profile['min_temperature']}-{profile['max_temperature']} C",
                ),
            )
        if humidity > profile["max_humidity"] or humidity < profile["min_humidity"]:
            conn.execute(
                "INSERT INTO alerts(vehicle_id, order_id, alert_type, level, title, message) VALUES(?,?,?,?,?,?)",
                (
                    vehicle["id"],
                    data.get("order_id"),
                    "humidity",
                    "warning",
                    "鸡苗舱湿度异常" if profile["cargo_type"] == "鸡苗" else "湿度异常",
                    f"{vehicle['plate_no']} 当前湿度 {humidity}%，要求 {profile['min_humidity']}-{profile['max_humidity']}%",
                ),
            )
        conn.commit()
        record = conn.execute("SELECT * FROM cargo_sensor_records WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(record)


def sensor_profile(order_id: object | None = None) -> dict:
    cargo_type = "鸡苗"
    if order_id:
        with connect() as conn:
            row = conn.execute("SELECT cargo_type FROM transport_orders WHERE id=?", (order_id,)).fetchone()
        if row:
            cargo_type = row["cargo_type"]
    if cargo_type in ("鸡苗", "种蛋", "雏鸡", "鸡苗筐"):
        return {
            "cargo_type": "鸡苗",
            "min_temperature": 22,
            "max_temperature": 30,
            "min_humidity": 45,
            "max_humidity": 75,
        }
    return {
        "cargo_type": cargo_type,
        "min_temperature": 0,
        "max_temperature": 8,
        "min_humidity": 30,
        "max_humidity": 80,
    }


def update_device_status(data: dict) -> dict:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO devices(device_no, device_type, protocol, status, firmware, battery, last_seen_at)
            VALUES(?, ?, 'http', ?, ?, ?, ?)
            ON CONFLICT(device_no) DO UPDATE SET status=excluded.status, firmware=excluded.firmware,
                                                battery=excluded.battery, last_seen_at=excluded.last_seen_at
            """,
            (data["device_no"], data.get("device_type", "other"), data.get("status", "online"), data.get("firmware", ""), data.get("battery"), data.get("reported_at")),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM devices WHERE device_no=?", (data["device_no"],)).fetchone()
        return dict(row)


def live_positions() -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT v.id AS vehicle_id, v.plate_no, v.status, p.lng, p.lat, p.speed, p.heading,
                   p.odometer, p.received_at, p.device_time
            FROM vehicles v
            LEFT JOIN gps_points p ON p.id = (
              SELECT id FROM gps_points WHERE vehicle_id = v.id ORDER BY received_at DESC LIMIT 1
            )
            ORDER BY v.plate_no
            """
        ).fetchall()
        return rows_to_dicts(rows)


def history(vehicle_id: int, start: str | None = None, end: str | None = None) -> list[dict]:
    sql = "SELECT * FROM gps_points WHERE vehicle_id=?"
    args: list[object] = [vehicle_id]
    if start:
        sql += " AND received_at >= ?"
        args.append(start)
    if end:
        sql += " AND received_at <= ?"
        args.append(end)
    sql += " ORDER BY received_at"
    with connect() as conn:
        return rows_to_dicts(conn.execute(sql, args).fetchall())
