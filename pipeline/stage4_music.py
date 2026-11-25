"""
Stage 4: Original Acoustic Score Generation
Synthesizes a traditional Ethiopian Tezeta pentatonic Kirar score
matching total duration (85.0s) for optional broadcast audio mix.
"""
import sys
from pathlib import Path
import numpy as np
from scipy.io import wavfile

AUDIO_DIR = Path("output/audio_merged_8")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def generate_score(total_dur: float = 85.0, sample_rate: int = 44100):
    music_wav = AUDIO_DIR / f"score_{int(total_dur)}s.wav"
    if music_wav.exists() and music_wav.stat().st_size > 100000:
        print(f"[Stage 4 - Music] [CACHED] {music_wav.name} ({music_wav.stat().st_size / 1024:.1f} KB)")
        return str(music_wav)
        
    print(f"\n[Stage 4 - Music] Synthesizing acoustic Kirar score ({total_dur:.1f}s)...")
    t = np.linspace(0, total_dur, int(sample_rate * total_dur), endpoint=False)
    pentatonic_freqs = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0]
    
    drone = 0.12 * np.sin(2 * np.pi * 110.0 * t) + 0.06 * np.sin(2 * np.pi * 164.81 * t)
    music_wave = drone.copy()
    
    pluck_interval = 1.3
    num_plucks = int(total_dur / pluck_interval)
    rng = np.random.RandomState(42)
    for i in range(num_plucks):
        start_time = i * pluck_interval
        pluck_len = 2.0
        start_idx = int(start_time * sample_rate)
        end_idx = min(len(t), start_idx + int(pluck_len * sample_rate))
        note_len = end_idx - start_idx
        if note_len <= 0:
            break
        t_pluck = np.linspace(0, pluck_len, int(pluck_len * sample_rate))[:note_len]
        freq = rng.choice(pentatonic_freqs)
        env = np.exp(-3.5 * t_pluck)
        pluck = 0.22 * (0.6 * np.sin(2 * np.pi * freq * t_pluck) + 0.3 * np.sin(2 * np.pi * (freq * 2) * t_pluck)) * env
        music_wave[start_idx:end_idx] += pluck
        
    fade_len = int(2.5 * sample_rate)
    music_wave[-fade_len:] *= np.linspace(1, 0, fade_len)
    
    max_val = np.max(np.abs(music_wave))
    if max_val > 0:
        music_wave = (music_wave / max_val) * 0.35
        
    wavfile.write(str(music_wav), sample_rate, (music_wave * 32767).astype(np.int16))
    print(f"[Stage 4 - Music] SUCCESS: Generated -> {music_wav}")
    return str(music_wav)

if __name__ == "__main__":
    generate_score()
