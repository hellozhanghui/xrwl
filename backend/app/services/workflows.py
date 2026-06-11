from __future__ import annotations

import json
from datetime import datetime

from backend.app.database import connect, rows_to_dicts


def list_definitions() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM workflow_definitions ORDER BY id").fetchall()
    definitions = rows_to_dicts(rows)
    for item in definitions:
        item["steps"] = json.loads(item.pop("steps_json"))
    return definitions


def save_definition_steps(code: str, steps: list[dict]) -> dict:
    if not steps:
        raise ValueError("steps are required")
    normalized = []
    for step in steps:
        if not step.get("code") or not step.get("name"):
            raise ValueError("step code and name are required")
        normalized.append(
            {
                "code": step["code"],
                "name": step["name"],
                "role": step.get("role", ""),
                "user_id": int(step["user_id"]) if step.get("user_id") else None,
            }
        )
    with connect() as conn:
        row = conn.execute("SELECT id FROM workflow_definitions WHERE code=?", (code,)).fetchone()
        if not row:
            raise LookupError("workflow definition not found")
        conn.execute("UPDATE workflow_definitions SET steps_json=? WHERE code=?", (json.dumps(normalized, ensure_ascii=False), code))
        conn.commit()
    return get_definition_detail(code)


def get_definition_detail(code: str) -> dict:
    row = get_definition(code)
    row["steps"] = json.loads(row.pop("steps_json"))
    return row


def list_instances(biz_type: str | None = None, biz_id: int | None = None) -> list[dict]:
    sql = "SELECT * FROM workflow_instances WHERE 1=1"
    args: list[object] = []
    if biz_type:
        sql += " AND biz_type=?"
        args.append(biz_type)
    if biz_id:
        sql += " AND biz_id=?"
        args.append(biz_id)
    sql += " ORDER BY started_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, args).fetchall()
    return rows_to_dicts(rows)


def list_tasks(user: dict, status: str = "pending") -> list[dict]:
    with connect() as conn:
        if user["role"] == "admin":
            rows = conn.execute(
                """
                SELECT t.*, i.definition_code, i.biz_type, i.biz_id, i.title AS instance_title
                FROM workflow_tasks t
                JOIN workflow_instances i ON i.id = t.instance_id
                WHERE t.status=?
                ORDER BY t.created_at DESC
                """,
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT t.*, i.definition_code, i.biz_type, i.biz_id, i.title AS instance_title
                FROM workflow_tasks t
                JOIN workflow_instances i ON i.id = t.instance_id
                WHERE t.status=? AND (t.assignee_role=? OR t.assignee_id=?)
                ORDER BY t.created_at DESC
                """,
                (status, user["role"], user["id"]),
            ).fetchall()
    return rows_to_dicts(rows)


def get_instance_detail(instance_id: int) -> dict:
    with connect() as conn:
        instance = conn.execute("SELECT * FROM workflow_instances WHERE id=?", (instance_id,)).fetchone()
        if not instance:
            raise LookupError("workflow instance not found")
        data = dict(instance)
        data["tasks"] = rows_to_dicts(conn.execute("SELECT * FROM workflow_tasks WHERE instance_id=? ORDER BY id", (instance_id,)).fetchall())
        data["actions"] = rows_to_dicts(conn.execute("SELECT * FROM workflow_actions WHERE instance_id=? ORDER BY created_at", (instance_id,)).fetchall())
        return data


def start_instance(definition_code: str, biz_type: str, biz_id: int, title: str, user: dict | None = None) -> dict:
    definition = get_definition(definition_code)
    existing = find_instance(biz_type, biz_id)
    if existing:
        return existing
    steps = json.loads(definition["steps_json"])
    first = steps[0]
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO workflow_instances(definition_code, biz_type, biz_id, title, current_step, started_by)
            VALUES(?,?,?,?,?,?)
            """,
            (definition_code, biz_type, biz_id, title, first["code"], user.get("id") if user else None),
        )
        instance_id = cur.lastrowid
        create_task(conn, instance_id, first)
        conn.execute(
            """
            INSERT INTO workflow_actions(instance_id, action, actor_id, actor_name, comment)
            VALUES(?,?,?,?,?)
            """,
            (instance_id, "start", user.get("id") if user else None, user.get("real_name", "") if user else "", "流程启动"),
        )
        conn.commit()
    return get_instance_detail(instance_id)


def advance_by_biz(biz_type: str, biz_id: int, action: str, user: dict | None = None, comment: str = "") -> dict | None:
    instance = find_instance(biz_type, biz_id)
    if not instance or instance["status"] != "running":
        return None
    return complete_current_task(instance["id"], action, user, comment)


def complete_task(task_id: int, action: str, user: dict, comment: str = "") -> dict:
    with connect() as conn:
        row = conn.execute("SELECT instance_id FROM workflow_tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        raise LookupError("workflow task not found")
    return complete_current_task(row["instance_id"], action, user, comment, task_id)


def complete_current_task(instance_id: int, action: str, user: dict | None = None, comment: str = "", task_id: int | None = None) -> dict:
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as conn:
        instance = conn.execute("SELECT * FROM workflow_instances WHERE id=?", (instance_id,)).fetchone()
        if not instance:
            raise LookupError("workflow instance not found")
        definition = get_definition(instance["definition_code"])
        steps = json.loads(definition["steps_json"])
        current_code = instance["current_step"]
        current_index = next((idx for idx, step in enumerate(steps) if step["code"] == current_code), -1)
        pending = conn.execute(
            """
            SELECT * FROM workflow_tasks
            WHERE instance_id=? AND status='pending' AND (? IS NULL OR id=?)
            ORDER BY id LIMIT 1
            """,
            (instance_id, task_id, task_id),
        ).fetchone()
        if pending:
            conn.execute(
                """
                UPDATE workflow_tasks
                SET status='completed', completed_by=?, completed_at=?, action=?, comment=?
                WHERE id=?
                """,
                (user.get("id") if user else None, now, action, comment, pending["id"]),
            )
            task_id = pending["id"]
        conn.execute(
            """
            INSERT INTO workflow_actions(instance_id, task_id, action, actor_id, actor_name, comment)
            VALUES(?,?,?,?,?,?)
            """,
            (instance_id, task_id, action, user.get("id") if user else None, user.get("real_name", "") if user else "", comment),
        )
        next_index = current_index + 1
        if action in ("reject", "cancel"):
            conn.execute("UPDATE workflow_instances SET status=?, completed_at=? WHERE id=?", (action, now, instance_id))
        elif next_index >= len(steps):
            conn.execute("UPDATE workflow_instances SET status='completed', current_step='', completed_at=? WHERE id=?", (now, instance_id))
        else:
            next_step = steps[next_index]
            conn.execute("UPDATE workflow_instances SET current_step=? WHERE id=?", (next_step["code"], instance_id))
            create_task(conn, instance_id, next_step)
        conn.commit()
    return get_instance_detail(instance_id)


def get_definition(code: str) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM workflow_definitions WHERE code=? AND enabled=1", (code,)).fetchone()
    if not row:
        raise LookupError("workflow definition not found")
    return dict(row)


def find_instance(biz_type: str, biz_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM workflow_instances WHERE biz_type=? AND biz_id=? ORDER BY id DESC LIMIT 1",
            (biz_type, biz_id),
        ).fetchone()
    return dict(row) if row else None


def create_task(conn, instance_id: int, step: dict) -> None:
    conn.execute(
        """
        INSERT INTO workflow_tasks(instance_id, step_code, step_name, assignee_role, assignee_id)
        VALUES(?,?,?,?,?)
        """,
        (instance_id, step["code"], step["name"], step.get("role", ""), step.get("user_id")),
    )
