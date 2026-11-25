"""
Stage 3: Moving Shots Generation
Renders camera motion for each keyframe using Ken Burns pans and zooms.
Matches the exact narration duration of each shot (85.0s total across 8 shots).
Implements caching to skip already-rendered clips unless forced.
"""
import json
import subprocess
import sys
from pathlib import Path
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
KEYFRAMES_DIR = Path("output/keyframes_authentic_gurage")
VIDEO_DIR = Path("output/video_merged_8")
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

def render_moving_shots(force: bool = False):
    with open("storyboard.json", "r", encoding="utf-8") as f:
        sb = json.load(f)
        
    shots = sb.get("shots", [])
    print(f"\n[Stage 3 - Moving Shots] Generating {len(shots)} cinematic clips...")
    
    clips = []
    for shot in shots:
        s_id = shot["shot_id"]
        dur = shot["duration_seconds"]
        kf_path = KEYFRAMES_DIR / f"{s_id}_keyframe.png"
        out_clip = VIDEO_DIR / f"{s_id}_clip.mp4"
        
        # Check cache
        if out_clip.exists() and not force:
            print(f"  {s_id}: [CACHED] {out_clip.name} ({out_clip.stat().st_size / 1024:.1f} KB)")
            clips.append(str(out_clip))
            continue
            
        total_frames = int(dur * 30)
        if s_id in ["SH_01", "SH_05"]:
            zoom_expr = "'min(zoom+0.0005,1.15)'"
        elif s_id in ["SH_02", "SH_04"]:
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
        print(f"  {s_id}: [RENDERED] {out_clip.name} ({dur:.2f}s)")
        clips.append(str(out_clip))
        
    # Write concat manifest
    manifest = VIDEO_DIR / "concat_list.txt"
    with open(manifest, "w", encoding="utf-8") as f:
        for c in clips:
            clean_p = str(Path(c).resolve()).replace("\\", "/")
            f.write(f"file '{clean_p}'\n")
            
    print(f"[Stage 3 - Moving Shots] SUCCESS: Manifest written to {manifest}")
    return str(manifest)

if __name__ == "__main__":
    render_moving_shots()
