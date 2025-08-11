import json
import os
import time
from pathlib import Path
from typing import Any, Dict

LOG_PATH = os.getenv("LOG_PATH", "data/memory_log.jsonl")


def append_log(event: str, payload: Dict[str, Any]) -> str:
    Path("data").mkdir(exist_ok=True)
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **payload,
    }
    line = json.dumps(rec, ensure_ascii=False)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    return line
