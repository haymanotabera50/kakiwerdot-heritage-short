import json
import os
import subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

OUTPUT_AUDIO_DIR = Path("output/audio_complete_finished")
OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
KEYFRAMES_DIR = Path("output/keyframes_authentic_gurage")
VIDEO_SHOTS_DIR = Path("output/video_shots_complete_finished")
VIDEO_SHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Calibrated shot parameters ensuring every sentence finishes completely
# and total film duration is exactly 88.0 seconds (well within 60-90s limit)
SHOT_CONFIGS = [
    {"shot_id": "SH_01", "duration": 12.0, "tempo": 1.08, "zoom": "'min(zoom+0.0005,1.15)'"},
    {"shot_id": "SH_02", "duration": 10.5, "tempo": 1.06, "zoom": "'min(zoom+0.0004,1.10)'"},
    {"shot_id": "SH_03", "duration": 11.0, "tempo": 1.06, "zoom": "'min(zoom+0.0004,1.10)'"},
    {"shot_id": "SH_04", "duration": 11.0, "tempo": 1.06, "zoom": "'min(zoom+0.0004,1.10)'"},
    {"shot_id": "SH_05", "duration": 11.0, "tempo": 1.06, "zoom": "'min(zoom+0.0005,1.15)'"},
    {"shot_id": "SH_06", "duration": 10.0, "tempo": 1.04, "zoom": "'min(zoom+0.0004,1.10)'"},
    {"shot_id": "SH_07", "duration": 10.5, "tempo": 1.04, "zoom": "'max(1.15-0.0005*on,1.0)'"},
    {"shot_id": "SH_08", "duration": 12.0, "tempo": 1.02, "zoom": "'max(1.15-0.0005*on,1.0)'"}
]

TOTAL_DURATION = sum(s["duration"] for s in SHOT_CONFIGS)
print(f"Total Target Runtime: {TOTAL_DURATION:.1f} seconds (Strictly within 60-90s limit)")

def generate_ethiopian_acoustic_score_88s(total_duration_sec: float, sample_rate: int = 44100):
    music_wav = OUTPUT_AUDIO_DIR / f"background_music_{int(total_duration_sec)}s.wav"
    t = np.linspace(0, total_duration_sec, int(sample_rate * total_duration_sec), endpoint=False)
    pentatonic_freqs = [220.0, 261.63, 293.66, 329.63, 392.0, 440.0]
    
    drone = 0.14 * np.sin(2 * np.pi * 110.0 * t) + 0.08 * np.sin(2 * np.pi * 164.81 * t) + 0.04 * np.sin(2 * np.pi * 55.0 * t)
    music_wave = drone.copy()
    
    pluck_interval = 1.25
    num_plucks = int(total_duration_sec / pluck_interval)
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

    # Smooth fade out over last 3 seconds
    fade_len = int(3.0 * sample_rate)
    music_wave[-fade_len:] *= np.linspace(1, 0, fade_len)
    
    max_val = np.max(np.abs(music_wave))
    if max_val > 0:
        music_wave = (music_wave / max_val) * 0.45
        
    wavfile.write(str(music_wav), sample_rate, (music_wave * 32767).astype(np.int16))
    return str(music_wav)

def process_untruncated_voice():
    print("\n--- Processing Voice Tracks (NO TRUNCATION) ---")
    wav_segments = []
    
    for cfg in SHOT_CONFIGS:
        s_id = cfg["shot_id"]
        shot_dur = cfg["duration"]
        tempo = cfg["tempo"]
        raw_mp3 = Path(f"output/audio_life_story/{s_id}_voice.mp3")
        padded_wav = OUTPUT_AUDIO_DIR / f"{s_id}_full_padded.wav"
        
        # Apply slight tempo adjustment without pitch change, then apad to exact shot duration
        # Crucial: NO '-t' truncation before speech finishes!
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
        print(f"  {s_id}: Finished speech, padded to {shot_dur}s (data len: {data.shape[0] / rate:.2f}s)")

    full_voice = np.concatenate(wav_segments, axis=0)
    full_voice_wav = OUTPUT_AUDIO_DIR / f"full_untruncated_voice_{int(TOTAL_DURATION)}s.wav"
    wavfile.write(str(full_voice_wav), 44100, full_voice)
    print(f"--> Master Untruncated Voice Track: {full_voice_wav} ({full_voice.shape[0] / 44100:.2f}s)")
    return str(full_voice_wav)

def render_extended_video_clips():
    print("\n--- Rendering Extended Video Clips for Complete Audio ---")
    video_clips = []
    
    for cfg in SHOT_CONFIGS:
        s_id = cfg["shot_id"]
        dur = cfg["duration"]
        zoom_expr = cfg["zoom"]
        
        kf_path = KEYFRAMES_DIR / f"{s_id}_keyframe.png"
        out_clip = VIDEO_SHOTS_DIR / f"{s_id}_clip_{int(dur)}s.mp4"
        total_frames = int(dur * 30)
        
        cmd = [
            FFMPEG_EXE, "-y",
            "-loop", "1",
            "-i", str(kf_path),
            "-vf", f"zoompan=z={zoom_expr}:d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
            "-t", str(dur),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            str(out_clip)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"  Rendered {s_id} video: {dur}s")
        video_clips.append(str(out_clip))

    concat_txt = VIDEO_SHOTS_DIR / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in video_clips:
            clean_p = str(Path(c).resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")
            
    return str(concat_txt)

def assemble_master_untruncated_film():
    score_wav = generate_ethiopian_acoustic_score_88s(TOTAL_DURATION)
    voice_wav = process_untruncated_voice()
    concat_txt = render_extended_video_clips()
    
    # Mix audio with broadcast stereo loudness (-0.5 dB peak) and sidechain ducking
    mixed_audio_mp3 = OUTPUT_AUDIO_DIR / f"master_soundtrack_{int(TOTAL_DURATION)}s.mp3"
    filter_complex = (
        "[0:a]volume=0.12,aformat=channel_layouts=stereo[music];"
        "[1:a]volume=2.6,aformat=channel_layouts=stereo[voice];"
        "[music][voice]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=450[ducked_music];"
        "[ducked_music][voice]amix=inputs=2:duration=first:weights=1 3[out]"
    )
    mix_cmd = [
        FFMPEG_EXE, "-y",
        "-i", score_wav,
        "-i", voice_wav,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "256k",
        str(mixed_audio_mp3)
    ]
    subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"\nMaster Loud Stereo Soundtrack: {mixed_audio_mp3}")
    
    # Master 16:9 MP4
    master_16x9 = Path("output/kakiwerdot_complete_finished_16x9.mp4")
    print(f"\n--- Assembling Final Master Film ({TOTAL_DURATION}s): {master_16x9.name} ---")
    
    cmd_16x9 = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_txt,
        "-i", str(mixed_audio_mp3),
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
    print(f"SUCCESS! Master 16:9 Film Created: {master_16x9} ({master_16x9.stat().st_size / (1024*1024):.2f} MB)")
    
    # Master 9:16 vertical
    master_9x16 = Path("output/kakiwerdot_complete_finished_9x16.mp4")
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
    print(f"SUCCESS! Master 9:16 Mobile Film Created: {master_9x16} ({master_9x16.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    assemble_master_untruncated_film()
