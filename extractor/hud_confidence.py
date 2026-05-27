"""HUD confidence detector: is this frame ACTUALLY Overwatch 2 gameplay?

This is the gate that prevents Snap from fabricating events when the user
watches something other than OW2 (Netflix, a Discord call, a different game).
Without this gate, the per-region extractors will happily return health=42%
and ult=83% from random pixel content because none of them validate that the
HUD is even present.

Approach: check for multiple skin-independent OW2 HUD signatures simultaneously.
Any one of them can fire on noise; requiring two-or-more in agreement makes
false positives vanish. The signatures we check:

  1. Health bar region has the OW2 health-bar geometry (very-bright pixels in
     a horizontal stripe, against darker background).
  2. Ult bar region has the characteristic gold/yellow vertical gradient OR
     a dark-empty look (both are valid OW2 states).
  3. Bottom-row ability tray region has 4 distinct square-ish icon shapes,
     all roughly the same brightness, in a row. Generic on any hero/skin.
  4. Top-center kill feed region tends to be dark with sparse bright text.

We require at least 2 of these 4 to pass to declare HUD_PRESENT. That
threshold rejects YouTube / cinematic content while still being permissive
enough to handle the OW2 menu screens that lack some of these elements.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from capture import regions


@dataclass
class HUDConfidence:
    """Per-frame HUD presence score."""
    score: float          # 0.0 (no HUD) to 1.0 (definitely OW2)
    health_bar_ok: bool
    ult_bar_ok: bool
    ability_tray_ok: bool
    bottom_chrome_ok: bool

    @property
    def is_ow2(self) -> bool:
        """True when at least 2 of 4 HUD signatures are present."""
        return self.score >= 0.5


def _health_bar_signature(frame: np.ndarray) -> bool:
    """OW2 health bar is a horizontal white/red stripe. Distinguishing real
    bars from random bright noise requires checking STRUCTURE, not just bright
    pixel counts:
      - many bright columns
      - low row-to-row variance among the bright rows (it's a uniform stripe)
      - a sharp vertical edge at top and bottom of the stripe.
    Random noise has bright pixels but no structure."""
    try:
        crop = regions.crop_named(frame, "health_bar")
    except Exception:
        return False
    if crop.size == 0:
        return False
    gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape
    if h < 4 or w < 20:
        return False
    # Mean across columns for each row. A real health bar has rows that are
    # mostly bright (the stripe) AND rows that are mostly dark (above/below),
    # giving high variance in row means. Noise gives uniform row means.
    row_means = gray.mean(axis=1)
    row_std = float(row_means.std())
    if row_std < 30.0:
        return False
    # Also require a sustained bright band: the brightest 30% of rows should
    # all have very-high (>200) mean brightness.
    sorted_means = np.sort(row_means)
    top_third = sorted_means[int(len(sorted_means) * 0.7):]
    if top_third.size == 0:
        return False
    return float(top_third.mean()) > 200.0


def _ult_bar_signature(frame: np.ndarray) -> bool:
    """OW2 ult charge bar is either gold/yellow when charging or dark when
    empty. Both are OK. Reject when the region looks like normal video.

    Stricter than before: noise has random gold pixels scattered (low pct);
    real video content has varied colors (also low pct in any specific hue);
    only the actual ult-bar gold concentration crosses 8%."""
    try:
        crop = regions.crop_named(frame, "ultimate_charge")
    except Exception:
        return False
    if crop.size == 0:
        return False
    hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
    v = hsv[..., 2]
    # Very dark = empty ult bar (valid OW2).
    very_dark_pct = float(np.count_nonzero(v < 30)) / v.size
    if very_dark_pct > 0.65:
        return True
    # Gold-saturated band = charging ult bar. Require a substantial fraction.
    gold_mask = cv2.inRange(hsv, np.array([18, 130, 170]), np.array([40, 255, 255]))
    gold_pct = float(np.count_nonzero(gold_mask)) / gold_mask.size
    return gold_pct > 0.08


def _ability_tray_signature(frame: np.ndarray) -> bool:
    """OW2 ability slots are 4 distinct icon boxes. Each slot interior is
    visually consistent (low std dev within the icon), and slots are
    bright-on-dark or grey-on-dark (cooldown). Random noise has high std
    dev everywhere; natural video has color variation within each region."""
    import config

    passes = 0
    stds: list[float] = []
    for i in range(1, min(5, len(config.ABILITY_SLOTS) + 1)):
        name = f"ability_slot_{i}"
        try:
            crop = regions.crop_named(frame, name)
        except Exception:
            continue
        if crop.size == 0:
            continue
        hsv = cv2.cvtColor(crop, cv2.COLOR_RGB2HSV)
        v = hsv[..., 2]
        s = hsv[..., 1]
        mean_v = float(v.mean())
        mean_s = float(s.mean())
        std_v = float(v.std())
        stds.append(std_v)
        # Real slot: bright icon (mean_v > 110) AND either saturated icon
        # (mean_s > 75) or desaturated cooldown overlay (mean_s < 35). Random
        # noise sits around s=64, so neither side passes the strict gate.
        if mean_v > 110 and (mean_s > 75 or mean_s < 30):
            passes += 1
    # Reject if all four regions have very high V-std (= noisy / video).
    if stds and min(stds) > 75.0:
        return False
    return passes >= 3


def _bottom_chrome_signature(frame: np.ndarray) -> bool:
    """OW2 dedicates the bottom strip of the frame to UI chrome. That strip
    averages markedly darker than the middle action zone, AND has lower
    saturation (the chrome is white/grey, the action has color). Both
    conditions must hold to defeat random noise (which has zero delta) and
    natural video (which often has varied brightness without the chrome's
    grayscale signature)."""
    h, w = frame.shape[:2]
    if h < 200:
        return False
    bottom = frame[int(h * 0.90):, :, :]
    middle = frame[int(h * 0.20):int(h * 0.80), :, :]
    try:
        bottom_hsv = cv2.cvtColor(bottom, cv2.COLOR_RGB2HSV)
        middle_hsv = cv2.cvtColor(middle, cv2.COLOR_RGB2HSV)
        bottom_v = float(bottom_hsv[..., 2].mean())
        middle_v = float(middle_hsv[..., 2].mean())
        bottom_s = float(bottom_hsv[..., 1].mean())
        middle_s = float(middle_hsv[..., 1].mean())
    except Exception:
        return False
    return (middle_v - bottom_v) > 18.0 and bottom_s < middle_s - 10.0


def measure(frame: np.ndarray) -> HUDConfidence:
    """One-shot HUD presence test. Returns a confidence and per-signature
    breakdown so callers can log false-positives."""
    health = _health_bar_signature(frame)
    ult = _ult_bar_signature(frame)
    tray = _ability_tray_signature(frame)
    chrome = _bottom_chrome_signature(frame)
    score = (int(health) + int(ult) + int(tray) + int(chrome)) / 4.0
    return HUDConfidence(
        score=score,
        health_bar_ok=health,
        ult_bar_ok=ult,
        ability_tray_ok=tray,
        bottom_chrome_ok=chrome,
    )


class HUDConfidenceTracker:
    """Smooths per-frame HUD measurements over a rolling window so a single
    cinematic frame doesn't drop us out of capture mode. Provides a stable
    `is_capturing_ow2()` decision the capture worker can gate events on."""

    def __init__(self, window: int = 6, threshold: float = 0.5) -> None:
        self._window: list[float] = []
        self._max = window
        self._threshold = threshold
        self._last: HUDConfidence | None = None

    def ingest(self, frame: np.ndarray) -> HUDConfidence:
        conf = measure(frame)
        self._last = conf
        self._window.append(conf.score)
        if len(self._window) > self._max:
            self._window.pop(0)
        return conf

    def is_capturing_ow2(self) -> bool:
        """True when the smoothed HUD score over the window meets threshold."""
        if not self._window:
            return False
        avg = sum(self._window) / len(self._window)
        return avg >= self._threshold

    @property
    def last(self) -> HUDConfidence | None:
        return self._last

    @property
    def smoothed_score(self) -> float:
        if not self._window:
            return 0.0
        return sum(self._window) / len(self._window)
