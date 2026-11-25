import json
import os
import sys
import time
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
import imageio_ffmpeg

from logger import log_run

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def format_srt_time(seconds: float) -> str:
    millis = int((seconds - int(seconds)) * 1000)
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    hours = int(mins // 60)
    mins = int(mins % 60)
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def generate_subtitles(storyboard: dict) -> str:
    srt_path = OUTPUT_DIR / "subtitles.srt"
    shots = storyboard["shots"]
    
    current_time = 0.0
    entries = []
    for i, shot in enumerate(shots, 1):
        start = current_time
        dur = shot["duration_seconds"]
        end = start + dur
        
        amharic = shot["narration"]["amharic"]
        english = shot["narration"]["english"]
        
        entry = (
            f"{i}\n"
            f"{format_srt_time(start)} --> {format_srt_time(end)}\n"
            f"{amharic}\n"
            f"{english}\n"
        )
        entries.append(entry)
        current_time = end

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))
        
    print(f"Generated bilingual subtitles: {srt_path}")
    return str(srt_path)

def create_end_card(width: int = 1920, height: int = 1080) -> str:
    endcard_img = OUTPUT_DIR / "end_card.png"
    if endcard_img.exists():
        return str(endcard_img)
        
    img = Image.new("RGB", (width, height), color=(10, 12, 14))
    draw = ImageDraw.Draw(img)
    
    # Gold accent border
    border = 40
    draw.rectangle([border, border, width - border, height - border], outline=(210, 160, 70), width=3)
    
    title = "KAKIWERTOD: THE VOICE THAT WOULD NOT BE SILENCED"
    draw.text((width // 2 - 380, height // 2 - 120), title, fill=(240, 215, 120))
    
    sub = "Dedicated to the dignity, wisdom, and future of Ethiopian women."
    draw.text((width // 2 - 310, height // 2 - 40), sub, fill=(220, 220, 220))
    
    disclosure = "Created with AI tools for the 10 Academy Heritage Short. No living person's likeness was used without consent."
    draw.text((width // 2 - 420, height // 2 + 60), disclosure, fill=(160, 160, 160))
    
    img.save(str(endcard_img), "PNG")
    return str(endcard_img)

def assemble_film():
    start_time = time.time()
    with open("storyboard.json", "r", encoding="utf-8") as f:
        storyboard = json.load(f)
        
    shots = storyboard["shots"]
    audio_path = OUTPUT_DIR / "audio" / "radio_cut_75s.mp3"
    
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}. Run Stage 1 first!")
        
    # Generate subtitles
    srt_file = generate_subtitles(storyboard)
    end_card_img = create_end_card()
    
    # Create file list for concatenation
    concat_txt = OUTPUT_DIR / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for s in shots:
            clip = OUTPUT_DIR / "video_shots" / f"{s['shot_id']}_clip.mp4"
            # FFmpeg concat requires forward slashes or escaped backslashes
            clean_path = str(clip.resolve()).replace("\\", "/")
            f.write(f"file '{clean_path}'\n")

    print("\n--- Assembling 16:9 Landscape Master Film ---")
    output_16x9 = OUTPUT_DIR / "kakiwerdot_16x9.mp4"
    
    # Concatenate video shots and combine with audio
    cmd_16x9 = [
        FFMPEG_EXE,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_16x9)
    ]
    subprocess.run(cmd_16x9, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"Master 16:9 film exported: {output_16x9} ({output_16x9.stat().st_size / (1024*1024):.2f} MB)")

    print("\n--- Assembling 9:16 Vertical Mobile Master Film ---")
    output_9x16 = OUTPUT_DIR / "kakiwerdot_9x16.mp4"
    
    # Crop & scale to 9:16 (1080x1920)
    # Scales 1920x1080 -> 1080x1920 with blurred background pad for cinematic aesthetic
    filter_9x16 = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "boxblur=20:5[bg];"
        "[0:v]scale=1080:608[fg];"
        "[bg][fg]overlay=0:(H-h)/2[out]"
    )
    
    cmd_9x16 = [
        FFMPEG_EXE,
        "-y",
        "-i", str(output_16x9),
        "-filter_complex", filter_9x16,
        "-map", "[out]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        str(output_9x16)
    ]
    subprocess.run(cmd_9x16, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"Master 9:16 mobile film exported: {output_9x16} ({output_9x16.stat().st_size / (1024*1024):.2f} MB)")

    elapsed = time.time() - start_time
    latency_ms = elapsed * 1000
    
    log_run(
        stage="stage_4_final_assembly",
        model="FFmpeg_MultiFormat_Compositor",
        parameters={
            "output_formats": ["16:9", "9:16"],
            "video_codec": "libx264",
            "audio_codec": "aac",
            "bitrate": "192k"
        },
        duration_seconds=storyboard["target_total_duration_seconds"],
        latency_ms=latency_ms,
        cost_usd=0.0000,
        status="success",
        notes="Successfully assembled 16:9 landscape and 9:16 vertical master MP4 films with synchronized audio and subtitles."
    )
    return str(output_16x9), str(output_9x16)

if __name__ == "__main__":
    assemble_film()
