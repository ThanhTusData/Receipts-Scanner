"""
MinIO/S3 object storage adapter
"""
from minio import Minio
from minio.error import S3Error
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from io import BytesIO

from data_manager.base import DataAdapter
from monitoring.logging_config import get_logger

logger = get_logger(__name__)


class S3DataAdapter(DataAdapter):
    """MinIO/S3 storage implementation"""
    
    def __init__(self):
        """Initialize S3 data adapter"""
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "receipts")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        # Initialize MinIO client
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        # Ensure bucket exists
        self._ensure_bucket()
        
        # Object keys
        self.receipts_key = "data/receipts.json"
        self.corrections_key = "data/corrections.json"
        self.images_prefix = "images/"
        
        logger.info(f"S3 adapter initialized: {self.endpoint}/{self.bucket_name}")
    
    def _ensure_bucket(self):
        """Ensure bucket exists"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.info(f"Bucket exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket: {str(e)}")
            raise
    
    def _get_object(self, object_key: str) -> Any:
        """Get object from S3"""
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            data = response.read()
            response.close()
            response.release_conn()
            return json.loads(data.decode('utf-8'))
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return None
            logger.error(f"Error getting object {object_key}: {str(e)}")
            return None
    
    def _put_object(self, object_key: str, data: Any) -> bool:
        """Put object to S3"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            data_bytes = json_data.encode('utf-8')
            data_stream = BytesIO(data_bytes)
            
            self.client.put_object(
                self.bucket_name,
                object_key,
                data_stream,
                len(data_bytes),
                content_type='application/json'
            )
            return True
        except S3Error as e:
            logger.error(f"Error putting object {object_key}: {str(e)}")
            return False
    
    def _load_receipts(self) -> List[Dict[str, Any]]:
        """Load receipts from S3"""
        receipts = self._get_object(self.receipts_key)
        return receipts if receipts is not None else []
    
    def _save_receipts(self, receipts: List[Dict[str, Any]]) -> bool:
        """Save receipts to S3"""
        return self._put_object(self.receipts_key, receipts)
    
    def save_receipt(self, receipt: Dict[str, Any]) -> bool:
        """Save a receipt"""
        try:
            receipts = self._load_receipts()
            
            # Check if receipt exists (update)
            existing_index = None
            for i, r in enumerate(receipts):
                if r.get('id') == receipt.get('id'):
                    existing_index = i
                    break
            
            if existing_index is not None:
                receipts[existing_index] = receipt
                logger.info(f"Updated receipt {receipt['id']}")
            else:
                receipts.append(receipt)
                logger.info(f"Saved new receipt {receipt['id']}")
            
            return self._save_receipts(receipts)
            
        except Exception as e:
            logger.error(f"Error saving receipt: {str(e)}")
            return False
    
    def get_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """Get a receipt by ID"""
        receipts = self._load_receipts()
        
        for receipt in receipts:
            if receipt.get('id') == receipt_id:
                return receipt
        
        return None
    
    def list_receipts(self) -> List[Dict[str, Any]]:
        """List all receipts"""
        return self._load_receipts()
    
    def delete_receipt(self, receipt_id: str) -> bool:
        """Delete a receipt"""
        try:
            receipts = self._load_receipts()
            
            # Find and remove receipt
            initial_count = len(receipts)
            receipts = [r for r in receipts if r.get('id') != receipt_id]
            
            if len(receipts) < initial_count:
                self._save_receipts(receipts)
                logger.info(f"Deleted receipt {receipt_id}")
                return True
            
            logger.warning(f"Receipt {receipt_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting receipt: {str(e)}")
            return False
    
    def upload_image(self, image_path: str, filename: str) -> str:
        """Upload image to S3"""
        try:
            object_key = f"{self.images_prefix}{filename}"
            
            self.client.fput_object(
                self.bucket_name,
                object_key,
                image_path,
                content_type='image/jpeg'
            )
            
            # Generate presigned URL (valid for 7 days)
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_key,
                expires=timedelta(days=7)
            )
            
            logger.info(f"Image uploaded to {object_key}")
            return url
            
        except S3Error as e:
            logger.error(f"Error uploading image: {str(e)}")
            return ""
    
    def save_correction(self, correction: Dict[str, Any]) -> bool:
        """Save a correction"""
        try:
            # Load existing corrections
            corrections = self._get_object(self.corrections_key)
            if corrections is None:
                corrections = []
            
            # Add new correction
            corrections.append(correction)
            
            # Save
            success = self._put_object(self.corrections_key, corrections)
            
            if success:
                logger.info(f"Saved correction for receipt {correction.get('receipt_id')}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving correction: {str(e)}")
            return False
    
    def load_corrections(self) -> List[Dict[str, Any]]:
        """Load all corrections"""
        try:
            corrections = self._get_object(self.corrections_key)
            return corrections if corrections is not None else []
            
        except Exception as e:
            logger.error(f"Error loading corrections: {str(e)}")
            return []
    
    def backup_data(self) -> str:
        """Backup data to S3"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_key = f"backups/backup_{timestamp}.json"
            
            # Combine all data
            backup_data = {
                "receipts": self._load_receipts(),
                "corrections": self.load_corrections(),
                "backup_time": datetime.now().isoformat()
            }
            
            self._put_object(backup_key, backup_data)
            
            logger.info(f"Data backed up to {backup_key}")
            return backup_key
            
        except Exception as e:
            logger.error(f"Error backing up data: {str(e)}")
            return ""


# Import at the end to avoid circular import issues
from datetime import timedelta