import json
import os
import time
import subprocess
from pathlib import Path
import numpy as np
from scipy.io import wavfile
import certifi
from gtts import gTTS
import imageio_ffmpeg

os.environ['SSL_CERT_FILE'] = certifi.where()

OUTPUT_DIR = Path("output")
AUDIO_DIR = Path("output/audio_new_first_person")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# Brand new intimate first-person Amharic narration from Kakiwerdot herself
NEW_NARRATION_SHOTS = [
    {
        "shot_id": "SH_01",
        "duration": 10.0,
        "amharic": "ስሜ ቃቄ ወርድወት ይባላል። የተወለድኩት በጉራጌ አምባ፣ በእንሰት ጥላ ስር ነው።",
        "english": "My name is Kake Werdwot. I was born in the Gurage highlands, beneath the shade of the Enset."
    },
    {
        "shot_id": "SH_02",
        "duration": 10.0,
        "amharic": "ከልጅነቴ ጀምሮ፣ የሴቶች ጉልበት ምድርን ሲመግብ፣ ድምፃቸው ግን በዝምታ ሲታፈን ተመለከትኩ።",
        "english": "From my youth, I saw women's labor feed the earth, yet their voices were silenced."
    },
    {
        "shot_id": "SH_03",
        "duration": 10.0,
        "amharic": "አባቶቻችን በያጆካ ሸንጎ ሲሰበሰቡ፣ ለሴት ልጅ ክብርና የመምረጥ መብት ዝም አልልም አልኩ።",
        "english": "When our fathers gathered at the Yajoka assembly, I refused to remain silent on women's dignity and choice."
    },
    {
        "shot_id": "SH_04",
        "duration": 10.0,
        "amharic": "ወደ ሸንጎው መሃል ወጣሁ፤ ፍርሃት አልነበረኝም—የሴቶች እውነትና ፍትሕ በልቤ ነደደ።",
        "english": "I stepped into the center of the council; I knew no fear—truth and justice burned in my heart."
    },
    {
        "shot_id": "SH_05",
        "duration": 10.0,
        "amharic": "«ሴት ልጅ የባህል ጌጥ ብቻ ሳትሆን፣ የማህበረሰቡ ምሰሶ ናት» አልኳቸው።",
        "english": "'A woman is not merely an ornament of culture, but the pillar of the community,' I declared."
    },
    {
        "shot_id": "SH_06",
        "duration": 10.0,
        "amharic": "ሽማግሌዎቹ ዝም ብለው አደመጡኝ፤ የጉራጌ ሴቶችም ራሳቸውን ቀና አድርገው አዩ።",
        "english": "The elders listened in solemn silence; and Gurage women held their heads high."
    },
    {
        "shot_id": "SH_07",
        "duration": 8.0,
        "amharic": "ዛሬም ድምፄ በእያንዳንዱ ኢትዮጵያዊት ተማሪ፣ በእውቀትና በነጻነት ጎዳና ይቀጥላል።",
        "english": "Today, my voice lives on in every Ethiopian student, on the path of knowledge and freedom."
    },
    {
        "shot_id": "SH_08",
        "duration": 10.0,
        "amharic": "ድምፃችን ክብራችን ነው፤ መጻኢያችንን በገዛ እጃችን እንጽፋለን።",
        "english": "Our voice is our dignity; we shall write our future with our own hands."
    }
]

TLDS = ["com", "co.uk", "ca", "co.za"]

def generate_voice_file(text: str, dest_mp3: Path, max_retries: int = 5):
    if dest_mp3.exists() and dest_mp3.stat().st_size > 1000:
        return True
    for attempt in range(max_retries):
        tld = TLDS[attempt % len(TLDS)]
        try:
            tts = gTTS(text=text, lang="am", tld=tld, slow=False)
            tts.save(str(dest_mp3))
            if dest_mp3.exists() and dest_mp3.stat().st_size > 1000:
                print(f"  [TTS Generated] {dest_mp3.name} ({dest_mp3.stat().st_size} bytes)")
                time.sleep(1.2)
                return True
        except Exception as e:
            time.sleep(2)
    return False

def build_new_first_person_soundtrack():
    print("--- Synthesizing New First-Person Amharic Narration ---")
    wav_segments = []
    
    for shot in NEW_NARRATION_SHOTS:
        s_id = shot["shot_id"]
        shot_dur = shot["duration"]
        text = shot["amharic"]
        
        raw_mp3 = AUDIO_DIR / f"{s_id}_raw.mp3"
        padded_wav = AUDIO_DIR / f"{s_id}_padded.wav"
        
        print(f"Synthesizing voice for {s_id} ({shot_dur}s): '{text}'")
        if not generate_voice_file(text, raw_mp3):
            raise RuntimeError(f"Could not generate TTS for {s_id}")

        # Check speech duration
        p = subprocess.run([FFMPEG_EXE, "-i", str(raw_mp3)], stderr=subprocess.PIPE, text=True)
        raw_dur = 0.0
        for l in p.stderr.splitlines():
            if "Duration:" in l:
                d_str = l.split("Duration:")[1].split(",")[0].strip()
                m, s = d_str.split(":")[1:]
                raw_dur = float(m)*60 + float(s)
                break
        print(f"  --> Speech length: {raw_dur:.2f}s | Shot window: {shot_dur:.2f}s | Natural Breathing Room: +{shot_dur - raw_dur:.2f}s")
        assert raw_dur < shot_dur, f"Speech {raw_dur}s exceeds {shot_dur}s!"

        # Pad silence to exact shot duration
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
        
        rate, data = wavfile.read(padded_wav)
        wav_segments.append(data)

    # Master speech track (78.0s)
    full_speech = np.concatenate(wav_segments, axis=0)
    full_speech_wav = AUDIO_DIR / "new_first_person_speech_78s.wav"
    wavfile.write(str(full_speech_wav), 44100, full_speech)
    total_dur = full_speech.shape[0] / 44100
    print(f"\nMaster Speech Track Created: {full_speech_wav} ({total_dur:.1f}s)")

    # Score track (78.0s)
    music_wav = Path("output/audio_synced_finished/score_78s.wav")
    
    # Mix into loud broadcast stereo (-0.4 dB peak) with sidechain ducking
    soundtrack_mp3 = AUDIO_DIR / "new_first_person_soundtrack_78s.mp3"
    filter_complex = (
        "[0:a]volume=0.12,aformat=channel_layouts=stereo[music];"
        "[1:a]volume=2.8,aformat=channel_layouts=stereo[voice];"
        "[music][voice]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=450[ducked_music];"
        "[ducked_music][voice]amix=inputs=2:duration=first:weights=1 3[out]"
    )
    mix_cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(music_wav),
        "-i", str(full_speech_wav),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ar", "44100",
        "-ac", "2",
        "-b:a", "256k",
        str(soundtrack_mp3)
    ]
    subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"Master Mixed Soundtrack: {soundtrack_mp3}")
    return str(soundtrack_mp3)

def assemble_new_film(soundtrack_path: str):
    concat_txt = Path("output/video_shots_authentic_gurage/concat_list_78s.txt")
    out_16x9 = OUTPUT_DIR / "kakiwerdot_new_first_person_synced_16x9.mp4"
    
    print(f"\n--- Assembling New 16:9 Synced Film: {out_16x9.name} ---")
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", soundtrack_path,
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
        str(out_16x9)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"SUCCESS! New 16:9 Film Created: {out_16x9} ({out_16x9.stat().st_size / (1024*1024):.2f} MB)")

    # 9:16 vertical
    out_9x16 = OUTPUT_DIR / "kakiwerdot_new_first_person_synced_9x16.mp4"
    filter_9x16 = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
        "[0:v]scale=1080:608[fg];"
        "[bg][fg]overlay=0:(H-h)/2[out]"
    )
    cmd_9x16 = [
        FFMPEG_EXE, "-y",
        "-i", str(out_16x9),
        "-filter_complex", filter_9x16,
        "-map", "[out]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(out_9x16)
    ]
    subprocess.run(cmd_9x16, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"SUCCESS! New 9:16 Mobile Film Created: {out_9x16} ({out_9x16.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    audio = build_new_first_person_soundtrack()
    assemble_new_film(audio)
