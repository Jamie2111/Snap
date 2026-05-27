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
import sys
import threading
import traceback
from pathlib import Path


def _html_url() -> str:
    return (Path(__file__).resolve().parent / "templates" / "overlay.html").as_uri()


class _OverlayApi:
    """JS bridge for the overlay's pause / stop buttons."""

    def send_command(self, cmd: str) -> None:
        try:
            sys.stdout.write(f"SNAP_CONTROL:{cmd}\n")
            sys.stdout.flush()
        except Exception:
            sys.stderr.write("send_command failed\n")
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

    # Start the reader once the window's loaded event fires. Do NOT touch
    # AppKit / NSApp here -- those calls from non-main threads crash Python.
    def on_loaded() -> None:
        threading.Thread(target=stdin_reader, daemon=True).start()

    try:
        window.events.loaded += on_loaded
    except Exception:
        # Fallback: start the reader anyway after a short delay.
        threading.Timer(0.5, lambda: threading.Thread(target=stdin_reader, daemon=True).start()).start()

    try:
        webview.start(debug=False)
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
