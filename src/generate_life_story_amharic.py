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

OUTPUT_AUDIO_DIR = Path("output/audio_life_story")
OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# The authentic life story of Kake Werdwot in Amharic
LIFE_STORY_SHOTS = [
    {
        "shot_id": "SH_01",
        "duration": 10.0,
        "amharic": "በጉራጌ አምባ በእንሰት ማሳዎች መካከል፣ በ19ኛው መቶ ክፍለ ዘመን አንዲት ጀግና ሴት ተወለደች—ስሟም ቃቄ ወርድወት ይባላል።",
        "english": "In the Gurage highlands amidst the Enset fields, in the 19th century a brave woman was born—her name was Kake Werdwot."
    },
    {
        "shot_id": "SH_02",
        "duration": 10.0,
        "amharic": "ወጣት ሳለች፣ የሴቶች የዕለት ተዕለት ድካምና በባህሉ የሚደርስባቸውን የግዳጅ ጋብቻ እና መከራ በልቧ አሰበችበት።",
        "english": "In her youth, she deeply reflected on women's daily toil and the burdens of forced marriage and hardship imposed by custom."
    },
    {
        "shot_id": "SH_03",
        "duration": 10.0,
        "amharic": "ሴቶች በሸንጎ ድምጽ ባልነበራቸው በዚያ ዘመን፣ ዝምታን ሰብራ የሴቶችን ብሶት ይዛ ወደ ያጆካ የሽማግሌዎች ጉባኤ አመራች።",
        "english": "In that era when women had no voice in assemblies, she broke the silence and carried women's grievances to the Yajoka council of elders."
    },
    {
        "shot_id": "SH_04",
        "duration": 10.0,
        "amharic": "ቃቄ ወርድወት አልፈራችም፤ በክብር ቆማ የሴቶችን የመምረጥ፣ የመከበርና የፍትሕ መብት በጠንካራ ቃላት አስደመጠች።",
        "english": "Kake Werdwot showed no fear; standing with dignity, she declared women's rights to choose, to be respected, and to have justice."
    },
    {
        "shot_id": "SH_05",
        "duration": 10.0,
        "amharic": "«ሴት ልጅ የቤት አገልጋይ ብቻ ሳትሆን፣ የማህበረሰቡ ምሰሶ ናት» በማለት በታሪክ የማይረሳውን የፍትሕ ጥሪ አሰማች።",
        "english": "'A woman is not merely a household servant, but the pillar of the community,' she proclaimed, sounding an unforgettable call for justice."
    },
    {
        "shot_id": "SH_06",
        "duration": 10.0,
        "amharic": "ሽማግሌዎቹ በአመክንዮዋና በድፍረቷ ተደንቀው አደመጧት፤ የጉራጌ ሴቶችም በድምጿ ብርታት አገኙ።",
        "english": "The elders listened in awe of her logic and courage; and Gurage women found strength in her voice."
    },
    {
        "shot_id": "SH_07",
        "duration": 8.0,
        "amharic": "የቃቄ የህይወት ትግል በባህል ውስጥ ለሴቶች ክብርና ለትምህርት በር የከፈተ፣ ለዛሬው ትውልድ ትልቅ ፋና ሆነ።",
        "english": "Kake's life struggle opened doors for women's dignity and education within culture, becoming a guiding light for today's generation."
    },
    {
        "shot_id": "SH_08",
        "duration": 7.0,
        "amharic": "ቃቄ ወርድወት ዛሬም በኢትዮጵያውያን ሴቶች ልብ ውስጥ አልሞተችም፤ ድምጿ የነጻነትና የክብራችን ዘላለማዊ አርማ ነው።",
        "english": "Kake Werdwot lives on in the hearts of Ethiopian women today; her voice remains an eternal symbol of our freedom and dignity."
    }
]

TLDS = ["com", "co.uk", "ca", "co.za"]

def generate_voice_file(text: str, dest_mp3: Path, max_retries: int = 4):
    if dest_mp3.exists() and dest_mp3.stat().st_size > 1000:
        return True
    for attempt in range(max_retries):
        tld = TLDS[attempt % len(TLDS)]
        try:
            tts = gTTS(text=text, lang="am", tld=tld, slow=False)
            tts.save(str(dest_mp3))
            if dest_mp3.exists() and dest_mp3.stat().st_size > 1000:
                time.sleep(1.2)
                return True
        except Exception as e:
            time.sleep(2)
    return False

def build_amharic_life_story_track():
    print("--- Synthesizing Spoken Amharic Narration: The Life of Kake Werdwot ---")
    wav_segments = []
    
    for shot in LIFE_STORY_SHOTS:
        s_id = shot["shot_id"]
        dur = shot["duration"]
        text = shot["amharic"]
        
        mp3_path = OUTPUT_AUDIO_DIR / f"{s_id}_voice.mp3"
        padded_wav = OUTPUT_AUDIO_DIR / f"{s_id}_padded.wav"
        
        print(f"Generating Amharic voice for {s_id} ({dur}s)...")
        if not generate_voice_file(text, mp3_path):
            raise RuntimeError(f"Could not synthesize Amharic speech for {s_id}")
            
        pad_cmd = [
            FFMPEG_EXE, "-y",
            "-i", str(mp3_path),
            "-af", f"apad=whole_dur={dur}",
            "-t", str(dur),
            "-ar", "44100",
            "-ac", "2",
            str(padded_wav)
        ]
        subprocess.run(pad_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        rate, data = wavfile.read(padded_wav)
        wav_segments.append(data)

    # Concatenate all 8 shots in numpy
    full_audio = np.concatenate(wav_segments, axis=0)
    full_speech_wav = OUTPUT_AUDIO_DIR / "kake_werdwot_life_speech_75s.wav"
    wavfile.write(full_speech_wav, 44100, full_audio)
    print(f"Master Amharic speech created: {full_speech_wav} ({full_audio.shape[0]/44100:.1f}s)")

    # Mix with acoustic Kirar score and sidechain ducking
    music_src = Path("output/audio/background_music_ace_step_simulation.wav")
    final_radio_cut = OUTPUT_AUDIO_DIR / "kake_werdwot_life_mixed_audio_75s.mp3"
    
    filter_complex = (
        "[0:a]volume=0.32[music];"
        "[1:a]volume=1.35[voice];"
        "[music][voice]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=400[ducked_music];"
        "[ducked_music][voice]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )
    
    mix_cmd = [
        FFMPEG_EXE, "-y",
        "-i", str(music_src),
        "-i", str(full_speech_wav),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-b:a", "192k",
        str(final_radio_cut)
    ]
    subprocess.run(mix_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"Final mixed audio with ducking: {final_radio_cut}")
    return str(final_radio_cut)

def assemble_16x9_life_story_film(audio_track_path: str):
    concat_txt = Path("output/video_shots_authentic_gurage/concat_list.txt")
    out_film_16x9 = Path("output/kakiwerdot_life_story_amharic_16x9.mp4")
    
    print(f"\n--- Assembling 16:9 Master Film: {out_film_16x9.name} ---")
    cmd = [
        FFMPEG_EXE, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt),
        "-i", audio_track_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(out_film_16x9)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"SUCCESS! Master 16:9 Life Story Film created: {out_film_16x9} ({out_film_16x9.stat().st_size / (1024*1024):.2f} MB)")
    return str(out_film_16x9)

if __name__ == "__main__":
    audio = build_amharic_life_story_track()
    assemble_16x9_life_story_film(audio)
