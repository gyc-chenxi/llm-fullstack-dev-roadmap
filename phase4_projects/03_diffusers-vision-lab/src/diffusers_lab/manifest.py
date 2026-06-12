from pathlib import Path
import json
import time
import uuid

def new_run_id(task: str, seed: int) -> str:
    ts = time.strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:6]
    return f"{task}_{ts}_seed{seed}_{short}"

def append_manifest(path: str | Path, record: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
