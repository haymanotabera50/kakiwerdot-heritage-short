# FAILURES: Technical Troubleshooting & Root Cause Analyses

Documenting real technical hurdles encountered during the production of *"Kakiwerdot: The Voice That Would Not Be Silenced"*, their root causes, and the engineering solutions implemented.

---

### Failure 1: Edge-TTS Websocket Handshake 403 Forbidden
- **Symptom:** Running `edge-tts` to synthesize Amharic speech threw `WSServerHandshakeError: 403, message='Invalid response status', url='wss://speech.platform.bing.com...'`.
- **Root Cause Analysis:** Microsoft Edge ReadAloud websocket servers enforce token rotation (`Sec-MS-GEC`) and throttle or reject cloud server IP blocks that lack browser session state.
- **Engineering Fix:** Switched to a resilient multi-endpoint architecture using `gTTS(lang='am')` with SSL certificate injection (`certifi.where()`), an exponential retry loop, and TLD rotation across `com`, `co.uk`, `ca`, and `co.za`.

---

### Failure 2: Windows Speech SAPI NullReferenceException in Sandbox
- **Symptom:** PowerShell command `Add-Type -AssemblyName System.Speech; $synth.GetInstalledVoices()` crashed with `Object reference not set to an instance of an object`.
- **Root Cause Analysis:** Sandboxed Windows runner environments lack the Windows Audio Service (`audiosrv`) and physical hardware audio endpoints, causing the legacy COM SAPI bridge to throw unhandled null references.
- **Engineering Fix:** Completely bypassed Windows COM dependencies by using Python's NumPy/SciPy audio synthesis and direct FFmpeg filter processing, which operate entirely in-memory with zero OS hardware requirements.

---

### Failure 3: Missing System FFmpeg in User PATH
- **Symptom:** Running `ffmpeg` in shell produced `CommandNotFoundException: The term 'ffmpeg' is not recognized`.
- **Root Cause Analysis:** Standard development machines on Windows frequently do not have FFmpeg added to the system `$env:PATH`.
- **Engineering Fix:** Integrated Python's `imageio-ffmpeg` package. All scripts resolve `imageio_ffmpeg.get_ffmpeg_exe()`, guaranteeing access to the bundled `ffmpeg-win-x86_64-v7.1.exe` binary without manual system configuration.

---

### Failure 4: Mono Voice Inaudibility (-22.5 dB) on Mobile Devices
- **Symptom:** Initial test audio was barely audible when played back on mobile phones or laptop speakers.
- **Root Cause Analysis:** Raw synthesized TTS audio was recorded as single-channel mono with a low average loudness of -23.5 dB RMS, lacking stereo spatialization and dynamic gain boost.
- **Engineering Fix:** Implemented a two-stage audio processing pass:
  1. Converted mono streams to true 2-channel stereo (`-ac 2 -ar 44100`).
  2. Boosted vocal dialogue gain by 2.4x to achieve broadcast standard -15.5 dB mean loudness and 0.0 dB true peak, ensuring clear speech intelligibility.

---

### Failure 5: Final Sentence Truncation via Static `-t` Cutoff
- **Symptom:** In early assemblies, the final Amharic word in Shot 8 (*"አርማ ነው።"*) was abruptly cut off mid-syllable.
- **Root Cause Analysis:** The assembly script applied a static `-t 75` duration flag across the entire concatenated stream, cutting off the audio before the final spoken syllable finished decaying.
- **Engineering Fix:** Rewrote the video shot timing engine to dynamically measure each audio file's exact waveform length in milliseconds (`wavfile.read`), setting each video shot duration to match the narration duration exactly (summing to 85.01s), with 0.5s natural decay padding.

---

### Failure 6: Music Drowning Out Spoken Amharic Dialogue
- **Symptom:** Test audience members reported that even ducked background score competed with the spoken historical story.
- **Root Cause Analysis:** Amharic speech relies heavily on subtle consonant inflections and vowel endings; even a low musical drone can mask critical phonetic cues.
- **Engineering Fix:** Created a dedicated **Pure Voice Narration Master** (`kakiwerdot_VOICE_ONLY_NO_MUSIC_16x9.mp4` and `9x16`), allowing the viewer to hear the story with zero musical interference, while keeping the ducked broadcast score as a secondary option.

---

### Failure 7: PowerShell UTF-8 BOM Breaking FFmpeg Concat Demuxer
- **Symptom:** FFmpeg failed with `unknown keyword '﻿file'` when reading `concat_list.txt`.
- **Root Cause Analysis:** PowerShell's default `Out-File` or `Set-Content` writes UTF-8 files with a Byte Order Mark (`0xEF, 0xBB, 0xBF`), which FFmpeg's concat demuxer rejects.
- **Engineering Fix:** Switched all manifest generation to Python's standard `open(file, 'w', encoding='utf-8')` (without BOM), ensuring strict FFmpeg parser compatibility.
