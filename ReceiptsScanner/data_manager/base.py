"""
Abstract data adapter interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class DataAdapter(ABC):
    """Abstract base class for data storage adapters"""
    
    @abstractmethod
    def save_receipt(self, receipt: Dict[str, Any]) -> bool:
        """
        Save a receipt
        
        Args:
            receipt: Receipt data dictionary
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    def get_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a receipt by ID
        
        Args:
            receipt_id: Receipt ID
            
        Returns:
            dict: Receipt data or None
        """
        pass
    
    @abstractmethod
    def list_receipts(self) -> List[Dict[str, Any]]:
        """
        List all receipts
        
        Returns:
            list: List of receipts
        """
        pass
    
    @abstractmethod
    def delete_receipt(self, receipt_id: str) -> bool:
        """
        Delete a receipt
        
        Args:
            receipt_id: Receipt ID
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    def upload_image(self, image_path: str, filename: str) -> str:
        """
        Upload image to storage
        
        Args:
            image_path: Path to image file
            filename: Destination filename
            
        Returns:
            str: Image URL or path
        """
        pass
    
    @abstractmethod
    def save_correction(self, correction: Dict[str, Any]) -> bool:
        """
        Save a correction for ML feedback
        
        Args:
            correction: Correction data
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    def load_corrections(self) -> List[Dict[str, Any]]:
        """
        Load all corrections
        
        Returns:
            list: List of corrections
        """
        pass
    
    @abstractmethod
    def backup_data(self) -> str:
        """
        Backup data
        
        Returns:
            str: Backup file path
        """
        pass