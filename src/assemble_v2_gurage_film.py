import json
import os
import subprocess
from pathlib import Path
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

artifactDir = Path(r"C:\Users\haymanotabera\.gemini\antigravity\brain\b395a557-06d5-4249-a81b-9fdde283a62c")
keyframe_dir = Path("output/keyframes_authentic_gurage")
video_shots_dir = Path("output/video_shots_authentic_gurage")
keyframe_dir.mkdir(parents=True, exist_ok=True)
video_shots_dir.mkdir(parents=True, exist_ok=True)

# Copy the authentic Gurage keyframes
shot_map = {
    "SH_01": artifactDir / "gurage_v2_sh01_1795585894468.jpg",
    "SH_02": artifactDir / "gurage_v2_sh02_1795585904333.jpg",
    "SH_03": artifactDir / "gurage_v2_sh03_1795585913459.jpg",
    "SH_04": artifactDir / "gurage_v2_sh04_1795585922770.jpg",
    "SH_05": artifactDir / "sh_05_keyframe_1795585331868.jpg",
    "SH_06": artifactDir / "sh_06_keyframe_v2_1795585365497.jpg",
    "SH_07": artifactDir / "sh_07_keyframe_1795585345956.jpg",
    "SH_08": artifactDir / "sh_08_keyframe_1795585355350.jpg"
}

import shutil
for shot_id, src_path in shot_map.items():
    dest_path = keyframe_dir / f"{shot_id}_keyframe.png"
    shutil.copyfile(src_path, dest_path)
    print(f"Copied {src_path.name} -> {dest_path}")

with open("storyboard.json", "r", encoding="utf-8") as f:
    storyboard = json.load(f)

shots = storyboard["shots"]
video_clips = []

print("\n--- Rendering Ken Burns video clips for Authentic Gurage cut ---")
for shot in shots:
    shot_id = shot["shot_id"]
    duration = shot["duration_seconds"]
    kf_path = keyframe_dir / f"{shot_id}_keyframe.png"
    out_clip = video_shots_dir / f"{shot_id}_clip.mp4"
    
    total_frames = int(duration * 30)
    seq = shot["sequence_number"]
    if seq in [1, 5]:
        zoom_expr = "'min(zoom+0.0006,1.15)'"
    elif seq in [2, 4]:
        zoom_expr = "'min(zoom+0.0004,1.10)'"
    elif seq in [7, 8]:
        zoom_expr = "'max(1.15-0.0006*on,1.0)'"
    else:
        zoom_expr = "'min(zoom+0.0005,1.12)'"

    cmd = [
        FFMPEG_EXE, "-y",
        "-loop", "1",
        "-i", str(kf_path),
        "-vf", f"zoompan=z={zoom_expr}:d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30",
        "-t", str(duration),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(out_clip)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"Rendered video clip: {out_clip} ({duration}s)")
    video_clips.append(str(out_clip))

# Concat video clips
concat_txt = video_shots_dir / "concat_list.txt"
with open(concat_txt, "w", encoding="utf-8") as f:
    for c in video_clips:
        clean_p = str(Path(c).resolve()).replace("\\", "/")
        f.write(f"file '{clean_p}'\n")

# Audio is the genuine Amharic spoken speech track!
audio_speech_track = Path("output/audio_v2/radio_cut_amharic_spoken_75s.mp3")
final_16x9 = Path("output/kakiwerdot_authentic_gurage_with_amharic_speech_16x9.mp4")

print(f"\n--- Assembling {final_16x9.name} with real Amharic voice ---")
cmd_16x9 = [
    FFMPEG_EXE, "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", str(concat_txt),
    "-i", str(audio_speech_track),
    "-c:v", "libx264",
    "-c:a", "aac",
    "-b:a", "192k",
    "-pix_fmt", "yuv420p",
    "-shortest",
    str(final_16x9)
]
subprocess.run(cmd_16x9, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"--> Master 16:9 Authentic Film Created: {final_16x9} ({final_16x9.stat().st_size / (1024*1024):.2f} MB)")

# Vertical mobile cut
final_9x16 = Path("output/kakiwerdot_authentic_gurage_with_amharic_speech_9x16.mp4")
filter_9x16 = (
    "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
    "boxblur=20:5[bg];"
    "[0:v]scale=1080:608[fg];"
    "[bg][fg]overlay=0:(H-h)/2[out]"
)
cmd_9x16 = [
    FFMPEG_EXE, "-y",
    "-i", str(final_16x9),
    "-filter_complex", filter_9x16,
    "-map", "[out]",
    "-map", "0:a",
    "-c:v", "libx264",
    "-c:a", "copy",
    "-pix_fmt", "yuv420p",
    str(final_9x16)
]
subprocess.run(cmd_9x16, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
print(f"--> Master 9:16 Authentic Mobile Film Created: {final_9x16} ({final_9x16.stat().st_size / (1024*1024):.2f} MB)")
print("ALL COMPLETE!")
