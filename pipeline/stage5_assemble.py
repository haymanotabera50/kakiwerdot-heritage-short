"""
Stage 5: Final Film Assembly
Muxes audio and video with exact sync into dual aspect ratios:
- 16:9 Landscape (1920x1080)
- 9:16 Mobile Vertical (1080x1920)
Provides both Pure Narration Sound (zero music) and Broadcast Master cuts.
"""
import subprocess
import sys
from pathlib import Path
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("output/audio_merged_8")
VIDEO_DIR = Path("output/video_merged_8")

def assemble():
    print("\n[Stage 5 - Assembly] Assembling final films...")
    concat_txt = VIDEO_DIR / "concat_list.txt"
    merged_voice_wav = AUDIO_DIR / "merged_8_narrations.wav"
    
    if not concat_txt.exists():
        print(f"ERROR: Video manifest {concat_txt} not found.")
        sys.exit(1)
    if not merged_voice_wav.exists():
        print(f"ERROR: Voice audio {merged_voice_wav} not found.")
        sys.exit(1)

    # 1. Pure Narration Master (16:9 Landscape, 85s, zero music)
    pure_16x9 = OUTPUT_DIR / "kakiwerdot_VOICE_ONLY_NO_MUSIC_16x9.mp4"
    print(f"  Rendering Pure Voice 16:9: {pure_16x9.name}...")
    cmd_pure_16x9 = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(merged_voice_wav),
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-af", "volume=2.4",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "256k",
        "-ar", "44100",
        "-ac", "2",
        "-shortest",
        "-movflags", "+faststart",
        str(pure_16x9)
    ]
    subprocess.run(cmd_pure_16x9, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  [DONE] {pure_16x9.name} ({pure_16x9.stat().st_size / (1024*1024):.2f} MB)")

    # 2. Pure Narration Master (9:16 Vertical Mobile, 85s)
    pure_9x16 = OUTPUT_DIR / "kakiwerdot_VOICE_ONLY_NO_MUSIC_9x16.mp4"
    print(f"  Rendering Pure Voice 9:16: {pure_9x16.name}...")
    filter_9x16 = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
        "[0:v]scale=1080:608[fg];"
        "[bg][fg]overlay=0:(H-h)/2[out]"
    )
    cmd_pure_9x16 = [
        FFMPEG_EXE, "-y",
        "-i", str(pure_16x9),
        "-filter_complex", filter_9x16,
        "-map", "[out]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(pure_9x16)
    ]
    subprocess.run(cmd_pure_9x16, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"  [DONE] {pure_9x16.name} ({pure_9x16.stat().st_size / (1024*1024):.2f} MB)")

    # 3. Broadcast Master with subtle ducked Kirar score
    music_wav = AUDIO_DIR / "score_85s.wav"
    if music_wav.exists():
        broadcast_16x9 = OUTPUT_DIR / "kakiwerdot_broadcast_master_16x9.mp4"
        broadcast_soundtrack = AUDIO_DIR / "soundtrack_broadcast_ducked_85s.mp3"
        filter_complex = (
            "[0:a]volume=0.08,aformat=channel_layouts=stereo[music];"
            "[1:a]volume=2.6,aformat=channel_layouts=stereo[voice];"
            "[music][voice]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=450[ducked_music];"
            "[ducked_music][voice]amix=inputs=2:duration=first:weights=1 3[out]"
        )
        mix_cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(music_wav),
            "-i", str(merged_voice_wav),
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-ar", "44100",
            "-ac", "2",
            "-b:a", "256k",
            str(broadcast_soundtrack)
        ]
        subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        cmd_broadcast_16x9 = [
            FFMPEG_EXE, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-i", str(broadcast_soundtrack),
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
            str(broadcast_16x9)
        ]
        subprocess.run(cmd_broadcast_16x9, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"  [DONE] Broadcast Master 16:9: {broadcast_16x9.name}")

    print("[Stage 5 - Assembly] SUCCESS: All exports finished.")

if __name__ == "__main__":
    assemble()
