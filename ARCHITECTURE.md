# ARCHITECTURE: AI Heritage Short Pipeline

## 1. System Overview & Core Principles

The pipeline is built around **reproducibility, contract validation, deterministic fallbacks, stage modularity, and transparent audit logging**. A single command (`python main.py`) triggers the complete multi-stage pipeline, regenerating or verifying the film from `storyboard.json`.

```
                    +------------------------------------+
                    |          storyboard.json           |
                    | (Validated via JSON Schema draft-7)|
                    +-----------------+------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+-----------------------+                                 +-----------------------+
| pipeline/             |                                 | pipeline/             |
| stage1_narration.py   |                                 | stage2_keyframes.py   |
| - Merges 8 voice files|                                 | - FLUX.1/FLUX.2       |
| - 44.1kHz stereo      |                                 |   anchor prompts      |
| - 85.0s master audio  |                                 | - MD5 cache checks    |
+-----------+-----------+                                 +-----------+-----------+
            |                                                         |
            |                                                         v
            |                                             +-----------------------+
            |                                             | pipeline/             |
            |                                             | stage3_shots.py       |
            |                                             | - Ken Burns camera pan|
            |                                             |   and zoom equations  |
            |                                             | - Matches exact speech|
            |                                             +-----------+-----------+
            |                                                         |
            +----------------------------+                            |
                                         |                            |
                                         v                            v
                                +-------------------------------------+
                                | pipeline/stage5_assemble.py         |
                                | - Muxes video & audio seamlessly    |
                                | - 16:9 Landscape & 9:16 Vertical    |
                                | - Pure Voice (Zero Music) Cut       |
                                | - Broadcast Master Cut with Score   |
                                | - Appends telemetry to runs.jsonl   |
                                +------------------+------------------+
                                                   |
                                                   v
                                   +----------------------------------+
                                   | output/                          |
                                   | - kakiwerdot_VOICE_ONLY_..._16x9 |
                                   | - kakiwerdot_VOICE_ONLY_..._9x16 |
                                   | - watch_film.html previewer      |
                                   +----------------------------------+
```

---

## 2. Stage Contracts & Boundaries

### Stage 0: Contract Validation (`pipeline/stage0_validate.py`)
- Reads `schema/storyboard.schema.json` and `storyboard.json`.
- Enforces runtime boundaries: 60s <= total duration <= 90s, shot durations between 2s and 15s, bilingual narration (`amharic` + `english`), and character anchor definitions.
- Exits with code 1 if any contract condition is violated.

### Stage 1: Narration Merging (`pipeline/stage1_narration.py`)
- Reads the 8 spoken Amharic voice files from `output/audio_life_story/SH_01_voice.mp3` through `SH_08_voice.mp3`.
- Converts each to standard 44.1kHz 2-channel stereo WAV.
- Concatenates them into `output/audio_merged_8/merged_8_narrations.wav` (85.01s total duration).
- Guarantees zero sentence truncation.

### Stage 2: Keyframe Verification (`pipeline/stage2_keyframes.py`)
- Verifies that all 8 keyframe images in `output/keyframes_authentic_gurage/` exist and match 1920x1080 resolution.
- Enforces character consistency through the Gurage visual anchor string (vibrant red/indigo woven dress, wrapped *shash* headscarf, *merkaz* beads).

### Stage 3: Moving Shots Generation (`pipeline/stage3_shots.py`)
- Generates 30fps MP4 video clips matching each shot's exact narration duration.
- Applies dynamic Ken Burns camera movements (`zoompan`):
  - SH_01 & SH_05: Slow push-in for contemplation and heroic climax.
  - SH_02 & SH_04: Gentle zoom for personal focus and resolve.
  - SH_03, SH_06, SH_07, SH_08: Subtle pull-back or horizontal pans for assembly and horizon views.
- Includes file-existence caching to skip already-rendered clips unless forced.

### Stage 4: Original Score Generation (`pipeline/stage4_music.py`)
- Generates an original acoustic backing score modeled on ACE-Step 1.5 generative principles using traditional Ethiopian Tezeta pentatonic modes (A, C, D, E, G).
- Stored as `output/audio_merged_8/score_85s.wav` for optional broadcast mixing.

### Stage 5: Final Multi-Format Assembly (`pipeline/stage5_assemble.py`)
- Produces:
  1. `output/kakiwerdot_VOICE_ONLY_NO_MUSIC_16x9.mp4`: Pure spoken voice narration with video, zero music.
  2. `output/kakiwerdot_VOICE_ONLY_NO_MUSIC_9x16.mp4`: Mobile vertical format with padded/blurred background.
  3. `output/kakiwerdot_broadcast_master_16x9.mp4`: Master cut with ducked Kirar score and AI end card.
- Applies `-movflags +faststart` for instant streaming playback.
- Logs structured execution metrics to `runs.jsonl`.
