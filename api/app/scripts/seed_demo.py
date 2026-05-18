from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.catalog import Brand, Car, CarAsset

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
        "slug": "mercedes-benz",
        "model_name": "E190",
        "year": 1982,
        "body_type": "Sedan",
        "description": "Mercedes-Benz 190E EVO",
        "base_price": None,
        "model_url": "/assets/models/mercedes_190e_evo_1982.glb",
        "hero_image_url": "/assets/uploads/images/e190.jpg",
    },
    {
        "slug": "toyota",
        "model_name": "Camry",
        "year": 2024,
        "body_type": "Sedan",
        "description": "Комфортный бизнес-седан",
        "base_price": 36000,
        "model_url": "/assets/models/toyota_camry/scene.gltf",
        "hero_image_url": "/assets/uploads/images/toyota_camry.jpg",
    },
    {
        "slug": "bmw",
        "model_name": "X5",
        "year": 2024,
        "body_type": "SUV",
        "description": "Премиальный SUV",
        "base_price": 72000,
        "model_type": "obj",
        "obj_url": "/assets/models/bmw-m3-sedan-2013/unpacked/BMW%20M3%20Sedan%20topaz%20blue.obj",
        "mtl_url": "/assets/models/bmw-m3-sedan-2013/unpacked/BMW%20M3%20Sedan%20topaz%20blue.mtl",
        "hero_image_url": "/assets/uploads/images/bmw_x5.jpg",
    },
    {
        "slug": "porsche",
        "model_name": "911 Carrera",
        "year": 2024,
        "body_type": "Coupe",
        "description": "Легендарный спорткар",
        "base_price": 125000,
        "model_url": "/assets/models/1989_porsche_911_964_carrera_4_safe.glb",
        "hero_image_url": "/assets/uploads/images/porsche_911_carrera.jpg",
    },
]


def main() -> None:
    db: Session = SessionLocal()
    try:
        for name, slug, country in BRANDS:
            brand = db.query(Brand).filter(Brand.slug == slug).first()
            if not brand:
                db.add(Brand(name=name, slug=slug, country=country))
        db.commit()

        brand_ids = {brand.slug: brand.id for brand in db.query(Brand).all()}

        for item in CARS:
            slug = item["slug"]
            model_name = item["model_name"]
            year = item["year"]
            body_type = item["body_type"]
            description = item["description"]
            base_price = item["base_price"]
            car = (
                db.query(Car)
                .filter(Car.brand_id == brand_ids[slug], Car.model_name == model_name, Car.year == year)
                .first()
            )
            if not car:
                car = Car(
                    brand_id=brand_ids[slug],
                    model_name=model_name,
                    year=year,
                    body_type=body_type,
                    description=description,
                    base_price=base_price,
                    specs={
                        "power_hp": 250,
                        "drivetrain": "AWD",
                        "range_km": 600,
                        "acceleration_sec": 6.0,
                    },
                    config={
                        "colors": ["#111827", "#dc2626", "#2563eb", "#f59e0b"],
                        "wheels": ["standard", "sport", "premium"],
                        "hero_image_url": item["hero_image_url"],
                        "model_url": item.get("model_url"),
                        "model_type": item.get("model_type", "gltf"),
                        "obj_url": item.get("obj_url"),
                        "mtl_url": item.get("mtl_url"),
                    },
                    published=True,
                )
                db.add(car)
                db.flush()
            else:
                car.body_type = body_type
                car.description = description
                car.base_price = base_price
                car.published = True
                current_cfg = dict(car.config or {})
                current_cfg.update(
                    {
                        "hero_image_url": item["hero_image_url"],
                        "model_url": item.get("model_url"),
                        "model_type": item.get("model_type", "gltf"),
                        "obj_url": item.get("obj_url"),
                        "mtl_url": item.get("mtl_url"),
                    }
                )
                car.config = current_cfg

            existing_model = (
                db.query(CarAsset)
                .filter(CarAsset.car_id == car.id, CarAsset.kind == "model_3d")
                .first()
            )
            model_url = item.get("model_url")
            if not existing_model and model_url and model_url.startswith("/assets/models/"):
                rel = model_url.replace("/assets/", "", 1)
                db.add(
                    CarAsset(
                        car_id=car.id,
                        kind="model_3d",
                        storage_key=rel,
                        public_url=f"/assets/{rel}",
                        version=1,
                    )
                )

        db.commit()
        print("Seed complete")
    finally:
        db.close()


if __name__ == "__main__":
    main()
