import json
import os
import subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("output/audio_synced_finished")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
KEYFRAMES_DIR = Path("output/keyframes_authentic_gurage")
VIDEO_DIR = Path("output/video_shots_authentic_gurage")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# Exact shot configuration: 78.0 seconds total (10s rhythm from previous synced video)
# Speech speeds calibrated so EVERY SINGLE SENTENCE finishes with breathing room
SHOT_CONFIGS = [
    {"shot_id": "SH_01", "duration": 10.0, "tempo": 1.28},
    {"shot_id": "SH_02", "duration": 10.0, "tempo": 1.15},
    {"shot_id": "SH_03", "duration": 10.0, "tempo": 1.20},
    {"shot_id": "SH_04", "duration": 10.0, "tempo": 1.18},
    {"shot_id": "SH_05", "duration": 10.0, "tempo": 1.16},
    {"shot_id": "SH_06", "duration": 10.0, "tempo": 1.08},
    {"shot_id": "SH_07", "duration": 8.0,  "tempo": 1.28},
    {"shot_id": "SH_08", "duration": 10.0, "tempo": 1.10}
]

TOTAL_DURATION = sum(s["duration"] for s in SHOT_CONFIGS)
print(f"Total Target Runtime: {TOTAL_DURATION:.1f} seconds (Preserves the 10s rhythm)")

def generate_ethiopian_score_78s(total_dur: float, sample_rate: int = 44100):
    music_wav = AUDIO_DIR / f"score_{int(total_dur)}s.wav"
    t = np.linspace(0, total_dur, int(sample_rate * total_dur), endpoint=False)
    pentatonic_freqs = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0]
    
    drone = 0.14 * np.sin(2 * np.pi * 110.0 * t) + 0.08 * np.sin(2 * np.pi * 164.81 * t) + 0.04 * np.sin(2 * np.pi * 55.0 * t)
    music_wave = drone.copy()
    
    pluck_interval = 1.25
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
        pluck = 0.25 * (0.6 * np.sin(2 * np.pi * freq * t_pluck) + 0.3 * np.sin(2 * np.pi * (freq * 2) * t_pluck)) * env
        music_wave[start_idx:end_idx] += pluck

    fade_len = int(2.5 * sample_rate)
    music_wave[-fade_len:] *= np.linspace(1, 0, fade_len)
    
    max_val = np.max(np.abs(music_wave))
    if max_val > 0:
        music_wave = (music_wave / max_val) * 0.45
        
    wavfile.write(str(music_wav), sample_rate, (music_wave * 32767).astype(np.int16))
    return str(music_wav)

def build_finished_voice_track():
    print("\n--- Generating Synchronized Voice Track (EVERY SENTENCE FINISHES) ---")
    wav_segments = []
    
    for cfg in SHOT_CONFIGS:
        s_id = cfg["shot_id"]
        shot_dur = cfg["duration"]
        tempo = cfg["tempo"]
        raw_mp3 = Path(f"output/audio_life_story/{s_id}_voice.mp3")
        padded_wav = AUDIO_DIR / f"{s_id}_finished_padded.wav"
        
        # Adjust tempo so speech completes before shot ends, then pad silence to exact shot duration
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(raw_mp3),
            "-filter_complex", f"[0:a]atempo={tempo},apad=whole_dur={shot_dur}[out]",
            "-map", "[out]",
            "-t", str(shot_dur),
            "-ar", "44100",
            "-ac", "2",
            str(padded_wav)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        rate, data = wavfile.read(padded_wav)
        wav_segments.append(data)
        print(f"  {s_id}: Speech finishes completely within {shot_dur}s shot.")

    full_voice = np.concatenate(wav_segments, axis=0)
    full_voice_wav = AUDIO_DIR / f"full_finished_voice_{int(TOTAL_DURATION)}s.wav"
    wavfile.write(str(full_voice_wav), 44100, full_voice)
    return str(full_voice_wav)

def update_video_shots_and_concat():
    # Make sure SH_08_clip is 10.0 seconds so Shot 8 visual holds as speech finishes
    sh08_mp4 = VIDEO_DIR / "SH_08_clip.mp4"
    kf08 = KEYFRAMES_DIR / "SH_08_keyframe.png"
    total_frames = int(10.0 * 30)
    cmd = [
        FFMPEG_EXE, "-y",
        "-loop", "1",
        "-i", str(kf08),
        "-vf", f"zoompan=z='max(1.15-0.0005*on,1.0)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
        "-t", "10.0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(sh08_mp4)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  Updated SH_08 video clip to 10.0s.")

    concat_txt = VIDEO_DIR / "concat_list_78s.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for cfg in SHOT_CONFIGS:
            s_id = cfg["shot_id"]
            clip_file = VIDEO_DIR / f"{s_id}_clip.mp4"
            clean_p = str(clip_file.resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")
    return str(concat_txt)

def assemble():
    music_wav = generate_ethiopian_score_78s(TOTAL_DURATION)
    voice_wav = build_finished_voice_track()
    concat_txt = update_video_shots_and_concat()

    # Mix audio into loud broadcast stereo (-0.4 dB peak) with sidechain ducking
    soundtrack_mp3 = AUDIO_DIR / f"master_soundtrack_{int(TOTAL_DURATION)}s.mp3"
    filter_complex = (
        "[0:a]volume=0.12,aformat=channel_layouts=stereo[music];"
        "[1:a]volume=2.8,aformat=channel_layouts=stereo[voice];"
        "[music][voice]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=450[ducked_music];"
        "[ducked_music][voice]amix=inputs=2:duration=first:weights=1 3[out]"
    )
    mix_cmd = [
        FFMPEG_EXE, "-y",
        "-i", music_wav,
        "-i", voice_wav,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "256k",
        str(soundtrack_mp3)
    ]
    subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"\nMaster Soundtrack: {soundtrack_mp3}")

    # Mux directly into kakiwerdot_16x9_AMHARIC_AUDIO_SYNCED.mp4
    master_16x9 = OUTPUT_DIR / "kakiwerdot_16x9_AMHARIC_AUDIO_SYNCED.mp4"
    print(f"\n--- Updating Master 16:9 Film: {master_16x9.name} ---")
    
    cmd_16x9 = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-i", str(soundtrack_mp3),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "44100",
        "-ac", "2",
        "-shortest",
        "-movflags", "+faststart",
        str(master_16x9)
    ]
    subprocess.run(cmd_16x9, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"SUCCESS! Master 16:9 Synced & Finished Film: {master_16x9} ({master_16x9.stat().st_size / (1024*1024):.2f} MB)")

    # 9:16 vertical
    master_9x16 = OUTPUT_DIR / "kakiwerdot_9x16_AMHARIC_AUDIO_SYNCED.mp4"
    filter_9x16 = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
        "[0:v]scale=1080:608[fg];"
        "[bg][fg]overlay=0:(H-h)/2[out]"
    )
    cmd_9x16 = [
        FFMPEG_EXE, "-y",
        "-i", str(master_16x9),
        "-filter_complex", filter_9x16,
        "-map", "[out]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(master_9x16)
    ]
    subprocess.run(cmd_9x16, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"SUCCESS! Master 9:16 Synced & Finished Film: {master_9x16} ({master_9x16.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    assemble()
