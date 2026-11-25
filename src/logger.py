import json
import time
from datetime import datetime, timezone
from pathlib import Path

RUNS_FILE = Path("runs.jsonl")

def log_run(stage: str, model: str, parameters: dict, duration_seconds: float, latency_ms: float, cost_usd: float, status: str, notes: str = ""):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "model": model,
        "parameters": parameters,
        "duration_seconds": round(duration_seconds, 2),
        "latency_ms": round(latency_ms, 2),
        "cost_usd": round(cost_usd, 6),
        "status": status,
        "notes": notes
    }
    with open(RUNS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"Logged to runs.jsonl: [{stage}] {model} - status: {status} ({latency_ms:.0f}ms, ${cost_usd:.4f})")
