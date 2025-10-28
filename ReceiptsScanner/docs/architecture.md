# Receipt Scanner - System Architecture

## Overview

Receipt Scanner is a microservices-based application for automated receipt processing, OCR extraction, and intelligent categorization using machine learning.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Streamlit UI (Port 8501)                                   │
│  - Receipt Upload                                           │
│  - Receipt Management                                       │
│  - Analytics Dashboard                                      │
│  - Settings                                                 │
└────────────┬────────────────────────────────────────────────┘
             │
             │ HTTP/REST API
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI (Port 8000)                                        │
│  - Receipt CRUD operations                                  │
│  - Upload handling                                          │
│  - Job status tracking                                      │
│  - Admin endpoints                                          │
│  - Prometheus metrics                                       │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Async Tasks (Celery)
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Processing Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Celery Workers (Port 8002 - Metrics)                      │
│  - Receipt processing                                       │
│  - Model retraining                                         │
│  - Data backup                                              │
│  - Job cleanup                                              │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────────────────┬──────────────────┬───────────┐
             ▼                  ▼                  ▼           ▼
    ┌────────────┐    ┌──────────────┐   ┌─────────────┐ ┌────────┐
    │ OCR Engine │    │ ML Classifier│   │ Data Manager│ │ Storage│
    │            │    │              │   │             │ │        │
    │ Tesseract  │    │ Sentence-    │   │ JSON/S3     │ │ MinIO  │
    │            │    │ BERT + LR    │   │ Adapters    │ │ Redis  │
    └────────────┘    └──────────────┘   └─────────────┘ └────────┘
```

## Component Details

### 1. Frontend Layer

#### Streamlit UI
- **Purpose**: User interface for receipt management
- **Technology**: Streamlit
- **Port**: 8501
- **Key Features**:
  - Multi-file receipt upload
  - Real-time processing status
  - Receipt viewing and editing
  - Spending analytics with visualizations
  - System settings and model management

### 2. API Layer

#### FastAPI Application
- **Purpose**: REST API for all operations
- **Technology**: FastAPI + Uvicorn
- **Port**: 8000
- **Endpoints**:
  - `POST /upload` - Upload receipts
  - `GET /receipts` - List receipts
  - `GET /receipts/{id}` - Get receipt
  - `PUT /receipts/{id}` - Update receipt
  - `DELETE /receipts/{id}` - Delete receipt
  - `GET /jobs/{id}` - Get job status
  - `POST /admin/retrain` - Trigger retraining
  - `GET /admin/metrics` - System metrics

#### Middleware
- CORS handling
- Request logging
- Prometheus metrics collection
- Error tracking (Sentry integration)

### 3. Worker Layer

#### Celery Workers
- **Purpose**: Async task processing
- **Technology**: Celery + Redis
- **Concurrency**: 4 workers (configurable)
- **Tasks**:
  1. **process_receipt_task**: OCR + entity extraction + classification
  2. **retrain_model_task**: Incremental model training
  3. **cleanup_old_jobs_task**: Periodic cleanup
  4. **backup_data_task**: Automated backups

### 4. Processing Components

#### OCR Engine
- **Implementation**: Tesseract OCR
- **Languages**: English + Vietnamese
- **Process**:
  1. Image preprocessing (grayscale, threshold, deskew)
  2. Text extraction with confidence scoring
  3. Bounding box detection

#### Receipt Processor
- **Purpose**: Extract structured entities from text
- **Patterns**:
  - Merchant name (keyword-based + heuristics)
  - Total amount (multiple currency formats)
  - Receipt date (multiple date formats)
  - Phone numbers (Vietnamese formats)
  - Line items (quantity × price patterns)

#### ML Classifier
- **Architecture**: Sentence-BERT + Logistic Regression
- **Model**: `paraphrase-multilingual-mpnet-base-v2`
- **Categories**: 8 categories (Food, Electronics, Clothing, etc.)
- **Training**: Initial + incremental with corrections
- **Confidence Threshold**: 0.6 (defaults to "Other" if lower)

### 5. Data Layer

#### Storage Adapters
Two implementations with common interface:

**JSON Adapter** (Development)
- File-based storage
- Receipts: `data/receipts.json`
- Corrections: `data/corrections.json`
- Thread-safe with locks

**S3 Adapter** (Production)
- MinIO/S3 object storage
- Scalable and distributed
- Presigned URLs for images
- Automatic backup to S3

#### Jobs Adapter
- Track async task status
- Thread-safe job management
- Automatic cleanup of old jobs

### 6. Supporting Services

#### Redis
- **Purpose**: Message broker and cache
- **Port**: 6379
- **Usage**:
  - Celery task queue
  - Result backend
  - Optional caching

#### MinIO
- **Purpose**: S3-compatible object storage
- **Ports**: 9000 (API), 9001 (Console)
- **Buckets**:
  - `receipts/images/` - Receipt images
  - `receipts/data/` - JSON data
  - `receipts/backups/` - Automated backups

#### Prometheus
- **Purpose**: Metrics collection and alerting
- **Port**: 9090
- **Metrics**:
  - HTTP request metrics
  - Receipt processing metrics
  - OCR/ML confidence scores
  - Celery task metrics
  - Error rates and latencies

#### Grafana
- **Purpose**: Visualization and dashboards
- **Port**: 3000
- **Dashboards**:
  - System overview
  - Receipt processing metrics
  - ML model performance
  - Error tracking

## Data Flow

### Receipt Processing Flow

```
1. User uploads image via Streamlit UI
   │
   ▼
2. FastAPI receives upload, saves to temp storage
   │
   ▼
3. Create Celery task, return job_id to user
   │
   ▼
4. Worker picks up task:
   a. Preprocess image
   b. OCR extraction
   c. Entity extraction (regex patterns)
   d. ML classification
   e. Upload image to MinIO
   f. Save receipt to database
   │
   ▼
5. Update job status to "completed"
   │
   ▼
6. UI polls for status, shows result
```

### Model Retraining Flow

```
1. User corrects category in UI
   │
   ▼
2. Correction saved to corrections.json
   │
   ▼
3. When threshold reached (50+ corrections):
   a. Load base training data
   b. Merge with corrections
   c. Train new model
   d. Save versioned model
   e. Update model metadata
   │
   ▼
4. New model automatically used for predictions
```

## Scalability Considerations

### Horizontal Scaling

**Workers**: Can run multiple worker instances
```yaml
worker1:
  <<: *worker
worker2:
  <<: *worker
```

**API**: Can be load-balanced
```
Nginx/HAProxy → API instances
```

### Vertical Scaling

- Increase worker concurrency
- Allocate more memory to ML models
- Increase Redis memory limits

### Storage Scaling

- Use external S3 (AWS S3, Google Cloud Storage)
- Implement CDN for image delivery
- Database sharding for large datasets

## Monitoring & Observability

### Metrics Collection
- Prometheus scrapes metrics every 15s
- Custom metrics for business logic
- Alert rules for anomalies

### Logging
- Structured logging with structlog
- JSON format for log aggregation
- Multiple log levels (DEBUG, INFO, WARNING, ERROR)

### Tracing
- Request tracking with correlation IDs
- Task execution tracing
- Performance profiling

## Security

### API Security
- CORS restrictions
- Rate limiting
- Input validation

### Data Security
- Encrypted connections (TLS/SSL in production)
- Access control for MinIO
- Environment-based secrets

### Infrastructure Security
- Network isolation with Docker networks
- Firewall rules
- Regular security updates

## Deployment

### Development
```bash
docker-compose up -d
```

### Production
- Use Docker Swarm or Kubernetes
- External managed services (Redis, S3)
- Load balancers and auto-scaling
- Monitoring and alerting setup

## Performance Metrics

### Target Metrics
- **OCR Processing**: < 5s per receipt
- **Classification**: < 1s per receipt
- **API Response**: < 100ms (95th percentile)
- **Upload Success Rate**: > 99%

### Optimization Strategies
- Image compression before processing
- Batch processing for multiple receipts
- Model caching
- Connection pooling
- Async processing for heavy tasks