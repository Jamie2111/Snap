"""Snap overlay: pywebview glass window.

Loads the overlay HTML in a native macOS WebKit window with backdrop blur,
real CSS transitions, and inline pause / stop controls. Runs as a subprocess
spawned by main.py.

  stdin  receives JSON snapshots, one per line (state, hero, tip, ...).
  stdout emits control commands the parent reads:
           "SNAP_CONTROL:PAUSE"  -> pause capture, keep session open
           "SNAP_CONTROL:RESUME" -> resume capture
           "SNAP_CONTROL:STOP"   -> end session and render report
"""

from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from typing import Any, Optional


def _html_url() -> str:
    here = Path(__file__).resolve().parent
    return (here / "templates" / "overlay.html").as_uri()


def _apply_macos_window_options(window) -> None:
    """Make the overlay visible across all macOS spaces, even on top of
    full-screen apps. Best-effort; silently no-ops on other platforms."""
    try:
        from AppKit import NSApp, NSWindowCollectionBehaviorCanJoinAllSpaces, NSWindowCollectionBehaviorStationary, NSScreenSaverWindowLevel
        # pywebview stores the NSWindow on the window object once shown
        ns_window = getattr(window, "native", None) or getattr(window, "_pywebview_window", None)
        if ns_window is None:
            # Walk the NSApp window list for the topmost frontmost panel
            for w in NSApp.windows():
                if w.title() == window.title:
                    ns_window = w
                    break
        if ns_window is None:
            return
        ns_window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorStationary
        )
        # Float above full-screen apps and Spaces transitions
        ns_window.setLevel_(NSScreenSaverWindowLevel)
    except Exception:
        pass


class _OverlayApi:
    """JS-callable bridge. Commands from the overlay UI come here and are
    forwarded to the parent process via stdout."""

    def send_command(self, cmd: str) -> None:
        sys.stdout.write(f"SNAP_CONTROL:{cmd}\n")
        sys.stdout.flush()


def run_overlay() -> None:
    try:
        import webview
    except ImportError:
        sys.stderr.write(
            "pywebview not installed. Run: pip install pywebview\n"
        )
        return

    api = _OverlayApi()
    # NOTE: we intentionally do NOT use transparent=True here. On macOS that
    # combination with frameless can leave the window invisible if anything
    # in the HTML load fails. Instead the window is opaque-dark and the
    # CSS body paints the glass effect on top. Much more reliable.
    window = webview.create_window(
        title="Snap",
        url=_html_url(),
        width=360,
        height=180,
        x=24,
        y=24,
        frameless=True,
        easy_drag=True,
        on_top=True,
        js_api=api,
        background_color="#0b0b0d",
    )

    def stdin_reader() -> None:
        """Forward JSON snapshots from stdin into the HTML window."""
        for raw in sys.stdin:
            line = raw.strip()
            if not line:
                continue
            try:
                snap = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                window.evaluate_js(f"window.snap_update && window.snap_update({json.dumps(snap)})")
            except Exception:
                pass

    def on_shown() -> None:
        _apply_macos_window_options(window)
        threading.Thread(target=stdin_reader, daemon=True).start()

    window.events.shown += on_shown
    try:
        webview.start(debug=False)
    except SystemExit:
        pass


if __name__ == "__main__":
    run_overlay()
