from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import sqlite3
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from init_db import DEFAULT_DB_PATH, init_database

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = DEFAULT_DB_PATH
UPLOADS_DIR = BASE_DIR / "assets" / "uploads"
ADMIN_LOGIN = os.getenv("AUTOVR_ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.getenv("AUTOVR_ADMIN_PASSWORD", "admin123")
ADMIN_TOKEN_SECRET = os.getenv("AUTOVR_ADMIN_SECRET", "change-this-secret")
ADMIN_TOKEN_TTL_SECONDS = 60 * 60 * 8


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _safe_filename(filename: str) -> str:
    return "".join(ch for ch in filename if ch.isalnum() or ch in ("-", "_", ".")).strip("._") or "upload.bin"


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _sign_token(payload_b64: str) -> str:
    digest = hmac.new(ADMIN_TOKEN_SECRET.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(digest)


def _issue_admin_token() -> str:
    payload = {
        "sub": ADMIN_LOGIN,
        "exp": int(time.time()) + ADMIN_TOKEN_TTL_SECONDS,
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign_token(payload_b64)
    return f"{payload_b64}.{signature}"


def _verify_admin_token(token: str) -> bool:
    if "." not in token:
        return False
    payload_b64, signature = token.split(".", 1)
    expected = _sign_token(payload_b64)
    if not hmac.compare_digest(signature, expected):
        return False

    try:
        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return False

    return payload.get("sub") == ADMIN_LOGIN and int(payload.get("exp", 0)) > int(time.time())


class AutoVRRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def _is_authorized_admin(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return False
        token = auth[7:].strip()
        return _verify_admin_token(token)

    def _require_admin_auth(self) -> bool:
        if self._is_authorized_admin():
            return True
        self._json_response(
            {"error": "unauthorized", "detail": "Admin token required"},
            status=HTTPStatus.UNAUTHORIZED,
        )
        return False

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._json_response({"ok": True, "service": "autovr-backend"})
            return

        if parsed.path == "/api/brands":
            self._handle_get_brands()
            return

        if parsed.path == "/api/cars":
            self._handle_get_cars(parse_qs(parsed.query))
            return

        if parsed.path == "/api/admin/cars":
            if not self._require_admin_auth():
                return
            self._handle_get_admin_cars(parse_qs(parsed.query))
            return

        if parsed.path.startswith("/api/admin/cars/"):
            if not self._require_admin_auth():
                return
            car_id = parsed.path.rsplit("/", 1)[-1]
            self._handle_get_admin_car_by_id(car_id)
            return

        if parsed.path.startswith("/api/cars/"):
            car_id = parsed.path.rsplit("/", 1)[-1]
            self._handle_get_car_by_id(car_id)
            return

        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/admin/login":
            self._handle_admin_login()
            return

        if parsed.path == "/api/cars":
            self._handle_create_car()
            return

        if parsed.path == "/api/admin/brands":
            if not self._require_admin_auth():
                return
            self._handle_create_brand()
            return

        if parsed.path == "/api/admin/cars":
            if not self._require_admin_auth():
                return
            self._handle_create_car_admin()
            return

        if parsed.path.endswith("/publish") and parsed.path.startswith("/api/admin/cars/"):
            if not self._require_admin_auth():
                return
            car_id = parsed.path.split("/")[-2]
            self._handle_publish_car(car_id)
            return

        if parsed.path.endswith("/trims") and parsed.path.startswith("/api/admin/cars/"):
            if not self._require_admin_auth():
                return
            car_id = parsed.path.split("/")[-2]
            self._handle_add_trim(car_id)
            return

        if parsed.path.endswith("/upload") and parsed.path.startswith("/api/admin/cars/"):
            if not self._require_admin_auth():
                return
            car_id = parsed.path.split("/")[-2]
            self._handle_upload_asset(car_id, parse_qs(parsed.query))
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Unknown API endpoint")

    def _read_json_body(self) -> dict | None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return None

    def _handle_admin_login(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid json")
            return

        login = str(payload.get("login", "")).strip()
        password = str(payload.get("password", "")).strip()

        if login != ADMIN_LOGIN or password != ADMIN_PASSWORD:
            self._json_response({"error": "invalid credentials"}, status=HTTPStatus.UNAUTHORIZED)
            return

        token = _issue_admin_token()
        self._json_response(
            {
                "ok": True,
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": ADMIN_TOKEN_TTL_SECONDS,
            }
        )

    def _handle_get_brands(self) -> None:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, slug, country FROM brands ORDER BY name ASC"
            ).fetchall()

        self._json_response([dict(row) for row in rows])

    def _cars_select_sql(self) -> str:
        return """
        SELECT
          c.id,
          b.name AS brand_name,
          b.slug AS brand_slug,
          c.model_name,
          c.year,
          c.body_type,
          c.description,
          c.power_hp,
          c.drivetrain,
          c.range_km,
          c.acceleration_sec,
          c.model_url,
          c.hero_image_url,
          c.base_price,
          c.published,
          c.fallback_color,
          c.fallback_scale
        FROM cars c
        JOIN brands b ON b.id = c.brand_id
        """

    def _handle_get_cars(self, query: dict[str, list[str]]) -> None:
        where = ["c.published = 1"]
        params: list[object] = []

        brand = (query.get("brand") or [""])[0].strip().lower()
        search = (query.get("search") or [""])[0].strip().lower()

        if brand:
            where.append("b.slug = ?")
            params.append(brand)

        if search:
            where.append("(lower(c.model_name) LIKE ? OR lower(b.name) LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern])

        sql = self._cars_select_sql()
        sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY b.name ASC, c.model_name ASC, c.year DESC"

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        payload = []
        for row in rows:
            item = dict(row)
            item["name"] = f"{item['brand_name']} {item['model_name']}"
            payload.append(item)

        self._json_response(payload)

    def _handle_get_admin_cars(self, query: dict[str, list[str]]) -> None:
        include_unpublished = (query.get("include_unpublished") or ["1"])[0] == "1"

        sql = self._cars_select_sql()
        params: list[object] = []

        if not include_unpublished:
            sql += " WHERE c.published = 1"

        sql += " ORDER BY c.updated_at DESC"

        with get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()

        payload = []
        for row in rows:
            item = dict(row)
            item["name"] = f"{item['brand_name']} {item['model_name']}"
            payload.append(item)

        self._json_response(payload)

    def _handle_get_admin_car_by_id(self, car_id: str) -> None:
        if not car_id.isdigit():
            self.send_error(HTTPStatus.BAD_REQUEST, "car id must be numeric")
            return

        with get_connection() as conn:
            row = conn.execute(
                self._cars_select_sql() + " WHERE c.id = ?",
                (int(car_id),),
            ).fetchone()
            if not row:
                self.send_error(HTTPStatus.NOT_FOUND, "car not found")
                return

            trims = conn.execute(
                """
                SELECT id, trim_name, trim_price, features_json, created_at
                FROM car_trims
                WHERE car_id = ?
                ORDER BY id ASC
                """,
                (int(car_id),),
            ).fetchall()

            media = conn.execute(
                """
                SELECT id, kind, file_url, sort_order, created_at
                FROM car_media
                WHERE car_id = ?
                ORDER BY sort_order ASC, id ASC
                """,
                (int(car_id),),
            ).fetchall()

        payload = dict(row)
        payload["name"] = f"{payload['brand_name']} {payload['model_name']}"
        payload["trims"] = [dict(t) for t in trims]
        payload["media"] = [dict(m) for m in media]
        for trim in payload["trims"]:
            try:
                trim["features"] = json.loads(trim.pop("features_json") or "{}")
            except json.JSONDecodeError:
                trim["features"] = {}

        self._json_response(payload)

    def _handle_get_car_by_id(self, car_id: str) -> None:
        if not car_id.isdigit():
            self.send_error(HTTPStatus.BAD_REQUEST, "car id must be numeric")
            return

        with get_connection() as conn:
            row = conn.execute(
                self._cars_select_sql() + " WHERE c.id = ? AND c.published = 1",
                (int(car_id),),
            ).fetchone()

            if row is None:
                self.send_error(HTTPStatus.NOT_FOUND, "car not found")
                return

            trims = conn.execute(
                """
                SELECT trim_name, trim_price, features_json
                FROM car_trims
                WHERE car_id = ?
                ORDER BY trim_price ASC
                """,
                (int(car_id),),
            ).fetchall()

        payload = dict(row)
        payload["name"] = f"{payload['brand_name']} {payload['model_name']}"
        payload["trims"] = []
        for trim in trims:
            item = dict(trim)
            try:
                item["features"] = json.loads(item.pop("features_json") or "{}")
            except json.JSONDecodeError:
                item["features"] = {}
            payload["trims"].append(item)
        self._json_response(payload)

    def _handle_create_brand(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid json")
            return

        required = ["name", "slug", "country"]
        missing = [field for field in required if field not in payload]
        if missing:
            self._json_response({"error": "missing fields", "fields": missing}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO brands (name, slug, country) VALUES (?, ?, ?)",
                    (payload["name"].strip(), payload["slug"].strip(), payload["country"].strip()),
                )
                conn.commit()
        except sqlite3.IntegrityError as exc:
            self._json_response({"error": "integrity error", "detail": str(exc)}, status=HTTPStatus.CONFLICT)
            return

        self._json_response({"ok": True, "brand_id": cursor.lastrowid}, status=HTTPStatus.CREATED)

    def _validate_car_payload(self, payload: dict) -> list[str]:
        required_fields = [
            "brand_slug",
            "model_name",
            "year",
            "body_type",
            "description",
            "power_hp",
            "drivetrain",
            "range_km",
            "acceleration_sec",
            "fallback_color",
            "fallback_scale",
        ]
        return [field for field in required_fields if field not in payload]

    def _insert_car(self, payload: dict, publish_default: int = 0) -> tuple[bool, int | None, str | None]:
        with get_connection() as conn:
            brand = conn.execute(
                "SELECT id FROM brands WHERE slug = ?", (payload["brand_slug"],)
            ).fetchone()

            if brand is None:
                return False, None, f"brand slug not found: {payload['brand_slug']}"

            try:
                cursor = conn.execute(
                    """
                    INSERT INTO cars (
                      brand_id, model_name, year, body_type, description,
                      power_hp, drivetrain, range_km, acceleration_sec,
                      model_url, hero_image_url, base_price, published,
                      fallback_color, fallback_scale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        int(brand["id"]),
                        str(payload["model_name"]),
                        int(payload["year"]),
                        str(payload["body_type"]),
                        str(payload["description"]),
                        int(payload["power_hp"]),
                        str(payload["drivetrain"]),
                        int(payload["range_km"]),
                        float(payload["acceleration_sec"]),
                        str(payload.get("model_url", "")),
                        str(payload.get("hero_image_url", "")),
                        float(payload["base_price"]) if payload.get("base_price") not in (None, "") else None,
                        int(payload.get("published", publish_default)),
                        str(payload["fallback_color"]),
                        str(payload["fallback_scale"]),
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                return False, None, str(exc)

        return True, cursor.lastrowid, None

    def _handle_create_car(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid json")
            return

        missing = self._validate_car_payload(payload)
        if missing:
            self._json_response({"error": "missing fields", "fields": missing}, status=HTTPStatus.BAD_REQUEST)
            return

        ok, car_id, error = self._insert_car(payload, publish_default=1)
        if not ok:
            status = HTTPStatus.BAD_REQUEST if "brand slug" in (error or "") else HTTPStatus.CONFLICT
            self._json_response({"error": error}, status=status)
            return

        self._json_response({"ok": True, "car_id": car_id}, status=HTTPStatus.CREATED)

    def _handle_create_car_admin(self) -> None:
        payload = self._read_json_body()
        if payload is None:
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid json")
            return

        missing = self._validate_car_payload(payload)
        if missing:
            self._json_response({"error": "missing fields", "fields": missing}, status=HTTPStatus.BAD_REQUEST)
            return

        ok, car_id, error = self._insert_car(payload, publish_default=0)
        if not ok:
            status = HTTPStatus.BAD_REQUEST if "brand slug" in (error or "") else HTTPStatus.CONFLICT
            self._json_response({"error": error}, status=status)
            return

        self._json_response({"ok": True, "car_id": car_id}, status=HTTPStatus.CREATED)

    def _handle_publish_car(self, car_id: str) -> None:
        if not car_id.isdigit():
            self.send_error(HTTPStatus.BAD_REQUEST, "car id must be numeric")
            return

        with get_connection() as conn:
            updated = conn.execute(
                "UPDATE cars SET published = 1, updated_at = datetime('now') WHERE id = ?",
                (int(car_id),),
            )
            conn.commit()

        if updated.rowcount == 0:
            self.send_error(HTTPStatus.NOT_FOUND, "car not found")
            return

        self._json_response({"ok": True, "car_id": int(car_id), "published": 1})

    def _handle_add_trim(self, car_id: str) -> None:
        if not car_id.isdigit():
            self.send_error(HTTPStatus.BAD_REQUEST, "car id must be numeric")
            return

        payload = self._read_json_body()
        if payload is None:
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid json")
            return

        required = ["trim_name"]
        missing = [field for field in required if field not in payload]
        if missing:
            self._json_response({"error": "missing fields", "fields": missing}, status=HTTPStatus.BAD_REQUEST)
            return

        features_json = json.dumps(payload.get("features", {}), ensure_ascii=False)

        with get_connection() as conn:
            car = conn.execute("SELECT id FROM cars WHERE id = ?", (int(car_id),)).fetchone()
            if not car:
                self.send_error(HTTPStatus.NOT_FOUND, "car not found")
                return

            cursor = conn.execute(
                """
                INSERT INTO car_trims (car_id, trim_name, trim_price, features_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    int(car_id),
                    str(payload["trim_name"]),
                    float(payload["trim_price"]) if payload.get("trim_price") not in (None, "") else None,
                    features_json,
                ),
            )
            conn.commit()

        self._json_response({"ok": True, "trim_id": cursor.lastrowid}, status=HTTPStatus.CREATED)

    def _handle_upload_asset(self, car_id: str, query: dict[str, list[str]]) -> None:
        if not car_id.isdigit():
            self.send_error(HTTPStatus.BAD_REQUEST, "car id must be numeric")
            return

        kind = (query.get("kind") or ["image"])[0].strip().lower()
        if kind not in {"image", "model"}:
            self.send_error(HTTPStatus.BAD_REQUEST, "kind must be image or model")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0:
            self.send_error(HTTPStatus.BAD_REQUEST, "empty file")
            return

        filename = _safe_filename(self.headers.get("X-Filename", "upload.bin"))
        body = self.rfile.read(content_length)

        subdir = "images" if kind == "image" else "models"
        destination_dir = UPLOADS_DIR / subdir
        destination_dir.mkdir(parents=True, exist_ok=True)

        destination_path = destination_dir / f"car_{car_id}_{filename}"
        destination_path.write_bytes(body)

        relative_url = str(destination_path.relative_to(BASE_DIR)).replace("\\", "/")

        with get_connection() as conn:
            car = conn.execute("SELECT id FROM cars WHERE id = ?", (int(car_id),)).fetchone()
            if not car:
                self.send_error(HTTPStatus.NOT_FOUND, "car not found")
                return

            if kind == "model":
                conn.execute(
                    "UPDATE cars SET model_url = ?, updated_at = datetime('now') WHERE id = ?",
                    (relative_url, int(car_id)),
                )
            else:
                conn.execute(
                    "UPDATE cars SET hero_image_url = ?, updated_at = datetime('now') WHERE id = ?",
                    (relative_url, int(car_id)),
                )

            next_sort = conn.execute(
                "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM car_media WHERE car_id = ?",
                (int(car_id),),
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO car_media (car_id, kind, file_url, sort_order) VALUES (?, ?, ?, ?)",
                (int(car_id), kind, relative_url, int(next_sort)),
            )
            conn.commit()

        self._json_response(
            {
                "ok": True,
                "car_id": int(car_id),
                "kind": kind,
                "file_url": relative_url,
            },
            status=HTTPStatus.CREATED,
        )

    def _json_response(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    init_database(DB_PATH)
    server = ThreadingHTTPServer((host, port), AutoVRRequestHandler)
    print(f"AutoVR backend started on http://{host}:{port}")
    print(f"Database: {DB_PATH}")
    server.serve_forever()


if __name__ == "__main__":
    run()
