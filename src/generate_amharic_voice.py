import json
import os
import time
import subprocess
from pathlib import Path
import certifi
from gtts import gTTS
import imageio_ffmpeg

os.environ['SSL_CERT_FILE'] = certifi.where()

OUTPUT_AUDIO_DIR = Path("output/audio_v2")
OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

TLDS = ["com", "co.uk", "ca", "co.za"]

def generate_voice_with_retry(text: str, dest_mp3: Path, max_retries: int = 5):
    if dest_mp3.exists() and dest_mp3.stat().st_size > 1000:
        print(f"  [Cache hit] {dest_mp3.name} already exists.")
        return True

    for attempt in range(max_retries):
        tld = TLDS[attempt % len(TLDS)]
        try:
            print(f"  Attempt {attempt + 1}/{max_retries} (tld={tld})...")
            tts = gTTS(text=text, lang="am", tld=tld, slow=False)
            tts.save(str(dest_mp3))
            if dest_mp3.exists() and dest_mp3.stat().st_size > 1000:
                print(f"  [Success] Saved {dest_mp3.name} ({dest_mp3.stat().st_size} bytes)")
                time.sleep(1.5)  # Politeness interval
                return True
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}. Retrying in 3 seconds...")
            time.sleep(3)

    return False

def generate_amharic_narration():
    with open("storyboard.json", "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    shots = storyboard["shots"]
    print(f"--- Generating Authentic Amharic Spoken Narration ({len(shots)} shots) ---")
    
    shot_audio_files = []
    
    for shot in shots:
        shot_id = shot["shot_id"]
        amharic_text = shot["narration"]["amharic"]
        shot_dur = shot["duration_seconds"]
        
        raw_mp3 = OUTPUT_AUDIO_DIR / f"{shot_id}_raw.mp3"
        padded_wav = OUTPUT_AUDIO_DIR / f"{shot_id}_padded.wav"
        
        print(f"\nProcessing {shot_id} ({shot_dur}s): '{amharic_text}'")
        success = generate_voice_with_retry(amharic_text, raw_mp3)
        if not success:
            raise RuntimeError(f"Failed to generate voice for {shot_id}")
            
        pad_cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(raw_mp3),
            "-af", f"apad=whole_dur={shot_dur}",
            "-t", str(shot_dur),
            "-ar", "44100",
            "-ac", "2",
            str(padded_wav)
        ]
        subprocess.run(pad_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        shot_audio_files.append(str(padded_wav))

    # Concat all 8 shots
    concat_list_file = OUTPUT_AUDIO_DIR / "voice_concat.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for fpath in shot_audio_files:
            clean_p = fpath.replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    full_narration_wav = OUTPUT_AUDIO_DIR / "amharic_narration_full.wav"
    concat_cmd = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
        "-c", "copy",
        str(full_narration_wav)
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    
    # Mix with acoustic backing music and ducking
    music_src = Path("output/audio/background_music_ace_step_simulation.wav")
    final_radio_cut = OUTPUT_AUDIO_DIR / "radio_cut_amharic_spoken_75s.mp3"
    
    filter_complex = (
        "[0:a]volume=0.35[music];"
        "[music][1:a]sidechaincompress=threshold=0.06:ratio=4:attack=50:release=400[ducked_music];"
        "[ducked_music][1:a]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )
    
    mix_cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(music_src),
        "-i", str(full_narration_wav),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-b:a", "192k",
        str(final_radio_cut)
    ]
    subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"\nFinal mixed Amharic spoken sound track: {final_radio_cut} ({final_radio_cut.stat().st_size / 1024:.1f} KB)")
    return str(final_radio_cut)

if __name__ == "__main__":
    generate_amharic_narration()
