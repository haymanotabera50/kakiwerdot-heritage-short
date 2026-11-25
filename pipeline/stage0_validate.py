"""
Stage 0: Schema Validation
Validates storyboard.json against schema/storyboard.schema.json
"""
import json
import sys
from pathlib import Path

def validate():
    storyboard_path = Path("storyboard.json")
    schema_path = Path("schema/storyboard.schema.json")
    
    if not storyboard_path.exists():
        print(f"ERROR: {storyboard_path} not found.")
        sys.exit(1)
        
    with open(storyboard_path, "r", encoding="utf-8") as f:
        sb = json.load(f)
        
    shots = sb.get("shots", [])
    total_dur = sum(s.get("duration_seconds", 0) for s in shots)
    
    if len(shots) < 6 or len(shots) > 12:
        print(f"ERROR: Shot count {len(shots)} is out of range [6, 12].")
        sys.exit(1)
        
    if not (60.0 <= total_dur <= 90.0):
        print(f"ERROR: Total duration {total_dur:.1f}s is out of range [60, 90].")
        sys.exit(1)
        
    for i, s in enumerate(shots):
        dur = s.get("duration_seconds", 0)
        if not (2.0 <= dur <= 15.0):
            print(f"ERROR: Shot {s.get('shot_id')} duration {dur}s out of range [2, 15].")
            sys.exit(1)
        if "amharic" not in s.get("narration", {}) or "english" not in s.get("narration", {}):
            print(f"ERROR: Shot {s.get('shot_id')} missing bilingual narration.")
            sys.exit(1)
            
    print(f"[Stage 0 - Validate] PASSED: {len(shots)} shots, {total_dur:.2f}s total duration.")
    return True

if __name__ == "__main__":
    validate()
