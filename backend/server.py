from __future__ import annotations

import json
import mimetypes
import os
import sys
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.api.router import dispatch_request
from backend.app.database import connect, init_db

FRONTEND = ROOT / "frontend" / "src"
UPLOADS = ROOT / "backend" / "uploads"


class LogisticsHandler(BaseHTTPRequestHandler):
    server_version = "XRLogistics/0.1"

    def do_GET(self) -> None:
        if self.path.startswith("/tiles/tianditu"):
            self.serve_tianditu_tile()
            return
        if self.path.startswith("/api/"):
            self.handle_api("GET")
            return
        if self.path.startswith("/uploads/"):
            self.serve_upload()
            return
        self.serve_static()

    def do_POST(self) -> None:
        self.handle_api("POST")

    def do_PUT(self) -> None:
        self.handle_api("PUT")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def handle_api(self, method: str) -> None:
        try:
            body = self.read_json()
            headers = {key.lower(): value for key, value in self.headers.items()}
            status, payload = dispatch_request(method, self.path, body, self.client_address[0], headers)
        except ValueError as exc:
            status, payload = 400, {"error": "bad_request", "message": str(exc)}
        except LookupError as exc:
            status, payload = 404, {"error": "not_found", "message": str(exc)}
        except PermissionError as exc:
            status, payload = 401, {"error": "unauthorized", "message": str(exc)}
        except Exception as exc:
            status, payload = 500, {"error": "server_error", "message": str(exc)}
        self.write_json(status, payload)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def write_json(self, status: int, payload: object) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def serve_static(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/":
            path = "/index.html"
        target = (FRONTEND / path.lstrip("/")).resolve()
        if not str(target).startswith(str(FRONTEND.resolve())) or not target.exists() or target.is_dir():
            self.write_json(404, {"error": "not_found"})
            return
        content = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_upload(self) -> None:
        path = urllib.parse.urlparse(self.path).path
        target = (UPLOADS / path.removeprefix("/uploads/")).resolve()
        if not str(target).startswith(str(UPLOADS.resolve())) or not target.exists() or target.is_dir():
            self.write_json(404, {"error": "not_found"})
            return
        content = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_tianditu_tile(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        query = {key: values[0] for key, values in urllib.parse.parse_qs(parsed.query).items()}
        layer = query.get("T", "vec_w")
        if layer not in ("vec_w", "cva_w"):
            self.write_json(400, {"error": "bad_request", "message": "unsupported tile layer"})
            return
        try:
            x = int(query["x"])
            y = int(query["y"])
            level = int(query["l"])
        except (KeyError, ValueError):
            self.write_json(400, {"error": "bad_request", "message": "x, y and l are required"})
            return
        tk = self.tianditu_tk()
        if not tk:
            self.write_json(404, {"error": "not_configured", "message": "tianditu tk is not configured"})
            return
        server = abs(x + y + level) % 8
        params = urllib.parse.urlencode({"T": layer, "x": x, "y": y, "l": level, "tk": tk})
        url = f"https://t{server}.tianditu.gov.cn/DataServer?{params}"
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                content = response.read()
                content_type = response.headers.get("Content-Type", "image/png")
        except Exception as exc:
            self.write_json(502, {"error": "tile_fetch_failed", "message": str(exc)})
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "public, max-age=86400")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def tianditu_tk(self) -> str:
        with connect() as conn:
            row = conn.execute("SELECT api_key FROM map_configs WHERE provider='tianditu' AND enabled=1").fetchone()
        return row["api_key"] if row and row["api_key"] else ""

    def send_cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


def main() -> None:
    init_db(seed=True)
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), LogisticsHandler)
    print(f"XR logistics vehicle system running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
