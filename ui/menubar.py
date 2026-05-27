"""macOS menu bar status app.

Subtle, glanceable. Title in the menu bar shows a recording dot plus elapsed
time. Click for a dropdown menu with hero, frames, events, and a Stop action.

Runs the rumps event loop on the main thread, so the capture loop must be
in a background thread. main.py handles the threading.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional

from ui.live_state import LiveState

log = logging.getLogger(__name__)


def _format_clock(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


def run(state: LiveState, on_stop: Optional[Callable[[], None]] = None) -> None:
    """Start the menu bar app on the main thread. Blocks until the user quits
    the app from the menu (or the capture loop signals stop_event)."""

    try:
        import rumps
    except ImportError:
        log.warning("rumps not installed; menu bar UI disabled")
        return

    class SnapBar(rumps.App):
        def __init__(self):
            super().__init__("Snap", title="●", quit_button=None)
            self.menu = [
                "Hero: —",
                "Frames: 0",
                "Events: —",
                rumps.separator,
                rumps.MenuItem("Stop session", callback=self._stop),
                rumps.MenuItem("Quit Snap", callback=self._quit),
            ]
            self._stopped = False
            self._timer = rumps.Timer(self._tick, 1.0)
            self._timer.start()

        def _tick(self, _sender):
            snap = state.snapshot()
            if snap.recording:
                # Pulse the dot in the title for visual heartbeat
                dot = "●" if (int(time.time()) % 2 == 0) else "○"
                self.title = f"{dot} {_format_clock(snap.elapsed_seconds)}"
            else:
                self.title = "○"
            self.menu["Hero: —"].title = f"Hero: {snap.hero.title() if snap.hero else '—'}"
            self.menu["Frames: 0"].title = f"Frames: {snap.frames_seen:,}"
            self.menu["Events: —"].title = (
                f"{snap.deaths} death(s)  ·  {snap.ults_used} ult(s)  ·  {snap.ults_wasted} wasted"
            )

        def _stop(self, _sender):
            if self._stopped:
                return
            self._stopped = True
            if on_stop:
                threading.Thread(target=on_stop, daemon=True).start()

        def _quit(self, _sender):
            if on_stop and not self._stopped:
                self._stopped = True
                on_stop()
            rumps.quit_application()

    SnapBar().run()
