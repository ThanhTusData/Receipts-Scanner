"""
Tests for receipt processor and entity extraction
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock

from processing.receipt_processor import ReceiptProcessor
from ocr_engines.base import OCRAdapter


class MockOCRAdapter(OCRAdapter):
    """Mock OCR adapter for testing"""
    
    def extract_text(self, image):
        return {
            "text": """
            SIÊU THỊ ABC
            123 Nguyen Hue, Q1, HCMC
            Tel: 0123456789
            
            Date: 15/10/2024
            
            Thịt bò        2 x 150000
            Rau xanh       1 x 50000
            Gạo 5kg        1 x 120000
            
            Subtotal: 320000
            Tax (10%): 32000
            Total: 352000 VND
            
            Thank you!
            """,
            "confidence": 0.95,
            "boxes": []
        }
    
    def get_config(self):
        return {"engine": "Mock", "version": "1.0"}


def test_receipt_processor_init():
    """Test receipt processor initialization"""
    ocr_adapter = MockOCRAdapter()
    processor = ReceiptProcessor(ocr_adapter)
    
    assert processor is not None
    assert processor.ocr_adapter is not None


def test_extract_text():
    """Test text extraction"""
    ocr_adapter = MockOCRAdapter()
    processor = ReceiptProcessor(ocr_adapter)
    
    # Create dummy image
    image = np.zeros((100, 100), dtype=np.uint8)
    
    result = processor.extract_text(image)
    
    assert "text" in result
    assert "confidence" in result
    assert len(result["text"]) > 0
    assert result["confidence"] > 0


def test_extract_merchant_name():
    """Test merchant name extraction"""
    ocr_adapter = MockOCRAdapter()
    processor = ReceiptProcessor(ocr_adapter)
    
    text = "SIÊU THỊ ABC\n123 Nguyen Hue"
    entities = processor.extract_entities(text)
    
    assert entities["merchant_name"] is not None
    assert len(entities["merchant_name"]) > 0


def test_extract_total_amount():
    """Test total amount extraction"""
    ocr_adapter = MockOCRAdapter()
    processor = ReceiptProcessor(ocr_adapter)
    
    text = "Total: 352,000 VND"
    entities = processor.extract_entities(text)
    
    assert entities["total_amount"] > 0


def test_extract_phone():
    """Test phone number extraction"""
    ocr_adapter = MockOCRAdapter()
    processor = ReceiptProcessor(ocr_adapter)
    
    text = "Tel: 0123456789"
    entities = processor.extract_entities(text)
    
    assert entities["phone"] is not None
    assert len(entities["phone"]) >= 10


def test_extract_items():
    """Test item extraction"""
    ocr_adapter = MockOCRAdapter()
    processor = ReceiptProcessor(ocr_adapter)
    
    text = """
    Thịt bò        2 x 150000
    Rau xanh       1 x 50000
    Gạo 5kg        1 x 120000
    """
    entities = processor.extract_entities(text)
    
    assert "items" in entities
    assert len(entities["items"]) > 0


def test_extract_entities_comprehensive():
    """Test comprehensive entity extraction"""
    ocr_adapter = MockOCRAdapter()
    processor = ReceiptProcessor(ocr_adapter)
    
    image = np.zeros((100, 100), dtype=np.uint8)
    ocr_result = processor.extract_text(image)
    entities = processor.extract_entities(ocr_result["text"])
    
    # Check all entity types
    assert "merchant_name" in entities
    assert "receipt_date" in entities
    assert "total_amount" in entities
    assert "phone" in entities
    assert "items" in entities
    
    # Check values
    assert entities["total_amount"] > 0
    assert entities["merchant_name"] != "Unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])