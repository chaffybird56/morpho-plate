"""Classical morphological enhancement chain for license-plate OCR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import cv2
import numpy as np

StepImage = np.ndarray


@dataclass(frozen=True)
class MorphologyStep:
    """A labeled snapshot from the enhancement pipeline."""

    title: str
    image: StepImage


def morphological_pipeline(
    roi: StepImage,
    *,
    blur_kernel: tuple[int, int] = (3, 3),
    dilate_kernel: tuple[int, int] = (2, 2),
    dilate_iterations: int = 1,
) -> list[MorphologyStep]:
    """Run grayscale → blur → Otsu → dilate → invert on a plate crop.

    Returns labeled snapshots suitable for OCR input and explainability thumbnails.
    """
    if roi.size == 0:
        return []

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, blur_kernel, 0)
    _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, dilate_kernel)
    dilated = cv2.dilate(otsu, kernel, iterations=dilate_iterations)
    inverted = 255 - dilated

    return [
        MorphologyStep("Gray", gray.copy()),
        MorphologyStep("Blur", blur.copy()),
        MorphologyStep("Otsu", otsu.copy()),
        MorphologyStep("Dilate", dilated.copy()),
        MorphologyStep("Invert", inverted.copy()),
    ]


def steps_as_tuples(steps: Sequence[MorphologyStep]) -> list[tuple[str, StepImage]]:
    """Backward-compatible (title, image) pairs for legacy callers."""
    return [(step.title, step.image) for step in steps]
