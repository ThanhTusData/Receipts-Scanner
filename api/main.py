# api/main.py
import os
import uuid
import tempfile
import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil

from data_manager.s3_adapter import S3Adapter
from data_manager.jobs_adapter import JobsAdapter
from workers.celery_app import celery_app  # keep import for side-effects
from workers.tasks import process_receipt_task

from pathlib import Path
from fastapi import BackgroundTasks
import json

# prometheus
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# sentry
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except Exception:
    SENTRY_AVAILABLE = False

APP_PORT = int(os.getenv("API_PORT", 8080))
METRICS_PATH = os.getenv("METRICS_PATH", "/metrics")

app = FastAPI(title="ReceiptsScanner API - Day4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

s3 = S3Adapter()
jobs = JobsAdapter()  # file-based jobs store at data/jobs.json

# Prometheus metrics
REQUEST_COUNT = Counter("api_request_total", "Total HTTP requests", ["method", "endpoint", "http_status"])
REQUEST_LATENCY = Histogram("api_request_latency_seconds", "Request latency in seconds", ["endpoint"])

# init Sentry if provided
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN and SENTRY_AVAILABLE:
    sentry_sdk.init(dsn=SENTRY_DSN, environment=os.getenv("ENV", "development"))

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
RECEIPTS_FILE = DATA_DIR / "receipts.json"
CORRECTIONS_FILE = DATA_DIR / "corrections.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class UploadResponse(BaseModel):
    job_id: str
    status: str


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    endpoint = request.url.path
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        # capture to sentry if available
        if SENTRY_DSN and SENTRY_AVAILABLE:
            sentry_sdk.capture_exception(e)
        raise
    finally:
        elapsed = time.time() - start
        try:
            REQUEST_LATENCY.labels(endpoint=endpoint).observe(elapsed)
            REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, http_status=str(status_code)).inc()
        except Exception:
            pass
    return response


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # basic validation
    filename = file.filename or f"upload_{uuid.uuid4().hex}"
    # stream to temp and then upload to S3
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        with tmp as f:
            shutil.copyfileobj(file.file, f)
        s3_key = f"uploads/{uuid.uuid4().hex}_{filename}"
        s3.upload_file(tmp.name, s3_key)
    finally:
        try:
            file.file.close()
        except:
            pass

    # create job entry
    job_id = uuid.uuid4().hex
    jobs.create_job(job_id, {"status": "queued", "s3_key": s3_key})

    # enqueue celery task
    process_receipt_task.delay(job_id, s3_key)

    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
def get_status(job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get(METRICS_PATH)
def metrics():
    """
    Prometheus scrape endpoint.
    """
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

# --- thêm vào api/main.py (ở sau các endpoint hiện có) ---

class CorrectionItem(BaseModel):
    id: str | None = None
    raw_text: str | None = None
    item_name: str | None = None
    category: str
    notes: str | None = None

@app.get("/admin/low_confidence")
def list_low_confidence(threshold: float = 0.6, limit: int = 100):
    """
    Return receipts with confidence < threshold (0..1) from data/receipts.json
    """
    try:
        if not RECEIPTS_FILE.exists():
            return {"items": []}
        with open(RECEIPTS_FILE, "r", encoding="utf-8") as f:
            receipts = json.load(f)
    except Exception:
        receipts = []
    out = []
    for r in receipts:
        conf = r.get("confidence", 0)
        # if confidence recorded as 0..100 convert to 0..1
        if conf > 1:
            conf = conf / 100.0
        if conf < threshold:
            out.append(r)
        if len(out) >= limit:
            break
    return {"count": len(out), "items": out}

@app.post("/feedback")
def post_feedback(item: CorrectionItem):
    """
    Append a correction to data/corrections.json
    """
    payload = item.dict()
    # normalize
    if not payload.get("raw_text") and payload.get("item_name"):
        payload["raw_text"] = payload.get("item_name")
    # ensure corrections file exists
    try:
        if CORRECTIONS_FILE.exists():
            with open(CORRECTIONS_FILE, "r", encoding="utf-8") as f:
                corrections = json.load(f)
        else:
            corrections = []
    except Exception:
        corrections = []
    corrections.append(payload)
    try:
        with open(CORRECTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(corrections, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save correction: {e}")
    return {"status": "ok", "saved": payload}

@app.post("/admin/retrain")
def trigger_retrain(background_tasks: BackgroundTasks):
    """
    Trigger retrain by enqueuing a Celery task (workers must have retrain task)
    """
    try:
        # try to enqueue Celery retrain task if available
        from workers.tasks import retrain_model_task
        # call asynchronously
        retrain_model_task.delay()
        return {"status": "enqueued"}
    except Exception as e:
        # fallback: run local subprocess (blocking)
        try:
            cmd = ["python", "-m", "ml.retrain", "--receipts-json", str(RECEIPTS_FILE), "--corrections-file", str(CORRECTIONS_FILE), "--models-root", "models"]
            background_tasks.add_task(lambda: subprocess.run(cmd))
            return {"status": "started_subprocess"}
        except Exception as e2:
            raise HTTPException(status_code=500, detail=f"Could not start retrain: {e} / {e2}")
