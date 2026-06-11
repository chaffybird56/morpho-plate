"""Thin wrapper around fast-alpr for detector + OCR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    from fast_alpr.alpr import ALPR
except ImportError as exc:  # pragma: no cover - optional at import for unit tests
    ALPR = None  # type: ignore[misc, assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


@dataclass(frozen=True)
class PlateDetection:
    text: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class ALPREngine:
    """Detect license plates and run OCR on video frames."""

    def __init__(self, detector_model: str) -> None:
        if ALPR is None:
            raise ImportError(
                "fast-alpr is required. Install with: pip install fast-alpr"
            ) from _IMPORT_ERROR
        self._alpr = ALPR(detector_model=detector_model)

    def predict(self, frame: np.ndarray) -> list[PlateDetection]:
        results: list[PlateDetection] = []
        for item in self._alpr.predict(frame):
            bbox = item.detection.bounding_box
            results.append(
                PlateDetection(
                    text=item.ocr.text,
                    confidence=float(item.ocr.confidence),
                    x1=float(bbox.x1),
                    y1=float(bbox.y1),
                    x2=float(bbox.x2),
                    y2=float(bbox.y2),
                )
            )
        return results
