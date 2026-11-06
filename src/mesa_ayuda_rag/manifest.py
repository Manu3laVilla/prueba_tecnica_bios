"""Manifiesto de archivos para indexación incremental (hash + tamaño + mtime)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileFingerprint:
    rel_path: str
    size: int
    mtime_ns: int
    sha256: str

    def to_dict(self) -> dict[str, object]:
        return {
            "rel_path": self.rel_path,
            "size": self.size,
            "mtime_ns": self.mtime_ns,
            "sha256": self.sha256,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> FileFingerprint:
        return cls(
            rel_path=str(data["rel_path"]),
            size=int(data["size"]),
            mtime_ns=int(data["mtime_ns"]),
            sha256=str(data["sha256"]),
        )


def fingerprint(path: Path, *, root: Path) -> FileFingerprint:
    stat = path.stat()
    rel = str(path.relative_to(root)).replace("\\", "/")
    # Hash ligero del contenido para detectar cambios reales
    digest = _file_hash(path)
    return FileFingerprint(
        rel_path=rel,
        size=stat.st_size,
        mtime_ns=int(stat.st_mtime_ns),
        sha256=digest,
    )


def _file_hash(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class Manifest:
    """Persistencia del manifiesto en JSON."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: dict[str, FileFingerprint] = {}
        self.load()

    def load(self) -> None:
        if not self.path.is_file():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        items = raw.get("files", [])
        for item in items:
            fp = FileFingerprint.from_dict(item)
            self.entries[fp.rel_path] = fp

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"updated_at": time.time(), "files": [e.to_dict() for e in self.entries.values()]}
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_unchanged(self, fp: FileFingerprint) -> bool:
        prev = self.entries.get(fp.rel_path)
        if prev is None:
            return False
        return prev.sha256 == fp.sha256 and prev.size == fp.size

    def upsert(self, fp: FileFingerprint) -> None:
        self.entries[fp.rel_path] = fp

    def removed_paths(self, current: set[str]) -> set[str]:
        return set(self.entries.keys()) - current
