"""
Tesseract OCR adapter implementation
"""
import pytesseract
from PIL import Image
import numpy as np
import os
from typing import Dict, Any
from ocr_engines.base import OCRAdapter
from monitoring.logging_config import get_logger

logger = get_logger(__name__)

class TesseractOCRAdapter(OCRAdapter):
    """Tesseract OCR implementation"""
    
    def __init__(self):
        """Initialize Tesseract OCR adapter"""
        self.tesseract_cmd = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")
        self.lang = os.getenv("TESSERACT_LANG", "eng+vie")
        self.psm = int(os.getenv("OCR_PSM", "6"))  # Page segmentation mode
        
        # Set Tesseract command path
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        
        logger.info(f"Tesseract initialized: lang={self.lang}, psm={self.psm}")
    
    def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract text from image using Tesseract
        
        Args:
            image: Image as numpy array (grayscale or RGB)
            
        Returns:
            dict with extracted text and confidence
        """
        try:
            # Convert numpy array to PIL Image
            if len(image.shape) == 2:  # Grayscale
                pil_image = Image.fromarray(image, mode='L')
            else:  # RGB
                pil_image = Image.fromarray(image, mode='RGB')
            
            # Configure Tesseract
            custom_config = f'--oem 3 --psm {self.psm}'
            
            # Extract text
            text = pytesseract.image_to_string(
                pil_image,
                lang=self.lang,
                config=custom_config
            )
            
            # Get detailed data for confidence calculation
            data = pytesseract.image_to_data(
                pil_image,
                lang=self.lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate average confidence
            confidences = [
                float(conf) for conf in data['conf'] 
                if conf != '-1'
            ]
            
            avg_confidence = (
                sum(confidences) / len(confidences) / 100.0
                if confidences else 0.0
            )
            
            logger.info(f"OCR extracted {len(text)} characters with confidence {avg_confidence:.2%}")
            
            return {
                "text": text.strip(),
                "confidence": avg_confidence,
                "boxes": self._extract_boxes(data) if data else []
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "boxes": []
            }
    
    def _extract_boxes(self, data: Dict) -> list:
        """Extract bounding boxes from OCR data"""
        boxes = []
        
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            if int(data['conf'][i]) > 0:  # Only include confident detections
                box = {
                    "text": data['text'][i],
                    "x": data['left'][i],
                    "y": data['top'][i],
                    "width": data['width'][i],
                    "height": data['height'][i],
                    "confidence": float(data['conf'][i]) / 100.0
                }
                boxes.append(box)
        
        return boxes
    
    def get_config(self) -> Dict[str, Any]:
        """Get Tesseract configuration"""
        return {
            "engine": "Tesseract",
            "version": pytesseract.get_tesseract_version(),
            "language": self.lang,
            "psm": self.psm,
            "command": self.tesseract_cmd
        }