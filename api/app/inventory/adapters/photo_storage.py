from __future__ import annotations

from pathlib import Path


class LocalPhotoStorage:
    """Implementa el Protocol PhotoStorage guardando en disco local.
    Migrable a S3/MinIO reimplementando el mismo puerto."""

    def __init__(self, base_dir: Path) -> None:
        self._base = base_dir
        self._base.mkdir(parents=True, exist_ok=True)

    def save(self, product_sku: str, content: bytes, filename: str) -> str:
        extension = Path(filename).suffix.lower()
        destination = self._base / f"{product_sku}{extension}"
        destination.write_bytes(content)
        return str(destination)

    def delete(self, path: str) -> None:
        Path(path).unlink(missing_ok=True)
