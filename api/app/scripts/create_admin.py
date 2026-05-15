import os

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole

ADMIN_EMAIL = os.getenv("AUTOVR_ADMIN_EMAIL", "admin@autovr.local")
ADMIN_PASSWORD = os.getenv("AUTOVR_ADMIN_PASSWORD", "admin123")
ADMIN_ROLE = os.getenv("AUTOVR_ADMIN_ROLE", "admin")


def main() -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if user:
            print("Admin already exists")
            return

        role = UserRole(ADMIN_ROLE)
        db.add(
            User(
                email=ADMIN_EMAIL,
                password_hash=hash_password(ADMIN_PASSWORD),
                role=role,
            )
        )
        db.commit()
        print(f"User created: {ADMIN_EMAIL} / {ADMIN_PASSWORD} ({role.value})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
