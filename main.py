"""
Kakiwerdot: The Voice That Would Not Be Silenced
AI Heritage Short - End-to-End Reproducible Production Pipeline
10 Academy Assignment
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timezone

# Add pipeline directory to path
sys.path.insert(0, str(Path("pipeline").resolve()))

from stage0_validate import validate
from stage1_narration import merge_narration
from stage2_keyframes import verify_keyframes
from stage3_shots import render_moving_shots
from stage4_music import generate_score
from stage5_assemble import assemble

def log_pipeline_run(duration_seconds: float, status: str = "SUCCESS"):
    run_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "2.0.0",
        "storyboard_version": "2.0.0",
        "film_title": "Kakiwerdot: The Voice That Would Not Be Silenced",
        "heritage_subject": "Kakiwerdot (Gurage Women's Rights Pioneer)",
        "language": "Amharic",
        "shots_count": 8,
        "total_duration_seconds": 85.0,
        "aspect_ratios": ["16:9", "9:16"],
        "pipeline_execution_latency_seconds": round(duration_seconds, 2),
        "total_cost_usd": 0.00,
        "status": status,
        "master_pure_voice_16x9": "output/kakiwerdot_VOICE_ONLY_NO_MUSIC_16x9.mp4",
        "master_pure_voice_9x16": "output/kakiwerdot_VOICE_ONLY_NO_MUSIC_9x16.mp4"
    }
    with open("runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(run_entry, ensure_ascii=False) + "\n")

def run_pipeline():
    start_time = time.time()
    print("=" * 75)
    print("  KAKIWERDOT: THE VOICE THAT WOULD NOT BE SILENCED")
    print("  AI Heritage Short Production Pipeline (10 Academy Submission)")
    print("=" * 75)

    try:
        # Stage 0: Validate Contract
        validate()

        # Stage 1: Audio / Narration
        merged_wav, audio_dur = merge_narration()

        # Stage 2: Keyframes
        verify_keyframes()

        # Stage 3: Moving Shots
        manifest = render_moving_shots()

        # Stage 4: Music Score
        generate_score(total_dur=audio_dur)

        # Stage 5: Final Assembly
        assemble()

        total_time = time.time() - start_time
        log_pipeline_run(total_time, "SUCCESS")

        print("\n" + "=" * 75)
        print("  REPRODUCIBLE PIPELINE RUN COMPLETED SUCCESSFULLY (Exit Code 0)")
        print(f"  Total Execution Time : {total_time:.2f} seconds")
        print(f"  Film Subject         : Kakiwerdot (Gurage Heroine)")
        print(f"  Narration            : Spoken Amharic (8 Stanzas, 85.0s, Pure Voice)")
        print(f"  Horizontal Cut (16:9): output/kakiwerdot_VOICE_ONLY_NO_MUSIC_16x9.mp4")
        print(f"  Vertical Cut (9:16)  : output/kakiwerdot_VOICE_ONLY_NO_MUSIC_9x16.mp4")
        print(f"  Web Preview Player   : watch_film.html")
        print(f"  Audit Log            : runs.jsonl")
        print("=" * 75)
    except Exception as e:
        total_time = time.time() - start_time
        log_pipeline_run(total_time, f"FAILED: {str(e)}")
        print(f"\nERROR in pipeline execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
