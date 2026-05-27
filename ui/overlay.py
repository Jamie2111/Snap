"""Snap overlay: pywebview WebKit window.

Loads the overlay HTML in a native macOS WebKit window. Runs as a subprocess
spawned by the launcher.

  stdin  receives JSON snapshots, one per line (state, hero, tip, ...).
  stdout emits control commands the parent reads:
           "SNAP_CONTROL:PAUSE"
           "SNAP_CONTROL:RESUME"
           "SNAP_CONTROL:STOP"

Anything that crashes here gets written to stderr by the parent's Popen
configuration, which routes stderr to data/sessions/.overlay.log so we can
post-mortem. Never use AppKit / NSApp from background threads.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import traceback
from pathlib import Path


def _html_url() -> str:
    return (Path(__file__).resolve().parent / "templates" / "overlay.html").as_uri()


# Filesystem fallback channel for control commands. The parent process polls
# this file every 200ms. Used as a redundant signal when stdout buffering on
# the macOS subprocess pipe drops STOP commands that were sent before any
# PAUSE/RESUME forced a flush. The parent injects the path via env so it
# matches its watcher.
_CONTROL_FILE = Path(os.environ.get("SNAP_OVERLAY_CONTROL_FILE", "")) if os.environ.get(
    "SNAP_OVERLAY_CONTROL_FILE"
) else None


class _OverlayApi:
    """JS bridge for the overlay's pause / stop buttons. Every command is
    written to BOTH stdout and a control file. Either channel is enough for
    the parent to act on it; redundancy guards against macOS pipe buffering
    eating the first STOP."""

    def send_command(self, cmd: str) -> None:
        cmd = (cmd or "").strip().upper()
        if not cmd:
            return
        try:
            sys.stdout.write(f"SNAP_CONTROL:{cmd}\n")
            sys.stdout.flush()
            # An extra newline forces some buffering policies to ship the line.
            try:
                os.fsync(sys.stdout.fileno())
            except Exception:
                pass
        except Exception:
            sys.stderr.write("send_command stdout write failed\n")
            traceback.print_exc(file=sys.stderr)
        # Filesystem fallback. The parent's signal reader polls this path.
        if _CONTROL_FILE is not None:
            try:
                _CONTROL_FILE.parent.mkdir(parents=True, exist_ok=True)
                # Append so multiple rapid commands aren't lost between polls.
                with _CONTROL_FILE.open("a") as f:
                    f.write(cmd + "\n")
            except Exception:
                sys.stderr.write("send_command signal-file write failed\n")
                traceback.print_exc(file=sys.stderr)


def run_overlay() -> None:
    try:
        import webview
    except ImportError:
        sys.stderr.write(
            "pywebview not installed. Run: pip install pywebview\n"
        )
        return

    try:
        api = _OverlayApi()
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
    except Exception:
        sys.stderr.write("create_window failed\n")
        traceback.print_exc(file=sys.stderr)
        return

    def stdin_reader() -> None:
        """Forward JSON snapshots from stdin into the HTML window. evaluate_js
        is thread-safe in pywebview; calling from this background thread is
        explicitly supported by the API."""
        try:
            for raw in sys.stdin:
                line = raw.strip()
                if not line:
                    continue
                try:
                    snap = json.loads(line)
                except json.JSONDecodeError:
                    continue
                try:
                    window.evaluate_js(
                        f"window.snap_update && window.snap_update({json.dumps(snap)})"
                    )
                except Exception:
                    pass
        except Exception:
            sys.stderr.write("stdin_reader crashed\n")
            traceback.print_exc(file=sys.stderr)

    # Start the reader once the window's loaded event fires.
    def on_loaded() -> None:
        threading.Thread(target=stdin_reader, daemon=True).start()

    try:
        window.events.loaded += on_loaded
    except Exception:
        threading.Timer(0.5, lambda: threading.Thread(target=stdin_reader, daemon=True).start()).start()

    def on_main_thread_post_start() -> None:
        """Runs on macOS main thread after the window is created. Schedules
        a repeating NSTimer (also on the main thread) that re-applies the
        Spaces-spanning collection behavior to every overlay-titled window.

        The retry loop matters because:
          - pywebview can create the NSWindow asynchronously after this
            callback fires, so the first attempt may find no windows.
          - macOS occasionally resets collection behavior when the window
            moves between screens or the dock state changes.
          - pywebview may recreate the window if the page reloads.

        We deliberately do NOT touch AppKit from a Python background thread:
        the user already hit a hard process crash when that happened. NSTimer
        runs on the runloop that scheduled it, which is the main runloop here.
        """
        try:
            from AppKit import (
                NSApp,
                NSWindowCollectionBehaviorCanJoinAllSpaces,
                NSWindowCollectionBehaviorStationary,
                NSWindowCollectionBehaviorFullScreenAuxiliary,
                NSWindowCollectionBehaviorIgnoresCycle,
            )
            from Foundation import NSObject, NSTimer
        except Exception:
            sys.stderr.write("AppKit import failed; overlay will not span Spaces\n")
            traceback.print_exc(file=sys.stderr)
            return

        mask = (
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
            | NSWindowCollectionBehaviorIgnoresCycle
        )
        # NSStatusWindowLevel = 25; above normal windows + full-screen apps.
        target_level = 25

        class _Applier(NSObject):
            """NSTimer target. The selector apply: runs on the main thread."""
            applied_ids = set()

            def apply_(self, _timer):
                try:
                    if NSApp is None:
                        return
                    windows = NSApp.windows()
                    if windows is None:
                        return
                    for w in windows:
                        try:
                            title = str(w.title())
                        except Exception:
                            continue
                        if title != "Snap":
                            continue
                        wid = id(w)
                        # We re-apply every iteration to defeat macOS resets.
                        try:
                            w.setCollectionBehavior_(mask)
                            w.setLevel_(target_level)
                        except Exception:
                            continue
                        try:
                            w.setHidesOnDeactivate_(False)
                        except Exception:
                            pass
                        if wid not in self.applied_ids:
                            self.applied_ids.add(wid)
                            sys.stderr.write(
                                f"Spaces behavior applied to overlay window 0x{wid:x}\n"
                            )
                except Exception:
                    sys.stderr.write("Spaces re-apply tick failed\n")
                    traceback.print_exc(file=sys.stderr)

        applier = _Applier.alloc().init()
        # Keep a strong reference so Python doesn't GC the applier or timer.
        if not hasattr(sys.modules[__name__], "_spaces_applier"):
            setattr(sys.modules[__name__], "_spaces_applier", applier)
        try:
            # First attempt right now (might be too early; that's fine, the
            # repeating timer will catch it within 500ms).
            applier.apply_(None)
            timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.5, applier, "apply:", None, True
            )
            setattr(sys.modules[__name__], "_spaces_timer", timer)
        except Exception:
            sys.stderr.write("Could not schedule Spaces-behavior NSTimer\n")
            traceback.print_exc(file=sys.stderr)

    try:
        webview.start(on_main_thread_post_start, debug=False)
    except SystemExit:
        pass
    except Exception:
        sys.stderr.write("webview.start failed\n")
        traceback.print_exc(file=sys.stderr)


if __name__ == "__main__":
    try:
        run_overlay()
    except Exception:
        sys.stderr.write("run_overlay top-level crashed\n")
        traceback.print_exc(file=sys.stderr)
