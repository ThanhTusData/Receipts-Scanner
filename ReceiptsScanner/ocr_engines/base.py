"""
Abstract OCR Adapter interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import numpy as np

class OCRAdapter(ABC):
    """Abstract base class for OCR engines"""
    
    @abstractmethod
    def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract text from image
        
        Args:
            image: Image as numpy array
            
        Returns:
            dict with keys:
                - text: Extracted text
                - confidence: Overall confidence score (0-1)
                - boxes: Optional bounding boxes for text regions
        """
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """
        Get OCR engine configuration
        
        Returns:
            dict: Configuration parameters
        """
        pass