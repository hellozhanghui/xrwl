from __future__ import annotations

from backend.app.database import connect, rows_to_dicts
from backend.app.services.orders import transition_order


def available_vehicles() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM vehicles WHERE status IN ('idle','available') ORDER BY plate_no").fetchall()
        return rows_to_dicts(rows)


def match_vehicles(data: dict) -> list[dict]:
    weight = float(data.get("cargo_weight", 0))
    volume = float(data.get("cargo_volume", 0))
    cargo_type = data.get("cargo_type", "鸡苗")
    with connect() as conn:
        rows = conn.execute("SELECT * FROM vehicles WHERE status IN ('idle','available')").fetchall()
    matches = []
    for row in rows_to_dicts(rows):
        reasons = []
        score = 100
        if row["load_capacity"] < weight:
            continue
        if row["box_volume"] and row["box_volume"] < volume:
            continue
        if is_chick_cargo(cargo_type) and not supports_chick_transport(row):
            continue
        if cargo_type == "cold_chain" and row["box_type"] not in ("refrigerated", "constant_temperature", "冷藏保温", "恒温通风"):
            continue
        if cargo_type == "dangerous" and "危化" not in row["vehicle_type"]:
            continue
        if row["load_capacity"]:
            utilization = min(weight / row["load_capacity"], 1)
            score -= int(abs(0.82 - utilization) * 30)
            reasons.append(f"载重利用率 {utilization:.0%}")
        if row["box_volume"]:
            volume_rate = min(volume / row["box_volume"], 1)
            score -= int(abs(0.75 - volume_rate) * 20)
            reasons.append(f"容积利用率 {volume_rate:.0%}")
        if is_chick_cargo(cargo_type):
            reasons.append("满足鸡苗恒温通风")
        elif cargo_type == "cold_chain":
            reasons.append("满足冷链温控")
        row["score"] = max(score, 0)
        row["match_reasons"] = reasons
        matches.append(row)
    return sorted(matches, key=lambda item: item["score"], reverse=True)


def is_chick_cargo(cargo_type: str) -> bool:
    return cargo_type in ("鸡苗", "种蛋", "雏鸡", "鸡苗筐")


def supports_chick_transport(vehicle: dict) -> bool:
    vehicle_type = vehicle.get("vehicle_type", "")
    box_type = vehicle.get("box_type", "")
    return (
        any(keyword in vehicle_type for keyword in ("鸡苗", "恒温", "冷链", "保温"))
        or box_type in ("恒温通风", "冷藏保温", "refrigerated", "constant_temperature")
    )


def assign(data: dict) -> dict:
    return transition_order(int(data["order_id"]), "assign", data)
