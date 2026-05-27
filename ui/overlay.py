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

    # Start the reader once the window's loaded event fires.
    def on_loaded() -> None:
        threading.Thread(target=stdin_reader, daemon=True).start()

    try:
        window.events.loaded += on_loaded
    except Exception:
        threading.Timer(0.5, lambda: threading.Thread(target=stdin_reader, daemon=True).start()).start()

    def on_main_thread_post_start() -> None:
        """Runs ONCE on the macOS main thread after the window is created.
        This is the only safe place to touch AppKit / NSWindow APIs.

        Sets the window to:
          - join all macOS Spaces (visible across Space switches)
          - stay above normal app windows (NSStatusWindowLevel = 25)
          - remain visible even when other apps go full-screen
        Each setting is wrapped individually; partial failure is fine."""
        try:
            from AppKit import NSWindowCollectionBehaviorCanJoinAllSpaces, NSWindowCollectionBehaviorStationary, NSWindowCollectionBehaviorFullScreenAuxiliary
        except Exception:
            sys.stderr.write("AppKit import failed; overlay will not span Spaces\n")
            return

        ns_window = None
        try:
            native = getattr(window, "native", None)
            if native is not None:
                # pywebview cocoa backend: native is the WKWebView; .window() returns NSWindow
                if hasattr(native, "window") and callable(native.window):
                    ns_window = native.window()
                else:
                    ns_window = native
        except Exception:
            ns_window = None

        if ns_window is None:
            # Fallback: walk NSApp.windows() looking for our title
            try:
                from AppKit import NSApp
                for w in (NSApp.windows() if NSApp else []):
                    try:
                        if str(w.title()) == "Snap":
                            ns_window = w
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        if ns_window is None:
            sys.stderr.write("could not locate NSWindow; overlay limited to current Space\n")
            return

        try:
            mask = (
                NSWindowCollectionBehaviorCanJoinAllSpaces
                | NSWindowCollectionBehaviorStationary
                | NSWindowCollectionBehaviorFullScreenAuxiliary
            )
            ns_window.setCollectionBehavior_(mask)
        except Exception:
            sys.stderr.write("setCollectionBehavior_ failed\n")
            traceback.print_exc(file=sys.stderr)
        try:
            # 25 = NSStatusWindowLevel; high enough to float over full-screen apps
            ns_window.setLevel_(25)
        except Exception:
            sys.stderr.write("setLevel_ failed\n")
            traceback.print_exc(file=sys.stderr)
        try:
            ns_window.setHidesOnDeactivate_(False)
        except Exception:
            pass

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
