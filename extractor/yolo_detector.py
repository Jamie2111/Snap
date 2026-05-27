"""ML-based character detection via YOLO.

This is layer 2 of the vision roadmap. Out of the box, this module uses a
pretrained YOLOv8n that ships with the ultralytics package; it detects
"person" boxes which serve as enemy-character localizations in Overwatch 2
gameplay. That removes the dependency on the in-game outline color setting
that the classical EnemyOutlineDetector requires.

Drop-in design: HeroYOLODetector implements the same Detector protocol as
extractor.vision.EnemyOutlineDetector. The VisionPipeline tries YOLO first
when ultralytics is installed and a model is available, and falls back to
the classical HSV detector otherwise. Either path produces Detections with
the same shape so downstream consumers (AimTracker, mechanics feedback)
work either way.

Fine-tuning on labeled OW2 data turns this into per-hero classification
(Tracer at (x,y) vs Brigitte at (x,y)). See VISION_ROADMAP.md for the data
collection plan. For tonight, "person bbox + confidence" is the upgrade.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

log = logging.getLogger(__name__)

# Confidence threshold below which we discard detections. Pretrained YOLOv8
# is conservative on game characters by default; 0.25 catches OW2 character
# silhouettes reliably while rejecting most background noise.
_DEFAULT_CONFIDENCE = 0.25

# COCO class IDs we treat as enemy characters. Pretrained YOLOv8 was trained
# on humans, so "person" (class 0) is the closest match for OW2 characters.
# After fine-tuning on labeled OW2 frames, we'll have per-hero class IDs.
_CHARACTER_CLASS_IDS: set[int] = {0}  # person


def is_available() -> bool:
    """True if ultralytics is importable. Used by the pipeline to decide
    between YOLO and classical CV at startup. Cheap; no model load."""
    try:
        import ultralytics  # noqa: F401
        return True
    except Exception:
        return False


def _resolve_model_path() -> str:
    """Pick the YOLO weights file. Search order:
        1. $SNAP_YOLO_WEIGHTS env var (if set, must exist)
        2. data/models/snap-ow2.pt (fine-tuned weights when the user trains one)
        3. yolov8n.pt (downloaded automatically by ultralytics on first run)
    """
    env_path = os.environ.get("SNAP_YOLO_WEIGHTS")
    if env_path and Path(env_path).exists():
        return env_path
    try:
        import config
        fine_tuned = config.BASE_DIR / "data" / "models" / "snap-ow2.pt"
        if fine_tuned.exists():
            return str(fine_tuned)
    except Exception:
        pass
    return "yolov8n.pt"


class HeroYOLODetector:
    """YOLO-based replacement for EnemyOutlineDetector.

    Lazy-loads the YOLO model on first detect() call so import time stays
    cheap. If ultralytics is missing or the model can't load, every detect()
    returns [] and a one-time warning is logged - the pipeline's classical
    fallback takes over from there."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence: float = _DEFAULT_CONFIDENCE,
        max_detections: int = 12,
        device: str = "cpu",
    ) -> None:
        self.model_path = model_path or _resolve_model_path()
        self.confidence = confidence
        self.max_detections = max_detections
        self.device = device
        self._model = None
        self._load_failed = False

    @property
    def model_available(self) -> bool:
        return self._model is not None

    def _ensure_model(self) -> bool:
        """Lazy-load the YOLO model. Returns True on success."""
        if self._model is not None:
            return True
        if self._load_failed:
            return False
        try:
            from ultralytics import YOLO  # type: ignore[import-not-found]
            self._model = YOLO(self.model_path)
            log.info(
                "YOLO model loaded (path=%s, device=%s, conf=%.2f)",
                self.model_path, self.device, self.confidence,
            )
            return True
        except Exception as e:
            log.warning(
                "YOLO model load failed (%s); falling back to classical CV. "
                "Install ultralytics + download weights to enable: pip install ultralytics",
                e,
            )
            self._load_failed = True
            return False

    def detect(self, frame: np.ndarray) -> list:
        """Run inference on one RGB frame. Returns Detection-shaped dicts that
        the VisionPipeline merges into its bundle. Returns [] gracefully on
        any error so the classical fallback isn't blocked."""
        from extractor.vision import Detection  # local import; avoid cycles

        if not self._ensure_model():
            return []
        try:
            # ultralytics expects BGR or RGB; pass our RGB frame as-is. The
            # model is fast enough at 640px input that we don't need to
            # downscale per-frame.
            results = self._model.predict(
                frame, conf=self.confidence, max_det=self.max_detections,
                device=self.device, verbose=False,
            )
        except Exception:
            log.exception("YOLO inference failed")
            return []
        out = []
        for r in results:
            try:
                boxes = r.boxes
                if boxes is None:
                    continue
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i].item())
                    if cls_id not in _CHARACTER_CLASS_IDS:
                        continue
                    conf = float(boxes.conf[i].item())
                    xyxy = boxes.xyxy[i].tolist()
                    x1, y1, x2, y2 = (int(v) for v in xyxy)
                    w = max(1, x2 - x1)
                    h = max(1, y2 - y1)
                    cx = x1 + w // 2
                    cy = y1 + h // 2
                    out.append(Detection(
                        kind="enemy_outline",  # matches classical detector's kind
                        confidence=conf,
                        bbox=(x1, y1, w, h),
                        center=(cx, cy),
                        meta={"source": "yolo", "class_id": cls_id, "area": w * h},
                    ))
            except Exception:
                log.exception("YOLO result parsing failed")
                continue
        return out
