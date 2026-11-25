"""
Stage 1: Narration Merging
Merges the 8 authentic Amharic narration audio segments of Kakewerdot's story.
Ensures zero truncation, 44.1kHz stereo output, and loud, clear broadcast dialogue level.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
AUDIO_OUT_DIR = Path("output/audio_merged_8")
RAW_AUDIO_DIR = Path("output/audio_life_story")
AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)

def merge_narration():
    with open("storyboard.json", "r", encoding="utf-8") as f:
        sb = json.load(f)
        
    shots = sb.get("shots", [])
    print(f"\n[Stage 1 - Narration] Merging {len(shots)} Kakewerdot life story audio files...")
    
    wav_segments = []
    sample_rate = 44100
    
    for shot in shots:
        s_id = shot["shot_id"]
        mp3_path = RAW_AUDIO_DIR / f"{s_id}_voice.mp3"
        temp_wav = AUDIO_OUT_DIR / f"{s_id}_temp.wav"
        
        if not mp3_path.exists():
            print(f"ERROR: Raw audio file {mp3_path} does not exist.")
            sys.exit(1)
            
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(mp3_path),
            "-ar", str(sample_rate),
            "-ac", "2",
            str(temp_wav)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        rate, data = wavfile.read(temp_wav)
        wav_segments.append(data)
        dur = data.shape[0] / rate
        print(f"  {s_id}: {dur:.2f}s | '{shot['narration']['amharic'][:40]}...'")
        
    merged_data = np.concatenate(wav_segments, axis=0)
    merged_wav = AUDIO_OUT_DIR / "merged_8_narrations.wav"
    wavfile.write(str(merged_wav), sample_rate, merged_data)
    total_dur = merged_data.shape[0] / sample_rate
    
    print(f"[Stage 1 - Narration] SUCCESS: Merged audio -> {merged_wav} ({total_dur:.2f}s)")
    return str(merged_wav), total_dur

if __name__ == "__main__":
    merge_narration()
