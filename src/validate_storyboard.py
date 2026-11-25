import json
import sys
from pathlib import Path

def validate():
    schema_path = Path("schema/storyboard.schema.json")
    storyboard_path = Path("storyboard.json")

    if not schema_path.exists():
        print(f"Error: Schema not found at {schema_path}")
        sys.exit(1)
    if not storyboard_path.exists():
        print(f"Error: Storyboard not found at {storyboard_path}")
        sys.exit(1)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    with open(storyboard_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Try jsonschema library if available
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        print("Schema validation PASSED using jsonschema validator.")
    except ImportError:
        print("Note: 'jsonschema' package not installed, running built-in validation checks...")
        # Core checks
        for req in schema.get("required", []):
            assert req in data, f"Missing required root field: {req}"
        
        assert 60.0 <= data["target_total_duration_seconds"] <= 90.0, "Total duration must be 60-90s"
        assert len(data["shots"]) >= 6, "Must have at least 6 shots"
        
        total_shot_duration = sum(s["duration_seconds"] for s in data["shots"])
        print(f"Total shots: {len(data['shots'])}, Total duration: {total_shot_duration:.1f}s")
        assert 60.0 <= total_shot_duration <= 90.0, f"Sum of shot durations ({total_shot_duration}s) outside 60-90s"

        for i, shot in enumerate(data["shots"]):
            for s_req in ["shot_id", "sequence_number", "duration_seconds", "narration", "visual_description", "camera", "lighting", "image_prompt", "video_prompt", "transition"]:
                assert s_req in shot, f"Shot {i+1} missing {s_req}"
            assert "amharic" in shot["narration"] and "english" in shot["narration"], f"Shot {i+1} narration must have amharic and english"

        print("Built-in schema validation PASSED successfully!")

    print(f"\nFilm Title: {data['title']}")
    print(f"Character: {data['character_reference']['name']} ({data['character_reference']['heritage']})")
    print(f"Total Shots: {len(data['shots'])}")
    print("Everything is ready for production pipeline!")

if __name__ == "__main__":
    validate()
