# Receipts_Scanner

**Receipts_Scanner** is an end-to-end pipeline for extracting structured information from retail receipts (images / PDFs), classifying categories, storing normalized data, and providing analytics and retraining workflows for continuous improvement.

---

## Table of Contents

* [Project Overview](#project-overview)
* [Business Value](#business-value)
* [Key Features](#key-features)
* [Repository Structure](#repository-structure)
* [Tech Stack & Tools](#tech-stack--tools)
* [Quick Start](#quick-start)

  * [Prerequisites](#prerequisites)
  * [Environment](#environment)
  * [Run Locally](#run-locally)
  * [Run with Docker / Compose](#run-with-docker--compose)
* [API Usage (examples)](#api-usage-examples)
* [Machine Learning & Retraining](#machine-learning--retraining)
* [Testing & CI](#testing--ci)
* [Monitoring & Observability](#monitoring--observability)
* [Recommended Improvements / Roadmap](#recommended-improvements--roadmap)
* [Contributing](#contributing)
* [License & Contact](#license--contact)

---

## Project Overview

Receipts_Scanner converts receipt images into structured records. The pipeline combines OCR, preprocessing, rule-based and ML-based classifiers to detect:

* merchant/place
* date/time
* line items (product names, quantities, prices)
* categories
* totals and taxes

Extracted records are normalized and stored as JSON (see `data/receipts.json`) and can be consumed by analytics, recommendation engines, or accounting systems.

## Business Value

* **Automation**: Reduce manual data entry time and human errors when processing receipts.
* **Analytics**: Enable spend-analysis, merchant insights, category trends, and customer behavior analytics.
* **Integrations**: Feed cleaned data to finance, CRM, or recommendation systems for cross-sell/up-sell.
* **Scalability**: Background workers and containerization support high-throughput ingestion.

## Key Features

* OCR adapter layer (Tesseract) to extract text from images. (`ocr_engines/tesseract_adapter.py`)
* Preprocessing to clean OCR output and normalize text (`preprocessing.py`).
* Receipt processor that assembles structured records (`receipt_processor.py`).
* Category classifier combining ML and rule-based methods (`category_classifier.py`).
* Data adapters for JSON, S3 and job storage (`data_manager/json_adapter.py`, `data_manager/s3_adapter.py`, `data_manager/jobs_adapter.py`).
* ML training, evaluation and retraining pipelines (`ml/train.py`, `ml/eval.py`, `ml/retrain.py`).
* Background processing using Celery workers (`workers/celery_app.py`, `workers/tasks.py`).
* Simple API entrypoint(s) (`app.py`, `api/main.py`).
* Test suite (`tests/`) and CI workflow (`.github/workflows/python-app.yml`).
* Monitoring with Prometheus configuration under `prometheus/`.

## Repository Structure

```text
Receipts_Scanner/
├── .github/
│   └── workflows/
│       └── python-app.yml
├── data/
│   └── receipts.json
├── images/
├── uploads/
├── analytics.py
├── app.py
├── category_classifier.py
├── config.py
├── data_manager/
│   ├── __init__.py
│   ├── json_adapter.py
│   ├── s3_adapter.py
│   └── jobs_adapter.py
├── ml/
│   ├── train.py
│   ├── eval.py
│   └── retrain.py
├── ocr_engines/
│   └── tesseract_adapter.py
├── preprocessing.py
├── receipt_processor.py
├── workers/
│   ├── celery_app.py
│   └── tasks.py
├── prometheus/
│   ├── prometheus.yml
│   └── alerts.yml
├── api/
│   └── main.py
├── tests/
│   ├── test_smoke.py
│   ├── test_processor.py
│   ├── test_classifier.py
│   ├── test_metrics.py
│   └── test_retrain.py
├── Dockerfile
├── Dockerfile.api
├── docker-compose.yml
├── .env
├── .env.example
├── logging_config.py
└── requirements.txt
```

## Tech Stack & Tools (purpose)

* **Python** — Core language for logic, ML, and APIs.
* **Tesseract OCR** (`ocr_engines/tesseract_adapter.py`) — Open-source OCR to extract text from receipt images.
* **Celery** (`workers/`) — Background task processing for async/scale (e.g., long OCR jobs, batch retraining).
* **Flask / FastAPI** (`app.py`, `api/main.py`) — Expose HTTP API for uploads, status, triggering retrain, health checks.
* **S3 adapter** (`data_manager/s3_adapter.py`) — Persist raw uploads or models in object storage.
* **Prometheus** (`prometheus/`) — Metrics and alerting for production monitoring.
* **PyTest** (`tests/`) — Unit and integration tests.
* **Docker / Docker Compose** — Containerize API, worker, Redis/Broker, and other services for local/dev deployment.
* **Logging config** — Centralized logging via `logging_config.py`.

## Quick Start

### Prerequisites

* Python 3.10+ (match CI matrix in `.github/workflows/python-app.yml`)
* Tesseract binary installed and available in PATH
* Docker & Docker Compose (optional but recommended for reproducible environment)
* Redis or RabbitMQ for Celery broker (if using background workers)

### Environment

1. Copy `.env.example` to `.env` and edit credentials and paths.

```bash
cp .env.example .env
# then edit .env
```

Key environment variables to set (examples):

```
APP_ENV=development
OCR_ENGINE=tesseract
S3_BUCKET=your-bucket
CELERY_BROKER_URL=redis://redis:6379/0
DATABASE_URL=sqlite:///data/receipts.db  # or your MySQL/Postgres URL
```

### Run Locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Run API
python app.py
# Or run API module under `api/`
python -m api.main
```

### Run with Docker / Compose

```bash
# Build
docker-compose build
# Start services (API, worker, broker, etc.)
docker-compose up --build
```

Or build API image only:

```bash
docker build -f Dockerfile.api -t receipts_api:latest .
docker run --env-file .env -p 8000:8000 receipts_api:latest
```

## API Usage (examples)

> The exact endpoints depend on `app.py`/`api/main.py`. Typical endpoints to implement:

* `GET /health` — health check
* `POST /upload` — upload receipt image (multipart/form-data) → returns job id
* `GET /status/{job_id}` — processing status
* `GET /receipts/{receipt_id}` — retrieve parsed JSON
* `POST /train` — trigger ML training / retrain (protected)

Example using `curl` to upload an image:

```bash
curl -X POST "http://localhost:8000/upload" -F "file=@/path/to/receipt.jpg"
```

## Machine Learning & Retraining

* Training scripts are in `ml/`:

  * `ml/train.py` — initial model training
  * `ml/eval.py` — evaluate model metrics (precision/recall/F1, confusion matrix)
  * `ml/retrain.py` — retrain pipeline for incremental updates
* Use `retrain.py` in background (Celery task) for periodic model updates or after collecting N new labeled receipts.
* Store models/artifacts in S3 or a model registry for reproducibility.

## Testing & CI

* Run tests locally with `pytest`:

```bash
pytest -q
```

* CI configuration exists at `.github/workflows/python-app.yml` to run tests on push/PR for supported Python versions.

## Monitoring & Observability

* Prometheus config is under `prometheus/` — expose prometheus-compatible metrics from the API and Celery workers.
* Use alerts in `prometheus/alerts.yml` to notify on error rate, queue backlog, or retrain failures.
* Add structured logs and correlate by `request_id` or `job_id`.

## Recommended Improvements / Roadmap

* **Improve OCR**: Add alternative OCR providers (Google Vision API, AWS Textract) and choose dynamically per image quality.
* **Model Registry**: Integrate a model registry (MLflow or Seldon) to version models and rollback safely.
* **Data Validation**: Add strict schema validation (e.g., Pydantic) for parsed receipts.
* **Labeling UI**: Add a small web UI to review and correct parsed receipts to build labeled training data.
* **Scale**: Migrate to Kubernetes and use horizontal autoscaling for API & workers.
* **Privacy & Security**: Encrypt stored receipts and PII at rest; ensure secure transport and RBAC for training endpoints.
* **Data Drift Detection**: Monitor model performance over time and automate retraining if drift detected.
* **End-to-end Tests**: Add e2e tests that simulate uploads through to parsed JSON storage.