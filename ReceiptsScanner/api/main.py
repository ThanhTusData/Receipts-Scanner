"""
FastAPI application - Main API endpoints for Receipt Scanner
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import os
import uuid
import logging

from api.middleware import setup_middleware
from workers.tasks import process_receipt_task, retrain_model_task
from data_manager.json_adapter import JSONDataAdapter
from data_manager.s3_adapter import S3DataAdapter
from data_manager.jobs_adapter import JobsAdapter
from monitoring.logging_config import get_logger
from monitoring.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    receipts_processed_total,
    processing_errors_total
)

# Initialize logger
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Receipt Scanner API",
    description="API for receipt scanning, OCR, and categorization",
    version="1.0.0"
)

# Setup middleware
setup_middleware(app)

# Initialize data adapters
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "json")

if STORAGE_BACKEND == "s3":
    data_adapter = S3DataAdapter()
else:
    data_adapter = JSONDataAdapter()

jobs_adapter = JobsAdapter()

# Pydantic models
class ReceiptUpdate(BaseModel):
    merchant_name: Optional[str] = None
    receipt_date: Optional[str] = None
    total_amount: Optional[float] = None
    category: Optional[str] = None
    items: Optional[List[str]] = None
    raw_text: Optional[str] = None

class ReceiptResponse(BaseModel):
    id: str
    merchant_name: Optional[str]
    receipt_date: Optional[str]
    total_amount: Optional[float]
    category: str
    confidence: float
    items: List[str]
    raw_text: str
    image_path: Optional[str]
    processed_at: str
    corrected: bool = False

class JobStatus(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

class MetricsResponse(BaseModel):
    total_receipts: int
    total_jobs: int
    pending_jobs: int
    failed_jobs: int
    avg_processing_time: float
    success_rate: float

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "storage_backend": STORAGE_BACKEND
    }

# Upload receipts endpoint
@app.post("/upload")
async def upload_receipts(files: List[UploadFile] = File(...)):
    """
    Upload receipt images for processing
    
    - **files**: List of image files (JPG, PNG, PDF)
    """
    logger.info(f"Received {len(files)} files for upload")
    
    http_requests_total.labels(method="POST", endpoint="/upload", status="200").inc()
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per upload")
    
    job_ids = []
    
    try:
        for file in files:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/jpg", "application/pdf"]
            if file.content_type not in allowed_types:
                logger.warning(f"Invalid file type: {file.content_type}")
                continue
            
            # Read file content
            file_content = await file.read()
            
            # Generate unique filename
            file_extension = file.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Save file temporarily
            temp_path = f"/tmp/{unique_filename}"
            with open(temp_path, "wb") as f:
                f.write(file_content)
            
            # Create processing job
            job = process_receipt_task.delay(temp_path, unique_filename)
            job_ids.append(job.id)
            
            # Track job
            jobs_adapter.create_job(
                job_id=job.id,
                task_type="process_receipt",
                status="pending",
                metadata={"filename": file.filename}
            )
            
            logger.info(f"Created job {job.id} for file {file.filename}")
        
        return {
            "message": f"Uploaded {len(job_ids)} files",
            "job_ids": job_ids
        }
        
    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}")
        processing_errors_total.labels(error_type="upload_error").inc()
        raise HTTPException(status_code=500, detail=str(e))

# Get job status
@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get status of a processing job"""
    logger.info(f"Fetching job status for {job_id}")
    
    try:
        job = jobs_adapter.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatus(**job)
        
    except Exception as e:
        logger.error(f"Error fetching job status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# List all receipts
@app.get("/receipts", response_model=List[ReceiptResponse])
async def list_receipts(
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    List all receipts with optional filtering
    
    - **limit**: Maximum number of receipts to return
    - **skip**: Number of receipts to skip (pagination)
    - **category**: Filter by category
    - **start_date**: Filter by start date (YYYY-MM-DD)
    - **end_date**: Filter by end date (YYYY-MM-DD)
    """
    logger.info(f"Listing receipts: limit={limit}, skip={skip}")
    
    try:
        receipts = data_adapter.list_receipts()
        
        # Apply filters
        if category:
            receipts = [r for r in receipts if r.get("category") == category]
        
        if start_date:
            receipts = [r for r in receipts if r.get("receipt_date", "") >= start_date]
        
        if end_date:
            receipts = [r for r in receipts if r.get("receipt_date", "") <= end_date]
        
        # Pagination
        total = len(receipts)
        receipts = receipts[skip:skip + limit]
        
        logger.info(f"Returning {len(receipts)} receipts (total: {total})")
        
        return receipts
        
    except Exception as e:
        logger.error(f"Error listing receipts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get single receipt
@app.get("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(receipt_id: str):
    """Get a single receipt by ID"""
    logger.info(f"Fetching receipt {receipt_id}")
    
    try:
        receipt = data_adapter.get_receipt(receipt_id)
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        return receipt
        
    except Exception as e:
        logger.error(f"Error fetching receipt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Update receipt
@app.put("/receipts/{receipt_id}", response_model=ReceiptResponse)
async def update_receipt(receipt_id: str, update_data: ReceiptUpdate):
    """Update receipt information and save as correction"""
    logger.info(f"Updating receipt {receipt_id}")
    
    try:
        receipt = data_adapter.get_receipt(receipt_id)
        
        if not receipt:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        # Track if category was corrected
        category_corrected = False
        original_category = receipt.get("category")
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        if "category" in update_dict and update_dict["category"] != original_category:
            category_corrected = True
        
        receipt.update(update_dict)
        receipt["corrected"] = True
        
        # Save updated receipt
        data_adapter.save_receipt(receipt)
        
        # Save correction for ML feedback
        if category_corrected:
            correction = {
                "receipt_id": receipt_id,
                "original_category": original_category,
                "corrected_category": update_dict["category"],
                "text": receipt.get("raw_text", ""),
                "merchant_name": receipt.get("merchant_name", ""),
                "items": receipt.get("items", []),
                "corrected_at": datetime.now().isoformat()
            }
            data_adapter.save_correction(correction)
            logger.info(f"Saved correction for receipt {receipt_id}")
        
        return receipt
        
    except Exception as e:
        logger.error(f"Error updating receipt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Delete receipt
@app.delete("/receipts/{receipt_id}")
async def delete_receipt(receipt_id: str):
    """Delete a receipt"""
    logger.info(f"Deleting receipt {receipt_id}")
    
    try:
        success = data_adapter.delete_receipt(receipt_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Receipt not found")
        
        return {"message": "Receipt deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting receipt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Get system metrics
@app.get("/admin/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get system metrics and statistics"""
    logger.info("Fetching system metrics")
    
    try:
        receipts = data_adapter.list_receipts()
        jobs = jobs_adapter.list_jobs()
        
        total_receipts = len(receipts)
        total_jobs = len(jobs)
        pending_jobs = len([j for j in jobs if j["status"] == "pending"])
        failed_jobs = len([j for j in jobs if j["status"] == "failed"])
        completed_jobs = len([j for j in jobs if j["status"] == "completed"])
        
        success_rate = completed_jobs / total_jobs if total_jobs > 0 else 0
        
        # Calculate average processing time
        processing_times = []
        for job in jobs:
            if job["status"] == "completed" and job.get("completed_at"):
                created = datetime.fromisoformat(job["created_at"])
                completed = datetime.fromisoformat(job["completed_at"])
                duration = (completed - created).total_seconds()
                processing_times.append(duration)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return MetricsResponse(
            total_receipts=total_receipts,
            total_jobs=total_jobs,
            pending_jobs=pending_jobs,
            failed_jobs=failed_jobs,
            avg_processing_time=avg_processing_time,
            success_rate=success_rate
        )
        
    except Exception as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Trigger model retraining
@app.post("/admin/retrain")
async def trigger_retrain():
    """Trigger ML model retraining with corrections"""
    logger.info("Triggering model retrain")
    
    try:
        job = retrain_model_task.delay()
        
        jobs_adapter.create_job(
            job_id=job.id,
            task_type="retrain_model",
            status="pending",
            metadata={"triggered_at": datetime.now().isoformat()}
        )
        
        return {
            "message": "Retraining job created",
            "job_id": job.id
        }
        
    except Exception as e:
        logger.error(f"Error triggering retrain: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Receipt Scanner API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)