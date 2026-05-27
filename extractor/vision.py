"""Vision detectors for in-game events that the UI does not expose.

Classical-CV implementations (HSV color masks, contour detection, frame
diffs). Designed as a detector framework so ML-based detectors can plug in
later behind the same Detector protocol without changing the call sites.

Current detectors:
    CrosshairLocator     constant: OW2 crosshair is screen center
    EnemyOutlineDetector finds the red/orange enemy-team outline blobs
    AbilityGlowDetector  matches per-ability color signatures (blade green,
                         pulse red flash, transcendence yellow burst, etc.)
    ScreenFlashDetector  large luminance spikes (impacts, shatter, etc.)

See VISION_ROADMAP.md for the ML detectors that would replace these for
true vision-API-grade accuracy.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional, Protocol

import cv2
import numpy as np

log = logging.getLogger(__name__)


@dataclass
class Detection:
    """A single detected thing in a frame."""
    kind: str
    confidence: float
    bbox: Optional[tuple[int, int, int, int]] = None  # x, y, w, h
    center: Optional[tuple[int, int]] = None
    meta: dict = field(default_factory=dict)


class Detector(Protocol):
    """All detectors take a frame, return a list of Detections."""

    def detect(self, frame: np.ndarray) -> list[Detection]: ...


class CrosshairLocator:
    """The OW2 crosshair is fixed at screen center. We do not need to detect
    it visually; we just emit it. Kept as a Detector so other code can treat
    it uniformly with the others."""

    def detect(self, frame: np.ndarray) -> list[Detection]:
        h, w = frame.shape[:2]
        return [Detection(kind="crosshair", confidence=1.0, center=(w // 2, h // 2))]


class EnemyOutlineDetector:
    """Finds bright red/orange outlines OW2 draws around enemy characters by
    default. This depends on the player having default outline color settings.

    Tunable thresholds in __init__. The default red-orange HSV band is wide
    enough to catch most enemy outline colors while rejecting health-bar pink
    and other reds in the UI by requiring high saturation + value."""

    def __init__(
        self,
        min_contour_area: int = 200,
        max_contour_area: int = 100_000,
        hsv_lower=(0, 140, 140),
        hsv_upper=(15, 255, 255),
        hsv_lower2=(165, 140, 140),
        hsv_upper2=(180, 255, 255),
    ):
        self.min_area = min_contour_area
        self.max_area = max_contour_area
        self.hsv_lower = np.array(hsv_lower, dtype=np.uint8)
        self.hsv_upper = np.array(hsv_upper, dtype=np.uint8)
        self.hsv_lower2 = np.array(hsv_lower2, dtype=np.uint8)
        self.hsv_upper2 = np.array(hsv_upper2, dtype=np.uint8)

    def detect(self, frame: np.ndarray) -> list[Detection]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, self.hsv_lower, self.hsv_upper)
        mask |= cv2.inRange(hsv, self.hsv_lower2, self.hsv_upper2)
        # Close small gaps in the outline
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out: list[Detection] = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < self.min_area or area > self.max_area:
                continue
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w // 2, y + h // 2
            out.append(Detection(
                kind="enemy_outline",
                confidence=min(1.0, area / 5000.0),
                bbox=(x, y, w, h),
                center=(cx, cy),
                meta={"area": int(area)},
            ))
        return out


# Per-ult-or-ability color signatures. Each entry is the dominant hue range
# (HSV) of the on-screen effect when the ability fires. These are starting
# values tuned for the default OW2 color profile; a future ML detector would
# replace this with per-ability classifiers.
ABILITY_COLOR_SIGNATURES: dict[str, dict] = {
    "dragonblade": {"hsv_lower": (40, 150, 150), "hsv_upper": (75, 255, 255),
                    "min_pixels_pct": 0.05, "description": "Genji blade green"},
    "primal_rage": {"hsv_lower": (15, 150, 100), "hsv_upper": (30, 255, 255),
                    "min_pixels_pct": 0.08, "description": "Winston angry orange"},
    "nano_boost": {"hsv_lower": (15, 200, 200), "hsv_upper": (35, 255, 255),
                   "min_pixels_pct": 0.04, "description": "Ana nano gold"},
    "transcendence": {"hsv_lower": (20, 100, 200), "hsv_upper": (35, 200, 255),
                      "min_pixels_pct": 0.06, "description": "Zen trans gold burst"},
    "amp_it_up": {"hsv_lower": (90, 100, 150), "hsv_upper": (115, 255, 255),
                  "min_pixels_pct": 0.04, "description": "Lucio amp cyan ring"},
}


class AbilityGlowDetector:
    """Detect per-ability screen glow / overlay color signatures.

    Each call returns 0+ Detections, one per ability whose color signature
    crosses its pixel-fraction threshold this frame."""

    def __init__(self, signatures: Optional[dict] = None):
        self.signatures = signatures or ABILITY_COLOR_SIGNATURES

    def detect(self, frame: np.ndarray) -> list[Detection]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
        total = hsv.shape[0] * hsv.shape[1]
        out: list[Detection] = []
        for ability, spec in self.signatures.items():
            mask = cv2.inRange(
                hsv,
                np.array(spec["hsv_lower"], dtype=np.uint8),
                np.array(spec["hsv_upper"], dtype=np.uint8),
            )
            pct = float(np.count_nonzero(mask)) / float(total)
            if pct >= spec["min_pixels_pct"]:
                out.append(Detection(
                    kind=f"ability_glow:{ability}",
                    confidence=min(1.0, pct / (spec["min_pixels_pct"] * 3.0)),
                    meta={"pct": round(pct, 4), "description": spec.get("description", "")},
                ))
        return out


class ScreenFlashDetector:
    """Large frame-to-frame luminance spike indicates an impact / shatter /
    flashbang / explosion. Stateful: needs the previous frame for diff."""

    def __init__(self, flash_threshold: float = 30.0):
        self.flash_threshold = flash_threshold
        self._prev_mean: Optional[float] = None

    def detect(self, frame: np.ndarray) -> list[Detection]:
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        mean = float(gray.mean())
        out: list[Detection] = []
        if self._prev_mean is not None:
            delta = abs(mean - self._prev_mean)
            if delta >= self.flash_threshold:
                out.append(Detection(
                    kind="screen_flash",
                    confidence=min(1.0, delta / 100.0),
                    meta={"delta": round(delta, 2)},
                ))
        self._prev_mean = mean
        return out


@dataclass
class VisionBundle:
    """One-call vision pass: run all detectors, return the merged list."""

    enemy_outlines: list[Detection] = field(default_factory=list)
    crosshair: Optional[Detection] = None
    ability_glows: list[Detection] = field(default_factory=list)
    screen_flash: Optional[Detection] = None


class VisionPipeline:
    """Orchestrates the standard detector set. Wired into the live capture
    loop as an optional pass that runs every frame. Keep this lightweight;
    classical CV is fast but per-frame allocations matter at 2 fps over
    long sessions.

    Enemy detection has two paths:
      - Primary: HeroYOLODetector (ML, ultralytics) when available. Identifies
        person silhouettes with confidence scores; independent of in-game
        outline color setting.
      - Fallback: EnemyOutlineDetector (HSV + contours). Requires default
        outline color; ships everywhere because it has zero dependencies.

    Both produce Detections with kind='enemy_outline' so downstream code
    (AimTracker, mechanics feedback) is unchanged."""

    def __init__(self, prefer_ml: bool = True):
        self.crosshair = CrosshairLocator()
        self._classical_outlines = EnemyOutlineDetector()
        self._ml_outlines = None
        self._ml_attempted = False
        self.prefer_ml = prefer_ml
        self.ability_glows = AbilityGlowDetector()
        self.screen_flash = ScreenFlashDetector()

    def _detect_enemies(self, frame: np.ndarray) -> list[Detection]:
        """Try YOLO first; fall back to classical CV if YOLO isn't available
        or fails. Tracking which path returned results lets us log once at
        startup so the user knows which detector is active."""
        if self.prefer_ml and not self._ml_attempted:
            self._ml_attempted = True
            try:
                from extractor.yolo_detector import HeroYOLODetector, is_available
                if is_available():
                    self._ml_outlines = HeroYOLODetector()
                    log.info("Vision: ML hero detector available, will try YOLO first")
                else:
                    log.info("Vision: ultralytics not installed, using classical CV detector")
            except Exception:
                log.exception("ML detector init failed; staying on classical CV")
        if self._ml_outlines is not None:
            try:
                ml_out = self._ml_outlines.detect(frame)
                if ml_out:
                    return ml_out
                # YOLO loaded but returned nothing this frame: not necessarily
                # an error (no character on screen). Use classical anyway to
                # catch outline-based silhouettes the ML may have missed.
            except Exception:
                log.exception("YOLO inference threw; using classical CV this frame")
        return self._classical_outlines.detect(frame)

    def process(self, frame: np.ndarray) -> VisionBundle:
        bundle = VisionBundle()
        try:
            bundle.crosshair = self.crosshair.detect(frame)[0]
        except Exception:
            log.exception("crosshair detect failed")
        try:
            bundle.enemy_outlines = self._detect_enemies(frame)
        except Exception:
            log.exception("enemy outline detect failed")
        try:
            bundle.ability_glows = self.ability_glows.detect(frame)
        except Exception:
            log.exception("ability glow detect failed")
        try:
            flashes = self.screen_flash.detect(frame)
            bundle.screen_flash = flashes[0] if flashes else None
        except Exception:
            log.exception("screen flash detect failed")
        return bundle

    @property
    def using_ml(self) -> bool:
        """True when the ML detector loaded successfully. UI / logs can use
        this to surface that the upgraded detector is active."""
        return self._ml_outlines is not None and self._ml_outlines.model_available
