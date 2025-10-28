#!/bin/bash
# Data backup script for Receipt Scanner

set -e

echo "Starting Receipt Scanner backup..."

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DATA_DIR="${DATA_DIR:-./data}"
MODELS_DIR="${MODELS_DIR:-./models}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p ${BACKUP_DIR}

# Backup filename
BACKUP_FILE="${BACKUP_DIR}/receipts_backup_${TIMESTAMP}.tar.gz"

echo "Backup file: ${BACKUP_FILE}"

# Create backup archive
echo "Creating backup archive..."
tar -czf ${BACKUP_FILE} \
    --exclude='*.log' \
    --exclude='__pycache__' \
    --exclude='.backup_*' \
    ${DATA_DIR} \
    ${MODELS_DIR}

# Get backup size
BACKUP_SIZE=$(du -h ${BACKUP_FILE} | cut -f1)
echo "Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Clean up old backups
echo "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find ${BACKUP_DIR} -name "receipts_backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete

# Count remaining backups
BACKUP_COUNT=$(ls -1 ${BACKUP_DIR}/receipts_backup_*.tar.gz 2>/dev/null | wc -l)
echo "Total backups retained: ${BACKUP_COUNT}"

# Optional: Upload to S3/MinIO
if [ ! -z "${S3_BACKUP_BUCKET}" ]; then
    echo "Uploading backup to S3..."
    
    if command -v aws &> /dev/null; then
        aws s3 cp ${BACKUP_FILE} s3://${S3_BACKUP_BUCKET}/backups/
        echo "✅ Backup uploaded to S3"
    elif command -v mc &> /dev/null; then
        mc cp ${BACKUP_FILE} myminio/${S3_BACKUP_BUCKET}/backups/
        echo "✅ Backup uploaded to MinIO"
    else
        echo "⚠️ Neither AWS CLI nor MinIO client found. Skipping S3 upload."
    fi
fi

echo "✅ Backup completed successfully!"
echo ""
echo "To restore from this backup:"
echo "  tar -xzf ${BACKUP_FILE} -C /"