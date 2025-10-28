"""
Celery tasks for async processing
"""
from celery import Task
from workers.celery_app import celery_app
from datetime import datetime
import uuid
import os
import time

from ocr_engines.tesseract_adapter import TesseractOCRAdapter
from processing.preprocessing import preprocess_image
from processing.receipt_processor import ReceiptProcessor
from ml.category_classifier import CategoryClassifier
from ml.retrain import retrain_model
from data_manager.json_adapter import JSONDataAdapter
from data_manager.s3_adapter import S3DataAdapter
from data_manager.jobs_adapter import JobsAdapter
from monitoring.logging_config import get_logger
from monitoring.metrics import (
    receipts_processed_total,
    processing_errors_total,
    ocr_confidence_score,
    classification_confidence_score,
    celery_task_duration_seconds
)

logger = get_logger(__name__)

# Initialize components
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "json")

if STORAGE_BACKEND == "s3":
    data_adapter = S3DataAdapter()
else:
    data_adapter = JSONDataAdapter()

jobs_adapter = JobsAdapter()
ocr_adapter = TesseractOCRAdapter()
receipt_processor = ReceiptProcessor(ocr_adapter)
classifier = CategoryClassifier()

# Custom task base class for better tracking
class CallbackTask(Task):
    """Base task class with status callbacks"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"Task {task_id} failed: {str(exc)}")
        jobs_adapter.update_job(
            job_id=task_id,
            status="failed",
            error=str(exc),
            completed_at=datetime.now().isoformat()
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"Task {task_id} succeeded")
        jobs_adapter.update_job(
            job_id=task_id,
            status="completed",
            result=retval,
            completed_at=datetime.now().isoformat()
        )

@celery_app.task(base=CallbackTask, bind=True, name="process_receipt")
def process_receipt_task(self, image_path: str, original_filename: str):
    """
    Process a receipt image: OCR + entity extraction + classification
    
    Args:
        image_path: Path to the image file
        original_filename: Original filename for storage
        
    Returns:
        dict: Processed receipt data
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger.info(f"Processing receipt: {original_filename} [Job: {task_id}]")
    
    try:
        # Update job status
        jobs_adapter.update_job(task_id, status="processing")
        
        # Step 1: Preprocess image
        logger.info("Step 1: Preprocessing image")
        preprocessed_image = preprocess_image(image_path)
        
        # Step 2: OCR extraction
        logger.info("Step 2: OCR extraction")
        ocr_result = receipt_processor.extract_text(preprocessed_image)
        raw_text = ocr_result.get("text", "")
        ocr_confidence = ocr_result.get("confidence", 0)
        
        ocr_confidence_score.observe(ocr_confidence)
        logger.info(f"OCR confidence: {ocr_confidence:.2%}")
        
        if not raw_text or len(raw_text) < 10:
            raise ValueError("OCR extraction failed or text too short")
        
        # Step 3: Entity extraction
        logger.info("Step 3: Entity extraction")
        entities = receipt_processor.extract_entities(raw_text)
        
        # Step 4: Category classification
        logger.info("Step 4: Category classification")
        classification_result = classifier.predict(raw_text, entities)
        
        category = classification_result["category"]
        classification_conf = classification_result["confidence"]
        
        classification_confidence_score.observe(classification_conf)
        logger.info(f"Classified as '{category}' with confidence {classification_conf:.2%}")
        
        # Step 5: Upload image to storage
        logger.info("Step 5: Uploading image")
        image_url = data_adapter.upload_image(image_path, original_filename)
        
        # Step 6: Create receipt record
        receipt_id = str(uuid.uuid4())
        receipt_data = {
            "id": receipt_id,
            "merchant_name": entities.get("merchant_name"),
            "receipt_date": entities.get("receipt_date"),
            "total_amount": entities.get("total_amount"),
            "category": category,
            "confidence": classification_conf,
            "items": entities.get("items", []),
            "raw_text": raw_text,
            "image_path": image_url,
            "ocr_confidence": ocr_confidence,
            "processed_at": datetime.now().isoformat(),
            "corrected": False
        }
        
        # Step 7: Save receipt
        logger.info("Step 7: Saving receipt")
        data_adapter.save_receipt(receipt_data)
        
        # Clean up temporary file
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # Track metrics
        duration = time.time() - start_time
        celery_task_duration_seconds.labels(task_name="process_receipt").observe(duration)
        receipts_processed_total.labels(status="success").inc()
        
        logger.info(f"Receipt processed successfully in {duration:.2f}s [Job: {task_id}]")
        
        return {
            "receipt_id": receipt_id,
            "status": "success",
            "category": category,
            "confidence": classification_conf,
            "duration": duration
        }
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        processing_errors_total.labels(error_type="processing_error").inc()
        receipts_processed_total.labels(status="failed").inc()
        
        # Clean up on error
        if os.path.exists(image_path):
            os.remove(image_path)
        
        raise


@celery_app.task(base=CallbackTask, bind=True, name="retrain_model")
def retrain_model_task(self):
    """
    Retrain the category classification model with corrections
    
    Returns:
        dict: Retraining results
    """
    start_time = time.time()
    task_id = self.request.id
    
    logger.info(f"Starting model retraining [Job: {task_id}]")
    
    try:
        # Update job status
        jobs_adapter.update_job(task_id, status="processing")
        
        # Load corrections
        corrections = data_adapter.load_corrections()
        
        if len(corrections) < int(os.getenv("RETRAIN_THRESHOLD", "50")):
            logger.info(f"Not enough corrections ({len(corrections)}). Skipping retrain.")
            return {
                "status": "skipped",
                "reason": "insufficient_corrections",
                "corrections_count": len(corrections)
            }
        
        logger.info(f"Retraining with {len(corrections)} corrections")
        
        # Perform retraining
        result = retrain_model(corrections)
        
        duration = time.time() - start_time
        celery_task_duration_seconds.labels(task_name="retrain_model").observe(duration)
        
        logger.info(f"Model retrained successfully in {duration:.2f}s")
        logger.info(f"New accuracy: {result.get('accuracy', 0):.2%}")
        
        return {
            "status": "success",
            "accuracy": result.get("accuracy"),
            "model_version": result.get("model_version"),
            "corrections_used": len(corrections),
            "duration": duration
        }
        
    except Exception as e:
        logger.error(f"Error retraining model: {str(e)}")
        processing_errors_total.labels(error_type="retrain_error").inc()
        raise


@celery_app.task(name="cleanup_old_jobs")
def cleanup_old_jobs_task():
    """Periodic task to cleanup old completed jobs"""
    logger.info("Running cleanup of old jobs")
    
    try:
        deleted_count = jobs_adapter.cleanup_old_jobs(days=7)
        logger.info(f"Cleaned up {deleted_count} old jobs")
        
        return {
            "status": "success",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {str(e)}")
        raise


@celery_app.task(name="backup_data")
def backup_data_task():
    """Periodic task to backup data"""
    logger.info("Running data backup")
    
    try:
        backup_path = data_adapter.backup_data()
        logger.info(f"Data backed up to {backup_path}")
        
        return {
            "status": "success",
            "backup_path": backup_path
        }
        
    except Exception as e:
        logger.error(f"Error backing up data: {str(e)}")
        raise


# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-jobs": {
        "task": "cleanup_old_jobs",
        "schedule": 86400.0,  # Daily
    },
    "backup-data": {
        "task": "backup_data",
        "schedule": 86400.0,  # Daily
    },
}