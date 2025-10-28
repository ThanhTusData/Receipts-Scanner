# Receipt Scanner - Complete Deployment Guide

## Files Created Summary

### ✅ Core Configuration (Complete)
- `README.md` - Project documentation
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template
- `.gitignore` - Git ignore rules
- `docker-compose.yml` - Multi-container orchestration
- `Dockerfile` - UI container
- `Dockerfile.api` - API & Worker container

### ✅ Application Layer (Complete)
- `app.py` - Streamlit UI main application

### ✅ API Layer (Complete)
- `api/__init__.py`
- `api/main.py` - FastAPI endpoints
- `api/middleware.py` - CORS and metrics middleware

### ✅ Workers Layer (Complete)
- `workers/__init__.py`
- `workers/celery_app.py` - Celery configuration
- `workers/tasks.py` - Background tasks

### ✅ OCR Engines (Complete)
- `ocr_engines/__init__.py`
- `ocr_engines/base.py` - Abstract OCR interface
- `ocr_engines/tesseract_adapter.py` - Tesseract implementation

### ✅ Processing Layer (Complete)
- `processing/__init__.py`
- `processing/preprocessing.py` - Image preprocessing
- `processing/patterns.py` - Regex patterns
- `processing/receipt_processor.py` - Entity extraction

### ✅ Machine Learning (Complete)
- `ml/__init__.py`
- `ml/config.py` - Categories and configuration
- `ml/category_classifier.py` - Classification model
- `ml/train.py` - Initial training script
- `ml/eval.py` - Evaluation script
- `ml/retrain.py` - Incremental retraining

### ✅ Data Management (Complete)
- `data_manager/__init__.py`
- `data_manager/base.py` - Abstract adapter interface
- `data_manager/json_adapter.py` - File-based storage
- `data_manager/s3_adapter.py` - MinIO/S3 storage
- `data_manager/jobs_adapter.py` - Job tracking

### ✅ Monitoring (Complete)
- `monitoring/__init__.py`
- `monitoring/logging_config.py` - Structured logging
- `monitoring/metrics.py` - Prometheus metrics

### ✅ Analytics
- `analytics/__init__.py`

### ✅ Prometheus & Grafana (Complete)
- `prometheus/prometheus.yml` - Prometheus config
- `prometheus/alerts.yml` - Alert rules

## Files Still Needed

### Analytics Module
Create `analytics/analytics.py` with spending insights and visualization functions.

### Grafana Configuration
- `grafana/provisioning/datasources.yml` - Prometheus datasource
- `grafana/provisioning/dashboards.yml` - Dashboard provisioning
- `grafana/dashboards/receipts_dashboard.json` - Pre-built dashboard

### Scripts
- `scripts/init_minio.sh` - Initialize MinIO buckets
- `scripts/backup_data.sh` - Manual backup script
- `scripts/deploy.sh` - Deployment helper

### Testing
- `tests/__init__.py`
- `tests/test_smoke.py` - Smoke tests
- `tests/test_processor.py` - Processor tests
- `tests/test_classifier.py` - ML tests
- `tests/test_retrain.py` - Retrain tests
- `tests/test_metrics.py` - Metrics tests

### Documentation
- `docs/architecture.md` - Architecture documentation
- `docs/api.md` - API documentation
- `docs/ml_pipeline.md` - ML workflow documentation

### CI/CD
- `.github/workflows/python-app.yml` - GitHub Actions CI

## Quick Start Deployment

### Step 1: Environment Setup

```bash
# Clone repository
git clone <your-repo-url>
cd ReceiptsScanner

# Copy environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### Step 2: Create Directories

```bash
# Create data directories
mkdir -p data models training_data logs

# Create Prometheus & Grafana directories
mkdir -p prometheus grafana/dashboards grafana/provisioning
```

### Step 3: Start Services

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Step 4: Initialize MinIO

```bash
# Install MinIO client
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc

# Configure MinIO
./mc alias set myminio http://localhost:9000 minioadmin minioadmin

# Create bucket
./mc mb myminio/receipts

# Set public read policy (optional)
./mc anonymous set download myminio/receipts
```

### Step 5: Train Initial Model

```bash
# Enter API container
docker-compose exec api bash

# Run training script
python -m ml.train

# Exit container
exit
```

### Step 6: Access Applications

- **Streamlit UI**: http://localhost:8501
- **FastAPI Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Flower (Celery)**: http://localhost:5555
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Production Deployment Checklist

### Security
- [ ] Change all default passwords in `.env`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure firewall rules
- [ ] Enable HTTPS/TLS
- [ ] Set up VPN or restrict access
- [ ] Configure Sentry DSN for error tracking

### Storage
- [ ] Configure S3/MinIO credentials
- [ ] Set up automated backups
- [ ] Configure backup retention policy
- [ ] Test backup restoration

### Monitoring
- [ ] Review Prometheus alert rules
- [ ] Configure alert notifications
- [ ] Set up Grafana dashboards
- [ ] Configure log aggregation (ELK, Splunk, etc.)

### Performance
- [ ] Adjust worker concurrency based on load
- [ ] Configure Redis persistence
- [ ] Set up database connection pooling
- [ ] Optimize Docker resource limits

### Maintenance
- [ ] Set up automated model retraining
- [ ] Configure log rotation
- [ ] Plan for data cleanup/archival
- [ ] Document operational procedures

## Troubleshooting

### Common Issues

#### 1. Tesseract Not Found
```bash
# Install Tesseract in container or host
apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-vie
```

#### 2. Redis Connection Errors
```bash
# Check Redis is running
docker-compose ps redis

# Restart Redis
docker-compose restart redis
```

#### 3. MinIO Access Denied
```bash
# Re-initialize MinIO buckets
./mc mb myminio/receipts --ignore-existing
./mc anonymous set download myminio/receipts
```

#### 4. Model Not Loading
```bash
# Train initial model
docker-compose exec api python -m ml.train
```

#### 5. High Memory Usage
```bash
# Adjust worker concurrency
# Edit docker-compose.yml
# Set CELERY_WORKER_CONCURRENCY=2
docker-compose restart worker
```

## Monitoring & Maintenance

### Daily Tasks
- Check error logs
- Monitor processing queue
- Review failed jobs

### Weekly Tasks
- Review accuracy metrics
- Check backup status
- Clean up old jobs

### Monthly Tasks
- Model retraining with corrections
- Performance optimization
- Security updates

## Scaling Considerations

### Horizontal Scaling
```yaml
# Add more workers in docker-compose.yml
worker2:
  <<: *worker
  container_name: receipts_worker_2

worker3:
  <<: *worker
  container_name: receipts_worker_3
```

### Vertical Scaling
```yaml
# Increase resources in docker-compose.yml
services:
  worker:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

### Load Balancing
- Use Nginx/HAProxy for API load balancing
- Separate read/write databases if needed
- Use Redis cluster for high availability

## Support & Resources

- **Documentation**: `/docs` directory
- **API Docs**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Community**: Discussions

## License

MIT License - See LICENSE file for details