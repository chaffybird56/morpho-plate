"""Runtime configuration for the ALPR pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    video_path: Path
    watchlist_path: Path | None = None
    detector_model: str = "yolo-v9-s-608-license-plate-end2end"
    window_title: str = "Morpho-Plate ALPR"
    show_window: bool = True
    output_path: Path | None = None
    min_roi_pixels: int = 10
    thumb_width: int = 80
    thumb_height: int = 60
    thumb_margin: int = 15
    quit_key: str = "q"
    builtin_watchlist: set[str] = field(default_factory=set)

    def resolve_watchlist_path(self) -> Path | None:
        if self.watchlist_path is not None:
            return self.watchlist_path
        return None
