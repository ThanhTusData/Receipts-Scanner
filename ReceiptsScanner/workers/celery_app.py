"""
Celery application configuration and Prometheus metrics server
"""
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import os
from prometheus_client import start_http_server, Counter, Histogram, Gauge
from monitoring.logging_config import get_logger
from monitoring.metrics import (
    celery_tasks_total,
    celery_task_duration_seconds,
    celery_task_failures_total,
    celery_active_workers
)

logger = get_logger(__name__)

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Initialize Celery app
celery_app = Celery(
    "receipt_scanner",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
)

logger.info(f"Celery configured with broker: {CELERY_BROKER_URL}")

# Metrics tracking
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Track task start"""
    logger.info(f"Task started: {task.name} [{task_id}]")
    celery_active_workers.inc()

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, retval=None, **kwargs):
    """Track task completion"""
    logger.info(f"Task completed: {task.name} [{task_id}]")
    
    celery_tasks_total.labels(
        task_name=task.name,
        status="success"
    ).inc()
    
    celery_active_workers.dec()

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Track task failure"""
    logger.error(f"Task failed: {sender.name} [{task_id}] - {str(exception)}")
    
    celery_tasks_total.labels(
        task_name=sender.name,
        status="failure"
    ).inc()
    
    celery_task_failures_total.labels(
        task_name=sender.name,
        exception_type=type(exception).__name__
    ).inc()
    
    celery_active_workers.dec()

# Start Prometheus metrics server for worker
def start_metrics_server():
    """Start Prometheus metrics HTTP server"""
    metrics_port = int(os.getenv("PROMETHEUS_PORT", 8002))
    try:
        start_http_server(metrics_port)
        logger.info(f"Prometheus metrics server started on port {metrics_port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {str(e)}")

# Start metrics server when module is imported by worker
if os.getenv("METRICS_ENABLED", "true").lower() == "true":
    import threading
    metrics_thread = threading.Thread(target=start_metrics_server, daemon=True)
    metrics_thread.start()