from app.db.base import Base
from app.db.session import engine
from app.models import *  # noqa: F401,F403 - ensure model metadata is registered
from app.scripts.create_admin import main as create_admin_main
from app.scripts.seed_demo import main as seed_demo_main


def main() -> None:
    Base.metadata.create_all(bind=engine)
    create_admin_main()
    seed_demo_main()
    print("Bootstrap complete")


if __name__ == "__main__":
    main()
