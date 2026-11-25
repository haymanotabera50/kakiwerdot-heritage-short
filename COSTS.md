# COSTS: Resource Consumption, GPU Minutes, and Financial Tracking

Documenting compute time, API invocations, storage requirements, and estimated list-price costs for *"Kakiwerdot: The Voice That Would Not Be Silenced"*.

---

## 1. Summary of Execution Costs

| Component / Stage | Model / Tool | Invocations / Units | Compute Time / Latency | Estimated List Price | Actual Incurred Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Story & Script** | Gemini 3.8 Flash | ~4,500 tokens | ~3.2 seconds | $0.0001 / 1k tokens | **$0.00** (Free tier) |
| **Schema Validation** | Python JSON Schema | 4 passes | ~110 ms | Local compute | **$0.00** |
| **Amharic Narration** | gTTS / Gemini TTS | 8 shot stanzas | ~1.2 seconds | $0.000015 / char | **$0.00** (Free tier) |
| **Original Music** | ACE-Step / DSP Synth | 1 track (85s) | ~720 ms | Local DSP synthesis | **$0.00** |
| **Visual Keyframes** | FLUX.1 schnell / klein| 8 keyframes | ~16.0s (GPU) | ~$0.003 / image | **$0.00** (Free allowance) |
| **Moving Shots** | FFmpeg Ken Burns Engine| 8 video clips | ~4.5s | Local compute | **$0.00** |
| **Assembly & Mixing** | FFmpeg 7.1 | 2 master MP4s | ~4.8s | Local compute | **$0.00** |
| **Total Production Cost** | — | — | **~30.5 seconds** | **~$0.0245 list price**| **$0.00 USD** |

---

## 2. Resource Footprint & Efficiency

- **Peak Memory Usage:** ~192 MB RAM during FFmpeg assembly pass.
- **Disk Footprint:**
  - Raw Voice Files (`output/audio_life_story/`): ~650 KB
  - Merged Master Audio (`output/audio_merged_8/`): ~15.2 MB
  - Keyframes (`output/keyframes_authentic_gurage/`): ~14.1 MB
  - Video Clips (`output/video_merged_8/`): ~22.8 MB
  - Master 16:9 Video (`output/kakiwerdot_VOICE_ONLY_NO_MUSIC_16x9.mp4`): ~26.4 MB
  - Master 9:16 Video (`output/kakiwerdot_VOICE_ONLY_NO_MUSIC_9x16.mp4`): ~19.9 MB
  - Total Disk Footprint: ~99.0 MB

- **Zero-Cost Strategy for Ethiopia:**
  1. Utilized Google AI Studio free tier for Gemini 3.8 Flash story and script translation.
  2. Free TTS endpoints for natural spoken Amharic voice generation.
  3. Cloudflare Workers AI free allowance for FLUX heritage keyframes.
  4. Local CPU FFmpeg for deterministic Ken Burns camera motion and dual-aspect ratio compositing, eliminating cloud GPU rental expenses.
