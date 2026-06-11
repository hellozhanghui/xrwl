from __future__ import annotations

from typing import Any

from backend.app.database import connect, rows_to_dicts


def list_rows(table: str, order_by: str = "id DESC") -> list[dict]:
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM {table} ORDER BY {order_by}").fetchall()
        return rows_to_dicts(rows)


def get_row(table: str, row_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (row_id,)).fetchone()
        return dict(row) if row else None


def insert_row(table: str, data: dict[str, Any]) -> dict:
    keys = [key for key, value in data.items() if value is not None]
    values = [data[key] for key in keys]
    placeholders = ", ".join(["?"] * len(keys))
    columns = ", ".join(keys)
    with connect() as conn:
        cur = conn.execute(f"INSERT INTO {table}({columns}) VALUES({placeholders})", values)
        conn.commit()
        return get_row(table, cur.lastrowid) or {}


def update_row(table: str, row_id: int, data: dict[str, Any]) -> dict | None:
    keys = [key for key, value in data.items() if value is not None]
    if not keys:
        return get_row(table, row_id)
    assignments = ", ".join([f"{key} = ?" for key in keys])
    values = [data[key] for key in keys] + [row_id]
    with connect() as conn:
        conn.execute(f"UPDATE {table} SET {assignments} WHERE id = ?", values)
        conn.commit()
        return get_row(table, row_id)
