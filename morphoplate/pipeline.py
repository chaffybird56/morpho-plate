"""Video processing loop orchestrating detection, morphology, and overlays."""

from __future__ import annotations

import cv2
import numpy as np

from morphoplate.alpr.engine import ALPREngine, PlateDetection
from morphoplate.config import Settings
from morphoplate.morphology.pipeline import morphological_pipeline
from morphoplate.viz.overlays import draw_detection_overlay, render_morphology_thumbnails
from morphoplate.watchlist import Watchlist


class VideoPipeline:
    """Process a video source frame-by-frame with ALPR and explainability overlays."""

    def __init__(self, settings: Settings, watchlist: Watchlist) -> None:
        self.settings = settings
        self.watchlist = watchlist
        self.engine = ALPREngine(settings.detector_model)
        self._writer: cv2.VideoWriter | None = None

    def _open_writer(self, frame: np.ndarray) -> None:
        if self.settings.output_path is None:
            return
        h, w = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._writer = cv2.VideoWriter(
            str(self.settings.output_path), fourcc, 25.0, (w, h)
        )

    def _process_detection(self, frame: np.ndarray, det: PlateDetection) -> None:
        is_hit = self.watchlist.contains(det.text)
        draw_detection_overlay(
            frame,
            x1=det.x1,
            y1=det.y1,
            x2=det.x2,
            y2=det.y2,
            plate_text=det.text,
            confidence=det.confidence,
            is_watchlist_hit=is_hit,
        )

        x1i, y1i = int(det.x1), int(det.y1)
        x2i, y2i = int(det.x2), int(det.y2)
        w, h = x2i - x1i, y2i - y1i
        if w <= self.settings.min_roi_pixels or h <= self.settings.min_roi_pixels:
            return

        roi = frame[y1i:y2i, x1i:x2i].copy()
        steps = morphological_pipeline(roi)
        render_morphology_thumbnails(
            frame,
            steps,
            anchor_x=x1i,
            anchor_y=y1i,
            thumb_width=self.settings.thumb_width,
            thumb_height=self.settings.thumb_height,
            margin=self.settings.thumb_margin,
        )

    def run(self) -> int:
        cap = cv2.VideoCapture(str(self.settings.video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {self.settings.video_path}")

        frames_written = 0
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if self._writer is None and self.settings.output_path is not None:
                    self._open_writer(frame)

                for det in self.engine.predict(frame):
                    self._process_detection(frame, det)

                if self._writer is not None:
                    self._writer.write(frame)
                    frames_written += 1

                if self.settings.show_window:
                    cv2.imshow(self.settings.window_title, frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord(self.settings.quit_key):
                        break
        finally:
            cap.release()
            if self._writer is not None:
                self._writer.release()
            if self.settings.show_window:
                cv2.destroyAllWindows()

        return frames_written
