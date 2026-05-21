"""
Запускать из корня проекта:  python3 apply_toyota_photo.py
"""
from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DST = BASE_DIR / "assets" / "uploads" / "images" / "toyota_camry_hero.jpg"
DB  = BASE_DIR / "data" / "autovr.sqlite3"


def find_source_image() -> Path | None:
    search_root = BASE_DIR / "images" / "images_for_cars"
    if not search_root.exists():
        return None
    # Ищем любую папку с "tayota" или "toyota" в названии
    for folder in search_root.iterdir():
        name_lower = folder.name.lower()
        if "tayota" in name_lower or "toyota" in name_lower:
            # Берём первый jpeg/jpg/webp/png внутри
            for ext in ("*.jpeg", "*.jpg", "*.webp", "*.png"):
                hits = list(folder.glob(ext))
                if hits:
                    return hits[0]
    return None


def main() -> None:
    src = find_source_image()
    if src is None:
        print("[ERROR] Не нашёл папку с фото Toyota в images/images_for_cars/")
        print("        Содержимое папки:")
        root = BASE_DIR / "images" / "images_for_cars"
        if root.exists():
            for p in root.iterdir():
                print(f"          {p.name}")
        return

    print(f"[INFO] Найдено фото: {src.relative_to(BASE_DIR)}")

    DST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src, DST)
    print(f"[OK]   Скопировано → {DST.relative_to(BASE_DIR)}")

    if not DB.exists():
        print(f"[WARN] База данных не найдена: {DB}")
        print("       Запусти сначала: python3 backend/init_db.py")
        return

    with sqlite3.connect(DB) as conn:
        rows = conn.execute(
            "UPDATE cars SET hero_image_url = ?, updated_at = datetime('now') WHERE model_name = 'Camry'",
            ("/assets/uploads/images/toyota_camry_hero.jpg",),
        ).rowcount
        conn.commit()

    if rows:
        print(f"[OK]   База обновлена — Toyota Camry получила новое фото ({rows} запись)")
    else:
        print("[WARN] Запись Camry не найдена в БД.")
        print("       Запусти: python3 backend/init_db.py  — потом повтори этот скрипт")


if __name__ == "__main__":
    main()
