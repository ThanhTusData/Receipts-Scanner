# workers/tasks.py
import os
import tempfile
import traceback
import time
from workers.celery_app import celery_app
from data_manager.s3_adapter import S3Adapter
from data_manager.jobs_adapter import JobsAdapter
from data_manager.json_adapter import insert_receipt # or use DataManager wrapper
from receipt_processor import ReceiptProcessorRefactor as ReceiptProcessor
import json

# prometheus metrics (exported via start_http_server in workers.celery_app)
try:
    from prometheus_client import Counter, Histogram
    JOBS_PROCESSED = Counter("worker_jobs_processed_total", "Total processed jobs", ["status"])
    JOB_PROCESSING_TIME = Histogram("worker_job_processing_time_seconds", "Job processing time (s)")
except Exception:
    JOBS_PROCESSED = None
    JOB_PROCESSING_TIME = None

# sentry
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except Exception:
    SENTRY_AVAILABLE = False

s3 = S3Adapter()
jobs = JobsAdapter()

@celery_app.task(name="process_receipt_task", bind=True)
def process_receipt_task(self, job_id: str, s3_key: str):
    start = time.time()
    try:
        jobs.update_job(job_id, {"status": "processing"})
        # download
        tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".img")
        tmpf.close()
        s3.download_file(s3_key, tmpf.name)

        # process
        rp = ReceiptProcessor()
        # receipt_processor.process accepts path or PIL.Image - our implementation accepts path string
        result = rp.process(tmpf.name)

        # put parsed data into receipts.json using your existing adapter
        # Use JobsAdapter to store result in job record
        jobs.update_job(job_id, {"status": "done", "result": result})

        # Also append to receipts list
        try:
            from data_manager import DataManager
            dm = DataManager()
            saved = {
                "id": result.get("id"),
                "store_name": result.get("entities", {}).get("store_name", ""),
                "total_amount": result.get("entities", {}).get("total_amount", 0),
                "date": result.get("entities", {}).get("date", ""),
                "raw_text": result.get("raw_text", ""),
                "processed_date": result.get("processed_date"),
                "confidence": result.get("entities", {}).get("confidence", 0),
                "items": result.get("entities", {}).get("items", []),
            }
            dm.add_receipt(saved)
        except Exception:
            from data_manager.jobs_adapter import append_receipt_fallback
            append_receipt_fallback(result)

        # metrics
        duration = time.time() - start
        if JOBS_PROCESSED:
            JOBS_PROCESSED.labels(status="success").inc()
        if JOB_PROCESSING_TIME:
            JOB_PROCESSING_TIME.observe(duration)

    except Exception as e:
        tb = traceback.format_exc()
        jobs.update_job(job_id, {"status": "failed", "error": str(e), "traceback": tb})
        # metrics
        if JOBS_PROCESSED:
            JOBS_PROCESSED.labels(status="failed").inc()
        # sentry capture
        try:
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)
        except Exception:
            pass
        # re-raise so Celery records failure
        raise
# --- thêm vào workers/tasks.py (cuối file) ---
@celery_app.task(name="retrain_model_task", bind=True)
def retrain_model_task(self):
    """
    Celery task to trigger retrain. It will run ml/retrain.py as a subprocess.
    """
    try:
        # paths (use DATA_DIR if set)
        receipts = os.getenv("RECEIPTS_JSON", "data/receipts.json")
        corrections = os.getenv("CORRECTIONS_FILE", "data/corrections.json")
        models_root = os.getenv("MODELS_ROOT", "models")
        cmd = ["python", "-m", "ml.retrain", "--receipts-json", receipts, "--corrections-file", corrections, "--models-root", models_root]
        # run subprocess; this keeps worker lightweight while retrain runs in separate process
        subprocess.check_call(cmd)
        return {"status": "ok"}
    except subprocess.CalledProcessError as e:
        # record failure
        raise
    except Exception as e:
        raise
