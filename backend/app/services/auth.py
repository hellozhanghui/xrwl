from __future__ import annotations

from datetime import datetime, timedelta

from backend.app.database import connect
from backend.app.security import new_token, verify_password

PUBLIC_PATHS = {
    "/api/health",
    "/api/auth/login",
}

DEVICE_PATHS = {
    "/api/device/gps/report",
    "/api/device/sensor/report",
    "/api/device/status",
}

ROLE_PERMISSIONS = {
    "admin": {"*"},
    "fleet_manager": {"vehicles", "devices", "reports", "alerts"},
    "dispatcher": {"orders", "routes", "dispatch", "tracking", "vehicles", "reports", "alerts"},
    "driver": {"orders", "tracking", "alerts"},
    "customer": {"orders"},
    "finance": {"tickets", "reports", "orders"},
}


def login(username: str, password: str) -> dict:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username=? AND status='active'", (username,)).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            raise ValueError("用户名或密码错误")
        token = new_token()
        expires_at = (datetime.now() + timedelta(hours=12)).isoformat(timespec="seconds")
        conn.execute(
            "INSERT INTO auth_sessions(token, user_id, expires_at) VALUES(?,?,?)",
            (token, row["id"], expires_at),
        )
        conn.commit()
        user = public_user(dict(row))
        return {"token": token, "expires_at": expires_at, "user": user}


def logout(token: str) -> None:
    if not token:
        return
    with connect() as conn:
        conn.execute("DELETE FROM auth_sessions WHERE token=?", (token,))
        conn.commit()


def authenticate(headers: dict[str, str], path: str) -> dict | None:
    if path in PUBLIC_PATHS or path in DEVICE_PATHS:
        return None
    token = extract_token(headers)
    if not token:
        raise PermissionError("缺少认证令牌")
    with connect() as conn:
        row = conn.execute(
            """
            SELECT u.*
            FROM auth_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token=? AND u.status='active' AND datetime(s.expires_at) > datetime('now')
            """,
            (token,),
        ).fetchone()
    if not row:
        raise PermissionError("登录已过期或令牌无效")
    return public_user(dict(row))


def authorize(user: dict | None, area: str) -> None:
    if user is None:
        return
    permissions = ROLE_PERMISSIONS.get(user["role"], set())
    if "*" in permissions or area in permissions:
        return
    raise PermissionError("当前角色无权访问该功能")


def extract_token(headers: dict[str, str]) -> str:
    value = headers.get("authorization") or headers.get("Authorization") or ""
    if value.lower().startswith("bearer "):
        return value.split(" ", 1)[1].strip()
    return ""


def public_user(user: dict) -> dict:
    user.pop("password_hash", None)
    return user
