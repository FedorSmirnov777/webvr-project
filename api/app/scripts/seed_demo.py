import shutil
from pathlib import Path
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.catalog import Brand, Car, CarAsset, CarTrim

# ── Copy car images from source folder into assets on first run ─────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[3]   # api/app/scripts/seed_demo.py → project root
_IMG_SRC = _PROJECT_ROOT / "images" / "images_for_cars"
_IMG_DST = _PROJECT_ROOT / "assets" / "uploads" / "images"

_IMAGE_COPIES = [
    ("tayota — копия/1614.jpeg",                                              "toyota_camry_hero.jpeg"),
    ("tayota/USB50TOC021E0101.webp",                                          "toyota_camry_2005_1.webp"),
    ("tayota/af788fc2-40e8-4b6e-b797-15acf0c0ffbe.png.webp",                "toyota_camry_2005_2.webp"),
    ("bmw/tumblr_mn7jviGYxX1qd1swho1_1280.jpg",                             "bmw_m3_2013_1.jpg"),
    ("bmw/bmw_m3_263436.jpg.webp",                                           "bmw_m3_2013_2.webp"),
    ("mercedes/Used-1990-Mercedes-Benz-190E-25-16-Evolution-II-1751037956.jpg", "mercedes_190e_1989_1.jpg"),
    ("mercedes/image.webp",                                                  "mercedes_190e_1989_2.webp"),
    ("porsche/porsche-911-3-2-coupe-wtl-1989.jpg.webp",                     "porsche_911_1989_1.webp"),
    ("porsche/porsche_911_1012961.jpg",                                      "porsche_911_1989_2.jpg"),
]


def _copy_images() -> None:
    """Copy car photos from images/images_for_cars → assets/uploads/images (always overwrite)."""
    _IMG_DST.mkdir(parents=True, exist_ok=True)
    for rel_src, dst_name in _IMAGE_COPIES:
        src = _IMG_SRC / rel_src
        dst = _IMG_DST / dst_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  Copied image: {dst_name}")

# ── Only the 4 brands we actually show ──────────────────────────────────────
BRANDS = [
    ("Toyota",        "toyota",   "Japan"),
    ("BMW",           "bmw",      "Germany"),
    ("Mercedes-Benz", "mercedes-benz", "Germany"),
    ("Porsche",       "porsche",  "Germany"),
]

# ── Car definitions ──────────────────────────────────────────────────────────
CARS = [
    # ── Toyota Avalon 2023 ────────────────────────────────────────────────
    {
        "slug": "toyota",
        "model_name": "Avalon",
        "year": 2023,
        "body_type": "Sedan",
        "description": (
            "Toyota Avalon 2023 — флагманский полноразмерный седан Toyota, олицетворяющий "
            "роскошь, комфорт и технологичность. Просторный салон бизнес-класса, адаптивный "
            "круиз-контроль, 9-дюймовый мультимедийный экран и мощный V6 делают его идеальным "
            "выбором для тех, кто ценит премиальный уровень езды без компромиссов."
        ),
        "base_price": 36225,
        "specs": {
            "engine":       "3.5 V6 (301 л.с.)",
            "transmission": "Автомат 8-ст.",
            "drivetrain":   "FWD",
            "fuel":         "Бензин",
            "power":        "301 л.с.",
            "acceleration": "6.3 с",
            "mileage":      0,
            "seats":        "5",
            "color":        "Midnight Black",
        },
        "model_url":    "/assets/models/toyota_camry/scene.gltf",
        "model_type":   "gltf",
        "hero_image_url": "/assets/uploads/images/tayota_avalon/toyota_avalon_hero.jpg",
        "extra_image_url": "/assets/uploads/images/tayota_avalon/tayota_avalon_2.jpg",
        "trims": [
            {
                "trim_name":  "XLE",
                "trim_price": 36225,
                "features": {
                    "engine":       "3.5 V6 (301 л.с.)",
                    "transmission": "Автомат 8-ст.",
                    "seats":        "5",
                    "color":        "Midnight Black",
                },
            },
            {
                "trim_name":  "XSE",
                "trim_price": 38500,
                "features": {
                    "engine":       "3.5 V6 (301 л.с.)",
                    "transmission": "Автомат 8-ст.",
                    "seats":        "5",
                    "color":        "Supersonic Red",
                },
            },
            {
                "trim_name":  "Limited",
                "trim_price": 43500,
                "features": {
                    "engine":       "3.5 V6 (301 л.с.)",
                    "transmission": "Автомат 8-ст.",
                    "seats":        "5",
                    "color":        "Celestial Silver",
                },
            },
        ],
    },

    # ── BMW M3 2013 ────────────────────────────────────────────────────────
    {
        "slug": "bmw",
        "model_name": "M3",
        "year": 2013,
        "body_type": "Sedan",
        "description": (
            "BMW M3 четвёртого поколения (F30 M Performance) — спортивный седан с "
            "рядным 6-цилиндровым твин-турбо двигателем и фирменным M xDrive. "
            "Баланс между повседневным комфортом и трековой производительностью."
        ),
        "base_price": 38000,
        "specs": {
            "engine":       "3.0 TwinTurbo (431 л.с.)",
            "transmission": "DCT 7-ст.",
            "drivetrain":   "RWD",
            "fuel":         "Бензин",
            "power":        "431 л.с.",
            "acceleration": "4.1 с",
            "mileage":      82000,
            "seats":        "5",
            "color":        "Topaz Blue",
        },
        "model_type": "obj",
        "obj_url":   "/assets/models/bmw-m3-sedan-2013/unpacked/BMW%20M3%20Sedan%20topaz%20blue.obj",
        "mtl_url":   "/assets/models/bmw-m3-sedan-2013/unpacked/BMW%20M3%20Sedan%20topaz%20blue.mtl",
        "hero_image_url":  "/assets/uploads/images/bmw_m3_2013_1.jpg",
        "extra_image_url": "/assets/uploads/images/bmw_m3_2013_2.webp",
        "trims": [
            {
                "trim_name":  "M3 Competition",
                "trim_price": 38000,
                "features": {
                    "engine":       "3.0 TwinTurbo (431 л.с.)",
                    "transmission": "DCT 7-ст.",
                    "drivetrain":   "RWD",
                    "color":        "Topaz Blue",
                },
            },
            {
                "trim_name":  "M3 Competition xDrive",
                "trim_price": 42000,
                "features": {
                    "engine":       "3.0 TwinTurbo (431 л.с.)",
                    "transmission": "DCT 7-ст.",
                    "drivetrain":   "AWD xDrive",
                    "color":        "Frozen Black",
                },
            },
            {
                "trim_name":  "M3 CS",
                "trim_price": 49500,
                "features": {
                    "engine":       "3.0 TwinTurbo (450 л.с.)",
                    "transmission": "DCT 7-ст.",
                    "drivetrain":   "AWD xDrive",
                    "color":        "Sao Paulo Yellow",
                },
            },
        ],
    },

    # ── Mercedes-Benz 190E 1989 ────────────────────────────────────────────
    {
        "slug": "mercedes-benz",
        "model_name": "190E",
        "year": 1989,
        "body_type": "Sedan",
        "description": (
            "Mercedes-Benz 190E 2.5-16 Evolution II — легенда немецкого автоспорта. "
            "Разработана совместно с Cosworth специально для чемпионата DTM. "
            "Лёгкий кузов W201, агрессивные аэродинамические обвесы и 235-сильный 16-клапанный мотор "
            "делают этот автомобиль настоящим коллекционным раритетом."
        ),
        "base_price": 185000,
        "specs": {
            "engine":       "2.5-16 EVO II (235 л.с.)",
            "transmission": "Механика 5-ст.",
            "drivetrain":   "RWD",
            "fuel":         "Бензин",
            "power":        "235 л.с.",
            "acceleration": "6.9 с",
            "mileage":      38000,
            "seats":        "5",
            "color":        "Brillant Schwarz",
        },
        "model_url":   "/assets/models/mercedes_190e_evo_1982.glb",
        "model_type":  "gltf",
        "hero_image_url":  "/assets/uploads/images/mercedes_190e_1989_1.jpg",
        "extra_image_url": "/assets/uploads/images/mercedes_190e_1989_2.webp",
        "trims": [
            {
                "trim_name":  "190E 2.0",
                "trim_price": 22000,
                "features": {
                    "engine":       "2.0 (90 л.с.)",
                    "transmission": "Механика 4-ст.",
                    "color":        "Astral Silber",
                },
            },
            {
                "trim_name":  "190E 2.3-16",
                "trim_price": 68000,
                "features": {
                    "engine":       "2.3-16 (185 л.с.)",
                    "transmission": "Механика 5-ст.",
                    "color":        "Rauchsilber",
                },
            },
            {
                "trim_name":  "190E 2.5-16 EVO II",
                "trim_price": 185000,
                "features": {
                    "engine":       "2.5-16 EVO II (235 л.с.)",
                    "transmission": "Механика 5-ст.",
                    "color":        "Brillant Schwarz",
                },
            },
        ],
    },

    # ── Porsche 911 Carrera 1989 ───────────────────────────────────────────
    {
        "slug": "porsche",
        "model_name": "911 Carrera",
        "year": 1989,
        "body_type": "Coupe",
        "description": (
            "Porsche 911 Carrera 3.2 (964) — последний воздушно-охлаждаемый 911 в его "
            "классическом виде. Культовый оппозитный шестицилиндровый двигатель 3.2 л, "
            "задняя компоновка и чистые линии кузова определили облик спорткара на десятилетия вперёд."
        ),
        "base_price": 98000,
        "specs": {
            "engine":       "3.2 Flat-6 (231 л.с.)",
            "transmission": "Механика 5-ст.",
            "drivetrain":   "RWD",
            "fuel":         "Бензин",
            "power":        "231 л.с.",
            "acceleration": "5.7 с",
            "mileage":      61000,
            "seats":        "2+2",
            "color":        "Guards Red",
        },
        "model_url":   "/assets/models/1989_porsche_911_964_carrera_4_safe.glb",
        "model_type":  "gltf",
        "hero_image_url":  "/assets/uploads/images/porsche_911_1989_1.webp",
        "extra_image_url": "/assets/uploads/images/porsche_911_1989_2.jpg",
        "trims": [
            {
                "trim_name":  "Carrera",
                "trim_price": 98000,
                "features": {
                    "engine":       "3.2 Flat-6 (231 л.с.)",
                    "drivetrain":   "RWD",
                    "color":        "Guards Red",
                },
            },
            {
                "trim_name":  "Carrera 4",
                "trim_price": 112000,
                "features": {
                    "engine":       "3.6 Flat-6 (250 л.с.)",
                    "drivetrain":   "AWD",
                    "color":        "Grand Prix White",
                },
            },
            {
                "trim_name":  "Carrera Turbo (930)",
                "trim_price": 145000,
                "features": {
                    "engine":       "3.3 Turbo Flat-6 (300 л.с.)",
                    "drivetrain":   "RWD",
                    "color":        "Slate Grey Metallic",
                },
            },
        ],
    },
]


def main() -> None:
    _copy_images()
    db: Session = SessionLocal()
    try:
        from app.models.catalog import Brand as BrandModel

        # ── Wipe ALL existing cars/assets/trims to start clean ────────────
        for sc in db.query(Car).all():
            db.query(CarAsset).filter(CarAsset.car_id == sc.id).delete()
            db.query(CarTrim).filter(CarTrim.car_id == sc.id).delete()
            db.delete(sc)
        db.commit()

        # ── Upsert only our 4 brands ───────────────────────────────────────
        for name, slug, country in BRANDS:
            brand = db.query(BrandModel).filter(BrandModel.slug == slug).first()
            if not brand:
                db.add(BrandModel(name=name, slug=slug, country=country))
        db.commit()

        brand_ids = {b.slug: b.id for b in db.query(BrandModel).all()}

        # ── Create cars fresh ──────────────────────────────────────────────
        for item in CARS:
            slug        = item["slug"]
            model_name  = item["model_name"]
            year        = item["year"]
            brand_id    = brand_ids[slug]

            config = {
                "colors":    ["#111827", "#dc2626", "#2563eb", "#f59e0b"],
                "wheels":    ["standard", "sport", "premium"],
                "hero_image_url": item["hero_image_url"],
                "model_url":  item.get("model_url"),
                "model_type": item.get("model_type", "gltf"),
                "obj_url":    item.get("obj_url"),
                "mtl_url":    item.get("mtl_url"),
            }

            car = Car(
                brand_id=brand_id,
                model_name=model_name,
                year=year,
                body_type=item["body_type"],
                description=item["description"],
                base_price=item["base_price"],
                specs=item["specs"],
                config=config,
                published=True,
            )
            db.add(car)
            db.flush()

            # ── Assets: hero image ─────────────────────────────────────────
            hero_key = item["hero_image_url"].replace("/assets/", "", 1)
            db.add(CarAsset(
                car_id=car.id, kind="image",
                storage_key=hero_key,
                public_url=item["hero_image_url"],
                version=1,
            ))

            # ── Assets: extra image ────────────────────────────────────────
            extra_url = item.get("extra_image_url")
            if extra_url:
                extra_key = extra_url.replace("/assets/", "", 1)
                db.add(CarAsset(
                    car_id=car.id, kind="image",
                    storage_key=extra_key,
                    public_url=extra_url,
                    version=2,
                ))

            # ── Assets: 3D model ───────────────────────────────────────────
            model_url = item.get("model_url") or item.get("obj_url")
            if model_url and model_url.startswith("/assets/models/"):
                rel = model_url.replace("/assets/", "", 1)
                db.add(CarAsset(
                    car_id=car.id, kind="model_3d",
                    storage_key=rel,
                    public_url=f"/assets/{rel}",
                    version=1,
                ))

            # ── Trims ──────────────────────────────────────────────────────
            for trim in item.get("trims", []):
                db.add(CarTrim(
                    car_id=car.id,
                    trim_name=trim["trim_name"],
                    trim_price=trim["trim_price"],
                    features=trim["features"],
                ))

        db.commit()
        print("Seed complete — 4 cars seeded")
    finally:
        db.close()


if __name__ == "__main__":
    main()
