"""Aim analysis. Combines crosshair position + enemy outline detections to
compute frame-by-frame aim metrics: distance to nearest enemy, fraction of
frames on-target, average miss distance.

Designed as a stateful aggregator: feed it one VisionBundle per frame, query
.snapshot() at the end of the session for the final metrics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

from extractor.vision import Detection, VisionBundle


@dataclass
class AimMetrics:
    frames_with_enemy_in_sight: int = 0
    frames_on_target: int = 0
    total_miss_distance: float = 0.0
    miss_samples: int = 0
    min_miss_distance: float = float("inf")
    max_miss_distance: float = 0.0
    near_misses: int = 0  # within 100 px (very close but not on target)

    @property
    def on_target_pct(self) -> float:
        if not self.frames_with_enemy_in_sight:
            return 0.0
        return self.frames_on_target / self.frames_with_enemy_in_sight

    @property
    def avg_miss_distance(self) -> float:
        if not self.miss_samples:
            return 0.0
        return self.total_miss_distance / self.miss_samples


class AimTracker:
    """Streaming aim tracker. Per frame: find nearest enemy outline center to
    crosshair, compute pixel distance, count as on-target if distance < radius."""

    def __init__(self, on_target_radius_px: int = 40):
        self.on_target_radius = on_target_radius_px
        self.metrics = AimMetrics()

    def ingest(self, bundle: VisionBundle) -> None:
        if bundle.crosshair is None or bundle.crosshair.center is None:
            return
        if not bundle.enemy_outlines:
            return
        self.metrics.frames_with_enemy_in_sight += 1
        cx, cy = bundle.crosshair.center
        nearest = self._nearest_enemy(cx, cy, bundle.enemy_outlines)
        if nearest is None:
            return
        ex, ey = nearest.center  # guaranteed by detector
        dist = math.hypot(ex - cx, ey - cy)
        self.metrics.total_miss_distance += dist
        self.metrics.miss_samples += 1
        self.metrics.min_miss_distance = min(self.metrics.min_miss_distance, dist)
        self.metrics.max_miss_distance = max(self.metrics.max_miss_distance, dist)
        if dist <= self.on_target_radius:
            self.metrics.frames_on_target += 1
        elif dist <= 100:
            self.metrics.near_misses += 1

    @staticmethod
    def _nearest_enemy(cx: int, cy: int, enemies: list[Detection]) -> Optional[Detection]:
        best: Optional[Detection] = None
        best_dist = float("inf")
        for e in enemies:
            if e.center is None:
                continue
            ex, ey = e.center
            d = math.hypot(ex - cx, ey - cy)
            if d < best_dist:
                best_dist = d
                best = e
        return best

    def snapshot(self) -> AimMetrics:
        m = self.metrics
        if m.min_miss_distance == float("inf"):
            m.min_miss_distance = 0.0
        return m
