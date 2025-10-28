# ReceiptsScanner

An intelligent receipt scanning and categorization system with OCR, machine learning, and comprehensive monitoring.

## Features

- 📸 **OCR Processing**: Tesseract-based text extraction from receipt images
- 🤖 **ML Classification**: Automatic category classification using Sentence-BERT
- 📊 **Analytics**: Spending insights and trend visualization
- ⚡ **Async Processing**: Celery-based background task processing
- 📦 **Storage**: MinIO/S3 compatible object storage
- 📈 **Monitoring**: Prometheus metrics + Grafana dashboards
- 🔄 **Continuous Learning**: Feedback loop for model improvement
- 🎨 **Modern UI**: Streamlit-based interface

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Streamlit  │────▶│   FastAPI   │────▶│   Celery    │
│     UI      │     │     API     │     │   Workers   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │     │   MinIO/S3  │
                    │   (Queue)   │     │  (Storage)  │
                    └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ Prometheus  │────▶│   Grafana   │
                    │  (Metrics)  │     │ (Dashboard) │
                    └─────────────┘     └─────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+ (for local development)
- Tesseract OCR installed

### Installation

1. **Clone the repository**
```bash
git clone ...
cd ReceiptsScanner
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Initialize MinIO buckets**
```bash
./scripts/init_minio.sh
```

5. **Train initial model**
```bash
docker-compose exec api python -m ml.train
```

### Access Points

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Development Setup

### Local Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Tesseract
# Ubuntu/Debian: apt-get install tesseract-ocr
# macOS: brew install tesseract
# Windows: Download from GitHub

# Set environment variables
export REDIS_URL=redis://localhost:6379/0
export MINIO_ENDPOINT=localhost:9000
export STORAGE_BACKEND=json  # or s3

# Run services
streamlit run app.py  # UI
uvicorn api.main:app --reload  # API
celery -A workers.celery_app worker --loglevel=info  # Worker
```

## Usage

### Scanning Receipts

1. Navigate to the "📸 Quét Hóa Đơn" page
2. Upload receipt image(s)
3. Wait for processing (async)
4. Review and correct extracted data
5. Save receipt

### Viewing Receipts

1. Go to "📋 Xem Hóa Đơn" page
2. Browse all receipts
3. Filter by date, category, merchant
4. Edit or delete receipts

### Analytics

1. Visit "📊 Phân Tích" page
2. View spending trends
3. Category breakdown
4. Monthly comparisons

### Model Retraining

```bash
# Manual retrain
docker-compose exec api python -m ml.retrain

# Via API
curl -X POST http://localhost:8000/admin/retrain
```

## API Endpoints

### Receipts
- `POST /upload` - Upload receipt images
- `GET /receipts` - List all receipts
- `GET /receipts/{id}` - Get receipt details
- `PUT /receipts/{id}` - Update receipt
- `DELETE /receipts/{id}` - Delete receipt

### Jobs
- `GET /jobs/{job_id}` - Get job status

### Admin
- `GET /admin/metrics` - System metrics
- `POST /admin/retrain` - Trigger model retraining
- `GET /health` - Health check

See [API Documentation](docs/api.md) for details.

## ML Pipeline

### Categories

1. **Thực Phẩm** (Food)
2. **Điện Tử** (Electronics)
3. **Quần Áo** (Clothing)
4. **Y Tế** (Healthcare)
5. **Giải Trí** (Entertainment)
6. **Du Lịch** (Travel)
7. **Gia Dụng** (Household)
8. **Khác** (Other)

### Model Architecture

- **Encoder**: Sentence-BERT (`paraphrase-multilingual-mpnet-base-v2`)
- **Classifier**: Logistic Regression
- **Training**: Incremental learning with human feedback

### Feedback Loop

1. User corrects category
2. Correction saved to `corrections.json`
3. Periodic retraining incorporates feedback
4. Model improves over time

## Monitoring

### Metrics

- Receipt processing success/failure rate
- OCR extraction confidence
- Classification accuracy
- Processing latency
- Queue depth

### Alerts

- High worker failure rate (>10%)
- Queue backlog (>100 jobs)
- Low disk space
- Model performance degradation

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_processor.py

# Run with coverage
pytest --cov=. --cov-report=html

# Smoke tests
pytest tests/test_smoke.py -v
```

## Deployment

### Production Checklist

- [ ] Set strong passwords in `.env`
- [ ] Configure S3/MinIO credentials
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Configure Sentry error tracking
- [ ] Review Prometheus alerts
- [ ] Set up log aggregation

### Backup & Restore

```bash
# Backup
./scripts/backup_data.sh

# Restore
cp data/.backup_YYYYMMDD_HHMMSS.json data/receipts.json
```

## Project Structure

See [Architecture Documentation](docs/architecture.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests
4. Submit pull request

## Troubleshooting

### Tesseract not found
```bash
# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-vie

# macOS
brew install tesseract tesseract-lang
```

### Redis connection failed
```bash
# Check Redis is running
docker-compose ps redis

# View logs
docker-compose logs redis
```

### MinIO access denied
```bash
# Re-initialize buckets
./scripts/init_minio.sh
```

## Support

- 📧 Email: support@receiptsscanner.com
- 🐛 Issues: GitHub Issues
- 📖 Docs: [Documentation](docs/)

## Acknowledgments

- Tesseract OCR
- Sentence Transformers
- Streamlit
- FastAPI
- Celery