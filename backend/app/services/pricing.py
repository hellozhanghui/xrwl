from __future__ import annotations

from backend.app.database import connect, rows_to_dicts
from backend.app.repositories.base import insert_row, update_row


def list_rate_configs() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM freight_rate_configs ORDER BY vehicle_type, cargo_type").fetchall()
        return rows_to_dicts(rows)


def save_rate_config(data: dict) -> dict:
    if not data.get("vehicle_type") or not data.get("cargo_type"):
        raise ValueError("vehicle_type and cargo_type are required")
    payload = {
        "vehicle_type": data.get("vehicle_type", "*"),
        "cargo_type": data.get("cargo_type", "*"),
        "base_rate_per_km": float(data.get("base_rate_per_km") or 8),
        "min_fee": float(data.get("min_fee") or 300),
        "return_multiplier": float(data.get("return_multiplier") or 1),
        "toll_multiplier": float(data.get("toll_multiplier") or 1),
        "loading_fee": float(data.get("loading_fee") or 0),
        "enabled": 1 if data.get("enabled", True) else 0,
    }
    if data.get("id"):
        row = update_row("freight_rate_configs", int(data["id"]), payload)
        if not row:
            raise LookupError("rate config not found")
        return row
    return insert_row("freight_rate_configs", payload)


def estimate(data: dict) -> dict:
    one_way_distance = float(data.get("one_way_distance") or data.get("planned_distance") or 0)
    toll_fee = float(data.get("toll_fee") or 0)
    vehicle_type = data.get("vehicle_type") or "*"
    cargo_type = data.get("cargo_type") or "*"
    return_strategy = data.get("return_strategy", "same_route")
    return_distance = calculate_return_distance(one_way_distance, return_strategy, data.get("return_distance"))
    billable_distance = round(one_way_distance + return_distance, 2)
    rate = resolve_rate(vehicle_type, cargo_type)
    freight_fee = max(
        billable_distance * float(rate["base_rate_per_km"]) + toll_fee * float(rate["toll_multiplier"]) + float(rate["loading_fee"]),
        float(rate["min_fee"]),
    )
    return {
        "vehicle_type": vehicle_type,
        "cargo_type": cargo_type,
        "return_strategy": return_strategy,
        "one_way_distance": round(one_way_distance, 2),
        "return_distance": round(return_distance, 2),
        "billable_distance": billable_distance,
        "base_rate_per_km": float(rate["base_rate_per_km"]),
        "toll_fee": round(toll_fee, 2),
        "toll_multiplier": float(rate["toll_multiplier"]),
        "loading_fee": float(rate["loading_fee"]),
        "min_fee": float(rate["min_fee"]),
        "freight_fee": round(freight_fee, 2),
        "formula": "max((单程公里 + 返程公里) * 公里单价 + 过路费 * 过路费系数 + 装卸附加费, 最低收费)",
    }


def calculate_return_distance(one_way_distance: float, strategy: str, explicit_return_distance: object = None) -> float:
    if explicit_return_distance not in (None, ""):
        return float(explicit_return_distance)
    if strategy == "none":
        return 0.0
    if strategy == "highway":
        return one_way_distance * 1.03
    if strategy == "empty_return_discount":
        return one_way_distance * 0.85
    return one_way_distance


def resolve_rate(vehicle_type: str, cargo_type: str) -> dict:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM freight_rate_configs
            WHERE enabled=1 AND vehicle_type=? AND cargo_type=?
            ORDER BY id DESC LIMIT 1
            """,
            (vehicle_type, cargo_type),
        ).fetchone()
        if not row:
            row = conn.execute(
                """
                SELECT * FROM freight_rate_configs
                WHERE enabled=1 AND vehicle_type=? AND cargo_type='*'
                ORDER BY id DESC LIMIT 1
                """,
                (vehicle_type,),
            ).fetchone()
        if not row:
            row = conn.execute(
                """
                SELECT * FROM freight_rate_configs
                WHERE enabled=1 AND vehicle_type='*' AND cargo_type=?
                ORDER BY id DESC LIMIT 1
                """,
                (cargo_type,),
            ).fetchone()
        if not row:
            row = conn.execute(
                "SELECT * FROM freight_rate_configs WHERE enabled=1 AND vehicle_type='*' AND cargo_type='*' ORDER BY id DESC LIMIT 1"
            ).fetchone()
    if not row:
        return {
            "base_rate_per_km": 8,
            "min_fee": 300,
            "return_multiplier": 1,
            "toll_multiplier": 1,
            "loading_fee": 0,
        }
    return dict(row)
