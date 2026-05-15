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
    ("toyota", "Camry", 2024, "Sedan", "Комфортный бизнес-седан", 36000, "toyota_camry_2024.glb"),
    ("bmw", "X5", 2024, "SUV", "Премиальный SUV", 72000, "bmw_x5_2024.glb"),
    ("mercedes-benz", "C-Class", 2024, "Sedan", "Бизнес-класс с премиум салоном", 68000, "mercedes_c_class_2024.glb"),
    ("audi", "A6", 2024, "Sedan", "Технологичный седан", 70000, "audi_a6_2024.glb"),
    ("tesla", "Model 3", 2024, "EV Sedan", "Электроседан", 52000, "tesla_model_3_2024.glb"),
    ("porsche", "911 Carrera", 2024, "Coupe", "Легендарный спорткар", 125000, "porsche_911_carrera_2024.glb"),
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

        for slug, model_name, year, body_type, description, base_price, glb_file in CARS:
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
                    },
                    published=True,
                )
                db.add(car)
                db.flush()

            existing_model = (
                db.query(CarAsset)
                .filter(CarAsset.car_id == car.id, CarAsset.kind == "model_3d")
                .first()
            )
            if not existing_model:
                rel = f"models/{glb_file}"
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
