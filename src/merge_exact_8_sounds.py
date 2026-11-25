import json
import os
import subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("output/audio_merged_8")
VIDEO_DIR = Path("output/video_merged_8")
KEYFRAMES_DIR = Path("output/keyframes_authentic_gurage")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# The exact 8 narration sound durations measured from the files
SHOT_DURATIONS = [
    ("SH_01", 12.36),
    ("SH_02", 10.56),
    ("SH_03", 11.21),
    ("SH_04", 10.90),
    ("SH_05", 10.70),
    ("SH_06", 9.58),
    ("SH_07", 9.74),
    ("SH_08", 9.96)
]

TOTAL_DURATION = sum(d[1] for d in SHOT_DURATIONS)
print(f"Total Merged 8 Narration Audio Duration: {TOTAL_DURATION:.2f} seconds")

def merge_the_8_sounds():
    print("\n--- Merging the 8 Narration Sounds Directly ---")
    wav_segments = []
    sample_rate = 44100
    
    for shot_id, dur in SHOT_DURATIONS:
        raw_mp3 = Path(f"output/audio_life_story/{shot_id}_voice.mp3")
        temp_wav = AUDIO_DIR / f"{shot_id}_temp.wav"
        
        # Convert each raw mp3 to exact 44100Hz stereo WAV without modifying pitch or speed
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(raw_mp3),
            "-ar", str(sample_rate),
            "-ac", "2",
            str(temp_wav)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        rate, data = wavfile.read(temp_wav)
        wav_segments.append(data)
        print(f"  Merged {shot_id}: {data.shape[0]/rate:.2f}s")

    # Direct concatenation of all 8 narration sounds
    merged_speech = np.concatenate(wav_segments, axis=0)
    merged_speech_wav = AUDIO_DIR / "merged_8_narrations.wav"
    wavfile.write(str(merged_speech_wav), sample_rate, merged_audio := merged_speech)
    actual_dur = merged_audio.shape[0] / sample_rate
    print(f"--> Combined 8 Narration Voice Track: {merged_speech_wav} ({actual_dur:.2f}s)")
    return str(merged_speech_wav), actual_dur

def generate_background_music(total_dur: float, sample_rate: int = 44100):
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

def render_matching_video_shots():
    print("\n--- Rendering 8 Video Shots Matching Exact Narration Durations ---")
    video_clips = []
    
    for shot_id, dur in SHOT_DURATIONS:
        kf_path = KEYFRAMES_DIR / f"{shot_id}_keyframe.png"
        out_clip = VIDEO_DIR / f"{shot_id}_clip.mp4"
        total_frames = int(dur * 30)
        
        # Camera motion expressions
        if shot_id in ["SH_01", "SH_05"]:
            zoom_expr = "'min(zoom+0.0005,1.15)'"
        elif shot_id in ["SH_02", "SH_04"]:
            zoom_expr = "'min(zoom+0.0004,1.10)'"
        else:
            zoom_expr = "'max(1.15-0.0005*on,1.0)'"

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
        print(f"  Rendered {shot_id} video: {dur:.2f}s")
        video_clips.append(str(out_clip))

    concat_txt = VIDEO_DIR / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in video_clips:
            clean_p = str(Path(c).resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")
            
    return str(concat_txt)

def assemble():
    merged_voice_wav, actual_dur = merge_the_8_sounds()
    music_wav = generate_background_music(actual_dur)
    concat_txt = render_matching_video_shots()
    
    # Mix into loud broadcast stereo (-0.4 dB peak) with sidechain ducking
    soundtrack_mp3 = AUDIO_DIR / "final_soundtrack_merged_8.mp3"
    filter_complex = (
        "[0:a]volume=0.12,aformat=channel_layouts=stereo[music];"
        "[1:a]volume=2.8,aformat=channel_layouts=stereo[voice];"
        "[music][voice]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=450[ducked_music];"
        "[ducked_music][voice]amix=inputs=2:duration=first:weights=1 3[out]"
    )
    mix_cmd = [
        FFMPEG_EXE, "-y",
        "-i", music_wav,
        "-i", merged_voice_wav,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "256k",
        str(soundtrack_mp3)
    ]
    subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"\nFinal Mixed Soundtrack: {soundtrack_mp3}")
    
    # 16:9 master video
    master_16x9 = OUTPUT_DIR / "kakiwerdot_merged_8_narrations_16x9.mp4"
    print(f"\n--- Assembling 16:9 Master Video: {master_16x9.name} ---")
    
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
    print(f"SUCCESS! Master 16:9 Film Created: {master_16x9} ({master_16x9.stat().st_size / (1024*1024):.2f} MB)")
    
    # 9:16 mobile master
    master_9x16 = OUTPUT_DIR / "kakiwerdot_merged_8_narrations_9x16.mp4"
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
    assemble()
