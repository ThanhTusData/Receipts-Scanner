# workers/celery_app.py
import os
from celery import Celery

# sentry
try:
    import sentry_sdk
    SENTRY_AVAILABLE = True
except Exception:
    SENTRY_AVAILABLE = False

# prometheus http server
try:
    from prometheus_client import start_http_server
    PROM_AVAILABLE = True
except Exception:
    PROM_AVAILABLE = False

# crontab for periodic tasks
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_BROKER = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

celery_app = Celery(
    "workers",
    broker=CELERY_BROKER,
    backend=CELERY_BACKEND,
)

# optional: few default config
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
)

# Configure optional periodic (beat) schedule if enabled via env
# Use environment variables:
#   ENABLE_CELERY_BEAT (default: "true")
#   RETRAIN_HOUR (default: 3)
#   RETRAIN_MINUTE (default: 0)
try:
    ENABLE_BEAT = os.getenv("ENABLE_CELERY_BEAT", "true").lower() in ("1", "true", "yes")
    if ENABLE_BEAT:
        # default: every day at RETRAIN_HOUR:RETRAIN_MINUTE (Asia/Ho_Chi_Minh)
        retrain_hour = int(os.getenv("RETRAIN_HOUR", "3"))
        retrain_minute = int(os.getenv("RETRAIN_MINUTE", "0"))
        celery_app.conf.beat_schedule = {
            "retrain-everyday-0300": {
                "task": "retrain_model_task",
                "schedule": crontab(hour=retrain_hour, minute=retrain_minute),
                "args": (),
            }
        }
        print(f"Celery beat enabled: retrain task scheduled daily at {retrain_hour:02d}:{retrain_minute:02d} (Asia/Ho_Chi_Minh)")
    else:
        # ensure no beat schedule set
        celery_app.conf.pop("beat_schedule", None)
except Exception as e:
    print("Failed to configure celery beat schedule:", e)

# Sentry for workers
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN and SENTRY_AVAILABLE:
    sentry_sdk.init(dsn=SENTRY_DSN, environment=os.getenv("ENV", "development"))

# Expose worker metrics via simple http server (pushgateway alternative)
WORKER_METRICS_PORT = int(os.getenv("WORKER_METRICS_PORT", 8002))
if PROM_AVAILABLE:
    try:
        # start a background HTTP server exposing prometheus metrics
        start_http_server(WORKER_METRICS_PORT)
        print(f"Prometheus metrics HTTP server started on :{WORKER_METRICS_PORT}")
    except Exception as e:
        print("Failed to start prometheus http server for worker:", e)
