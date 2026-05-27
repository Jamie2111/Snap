"""Screen capture loop.

Live mode (Windows): uses mss to capture frames and pywin32 to check the active
window. Stops capturing when Overwatch 2 loses focus.

Replay mode (any platform): yields frames from a directory of saved PNGs.

Frames produced by the loop are emitted as a stream of (timestamp, frame, in_focus)
tuples. The caller decides what to do with them (extract state, save to disk).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import mss
import numpy as np
from PIL import Image

import config

log = logging.getLogger(__name__)


@dataclass
class CaptureFrame:
    timestamp: float
    frame: np.ndarray
    in_focus: bool


@dataclass
class SessionRecord:
    session_id: str
    start_time: float
    end_time: float | None = None
    hero_played: str | None = None
    map_name: str | None = None
    frame_count: int = 0
    raw_events: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "hero_played": self.hero_played,
            "map_name": self.map_name,
            "frame_count": self.frame_count,
            "raw_events": self.raw_events,
        }


def _windows_active_window_title() -> str:
    if not config.IS_WINDOWS:
        return ""
    try:
        import win32gui  # type: ignore[import-not-found]

        hwnd = win32gui.GetForegroundWindow()
        return win32gui.GetWindowText(hwnd) or ""
    except Exception:
        log.exception("Could not read active window title")
        return ""


def is_overwatch_focused() -> bool:
    """True if OW2 is the foreground window. Always True off-Windows so the
    caller can decide what to do (replay mode does not need focus checks)."""
    if not config.IS_WINDOWS:
        return True
    title = _windows_active_window_title()
    return any(frag.lower() in title.lower() for frag in config.OW2_WINDOW_TITLE_FRAGMENTS)


def _screen_capture_iter(fps: int) -> Iterator[CaptureFrame]:
    import cv2  # used for resize on Retina / non-1080p displays

    interval = 1.0 / max(fps, 1)
    next_tick = time.monotonic()
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            in_focus = is_overwatch_focused()
            ts = time.time()
            shot = sct.grab(monitor)
            frame = np.array(shot)[:, :, :3][:, :, ::-1].copy()
            h, w = frame.shape[:2]
            if (w, h) != (1920, 1080):
                frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_AREA)
            yield CaptureFrame(timestamp=ts, frame=frame, in_focus=in_focus)
            next_tick += interval
            sleep_for = next_tick - time.monotonic()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                next_tick = time.monotonic()


def live_capture(
    save_frames: bool = True,
    fps: int = config.CAPTURE_FPS,
    stop_after_seconds_unfocused: float = 5.0,
) -> Iterator[tuple[CaptureFrame, SessionRecord, Path]]:
    """Live capture loop. Yields one CaptureFrame at a time along with the
    current SessionRecord and its on-disk directory. Stops when OW2 has been
    unfocused for `stop_after_seconds_unfocused` seconds.

    Wraps each iteration in try/except so a single bad frame never kills the
    capture (per spec rule: never crash)."""

    session_id = uuid.uuid4().hex[:12]
    session_dir = config.SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    frames_dir = session_dir / "frames"
    frames_dir.mkdir(exist_ok=True)
    record = SessionRecord(session_id=session_id, start_time=time.time())

    log.info("Starting live capture session %s -> %s", session_id, session_dir)

    last_focused = time.monotonic()
    try:
        for cf in _screen_capture_iter(fps=fps):
            try:
                if cf.in_focus:
                    last_focused = time.monotonic()
                    record.frame_count += 1
                    if save_frames:
                        path = frames_dir / f"{cf.timestamp:.3f}.png"
                        Image.fromarray(cf.frame).save(path)
                    yield cf, record, session_dir
                else:
                    if time.monotonic() - last_focused > stop_after_seconds_unfocused:
                        log.info("OW2 unfocused for >%ss, ending session", stop_after_seconds_unfocused)
                        break
            except Exception:
                log.exception("Capture iteration failed; continuing")
    finally:
        record.end_time = time.time()
        write_session_manifest(session_dir, record)
        log.info(
            "Session %s ended. Frames captured: %d", session_id, record.frame_count
        )


def write_session_manifest(session_dir: Path, record: SessionRecord) -> None:
    manifest = session_dir / "session.json"
    with manifest.open("w") as f:
        json.dump(record.to_dict(), f, indent=2, default=str)


def replay_iter(session_dir: Path) -> Iterator[CaptureFrame]:
    """Yield CaptureFrames from a directory of saved PNG frames, ordered by
    timestamp. The timestamp comes from the filename ('<unix_ts>.png')."""

    session_dir = Path(session_dir)
    frames_dir = session_dir / "frames" if (session_dir / "frames").exists() else session_dir
    paths = sorted(frames_dir.glob("*.png"))
    log.info("Replaying %d frames from %s", len(paths), frames_dir)
    for p in paths:
        try:
            ts = float(p.stem)
        except ValueError:
            ts = p.stat().st_mtime
        img = np.array(Image.open(p).convert("RGB"))
        yield CaptureFrame(timestamp=ts, frame=img, in_focus=True)


def video_iter(video_path: Path, fps: int = 2) -> Iterator[CaptureFrame]:
    """Yield CaptureFrames from a video file at the given fps.

    Works on any MP4 / MOV / MKV / WebM that OpenCV can decode. Frames are
    auto-resized to 1920x1080 to match the HUD region coords, so YouTube
    downloads at any resolution work as long as the underlying gameplay was
    recorded at 16:9 with the default HUD.
    """
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise FileNotFoundError(f"Could not open video: {video_path}")
    video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    skip = max(1, int(round(video_fps / max(fps, 1))))
    log.info(
        "Video %s: %.1f fps, %d frames, sampling every %d frame(s)",
        video_path, video_fps, total_frames, skip,
    )
    frame_idx = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % skip == 0:
                h, w = frame.shape[:2]
                if (w, h) != (1920, 1080):
                    frame = cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_AREA)
                # cv2 returns BGR; rest of the pipeline expects RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ts = frame_idx / video_fps
                yield CaptureFrame(timestamp=ts, frame=frame_rgb, in_focus=True)
            frame_idx += 1
    finally:
        cap.release()


def synthesize_blank_frame(width: int = 1920, height: int = 1080) -> np.ndarray:
    return np.zeros((height, width, 3), dtype=np.uint8)
