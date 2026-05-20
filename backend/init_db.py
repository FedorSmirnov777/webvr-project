from __future__ import annotations

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "autovr.sqlite3"


BRANDS = [
    ("Toyota", "toyota", "Japan"),
    ("BMW", "bmw", "Germany"),
    ("Mercedes-Benz", "mercedes-benz", "Germany"),
    ("Audi", "audi", "Germany"),
    ("Tesla", "tesla", "USA"),
    ("Porsche", "porsche", "Germany"),
]


CARS = [
    {
        "brand_slug": "toyota",
        "model_name": "Camry",
        "year": 2024,
        "body_type": "Sedan",
        "description": "Бизнес-седан с высоким уровнем комфорта и надежности.",
        "power_hp": 249,
        "drivetrain": "FWD",
        "range_km": 850,
        "acceleration_sec": 7.2,
        "model_url": "assets/models/toyota_camry_2024.glb",
        "hero_image_url": "/assets/uploads/images/toyota_camry_hero.jpg",
        "base_price": 35500,
        "fallback_color": "#2563eb",
        "fallback_scale": "1.7 0.78 3.4",
        "published": 1,
    },
    {
        "brand_slug": "bmw",
        "model_name": "X5",
        "year": 2024,
        "body_type": "SUV",
        "description": "Премиальный кроссовер с полным приводом и продвинутой электроникой.",
        "power_hp": 340,
        "drivetrain": "AWD",
        "range_km": 760,
        "acceleration_sec": 5.5,
        "model_url": "assets/models/bmw_x5_2024.glb",
        "hero_image_url": "",
        "base_price": 74200,
        "fallback_color": "#111827",
        "fallback_scale": "1.75 0.82 3.5",
        "published": 1,
    },
    {
        "brand_slug": "mercedes-benz",
        "model_name": "C-Class",
        "year": 2024,
        "body_type": "Sedan",
        "description": "Седан бизнес-класса с акцентом на комфорт и технологии.",
        "power_hp": 258,
        "drivetrain": "RWD",
        "range_km": 790,
        "acceleration_sec": 6.0,
        "model_url": "assets/models/mercedes_c_class_2024.glb",
        "hero_image_url": "",
        "base_price": 61600,
        "fallback_color": "#9ca3af",
        "fallback_scale": "1.68 0.76 3.3",
        "published": 1,
    },
    {
        "brand_slug": "audi",
        "model_name": "A6",
        "year": 2024,
        "body_type": "Sedan",
        "description": "Технологичный представительский седан с фирменным quattro.",
        "power_hp": 265,
        "drivetrain": "AWD",
        "range_km": 780,
        "acceleration_sec": 5.9,
        "model_url": "assets/models/audi_a6_2024.glb",
        "hero_image_url": "",
        "base_price": 65800,
        "fallback_color": "#0f766e",
        "fallback_scale": "1.7 0.76 3.35",
        "published": 1,
    },
    {
        "brand_slug": "tesla",
        "model_name": "Model 3",
        "year": 2024,
        "body_type": "EV Sedan",
        "description": "Электроседан с быстрым откликом и современной цифровой платформой.",
        "power_hp": 351,
        "drivetrain": "AWD",
        "range_km": 629,
        "acceleration_sec": 4.4,
        "model_url": "assets/models/tesla_model_3_2024.glb",
        "hero_image_url": "",
        "base_price": 50990,
        "fallback_color": "#dc2626",
        "fallback_scale": "1.62 0.72 3.2",
        "published": 1,
    },
    {
        "brand_slug": "porsche",
        "model_name": "911 Carrera",
        "year": 2024,
        "body_type": "Coupe",
        "description": "Культовое спортивное купе с динамикой и точной управляемостью.",
        "power_hp": 385,
        "drivetrain": "RWD",
        "range_km": 640,
        "acceleration_sec": 4.2,
        "model_url": "assets/models/porsche_911_carrera_2024.glb",
        "hero_image_url": "",
        "base_price": 124500,
        "fallback_color": "#f59e0b",
        "fallback_scale": "1.55 0.66 3.0",
        "published": 1,
    },
]


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS brands (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  slug TEXT NOT NULL UNIQUE,
  country TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cars (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  brand_id INTEGER NOT NULL,
  model_name TEXT NOT NULL,
  year INTEGER NOT NULL,
  body_type TEXT NOT NULL,
  description TEXT NOT NULL,
  power_hp INTEGER NOT NULL,
  drivetrain TEXT NOT NULL,
  range_km INTEGER NOT NULL,
  acceleration_sec REAL NOT NULL,
  model_url TEXT NOT NULL,
  hero_image_url TEXT NOT NULL DEFAULT '',
  base_price REAL,
  published INTEGER NOT NULL DEFAULT 0,
  fallback_color TEXT NOT NULL,
  fallback_scale TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE,
  UNIQUE (brand_id, model_name, year)
);

CREATE TABLE IF NOT EXISTS car_media (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  car_id INTEGER NOT NULL,
  kind TEXT NOT NULL,
  file_url TEXT NOT NULL,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS car_trims (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  car_id INTEGER NOT NULL,
  trim_name TEXT NOT NULL,
  trim_price REAL,
  features_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (car_id) REFERENCES cars(id) ON DELETE CASCADE
);
"""


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _ensure_backward_compatible_columns(conn: sqlite3.Connection) -> None:
    columns = _table_columns(conn, "cars")

    if "hero_image_url" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN hero_image_url TEXT NOT NULL DEFAULT ''")
    if "base_price" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN base_price REAL")
    if "published" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN published INTEGER NOT NULL DEFAULT 0")
    if "power_hp" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN power_hp INTEGER NOT NULL DEFAULT 0")
    if "drivetrain" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN drivetrain TEXT NOT NULL DEFAULT ''")
    if "range_km" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN range_km INTEGER NOT NULL DEFAULT 0")
    if "acceleration_sec" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN acceleration_sec REAL NOT NULL DEFAULT 0")
    if "fallback_color" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN fallback_color TEXT NOT NULL DEFAULT '#2563eb'")
    if "fallback_scale" not in columns:
        conn.execute("ALTER TABLE cars ADD COLUMN fallback_scale TEXT NOT NULL DEFAULT '1.7 0.78 3.4'")


def init_database(db_path: Path = DEFAULT_DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(SCHEMA_SQL)
        _ensure_backward_compatible_columns(conn)

        conn.executemany(
            """
            INSERT INTO brands (name, slug, country)
            VALUES (?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
              name = excluded.name,
              country = excluded.country
            """,
            BRANDS,
        )

        brand_id_by_slug = {
            row[1]: row[0] for row in conn.execute("SELECT id, slug FROM brands")
        }

        for car in CARS:
            conn.execute(
                """
                INSERT INTO cars (
                  brand_id, model_name, year, body_type, description,
                  power_hp, drivetrain, range_km, acceleration_sec,
                  model_url, hero_image_url, base_price, published,
                  fallback_color, fallback_scale
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(brand_id, model_name, year) DO UPDATE SET
                  body_type = excluded.body_type,
                  description = excluded.description,
                  power_hp = excluded.power_hp,
                  drivetrain = excluded.drivetrain,
                  range_km = excluded.range_km,
                  acceleration_sec = excluded.acceleration_sec,
                  model_url = excluded.model_url,
                  hero_image_url = excluded.hero_image_url,
                  base_price = excluded.base_price,
                  fallback_color = excluded.fallback_color,
                  fallback_scale = excluded.fallback_scale,
                  updated_at = datetime('now')
                """,
                (
                    brand_id_by_slug[car["brand_slug"]],
                    car["model_name"],
                    car["year"],
                    car["body_type"],
                    car["description"],
                    car["power_hp"],
                    car["drivetrain"],
                    car["range_km"],
                    car["acceleration_sec"],
                    car["model_url"],
                    car["hero_image_url"],
                    car["base_price"],
                    car["published"],
                    car["fallback_color"],
                    car["fallback_scale"],
                ),
            )

        conn.commit()


if __name__ == "__main__":
    init_database()
    print(f"Database initialized: {DEFAULT_DB_PATH}")
