"""Frame overlays: bounding boxes, labels, and morphology explainability thumbnails."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import cv2
import numpy as np

from morphoplate.morphology.pipeline import MorphologyStep, StepImage

Color = tuple[int, int, int]


@dataclass(frozen=True)
class PlateStyle:
    match_color: Color = (0, 255, 0)
    watchlist_color: Color = (0, 0, 255)
    box_thickness: int = 3
    font_scale: float = 1.2
    font_thickness: int = 3


def draw_detection_overlay(
    frame: np.ndarray,
    *,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    plate_text: str,
    confidence: float,
    is_watchlist_hit: bool,
    style: PlateStyle | None = None,
) -> None:
    """Draw plate bounding box and OCR label banner on frame (in-place)."""
    style = style or PlateStyle()
    color = style.watchlist_color if is_watchlist_hit else style.match_color

    x1i, y1i, x2i, y2i = int(x1), int(y1), int(x2), int(y2)
    cv2.rectangle(frame, (x1i, y1i), (x2i, y2i), color, style.box_thickness)

    label = f"{plate_text} ({confidence:.2f})"
    (tw, th), _ = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, style.font_scale, style.font_thickness
    )
    text_x = x1i
    text_y = max(y1i - 10, th + 10)
    cv2.rectangle(
        frame,
        (text_x - 5, text_y - th - 10),
        (text_x + tw + 5, text_y + 5),
        (255, 255, 255),
        -1,
    )
    cv2.putText(
        frame,
        label,
        (text_x, text_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        style.font_scale,
        (0, 0, 0),
        style.font_thickness,
    )


def _to_bgr_thumbnail(
    image: StepImage,
    width: int,
    height: int,
) -> np.ndarray:
    if len(image.shape) == 2:
        bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        bgr = image.copy()
    return cv2.resize(bgr, (width, height), interpolation=cv2.INTER_AREA)


def render_morphology_thumbnails(
    frame: np.ndarray,
    steps: Sequence[MorphologyStep],
    *,
    anchor_x: int,
    anchor_y: int,
    thumb_width: int = 80,
    thumb_height: int = 60,
    margin: int = 15,
) -> None:
    """Stack morphology step thumbnails above a detection (in-place)."""
    if not steps:
        return

    thumbs = [
        _to_bgr_thumbnail(step.image, thumb_width, thumb_height) for step in steps
    ]
    total_height = len(thumbs) * (thumb_height + margin)
    top_overlay = max(0, anchor_y - total_height - 40)

    left_overlay = anchor_x
    right_overlay = left_overlay + thumb_width
    if right_overlay > frame.shape[1]:
        right_overlay = frame.shape[1]
        left_overlay = max(0, right_overlay - thumb_width)

    current_y = top_overlay
    for thumb in thumbs:
        h_, w_ = thumb.shape[:2]
        bottom_y = current_y + h_
        if bottom_y > frame.shape[0]:
            break
        frame[current_y:bottom_y, left_overlay : left_overlay + w_] = thumb
        current_y += h_ + margin
