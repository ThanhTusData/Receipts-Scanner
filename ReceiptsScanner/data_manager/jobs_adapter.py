"""
Job tracking adapter for managing async task status
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from threading import Lock

from monitoring.logging_config import get_logger

logger = get_logger(__name__)


class JobsAdapter:
    """Thread-safe job tracking"""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize jobs adapter
        
        Args:
            data_dir: Directory for job data storage
        """
        self.data_dir = data_dir or os.getenv("DATA_DIR", "./data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.jobs_file = os.path.join(self.data_dir, "jobs.json")
        self.lock = Lock()
        
        # Initialize file
        if not os.path.exists(self.jobs_file):
            with open(self.jobs_file, 'w') as f:
                json.dump({}, f)
        
        logger.info(f"Jobs adapter initialized: {self.jobs_file}")
    
    def _load_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Load jobs from file"""
        try:
            with open(self.jobs_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading jobs: {str(e)}")
            return {}
    
    def _save_jobs(self, jobs: Dict[str, Dict[str, Any]]) -> bool:
        """Save jobs to file"""
        try:
            with self.lock:
                with open(self.jobs_file, 'w') as f:
                    json.dump(jobs, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving jobs: {str(e)}")
            return False
    
    def create_job(self, job_id: str, task_type: str, status: str = "pending",
                   metadata: Dict[str, Any] = None) -> bool:
        """
        Create a new job
        
        Args:
            job_id: Unique job ID
            task_type: Type of task
            status: Initial status
            metadata: Optional metadata
            
        Returns:
            bool: Success status
        """
        try:
            jobs = self._load_jobs()
            
            jobs[job_id] = {
                "job_id": job_id,
                "task_type": task_type,
                "status": status,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "completed_at": None,
                "result": None,
                "error": None
            }
            
            self._save_jobs(jobs)
            logger.info(f"Created job {job_id} ({task_type})")
            return True
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job by ID
        
        Args:
            job_id: Job ID
            
        Returns:
            dict: Job data or None
        """
        jobs = self._load_jobs()
        return jobs.get(job_id)
    
    def update_job(self, job_id: str, status: str = None, result: Any = None,
                   error: str = None, completed_at: str = None) -> bool:
        """
        Update job status
        
        Args:
            job_id: Job ID
            status: New status
            result: Job result
            error: Error message
            completed_at: Completion timestamp
            
        Returns:
            bool: Success status
        """
        try:
            jobs = self._load_jobs()
            
            if job_id not in jobs:
                logger.warning(f"Job {job_id} not found")
                return False
            
            if status:
                jobs[job_id]["status"] = status
            
            if result is not None:
                jobs[job_id]["result"] = result
            
            if error:
                jobs[job_id]["error"] = error
            
            if completed_at:
                jobs[job_id]["completed_at"] = completed_at
            
            jobs[job_id]["updated_at"] = datetime.now().isoformat()
            
            self._save_jobs(jobs)
            logger.info(f"Updated job {job_id}: status={status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job: {str(e)}")
            return False
    
    def list_jobs(self, status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List jobs with optional filtering
        
        Args:
            status: Filter by status
            limit: Maximum number of jobs
            
        Returns:
            list: List of jobs
        """
        jobs = self._load_jobs()
        job_list = list(jobs.values())
        
        # Filter by status
        if status:
            job_list = [j for j in job_list if j.get("status") == status]
        
        # Sort by created_at (newest first)
        job_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Limit
        return job_list[:limit]
    
    def cleanup_old_jobs(self, days: int = 7) -> int:
        """
        Remove old completed jobs
        
        Args:
            days: Keep jobs newer than this many days
            
        Returns:
            int: Number of jobs deleted
        """
        try:
            jobs = self._load_jobs()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            initial_count = len(jobs)
            
            # Keep recent jobs and pending/processing jobs
            jobs_to_keep = {}
            for job_id, job in jobs.items():
                created_at = datetime.fromisoformat(job.get("created_at", datetime.now().isoformat()))
                status = job.get("status")
                
                if created_at > cutoff_date or status in ["pending", "processing"]:
                    jobs_to_keep[job_id] = job
            
            self._save_jobs(jobs_to_keep)
            
            deleted_count = initial_count - len(jobs_to_keep)
            logger.info(f"Cleaned up {deleted_count} old jobs")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up jobs: {str(e)}")
            return 0