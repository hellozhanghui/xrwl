from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Iterable

from backend.app.security import hash_password

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "logistics.sqlite"


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL DEFAULT '',
  real_name TEXT NOT NULL,
  phone TEXT DEFAULT '',
  role TEXT NOT NULL CHECK(role IN ('admin','fleet_manager','dispatcher','driver','customer','finance')),
  status TEXT NOT NULL DEFAULT 'active',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT NOT NULL UNIQUE,
  user_id INTEGER NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vehicles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plate_no TEXT NOT NULL UNIQUE,
  vehicle_type TEXT NOT NULL,
  photo_image TEXT DEFAULT '',
  brand_model TEXT DEFAULT '',
  load_capacity REAL NOT NULL DEFAULT 0,
  box_volume REAL NOT NULL DEFAULT 0,
  box_type TEXT NOT NULL DEFAULT 'normal',
  status TEXT NOT NULL DEFAULT 'idle',
  organization TEXT DEFAULT '',
  driver_id INTEGER,
  gps_device_id TEXT DEFAULT '',
  sensor_device_id TEXT DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(driver_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS vehicle_drivers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  phone TEXT DEFAULT '',
  license_no TEXT DEFAULT '',
  qualification_no TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'active',
  is_default INTEGER NOT NULL DEFAULT 0,
  remark TEXT DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vehicle_maintenance (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id INTEGER NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  service_date DATE NOT NULL,
  mileage REAL DEFAULT 0,
  cost REAL DEFAULT 0,
  next_due_date DATE,
  next_due_mileage REAL,
  vendor TEXT DEFAULT '',
  remark TEXT DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vehicle_certificates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id INTEGER NOT NULL,
  cert_type TEXT NOT NULL,
  cert_no TEXT DEFAULT '',
  provider TEXT DEFAULT '',
  start_date DATE,
  end_date DATE,
  amount REAL DEFAULT 0,
  attachment_id INTEGER,
  status TEXT NOT NULL DEFAULT 'normal',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS devices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_no TEXT NOT NULL UNIQUE,
  device_type TEXT NOT NULL,
  protocol TEXT NOT NULL DEFAULT 'http',
  vehicle_id INTEGER,
  status TEXT NOT NULL DEFAULT 'offline',
  firmware TEXT DEFAULT '',
  battery REAL,
  last_seen_at DATETIME,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS device_vendor_adapters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vendor_name TEXT NOT NULL,
  protocol TEXT NOT NULL,
  endpoint TEXT DEFAULT '',
  auth_type TEXT DEFAULT 'none',
  secret TEXT DEFAULT '',
  callback_url TEXT DEFAULT '',
  enabled INTEGER NOT NULL DEFAULT 1,
  remark TEXT DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS gps_points (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id INTEGER NOT NULL,
  order_id INTEGER,
  device_no TEXT NOT NULL,
  lng REAL NOT NULL,
  lat REAL NOT NULL,
  speed REAL DEFAULT 0,
  heading REAL DEFAULT 0,
  odometer REAL DEFAULT 0,
  acc INTEGER DEFAULT 0,
  device_time DATETIME,
  received_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS cargo_sensor_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id INTEGER NOT NULL,
  order_id INTEGER,
  device_no TEXT NOT NULL,
  box_no TEXT DEFAULT '',
  temperature REAL NOT NULL,
  humidity REAL NOT NULL,
  battery REAL,
  signal REAL,
  device_time DATETIME,
  received_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS transport_orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_no TEXT NOT NULL UNIQUE,
  customer_id INTEGER,
  vehicle_id INTEGER,
  driver_id INTEGER,
  cargo_name TEXT NOT NULL,
  cargo_type TEXT NOT NULL DEFAULT 'general',
  cargo_weight REAL NOT NULL DEFAULT 0,
  cargo_volume REAL NOT NULL DEFAULT 0,
  planned_distance REAL DEFAULT 0,
  return_distance REAL DEFAULT 0,
  billable_distance REAL DEFAULT 0,
  actual_distance REAL DEFAULT 0,
  estimated_fee REAL DEFAULT 0,
  actual_fee REAL DEFAULT 0,
  pricing_detail TEXT DEFAULT '',
  order_description TEXT DEFAULT '',
  ticket_exception TEXT DEFAULT '',
  completed_confirmed_by TEXT DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  confirmation_token TEXT DEFAULT '',
  confirmed_by TEXT DEFAULT '',
  confirmed_ip TEXT DEFAULT '',
  confirmed_at DATETIME,
  started_at DATETIME,
  completed_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(customer_id) REFERENCES users(id),
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
  FOREIGN KEY(driver_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_change_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  before_status TEXT DEFAULT '',
  after_status TEXT DEFAULT '',
  changed_by INTEGER,
  changed_by_name TEXT DEFAULT '',
  remark TEXT DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(order_id) REFERENCES transport_orders(id) ON DELETE CASCADE,
  FOREIGN KEY(changed_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_stops (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER NOT NULL,
  stop_type TEXT NOT NULL,
  sequence_no INTEGER NOT NULL,
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  lng REAL,
  lat REAL,
  contact TEXT DEFAULT '',
  phone TEXT DEFAULT '',
  planned_arrival DATETIME,
  actual_arrival DATETIME,
  FOREIGN KEY(order_id) REFERENCES transport_orders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS route_plans (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER,
  provider TEXT NOT NULL DEFAULT 'mock',
  preference TEXT NOT NULL DEFAULT 'fastest',
  planned_distance REAL NOT NULL,
  return_distance REAL NOT NULL DEFAULT 0,
  billable_distance REAL NOT NULL DEFAULT 0,
  planned_duration INTEGER NOT NULL,
  toll_fee REAL NOT NULL DEFAULT 0,
  freight_fee REAL NOT NULL DEFAULT 0,
  polyline TEXT NOT NULL,
  raw_response TEXT DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(order_id) REFERENCES transport_orders(id)
);

CREATE TABLE IF NOT EXISTS freight_rate_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_type TEXT NOT NULL DEFAULT '*',
  cargo_type TEXT NOT NULL DEFAULT '*',
  base_rate_per_km REAL NOT NULL DEFAULT 8,
  min_fee REAL NOT NULL DEFAULT 300,
  return_multiplier REAL NOT NULL DEFAULT 1,
  toll_multiplier REAL NOT NULL DEFAULT 1,
  loading_fee REAL NOT NULL DEFAULT 0,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL DEFAULT '',
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id INTEGER,
  vehicle_id INTEGER,
  ticket_type TEXT NOT NULL,
  amount REAL NOT NULL DEFAULT 0,
  ticket_no TEXT DEFAULT '',
  issued_at DATE,
  attachment_id INTEGER,
  status TEXT NOT NULL DEFAULT 'pending',
  rejection_reason TEXT DEFAULT '',
  reviewed_by INTEGER,
  reviewed_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(order_id) REFERENCES transport_orders(id),
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
);

CREATE TABLE IF NOT EXISTS attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_type TEXT DEFAULT '',
  biz_type TEXT DEFAULT '',
  biz_id INTEGER,
  uploaded_by INTEGER,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(uploaded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS map_configs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  provider TEXT NOT NULL UNIQUE,
  api_key TEXT DEFAULT '',
  secret TEXT DEFAULT '',
  base_url TEXT DEFAULT '',
  route_path TEXT DEFAULT '',
  geocode_path TEXT DEFAULT '',
  reverse_geocode_path TEXT DEFAULT '',
  poi_path TEXT DEFAULT '',
  static_map_path TEXT DEFAULT '',
  enabled INTEGER NOT NULL DEFAULT 0,
  quota_limit INTEGER DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_definitions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  biz_type TEXT NOT NULL,
  steps_json TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workflow_instances (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  definition_code TEXT NOT NULL,
  biz_type TEXT NOT NULL,
  biz_id INTEGER NOT NULL,
  title TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'running',
  current_step TEXT DEFAULT '',
  started_by INTEGER,
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME,
  FOREIGN KEY(started_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS workflow_tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instance_id INTEGER NOT NULL,
  step_code TEXT NOT NULL,
  step_name TEXT NOT NULL,
  assignee_role TEXT DEFAULT '',
  assignee_id INTEGER,
  status TEXT NOT NULL DEFAULT 'pending',
  due_at DATETIME,
  completed_by INTEGER,
  completed_at DATETIME,
  action TEXT DEFAULT '',
  comment TEXT DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
  FOREIGN KEY(assignee_id) REFERENCES users(id),
  FOREIGN KEY(completed_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS workflow_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  instance_id INTEGER NOT NULL,
  task_id INTEGER,
  action TEXT NOT NULL,
  actor_id INTEGER,
  actor_name TEXT DEFAULT '',
  comment TEXT DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(instance_id) REFERENCES workflow_instances(id) ON DELETE CASCADE,
  FOREIGN KEY(task_id) REFERENCES workflow_tasks(id),
  FOREIGN KEY(actor_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS alerts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vehicle_id INTEGER,
  order_id INTEGER,
  alert_type TEXT NOT NULL,
  level TEXT NOT NULL,
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(vehicle_id) REFERENCES vehicles(id),
  FOREIGN KEY(order_id) REFERENCES transport_orders(id)
);

CREATE INDEX IF NOT EXISTS idx_gps_vehicle_time ON gps_points(vehicle_id, received_at);
CREATE INDEX IF NOT EXISTS idx_sensor_vehicle_time ON cargo_sensor_records(vehicle_id, received_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON transport_orders(status);
CREATE INDEX IF NOT EXISTS idx_vehicle_drivers_vehicle ON vehicle_drivers(vehicle_id, status);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON auth_sessions(token);
CREATE INDEX IF NOT EXISTS idx_workflow_biz ON workflow_instances(biz_type, biz_id);
CREATE INDEX IF NOT EXISTS idx_workflow_tasks_status ON workflow_tasks(status, assignee_role, assignee_id);
"""


def init_db(seed: bool = True) -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        migrate_db(conn)
        if seed:
            seed_db(conn)


def migrate_db(conn: sqlite3.Connection) -> None:
    ensure_columns(
        conn,
        "vehicles",
        {
            "photo_image": "TEXT DEFAULT ''",
        },
    )
    ensure_columns(
        conn,
        "transport_orders",
        {
            "return_distance": "REAL DEFAULT 0",
            "billable_distance": "REAL DEFAULT 0",
            "pricing_detail": "TEXT DEFAULT ''",
            "order_description": "TEXT DEFAULT ''",
            "ticket_exception": "TEXT DEFAULT ''",
            "completed_confirmed_by": "TEXT DEFAULT ''",
        },
    )
    ensure_columns(
        conn,
        "route_plans",
        {
            "return_distance": "REAL DEFAULT 0",
            "billable_distance": "REAL DEFAULT 0",
            "freight_fee": "REAL DEFAULT 0",
        },
    )
    ensure_columns(
        conn,
        "tickets",
        {
            "rejection_reason": "TEXT DEFAULT ''",
            "reviewed_by": "INTEGER",
            "reviewed_at": "DATETIME",
        },
    )
    ensure_columns(
        conn,
        "map_configs",
        {
            "route_path": "TEXT DEFAULT ''",
            "geocode_path": "TEXT DEFAULT ''",
            "reverse_geocode_path": "TEXT DEFAULT ''",
            "poi_path": "TEXT DEFAULT ''",
            "static_map_path": "TEXT DEFAULT ''",
        },
    )
    users = conn.execute("SELECT id, username, password_hash FROM users").fetchall()
    defaults = {
        "admin": "admin123",
        "dispatcher": "dispatch123",
        "driver-zhang": "driver123",
        "customer-a": "customer123",
    }
    for user in users:
        if not user["password_hash"] and user["username"] in defaults:
            conn.execute(
                "UPDATE users SET password_hash=? WHERE id=?",
                (hash_password(defaults[user["username"]]), user["id"]),
            )
    ensure_reference_data(conn)
    ensure_vehicle_driver_profiles(conn)
    conn.commit()


def ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for column, definition in columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_reference_data(conn: sqlite3.Connection) -> None:
    ensure_system_settings(conn)
    map_count = conn.execute("SELECT COUNT(*) AS total FROM map_configs").fetchone()["total"]
    if not map_count:
        conn.executemany(
            """
            INSERT INTO map_configs(provider, api_key, secret, base_url, enabled, quota_limit)
            VALUES(?,?,?,?,?,?)
            """,
            [
                ("mock", "", "", "internal://mock-map", 1, 0),
                ("tianditu", "", "", "https://api.tianditu.gov.cn", 1, 10000),
                ("ditu", "", "", "https://open.dituhui.com", 0, 10000),
            ],
        )
    tianditu = conn.execute("SELECT id FROM map_configs WHERE provider='tianditu'").fetchone()
    if not tianditu:
        conn.execute(
            """
            INSERT INTO map_configs(provider, api_key, secret, base_url, route_path, geocode_path,
                                    reverse_geocode_path, poi_path, static_map_path, enabled, quota_limit)
            VALUES('tianditu', '', '', 'https://api.tianditu.gov.cn', '/drive', '/geocoder',
                   '/geocoder', '/v2/search', '/DataServer', 1, 10000)
            """
        )
    conn.execute(
        """
        UPDATE map_configs
        SET enabled = 1,
            base_url = COALESCE(NULLIF(base_url, ''), 'https://api.tianditu.gov.cn'),
            route_path = COALESCE(NULLIF(route_path, ''), '/drive'),
            geocode_path = COALESCE(NULLIF(geocode_path, ''), '/geocoder'),
            reverse_geocode_path = COALESCE(NULLIF(reverse_geocode_path, ''), '/geocoder'),
            poi_path = COALESCE(NULLIF(poi_path, ''), '/v2/search'),
            static_map_path = COALESCE(NULLIF(static_map_path, ''), '/DataServer')
        WHERE provider = 'tianditu'
        """
    )
    conn.execute(
        """
        UPDATE map_configs
        SET enabled = 0,
            base_url = COALESCE(NULLIF(base_url, ''), 'https://open.dituhui.com'),
            route_path = COALESCE(NULLIF(route_path, ''), '/route/driving'),
            geocode_path = COALESCE(NULLIF(geocode_path, ''), '/geocode'),
            reverse_geocode_path = COALESCE(NULLIF(reverse_geocode_path, ''), '/reverse-geocode'),
            poi_path = COALESCE(NULLIF(poi_path, ''), '/poi/search'),
            static_map_path = COALESCE(NULLIF(static_map_path, ''), '/static-map')
        WHERE provider = 'ditu'
        """
    )
    adapter_count = conn.execute("SELECT COUNT(*) AS total FROM device_vendor_adapters").fetchone()["total"]
    if not adapter_count:
        conn.execute(
            """
            INSERT INTO device_vendor_adapters(vendor_name, protocol, endpoint, auth_type, callback_url, enabled, remark)
            VALUES('标准 HTTP 网关', 'http', '/api/device/gps/report', 'token', '/api/device/status', 1, '预留厂商推送入口')
            """
        )
    workflow_count = conn.execute("SELECT COUNT(*) AS total FROM workflow_definitions").fetchone()["total"]
    if not workflow_count:
        conn.executemany(
            """
            INSERT INTO workflow_definitions(code, name, biz_type, steps_json, enabled)
            VALUES(?,?,?,?,1)
            """,
            [
                (
                    "transport_order",
                    "运输订单流程",
                    "order",
                    json.dumps(
                        [
                            *chick_transport_steps(),
                        ],
                        ensure_ascii=False,
                    ),
                ),
                (
                    "ticket_review",
                    "票据审核流程",
                    "ticket",
                    json.dumps(
                        [
                            {"code": "submit", "name": "票据提交", "role": "finance"},
                            {"code": "review", "name": "财务审核", "role": "finance"},
                        ],
                        ensure_ascii=False,
                    ),
                ),
            ],
        )
    rate_count = conn.execute("SELECT COUNT(*) AS total FROM freight_rate_configs").fetchone()["total"]
    if not rate_count:
        conn.executemany(
            """
            INSERT INTO freight_rate_configs(vehicle_type, cargo_type, base_rate_per_km, min_fee,
                                             return_multiplier, toll_multiplier, loading_fee, enabled)
            VALUES(?,?,?,?,?,?,?,1)
            """,
            [
                ("*", "*", 8.0, 300.0, 1.0, 1.0, 0.0),
                ("冷链车", "cold_chain", 11.5, 500.0, 1.0, 1.0, 180.0),
                ("危化车", "dangerous", 16.0, 900.0, 1.0, 1.0, 300.0),
            ],
        )
    ensure_chick_transport_reference_data(conn)
    ensure_existing_workflows(conn)


def ensure_vehicle_driver_profiles(conn: sqlite3.Connection) -> None:
    vehicles = conn.execute(
        """
        SELECT v.id AS vehicle_id, v.driver_id, u.real_name, u.phone
        FROM vehicles v
        LEFT JOIN users u ON u.id = v.driver_id AND u.role='driver'
        WHERE v.driver_id IS NOT NULL
        """
    ).fetchall()
    for vehicle in vehicles:
        profile_exists = conn.execute("SELECT id FROM vehicle_drivers WHERE id=?", (vehicle["driver_id"],)).fetchone()
        if profile_exists:
            continue
        if not vehicle["real_name"]:
            continue
        existing = conn.execute(
            "SELECT id FROM vehicle_drivers WHERE vehicle_id=? AND name=?",
            (vehicle["vehicle_id"], vehicle["real_name"]),
        ).fetchone()
        if existing:
            profile_id = existing["id"]
        else:
            cur = conn.execute(
                """
                INSERT INTO vehicle_drivers(vehicle_id, name, phone, status, is_default, remark)
                VALUES(?,?,?,?,1,?)
                """,
                (vehicle["vehicle_id"], vehicle["real_name"], vehicle["phone"] or "", "active", "由旧司机用户迁移"),
            )
            profile_id = cur.lastrowid
        conn.execute("UPDATE vehicles SET driver_id=? WHERE id=?", (profile_id, vehicle["vehicle_id"]))
        conn.execute(
            "UPDATE transport_orders SET driver_id=? WHERE vehicle_id=? AND driver_id=?",
            (profile_id, vehicle["vehicle_id"], vehicle["driver_id"]),
        )


def ensure_system_settings(conn: sqlite3.Connection) -> None:
    defaults = {
        "default_origin_name": "兴芮孵化基地",
        "default_origin_province": "河北省",
        "default_origin_city": "保定市",
        "default_origin_address": "河北省保定市莲池区仓储路1号",
        "route_highway_priority": "true",
        "seal_image": "",
        "seal_name": "兴芮物流",
    }
    for key, value in defaults.items():
        conn.execute(
            """
            INSERT INTO system_settings(key, value)
            VALUES(?, ?)
            ON CONFLICT(key) DO NOTHING
            """,
            (key, value),
        )


def chick_transport_steps() -> list[dict]:
    return [
        {"code": "confirm", "name": "订单审核与鸡苗批次确认", "role": "dispatcher"},
        {"code": "assign", "name": "恒温车派车与司机确认", "role": "dispatcher"},
        {"code": "start", "name": "装车检查与发车确认", "role": "driver"},
        {"code": "complete", "name": "到达签收与回单归档", "role": "dispatcher"},
    ]


def ensure_chick_transport_reference_data(conn: sqlite3.Connection) -> None:
    steps = json.dumps(chick_transport_steps(), ensure_ascii=False)
    exists = conn.execute("SELECT id FROM workflow_definitions WHERE code='transport_order'").fetchone()
    if exists:
        conn.execute(
            """
            UPDATE workflow_definitions
            SET name='鸡苗运输订单流程', steps_json=?, biz_type='order', enabled=1
            WHERE code='transport_order'
            """,
            (steps,),
        )
    else:
        conn.execute(
            """
            INSERT INTO workflow_definitions(code, name, biz_type, steps_json, enabled)
            VALUES('transport_order', '鸡苗运输订单流程', 'order', ?, 1)
            """,
            (steps,),
        )
    conn.execute(
        """
        UPDATE vehicles
        SET vehicle_type='鸡苗恒温车', box_type='恒温通风'
        WHERE plate_no='冀F12345'
        """
    )
    conn.execute(
        """
        UPDATE vehicles
        SET vehicle_type='雏鸡配送车', box_type='保温通风'
        WHERE plate_no='冀F67890'
        """
    )
    conn.execute(
        """
        UPDATE vehicles
        SET vehicle_type='应急保障车', box_type='普通厢体'
        WHERE plate_no='冀F88888'
        """
    )
    conn.execute("UPDATE vehicles SET vehicle_type='厢式通风车' WHERE vehicle_type='厢货'")
    conn.execute("UPDATE vehicles SET box_type='普通厢体' WHERE box_type='normal'")
    conn.execute("UPDATE vehicles SET box_type='冷藏保温' WHERE box_type='refrigerated'")
    conn.execute("UPDATE vehicles SET box_type='恒温通风' WHERE box_type='constant_temperature'")
    conn.execute(
        """
        UPDATE transport_orders
        SET cargo_name='鸡苗', cargo_type='鸡苗'
        WHERE order_no='XR202606090001'
        """
    )
    rate_exists = conn.execute(
        "SELECT id FROM freight_rate_configs WHERE vehicle_type='鸡苗恒温车' AND cargo_type='鸡苗'"
    ).fetchone()
    if not rate_exists:
        conn.execute(
            """
            INSERT INTO freight_rate_configs(vehicle_type, cargo_type, base_rate_per_km, min_fee,
                                             return_multiplier, toll_multiplier, loading_fee, enabled)
            VALUES('鸡苗恒温车', '鸡苗', 12.0, 600.0, 1.0, 1.0, 220.0, 1)
            """
        )
    maintenance_exists = conn.execute("SELECT id FROM vehicle_maintenance WHERE vehicle_id=1").fetchone()
    if not maintenance_exists:
        conn.execute(
            """
            INSERT INTO vehicle_maintenance(vehicle_id, type, title, service_date, mileage, cost,
                                            next_due_date, next_due_mileage, vendor, remark)
            VALUES(1, '保养', '鸡苗恒温舱风机与温控系统保养', '2026-05-01', 32000, 860,
                   '2026-06-18', 36000, '保定恒温车服务站', '鸡苗运输前重点检查')
            """
        )


def ensure_existing_workflows(conn: sqlite3.Connection) -> None:
    order_steps = chick_transport_steps()
    order_step_by_status = {
        "pending": 0,
        "confirmed": 1,
        "assigned": 2,
        "in_transit": 3,
    }
    for order in conn.execute("SELECT id, order_no, status FROM transport_orders").fetchall():
        exists = conn.execute("SELECT id FROM workflow_instances WHERE biz_type='order' AND biz_id=?", (order["id"],)).fetchone()
        if exists:
            continue
        completed = order["status"] == "completed"
        index = order_step_by_status.get(order["status"], 0)
        current = "" if completed else order_steps[index]["code"]
        cur = conn.execute(
            """
            INSERT INTO workflow_instances(definition_code, biz_type, biz_id, title, status, current_step, completed_at)
            VALUES('transport_order', 'order', ?, ?, ?, ?, CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END)
            """,
            (order["id"], f"运输订单 {order['order_no']}", "completed" if completed else "running", current, 1 if completed else 0),
        )
        if not completed:
            create_seed_task(conn, cur.lastrowid, order_steps[index])
    ticket_steps = [
        {"code": "submit", "name": "票据提交", "role": "finance"},
        {"code": "review", "name": "财务审核", "role": "finance"},
    ]
    for ticket in conn.execute("SELECT id, ticket_no, status FROM tickets").fetchall():
        exists = conn.execute("SELECT id FROM workflow_instances WHERE biz_type='ticket' AND biz_id=?", (ticket["id"],)).fetchone()
        if exists:
            continue
        completed = ticket["status"] in ("approved", "rejected")
        cur = conn.execute(
            """
            INSERT INTO workflow_instances(definition_code, biz_type, biz_id, title, status, current_step, completed_at)
            VALUES('ticket_review', 'ticket', ?, ?, ?, ?, CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END)
            """,
            (ticket["id"], f"票据审核 {ticket['ticket_no'] or ticket['id']}", "completed" if ticket["status"] == "approved" else ("rejected" if ticket["status"] == "rejected" else "running"), "" if completed else "review", 1 if completed else 0),
        )
        if not completed:
            create_seed_task(conn, cur.lastrowid, ticket_steps[1])


def create_seed_task(conn: sqlite3.Connection, instance_id: int, step: dict) -> None:
    conn.execute(
        """
        INSERT INTO workflow_tasks(instance_id, step_code, step_name, assignee_role, assignee_id)
        VALUES(?,?,?,?,NULL)
        """,
        (instance_id, step["code"], step["name"], step["role"]),
    )


def seed_db(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
    if count:
        return

    conn.executemany(
        "INSERT INTO users(username, password_hash, real_name, phone, role) VALUES(?,?,?,?,?)",
        [
            ("admin", hash_password("admin123"), "系统管理员", "13800000000", "admin"),
            ("dispatcher", hash_password("dispatch123"), "调度员", "13800000001", "dispatcher"),
            ("driver-zhang", hash_password("driver123"), "张师傅", "13800000002", "driver"),
            ("customer-a", hash_password("customer123"), "保定客户A", "13800000003", "customer"),
        ],
    )
    driver_id = conn.execute("SELECT id FROM users WHERE username='driver-zhang'").fetchone()["id"]
    conn.executemany(
        """
        INSERT INTO vehicles(plate_no, vehicle_type, brand_model, load_capacity, box_volume, box_type, status,
                             organization, driver_id, gps_device_id, sensor_device_id)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        [
            ("冀F12345", "鸡苗恒温车", "福田欧马可 2023", 8.0, 42.0, "恒温通风", "idle", "一车队", driver_id, "GPS-001", "TH-001"),
            ("冀F67890", "雏鸡配送车", "江淮帅铃 2022", 5.0, 28.0, "保温通风", "idle", "一车队", None, "GPS-002", ""),
            ("冀F88888", "应急保障车", "东风天锦 2021", 15.0, 0.0, "普通厢体", "maintenance", "二车队", None, "GPS-003", ""),
        ],
    )
    driver_profile = conn.execute(
        """
        INSERT INTO vehicle_drivers(vehicle_id, name, phone, license_no, qualification_no, status, is_default, remark)
        VALUES(1, '张师傅', '13800000002', '', '', 'active', 1, '鸡苗恒温车默认司机')
        """
    )
    conn.execute("UPDATE vehicles SET driver_id=? WHERE id=1", (driver_profile.lastrowid,))
    conn.executemany(
        "INSERT INTO devices(device_no, device_type, vehicle_id, status, last_seen_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)",
        [
            ("GPS-001", "gps", 1, "online"),
            ("TH-001", "temperature", 1, "online"),
            ("GPS-002", "gps", 2, "offline"),
            ("GPS-003", "gps", 3, "offline"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO vehicle_certificates(vehicle_id, cert_type, cert_no, provider, start_date, end_date, amount, status)
        VALUES(?,?,?,?,?,?,?,?)
        """,
        [
            (1, "insurance", "BX2026001", "人保财险", "2026-01-01", "2026-12-31", 8200, "normal"),
            (1, "transport_permit", "TP2026001", "交通运输局", "2026-01-01", "2026-07-01", 600, "normal"),
            (2, "inspection", "NJ2026002", "车管所", "2025-07-01", "2026-06-20", 300, "normal"),
        ],
    )
    conn.execute(
        """
        INSERT INTO transport_orders(order_no, customer_id, vehicle_id, driver_id, cargo_name, cargo_type,
                                     cargo_weight, cargo_volume, planned_distance, estimated_fee, status,
                                     confirmation_token)
        VALUES('XR202606090001', 4, 1, ?, '鸡苗', '鸡苗', 3.2, 18.5, 186.4, 4200, 'confirmed', 'demo-token')
        """,
        (driver_profile.lastrowid,),
    )
    order_id = conn.execute("SELECT id FROM transport_orders WHERE order_no='XR202606090001'").fetchone()["id"]
    conn.executemany(
        """
        INSERT INTO order_stops(order_id, stop_type, sequence_no, name, address, lng, lat, contact, phone)
        VALUES(?,?,?,?,?,?,?,?,?)
        """,
        [
            (order_id, "pickup", 1, "保定仓", "河北省保定市莲池区仓储路1号", 115.5001, 38.8571, "王经理", "13810000001"),
            (order_id, "delivery", 2, "石家庄门店", "河北省石家庄市长安区中山东路", 114.5149, 38.0428, "李经理", "13810000002"),
        ],
    )
    conn.executemany(
        """
        INSERT INTO map_configs(provider, api_key, secret, base_url, route_path, geocode_path,
                                reverse_geocode_path, poi_path, static_map_path, enabled, quota_limit)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
        """,
        [
            ("mock", "", "", "internal://mock-map", "", "", "", "", "", 1, 0),
            ("tianditu", "", "", "https://api.tianditu.gov.cn", "/drive", "/geocoder", "/geocoder", "/v2/search", "/DataServer", 1, 10000),
            ("ditu", "", "", "https://open.dituhui.com", "/route/driving", "/geocode", "/reverse-geocode", "/poi/search", "/static-map", 0, 10000),
        ],
    )
    conn.execute(
        """
        INSERT INTO device_vendor_adapters(vendor_name, protocol, endpoint, auth_type, callback_url, enabled, remark)
        VALUES('标准 HTTP 网关', 'http', '/api/device/gps/report', 'token', '/api/device/status', 1, '预留厂商推送入口')
        """
    )
    conn.commit()
