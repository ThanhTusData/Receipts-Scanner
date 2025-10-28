"""
Prometheus metrics definitions
"""
from prometheus_client import Counter, Histogram, Gauge, Summary

# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0)
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# Receipt Processing Metrics
receipts_processed_total = Counter(
    'receipts_processed_total',
    'Total receipts processed',
    ['status']
)

processing_errors_total = Counter(
    'processing_errors_total',
    'Total processing errors',
    ['error_type']
)

ocr_confidence_score = Histogram(
    'ocr_confidence_score',
    'OCR confidence scores',
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

classification_confidence_score = Histogram(
    'classification_confidence_score',
    'Classification confidence scores',
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
)

# Celery Task Metrics
celery_tasks_total = Counter(
    'celery_tasks_total',
    'Total Celery tasks',
    ['task_name', 'status']
)

celery_task_duration_seconds = Histogram(
    'celery_task_duration_seconds',
    'Celery task duration in seconds',
    ['task_name'],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0)
)

celery_task_failures_total = Counter(
    'celery_task_failures_total',
    'Total Celery task failures',
    ['task_name', 'exception_type']
)

celery_active_workers = Gauge(
    'celery_active_workers',
    'Number of active Celery workers'
)

# Data Metrics
receipts_total = Gauge(
    'receipts_total',
    'Total number of receipts in database'
)

corrections_total = Gauge(
    'corrections_total',
    'Total number of corrections'
)

# Storage Metrics
storage_operations_total = Counter(
    'storage_operations_total',
    'Total storage operations',
    ['operation', 'status']
)

# ML Model Metrics
model_predictions_total = Counter(
    'model_predictions_total',
    'Total model predictions',
    ['category']
)

model_retraining_total = Counter(
    'model_retraining_total',
    'Total model retraining runs',
    ['status']
)

model_accuracy = Gauge(
    'model_accuracy',
    'Current model accuracy'
)