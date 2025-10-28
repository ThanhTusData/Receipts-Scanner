"""
Receipt processor for entity extraction using regex patterns
"""
import re
from typing import Dict, Any, List
import numpy as np
from datetime import datetime

from ocr_engines.base import OCRAdapter
from processing.patterns import (
    DATE_PATTERNS, AMOUNT_PATTERNS, PHONE_PATTERNS,
    MERCHANT_KEYWORDS, ITEM_PATTERNS, TAX_PATTERNS,
    ADDRESS_PATTERNS, IGNORE_KEYWORDS,
    clean_amount, clean_phone, clean_date
)
from monitoring.logging_config import get_logger

logger = get_logger(__name__)


class ReceiptProcessor:
    """Process receipt text and extract structured entities"""
    
    def __init__(self, ocr_adapter: OCRAdapter):
        """
        Initialize receipt processor
        
        Args:
            ocr_adapter: OCR adapter for text extraction
        """
        self.ocr_adapter = ocr_adapter
        logger.info("Receipt processor initialized")
    
    def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract text from receipt image
        
        Args:
            image: Preprocessed image
            
        Returns:
            dict: OCR result with text and confidence
        """
        return self.ocr_adapter.extract_text(image)
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract structured entities from receipt text
        
        Args:
            text: Raw OCR text
            
        Returns:
            dict: Extracted entities
        """
        logger.info("Extracting entities from receipt text")
        
        entities = {
            "merchant_name": self._extract_merchant_name(text),
            "receipt_date": self._extract_date(text),
            "total_amount": self._extract_total_amount(text),
            "phone": self._extract_phone(text),
            "address": self._extract_address(text),
            "items": self._extract_items(text),
            "tax": self._extract_tax(text)
        }
        
        logger.info(f"Extracted entities: merchant={entities['merchant_name']}, "
                   f"amount={entities['total_amount']}, date={entities['receipt_date']}")
        
        return entities
    
    def _extract_merchant_name(self, text: str) -> str:
        """Extract merchant/store name"""
        # Try keyword-based patterns first
        for pattern in MERCHANT_KEYWORDS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                return self._clean_merchant_name(name)
        
        # Fallback: use first line with capital letters
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            # Look for lines with multiple capital letters
            if len(line) > 5 and sum(1 for c in line if c.isupper()) >= 3:
                return self._clean_merchant_name(line)
        
        return "Unknown"
    
    def _clean_merchant_name(self, name: str) -> str:
        """Clean merchant name by removing special characters"""
        # Remove common receipt keywords
        for keyword in IGNORE_KEYWORDS:
            name = re.sub(keyword, '', name, flags=re.IGNORECASE)
        
        # Clean up
        name = re.sub(r'[^\w\s\u00C0-\u1EF9]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip()[:100] if name.strip() else "Unknown"
    
    def _extract_date(self, text: str) -> str:
        """Extract receipt date"""
        for pattern in DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    date_str = match.group(0)
                    cleaned = clean_date(date_str)
                    if cleaned and cleaned != date_str:
                        return cleaned
                except Exception as e:
                    logger.warning(f"Date parsing failed: {str(e)}")
                    continue
        
        # Fallback to today's date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_total_amount(self, text: str) -> float:
        """Extract total amount"""
        amounts = []
        
        for pattern in AMOUNT_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount_str = match.group(1)
                    amount = clean_amount(amount_str)
                    if amount > 0:
                        amounts.append(amount)
                except (IndexError, ValueError) as e:
                    continue
        
        # Return the largest amount found (likely to be total)
        return max(amounts) if amounts else 0.0
    
    def _extract_phone(self, text: str) -> str:
        """Extract phone number"""
        for pattern in PHONE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phone = match.group(1) if len(match.groups()) > 0 else match.group(0)
                cleaned = clean_phone(phone)
                if len(cleaned) >= 10:
                    return cleaned
        
        return ""
    
    def _extract_address(self, text: str) -> str:
        """Extract address"""
        for pattern in ADDRESS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                address = match.group(1).strip()
                if len(address) > 10:
                    return address[:200]
        
        return ""
    
    def _extract_items(self, text: str) -> List[str]:
        """Extract line items from receipt"""
        items = []
        
        for pattern in ITEM_PATTERNS:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                try:
                    # Get item name (usually first group)
                    item_name = match.group(1).strip()
                    
                    # Clean item name
                    item_name = self._clean_item_name(item_name)
                    
                    if item_name and len(item_name) > 2:
                        items.append(item_name)
                except Exception as e:
                    continue
        
        # Deduplicate while preserving order
        seen = set()
        unique_items = []
        for item in items:
            if item.lower() not in seen:
                seen.add(item.lower())
                unique_items.append(item)
        
        return unique_items[:20]  # Limit to 20 items
    
    def _clean_item_name(self, name: str) -> str:
        """Clean item name"""
        # Remove numbers at the end
        name = re.sub(r'\s*\d+[\.,]?\d*\s*$', '', name)
        
        # Remove special characters
        name = re.sub(r'[^\w\s\u00C0-\u1EF9]', ' ', name)
        
        # Clean whitespace
        name = ' '.join(name.split())
        
        return name.strip()
    
    def _extract_tax(self, text: str) -> float:
        """Extract tax/VAT amount"""
        for pattern in TAX_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    tax_str = match.group(1)
                    return clean_amount(tax_str)
                except Exception:
                    continue
        
        return 0.0