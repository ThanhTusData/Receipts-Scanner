"""
JSON file-based data storage adapter
"""
import json
import os
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from threading import Lock

from data_manager.base import DataAdapter
from monitoring.logging_config import get_logger

logger = get_logger(__name__)


class JSONDataAdapter(DataAdapter):
    """JSON file-based storage implementation"""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize JSON data adapter
        
        Args:
            data_dir: Directory for data storage
        """
        self.data_dir = data_dir or os.getenv("DATA_DIR", "./data")
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.receipts_file = os.path.join(self.data_dir, "receipts.json")
        self.corrections_file = os.path.join(self.data_dir, "corrections.json")
        self.images_dir = os.path.join(self.data_dir, "images")
        
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Thread safety
        self.lock = Lock()
        
        # Initialize files
        self._init_files()
        
        logger.info(f"JSON adapter initialized: {self.data_dir}")
    
    def _init_files(self):
        """Initialize JSON files if they don't exist"""
        if not os.path.exists(self.receipts_file):
            with open(self.receipts_file, 'w') as f:
                json.dump([], f)
        
        if not os.path.exists(self.corrections_file):
            with open(self.corrections_file, 'w') as f:
                json.dump([], f)
    
    def _load_receipts(self) -> List[Dict[str, Any]]:
        """Load receipts from file"""
        try:
            with open(self.receipts_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading receipts: {str(e)}")
            return []
    
    def _save_receipts(self, receipts: List[Dict[str, Any]]) -> bool:
        """Save receipts to file"""
        try:
            with self.lock:
                with open(self.receipts_file, 'w') as f:
                    json.dump(receipts, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving receipts: {str(e)}")
            return False
    
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
        """Upload image to local storage"""
        try:
            destination = os.path.join(self.images_dir, filename)
            shutil.copy2(image_path, destination)
            logger.info(f"Image saved to {destination}")
            return destination
            
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return ""
    
    def save_correction(self, correction: Dict[str, Any]) -> bool:
        """Save a correction"""
        try:
            with self.lock:
                # Load existing corrections
                if os.path.exists(self.corrections_file):
                    with open(self.corrections_file, 'r') as f:
                        corrections = json.load(f)
                else:
                    corrections = []
                
                # Add new correction
                corrections.append(correction)
                
                # Save
                with open(self.corrections_file, 'w') as f:
                    json.dump(corrections, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved correction for receipt {correction.get('receipt_id')}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving correction: {str(e)}")
            return False
    
    def load_corrections(self) -> List[Dict[str, Any]]:
        """Load all corrections"""
        try:
            if os.path.exists(self.corrections_file):
                with open(self.corrections_file, 'r') as f:
                    return json.load(f)
            return []
            
        except Exception as e:
            logger.error(f"Error loading corrections: {str(e)}")
            return []
    
    def backup_data(self) -> str:
        """Backup data files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.data_dir, f".backup_{timestamp}.json")
            
            # Combine all data
            backup_data = {
                "receipts": self._load_receipts(),
                "corrections": self.load_corrections(),
                "backup_time": datetime.now().isoformat()
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data backed up to {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error backing up data: {str(e)}")
            return ""