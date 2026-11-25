import json
import os
import subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import imageio_ffmpeg

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()
INPUT_DIR = Path("output/audio_life_story")
OUTPUT_DIR = Path("output/merged_narration")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def merge_voices(pause_seconds: float = 0.85):
    """
    Merges the 8 individual narration voice files into a single, seamless,
    continuous narration track with natural conversational breath pauses.
    """
    print(f"--- Merging 8 Narration Voice Files with {pause_seconds}s Natural Breathing Pauses ---")
    
    # 1. Convert each raw mp3 into standard PCM WAV
    sample_rate = 44100
    pause_samples = int(pause_seconds * sample_rate)
    silence_gap = np.zeros((pause_samples, 2), dtype=np.int16)
    
    audio_segments = []
    
    for i in range(1, 9):
        shot_id = f"SH_0{i}"
        mp3_file = INPUT_DIR / f"{shot_id}_voice.mp3"
        tmp_wav = OUTPUT_DIR / f"{shot_id}_clean.wav"
        
        # Convert mp3 to 44.1kHz stereo 16-bit WAV with gentle silenceremove
        cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(mp3_file),
            "-af", "silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse",
            "-ar", str(sample_rate),
            "-ac", "2",
            str(tmp_wav)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        rate, data = wavfile.read(tmp_wav)
        audio_segments.append(data)
        print(f"  Processed {shot_id}: duration = {data.shape[0] / rate:.2f}s")
        
        # Add natural breathing pause between sentences (except after the last one)
        if i < 8:
            audio_segments.append(silence_gap)

    # 2. Concatenate all audio segments
    merged_audio = np.concatenate(audio_segments, axis=0)
    total_speech_duration = merged_audio.shape[0] / sample_rate
    print(f"\nUnified Merged Speech Duration: {total_speech_duration:.2f} seconds")
    
    merged_wav = OUTPUT_DIR / "kakiwerdot_merged_narration_clean.wav"
    wavfile.write(merged_wav, sample_rate, merged_audio)
    
    # Export clean merged MP3
    merged_mp3 = OUTPUT_DIR / "kakiwerdot_merged_narration_clean.mp3"
    cmd_mp3 = [
        FFMPEG_EXE, "-y",
        "-i", str(merged_wav),
        "-b:a", "192k",
        str(merged_mp3)
    ]
    subprocess.run(cmd_mp3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"--> Standalone Merged Narration MP3: {merged_mp3} ({merged_mp3.stat().st_size / 1024:.1f} KB)")
    
    # 3. Create full-film paced track (fit into 75-second timeline with intro and outro breathing space)
    # Intro pause: 2.0s of evocative Kirar strings before speech starts
    # Speech: ~50s of continuous narrative
    # Outro: ~23s of swelling strings and hero conclusion
    intro_samples = int(2.0 * sample_rate)
    intro_gap = np.zeros((intro_samples, 2), dtype=np.int16)
    
    total_film_samples = int(75.0 * sample_rate)
    remaining_samples = total_film_samples - (intro_samples + merged_audio.shape[0])
    
    if remaining_samples > 0:
        outro_gap = np.zeros((remaining_samples, 2), dtype=np.int16)
        timeline_audio = np.concatenate([intro_gap, merged_audio, outro_gap], axis=0)
    else:
        timeline_audio = np.concatenate([intro_gap, merged_audio], axis=0)
        
    timeline_wav = OUTPUT_DIR / "kakiwerdot_narration_timed_75s.wav"
    wavfile.write(timeline_wav, sample_rate, timeline_audio)
    
    # 4. Mix with acoustic Kirar score and sidechain ducking
    music_src = Path("output/audio/background_music_ace_step_simulation.wav")
    final_mixed_mp3 = OUTPUT_DIR / "kakiwerdot_merged_narration_music_ducked_75s.mp3"
    
    filter_complex = (
        "[0:a]volume=0.32[music];"
        "[1:a]volume=1.35[voice];"
        "[music][voice]sidechaincompress=threshold=0.07:ratio=4.5:attack=40:release=450[ducked_music];"
        "[ducked_music][voice]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )
    mix_cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(music_src),
        "-i", str(timeline_wav),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-b:a", "192k",
        str(final_mixed_mp3)
    ]
    subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"--> Master Mixed Audio (Merged Narration + Music): {final_mixed_mp3}")

    # 5. Assemble new 16:9 video film with this merged continuous narration!
    concat_txt = Path("output/video_shots_authentic_gurage/concat_list.txt")
    new_video_16x9 = Path("output/kakiwerdot_merged_narration_life_story_16x9.mp4")
    
    print(f"\n--- Assembling New 16:9 Film: {new_video_16x9.name} ---")
    video_cmd = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", str(final_mixed_mp3),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(new_video_16x9)
    ]
    subprocess.run(video_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"SUCCESS! New 16:9 Video Created: {new_video_16x9} ({new_video_16x9.stat().st_size / (1024*1024):.2f} MB)")
    
    return str(merged_mp3), str(final_mixed_mp3), str(new_video_16x9)

if __name__ == "__main__":
    merge_voices()
