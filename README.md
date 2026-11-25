# Kakiwerdot: The Voice That Would Not Be Silenced
### AI-Content Generation: The Heritage Short (10 Academy Submission)

[![10 Academy Heritage Short](https://img.shields.io/badge/10_Academy-Heritage_Short-blue.svg)](https://10academy.org)
[![Duration](https://img.shields.io/badge/Duration-85.0_Seconds-green.svg)](#)
[![Pipeline](https://img.shields.io/badge/Pipeline-100%25_Reproducible-orange.svg)](#)
[![Culture](https://img.shields.io/badge/Culture-Authentic_Gurage-red.svg)](#)
[![Language](https://img.shields.io/badge/Language-Spoken_Amharic-purple.svg)](#)

A powerful, culturally authentic, and reproducible 85-second documentary short film celebrating the historic Gurage women's rights pioneer **Kakiwerdot** (ቃቄ ወርድወት), narrated in spoken Amharic with authentic Gurage attire, Ken Burns camera motion, and AI transparency disclosure.

---

## 1. Quick Start: One-Command Execution

A stranger can clone this repository, run **one command**, and regenerate or verify the entire film end-to-end:

```bash
python main.py
```

### Generated Deliverables:
- **Horizontal Master (16:9 Landscape, 85s):** `output/kakiwerdot_VOICE_ONLY_NO_MUSIC_16x9.mp4`
- **Vertical Mobile Master (9:16 Vertical, 85s):** `output/kakiwerdot_VOICE_ONLY_NO_MUSIC_9x16.mp4`
- **Interactive Browser Player:** `watch_film.html` (Double-click to open in any browser)
- **Audio Master Track:** `output/audio_merged_8/merged_8_narrations.wav` (44.1kHz Stereo, -15.5 dB mean, 0.0 dB true peak)
- **Execution Telemetry Audit:** `runs.jsonl`

---

## 2. Viewing the Film

Open `watch_film.html` in your web browser:
```bash
start watch_film.html
```
The viewer includes:
- Toggle between **16:9 Landscape** and **9:16 Vertical Mobile**.
- Pure spoken Amharic voice narration of the 8-stanza life story.
- Full synchronized script display (Amharic text + English translation) for all 8 shots.

---

## 3. Pipeline Architecture & Modular Stages

The pipeline follows a decoupled, contract-driven architecture governed by `storyboard.json` and validated against `schema/storyboard.schema.json`:

```
storyboard.json (Contract) ──> schema/storyboard.schema.json
        │
        ├──> pipeline/stage0_validate.py  (JSON Schema validation)
        ├──> pipeline/stage1_narration.py (Merges the 8 Amharic voice segments into 85s master audio)
        ├──> pipeline/stage2_keyframes.py (FLUX keyframe verification & caching)
        ├──> pipeline/stage3_shots.py     (Ken Burns pan/zoom camera motion matching speech duration)
        ├──> pipeline/stage4_music.py     (Ethiopian Tezeta pentatonic score synthesis)
        └──> pipeline/stage5_assemble.py  (16:9 & 9:16 MP4 compositing with subtitles & AI end card)
```

Each stage reads `storyboard.json` and writes its own cached outputs, allowing any single shot to be regenerated independently.

---

## 4. Repository Structure

```
tnx/
├── schema/
│   └── storyboard.schema.json         # JSON Schema Draft-07 contract
├── pipeline/
│   ├── stage0_validate.py             # Schema validation
│   ├── stage1_narration.py            # 8-shot narration merging
│   ├── stage2_keyframes.py            # Authentic Gurage keyframe caching
│   ├── stage3_shots.py                # Video motion generation
│   ├── stage4_music.py                # Acoustic Kirar score synthesis
│   └── stage5_assemble.py             # Dual aspect ratio master compositing
├── output/
│   ├── audio_life_story/              # The 8 individual Amharic voice recordings
│   ├── audio_merged_8/                # Merged 85s master voice track & score
│   ├── keyframes_authentic_gurage/    # 8 photorealistic Gurage keyframes (1080p)
│   ├── video_merged_8/                # 8 motion video clips matching narration
│   ├── kakiwerdot_VOICE_ONLY_NO_MUSIC_16x9.mp4  # Master 16:9 Film (85s)
│   └── kakiwerdot_VOICE_ONLY_NO_MUSIC_9x16.mp4  # Master 9:16 Mobile Film (85s)
├── main.py                            # One-command master runner
├── storyboard.json                    # Central contract (8 shots, durations, prompts)
├── runs.jsonl                         # Audit log for every pipeline run
├── watch_film.html                    # In-browser interactive video player
├── DESIGN.md                          # Audience intent & user test iterations
├── ARCHITECTURE.md                    # Technical pipeline specification & caching
├── EXPERIMENTS.md                     # 12 documented hypotheses and results
├── FAILURES.md                        # Real failure modes and engineering solutions
├── COSTS.md                           # Measured latency & list-price equivalents ($0.00 actual)
└── ETHICS.md                          # Cultural safeguards, licenses & AI disclosure
```

---

## 5. Summary of Costs

| Stage | Model / Tool | Runtime / Latency | List-Price Equivalent | Actual Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Storyboard & Script** | Gemini 3.8 Flash | 3.2s | $0.0004 | **$0.00** (Free tier) |
| **Narration** | gTTS / Gemini TTS | 8 shots | $0.0001 | **$0.00** (Free tier) |
| **Keyframes** | FLUX.1 schnell / klein | 16.0s | $0.0240 | **$0.00** (Free allowance) |
| **Motion Shots** | FFmpeg Ken Burns Engine| 4.5s | $0.0000 | **$0.00** (Local compute) |
| **Assembly** | FFmpeg 7.1 | 4.8s | $0.0000 | **$0.00** (Local compute) |
| **Total** | — | **~28.5s** | **$0.0245** | **$0.00 USD** |
