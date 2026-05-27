"""Auto-detect the gameplay viewport inside a captured frame.

When the user is running OW2 fullscreen at 1920x1080 on their primary
monitor, the captured frame IS the gameplay. No detection needed.

But when they're testing on a YouTube video in a browser, the gameplay
rectangle is a 16:9 region inside a Chrome window, surrounded by browser
chrome (tabs, address bar) and the macOS menu bar / dock. The HUD region
coords break completely because they assume the game fills the screen.

This module finds the largest 16:9 darkish rectangle in a frame and
returns its (x, y, w, h). The capture loop then crops to that region and
resizes to 1920x1080 before HUD extraction. After the first detection we
cache the result so we're not re-detecting every frame.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Viewport:
    x: int
    y: int
    w: int
    h: int

    @property
    def is_fullscreen(self) -> bool:
        return self.x == 0 and self.y == 0 and self.w >= 1900 and self.h >= 1060

    def crop(self, frame: np.ndarray) -> np.ndarray:
        return frame[self.y : self.y + self.h, self.x : self.x + self.w]


def detect_viewport(frame: np.ndarray, target_aspect: float = 16 / 9) -> Optional[Viewport]:
    """Find the largest 16:9 darker-than-surroundings rectangle. Heuristic:
        1. Downscale for speed.
        2. Threshold to a binary mask of "darker than average" pixels.
        3. Find external contours.
        4. Pick the largest that's at least 30% of frame area AND has aspect
           ratio within 8% of 16:9.

    Returns None if nothing convincing is found, signalling the caller to
    treat the entire frame as the viewport.
    """
    h, w = frame.shape[:2]
    if h == 0 or w == 0:
        return None

    # Downscale to ~640 wide for fast contour work
    scale = 640.0 / w if w > 640 else 1.0
    small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale != 1.0 else frame.copy()
    sh, sw = small.shape[:2]

    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    # Anything notably darker than the median is part of the gameplay
    # region. OW2 frames have plenty of dark areas (sky, shadows, HUD
    # background) so this works without being TOO specific.
    median = float(np.median(gray))
    threshold = max(20.0, median * 0.55)
    mask = (gray < threshold).astype(np.uint8) * 255
    # Close gaps so a single dark rectangle dominates
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    frame_area = sw * sh
    candidates: list[tuple[int, int, int, int, float]] = []
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        area = cw * ch
        if area < 0.20 * frame_area:
            continue
        if ch == 0:
            continue
        aspect = cw / ch
        # Allow either 16:9 (game) or near-square (avoid full-screen wallpapers)
        if abs(aspect - target_aspect) / target_aspect > 0.12:
            continue
        candidates.append((x, y, cw, ch, area))

    if not candidates:
        return None
    candidates.sort(key=lambda t: t[4], reverse=True)
    bx, by, bw, bh, _ = candidates[0]
    # Scale coords back to original frame size
    inv = 1.0 / scale
    return Viewport(
        x=int(bx * inv),
        y=int(by * inv),
        w=int(bw * inv),
        h=int(bh * inv),
    )


class ViewportCache:
    """One-time detection + caching. The capture loop calls .ensure(frame)
    every frame; the first call detects, subsequent calls return the cached
    Viewport. If the frame dimensions change mid-session (e.g. window
    resized), the cache invalidates and we re-detect."""

    def __init__(self) -> None:
        self._viewport: Optional[Viewport] = None
        self._frame_shape: Optional[tuple[int, int]] = None
        self._tried_detect: bool = False

    def ensure(self, frame: np.ndarray) -> Optional[Viewport]:
        h, w = frame.shape[:2]
        if self._frame_shape != (h, w):
            self._viewport = None
            self._tried_detect = False
            self._frame_shape = (h, w)
        if not self._tried_detect:
            self._tried_detect = True
            try:
                detected = detect_viewport(frame)
            except Exception:
                log.exception("Viewport detection failed")
                detected = None
            if detected is not None and not detected.is_fullscreen:
                log.info(
                    "Viewport auto-detected: x=%d y=%d w=%d h=%d (frame %dx%d)",
                    detected.x, detected.y, detected.w, detected.h, w, h,
                )
                self._viewport = detected
            else:
                log.info("Treating full frame as viewport (no smaller region detected)")
        return self._viewport

    def normalize(self, frame: np.ndarray) -> np.ndarray:
        """Return a 1920x1080 RGB frame: either the auto-detected gameplay
        viewport resized, or the input itself if it's already 1920x1080.
        Always returns the same shape so downstream extractors don't care."""
        target = (1920, 1080)
        vp = self.ensure(frame)
        if vp is not None and not vp.is_fullscreen:
            try:
                cropped = vp.crop(frame)
                if cropped.size > 0:
                    return cv2.resize(cropped, target, interpolation=cv2.INTER_AREA)
            except Exception:
                pass
        h, w = frame.shape[:2]
        if (w, h) == target:
            return frame
        return cv2.resize(frame, target, interpolation=cv2.INTER_AREA)
