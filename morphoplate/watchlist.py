"""Watchlist loading and plate-string normalization."""

from __future__ import annotations

import re
from pathlib import Path


def normalize_plate(text: str) -> str:
    """Uppercase and strip separators for consistent lookup."""
    return re.sub(r"[\s\-]", "", text.upper())


class Watchlist:
    """In-memory set of normalized plate strings."""

    def __init__(self, plates: set[str] | None = None) -> None:
        self._plates = plates or set()

    @classmethod
    def from_iterable(cls, plates: list[str]) -> Watchlist:
        return cls({normalize_plate(p) for p in plates if p.strip()})

    @classmethod
    def from_file(cls, path: Path | str) -> Watchlist:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Watchlist file not found: {path}")

        plates: set[str] = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            plates.add(normalize_plate(line))
        return cls(plates)

    def contains(self, plate_text: str) -> bool:
        return normalize_plate(plate_text) in self._plates

    def __len__(self) -> int:
        return len(self._plates)

    def __iter__(self):
        return iter(self._plates)
