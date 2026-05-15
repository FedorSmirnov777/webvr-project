from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings


class StorageService:
    def __init__(self) -> None:
        self.base_dir = Path(settings.uploads_dir)

    def ensure_dirs(self) -> None:
        (self.base_dir / "models").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "images").mkdir(parents=True, exist_ok=True)

    def upload_local(self, file: UploadFile, prefix: str) -> tuple[str, str]:
        self.ensure_dirs()
        extension = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "bin"
        filename = f"{prefix.replace('/', '_')}.{extension}"

        kind = "models" if "model" in prefix else "images"
        path = self.base_dir / kind / filename

        with path.open("wb") as target:
            target.write(file.file.read())

        relative = path.relative_to(self.base_dir.parent)
        public_url = f"/assets/{relative.as_posix()}"
        return relative.as_posix(), public_url
