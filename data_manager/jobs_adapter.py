# data_manager/jobs_adapter.py
import json
from pathlib import Path
from threading import Lock
from datetime import datetime
import os

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(exist_ok=True)
JOBS_FILE = DATA_DIR / "jobs.json"
RECEIPTS_FILE = DATA_DIR / "receipts.json"

_lock = Lock()

def _read_jobs():
    if not JOBS_FILE.exists():
        return {}
    try:
        return json.loads(JOBS_FILE.read_text(encoding="utf-8"))
    except:
        return {}

def _write_jobs(d):
    JOBS_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

def _append_receipt(r):
    try:
        if not RECEIPTS_FILE.exists():
            RECEIPTS_FILE.write_text("[]", encoding="utf-8")
        arr = json.loads(RECEPTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        arr = []
    arr.append(r)
    RECEIPTS_FILE.write_text(json.dumps(arr, ensure_ascii=False, indent=2), encoding="utf-8")

class JobsAdapter:
    def __init__(self):
        self.jobs_file = JOBS_FILE
        self._lock = _lock

    def create_job(self, job_id: str, payload: dict):
        with self._lock:
            data = _read_jobs()
            data[job_id] = {"id": job_id, "created_at": datetime.utcnow().isoformat()+"Z", **payload}
            _write_jobs(data)
            return data[job_id]

    def get_job(self, job_id: str):
        with self._lock:
            data = _read_jobs()
            return data.get(job_id)

    def update_job(self, job_id: str, updates: dict):
        with self._lock:
            data = _read_jobs()
            if job_id not in data:
                return None
            data[job_id].update(updates)
            data[job_id]["updated_at"] = datetime.utcnow().isoformat()+"Z"
            _write_jobs(data)
            return data[job_id]

def append_receipt_fallback(result):
    # normalize result into receipt-like dict
    rec = {
        "id": result.get("id"),
        "store_name": result.get("entities", {}).get("store_name", ""),
        "total_amount": result.get("entities", {}).get("total_amount", 0),
        "date": result.get("entities", {}).get("date", ""),
        "raw_text": result.get("raw_text", ""),
        "processed_date": result.get("processed_date"),
        "confidence": result.get("entities", {}).get("confidence", 0),
        "items": result.get("entities", {}).get("items", []),
    }
    _append_receipt(rec)
