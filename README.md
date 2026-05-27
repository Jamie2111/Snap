# Snap

Local, AI-powered Overwatch 2 coach. Captures your screen, extracts game state via computer vision and OCR, and produces a post-game terminal report that thinks like a professional coach. Liquid memory layer means every session adds to a compounding model of your specific play.

No external API calls. Everything runs locally.

## Requirements

### Windows (runtime, where OW2 runs)

1. Python 3.11 or newer
2. [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) installed
3. Overwatch 2 in **Borderless Windowed** mode at **1920x1080**, default HUD scale
4. Git (for cloning the repo)

### macOS (development only)

Same as Windows, except:
- Install Tesseract via `brew install tesseract`
- Live capture is disabled. Use `--replay` or `--demo` modes for testing.

## Setup

```bash
git clone <repo-url> Snap
cd Snap
python -m venv .venv

# macOS / Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

If Tesseract is not on your PATH, set the `TESSERACT_CMD` environment variable to its full path.

## Running

### Live (Windows, OW2 open)

```bash
python main.py --live
```

You will be prompted for the hero you are starting on. Snap will detect hero swaps automatically when you open the scoreboard (hold Tab).

### Replay (Mac / Windows, against saved frames)

```bash
python main.py --replay data/sessions/<session-id>/
```

### Demo (any platform, canned session)

```bash
python main.py --demo
```

Shows the full post-game report from a synthetic session. Useful for verifying the install.

## Output

After each session, Snap prints a Rich-formatted terminal report and writes a markdown file to `data/reports/`. The SQLite database at `data/profiles/snap.db` holds the persistent player model.
