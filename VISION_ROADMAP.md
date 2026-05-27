# Vision Roadmap

Snap's vision stack (extractor/vision.py) currently uses classical CV: HSV
color masks, contour detection, and frame-difference luminance. This catches
real signal but does not match what a hosted vision API (Claude / GPT-4V)
would produce on the same frames. This doc traces the path from where we are
to local vision-API-grade accuracy.

## Current layer: classical CV (shipped)

| Detector | Method | What it captures |
|---|---|---|
| CrosshairLocator | Constant (screen center) | Where you're aiming |
| EnemyOutlineDetector | HSV mask for red/orange + contour filtering | Enemy character silhouettes |
| AbilityGlowDetector | Per-ability HSV color signatures with min-pixel-pct thresholds | Major ult activations (blade green, nano gold, etc.) |
| ScreenFlashDetector | Frame-to-frame luminance delta | Impacts, shatters, flashbangs |

Consumed by:
- `extractor/aim.py:AimTracker` → on-target %, avg miss distance, near-miss count
- `feedback/engine.py:_mechanics()` → Mechanics tier in the post-game report

### Known limits

1. **Outline color depends on settings.** OW2 default is red, but players can
   change it. Custom color = detector misses everything.
2. **No character identity from silhouettes.** We know "an enemy is here," not
   "the Brigitte is here."
3. **Ability detection is coarse.** A green glow could be Genji blade, Lucio
   amp-up green ring, or background scenery.
4. **No event correlation.** We see a glow + a death but cannot say "Genji
   bladed *you* specifically." 5. **No projectile / hitbox tracking.** Pulse bomb stuck vs detonated in air?
   Currently invisible.

## Next layer: pretrained YOLO + fine-tune (SHIPPED)

**Status:** Pretrained YOLOv8n is wired in `extractor/yolo_detector.py`.
`VisionPipeline` tries it first when `ultralytics` is installed, falls back
to classical HSV outline detection otherwise. Both produce the same
`Detection` shape so downstream consumers are unchanged.

**To enable:**
```
pip install ultralytics
```
First `--live` or `--video` run will auto-download `yolov8n.pt` (~6MB). Set
`SNAP_YOLO_WEIGHTS=/path/to/weights.pt` to override, or drop a fine-tuned
model at `data/models/snap-ow2.pt` and Snap will pick it up automatically.

**Out-of-the-box:** detects "person" boxes (COCO class 0) as enemy
characters. This is already a big upgrade because it doesn't depend on the
OW2 outline color setting.

**To unlock per-hero identification (1-2 week project):**
1. **Data collection.** Grab ~500 OW2 frames per hero across maps, modes,
   skins. Tools: yt-dlp on pro gameplay channels + ffmpeg extract. Target
   ~20,000 frames total.
2. **Annotation.** Label boxes + hero class. Use Roboflow / Label Studio
   (free tier). Auto-bootstrap with SAM (Segment Anything) + manual cleanup.
3. **Fine-tune YOLOv8.** ~4 hours on a single GPU (rent a Lambda Cloud
   instance for $1-2). 80%+ mAP achievable for character detection.
4. **Drop in.** Save the fine-tuned weights to `data/models/snap-ow2.pt`.
   No code change required - `_resolve_model_path()` already looks there.
5. **Update `_CHARACTER_CLASS_IDS`** in `extractor/yolo_detector.py` to
   include the new per-hero classes.

Outputs Snap gains (with fine-tune):
- Per-frame "Brigitte at (x, y)" not just "enemy at (x, y)"
- Robust to skin variations once skin frames are in training data
- Confidence scores per detection (no more threshold tuning by hand)

## Layer after that: per-ability outcome models

**Cost:** 2-4 weeks. **Adds:** "pulse bomb stuck / cleaned / killed N."

Per-ability binary classifiers trained on short video clips around the moment
the ability fires:

| Ability | Outcome classes | Signal |
|---|---|---|
| Pulse bomb | stuck, detonated_in_air, destroyed | Red projectile + explosion radius |
| Sleep dart | hit, missed | Sleep zzz icon on a character |
| Earthshatter | wiped, fizzled | Stun icon spread + downed targets |
| Dragonblade | active_now, finished | Persistent green glow on Genji model |
| Trans | covered_team, used_late | Yellow burst centered on Zen + ally HP recovery |

Each model: ~1000 labeled clips, ResNet-18 backbone, 5 minutes to train per
ability. ~24 abilities matter at GM-level coaching = ~2 days of training
compute total.

Wiring: a new `AbilityOutcomeTracker` watches `AbilityGlowDetector` fires,
extracts a 3-second clip around each, runs the relevant per-ability
classifier, attaches the outcome to the corresponding `UltimateUsed` event.

## Layer after that: pose + crosshair-on-target

**Cost:** 3-6 weeks. **Adds:** mechanical aim coaching.

1. Train **MediaPipe-style pose detection** on OW characters (more body-shape
   variation than humans, so pretrained models do poorly).
2. **Headshot box** per detected character = top 20% of bbox.
3. **Crosshair-on-head %** instead of crosshair-on-bbox %.
4. **Tracking persistence**: ByteTrack to keep "this is the same Brigitte"
   between frames so micro-corrections vs flicks can be distinguished.

Outputs Snap gains:
- "You hit head 18% of body shots. Pro avg is 35%."
- "Your reflicks are tighter than your trackshots. Try heroes with one-shot
  bursts (Widow, Hanzo) over sustained DPS."
- "You drift below targets during long fights. Sensitivity may be too high."

## Long horizon: full event-graph from vision alone

**Cost:** months. **Adds:** Snap stops depending on the HUD.

Replace HUD-region extraction (`extractor/game_state.py`) with a unified
end-to-end model that reads every frame and emits a structured event stream:
death events, ult use events, ability hit events, fight start/end, point
captures, all from pixels. At that point Snap becomes resolution-agnostic,
HUD-scale-agnostic, and works on any video without configuration.

This is the equivalent of what Claude / GPT-4V do today via their multimodal
backbones, but specialized for one game. The right architecture is probably
a small video transformer (V-JEPA / VideoMAE-style) fine-tuned on annotated
gameplay segments.

## Why this is the order

Each layer is independently useful and unlocks the next:

- **Pretrained YOLO** removes the outline-color dependency, gives identity.
- **Ability outcome models** require YOLO to know which character fired the ult.
- **Pose models** require character bboxes from YOLO.
- **Full vision pipeline** is a research project, not a weekend hack.

Snap can sit comfortably at the classical-CV layer for a long time. The
upgrade path is clear; what changes is what coaching depth you want to fund.
