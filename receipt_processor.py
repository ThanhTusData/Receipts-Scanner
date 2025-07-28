import cv2
import pytesseract
import re
import os
import numpy as np
from PIL import Image

class ReceiptProcessor:
    def __init__(self):
        # Cấu hình Tesseract
        os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Compiled regex patterns cho hiệu suất tốt hơn
        self.patterns = {
            'amount': re.compile(r'([0-9]{1,3}(?:[,\.][0-9]{3})+|[0-9]+[,\.][0-9]{3}|[0-9]{4,})'),
            'date': re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}\.\d{1,2}\.\d{2,4})'),
            'phone': re.compile(r'([0-9]{3,4}[\s\-]?[0-9]{3,4}[\s\-]?[0-9]{3,4}|\+84[0-9\s\-]{8,12})'),
            'total_keywords': re.compile(r'(tổng|total|thành tiền|sum)', re.IGNORECASE),
            'store_keywords': re.compile(r'(shop|store|cửa hàng|công ty|co\.ltd|ltd)', re.IGNORECASE),
            'currency': re.compile(r'(VND|VNĐ|đ|dong)', re.IGNORECASE)
        }
    
    def preprocess_image_simple(self, image):
        """Tiền xử lý ảnh đơn giản"""
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh
    
    def preprocess_image_enhanced(self, image):
        """Tiền xử lý ảnh nâng cao"""
        if isinstance(image, Image.Image):
            image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image.copy()
        
        # CLAHE và adaptive threshold
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        return cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    def extract_text_ocr(self, image):
        """Trích xuất text với multiple methods"""
        configs = [
            (self.preprocess_image_simple(image), r'--oem 3 --psm 6'),
            (self.preprocess_image_enhanced(image), r'--oem 3 --psm 6'),
            (self.preprocess_image_simple(image), r'--oem 3 --psm 4')
        ]
        
        texts = []
        for processed_img, config in configs:
            try:
                text = pytesseract.image_to_string(processed_img, config=config, lang='vie').strip()
                if len(text) > 10:
                    texts.append(text)
            except:
                continue
        
        return self._select_best_text(texts) if texts else ""
    
    def _select_best_text(self, texts):
        """Chọn text tốt nhất dựa trên scoring nhanh"""
        best_text = ""
        best_score = -1
        
        for text in texts:
            # Scoring nhanh với weighted features
            score = (
                20 if 50 <= len(text) <= 2000 else 0,
                30 if self.patterns['amount'].search(text) else 0,
                25 if self.patterns['currency'].search(text) else 0,
                20 if self.patterns['date'].search(text) else 0,
                25 if self.patterns['total_keywords'].search(text) else 0,
                15 if 3 <= len([l for l in text.split('\n') if l.strip()]) <= 30 else 0
            )
            total_score = sum(score)
            
            if total_score > best_score:
                best_score = total_score
                best_text = text
        
        return best_text
    
    def extract_entities_smart(self, text):
        """Trích xuất thông tin thông minh và nhanh"""
        if not text:
            return self._empty_result()
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Tìm các thông tin cần thiết trong một lần duyệt
        entities = {
            'store_name': '',
            'total_amount': 0.0,
            'date': '',
            'items': [],
            'phone': '',
            'address': '',
            'confidence': 0
        }
        
        amounts = []
        
        for i, line in enumerate(lines):
            # Store name - thường ở 3 dòng đầu, ít số, có từ khóa
            if i < 3 and not entities['store_name']:
                if len(self.patterns['amount'].findall(line)) < 2 and len(line) > 3:
                    if self.patterns['store_keywords'].search(line) or not any(char.isdigit() for char in line[:len(line)//2]):
                        entities['store_name'] = line[:50]
            
            # Date
            if not entities['date']:
                date_match = self.patterns['date'].search(line)
                if date_match:
                    entities['date'] = date_match.group(1)
            
            # Phone
            if not entities['phone']:
                phone_match = self.patterns['phone'].search(line)
                if phone_match:
                    entities['phone'] = phone_match.group(1)
            
            # Address
            if 'địa chỉ' in line.lower() or 'address' in line.lower():
                entities['address'] = line
            
            # Amounts
            line_amounts = self._extract_amounts_from_line(line)
            amounts.extend(line_amounts)
            
            # Total amount - ưu tiên dòng có từ khóa
            if self.patterns['total_keywords'].search(line) and line_amounts:
                entities['total_amount'] = max(line_amounts)
            
            # Items - dòng có cả text và số, không phải total
            if (len([c for c in line if c.isalpha()]) > 3 and 
                line_amounts and 
                not self.patterns['total_keywords'].search(line)):
                item_name = re.sub(r'\d+[,\.\d]*.*$', '', line).strip()
                if len(item_name) > 2:
                    entities['items'].append({
                        'name': item_name[:30],
                        'price': max(line_amounts)
                    })
        
        # Fallbacks
        if not entities['total_amount'] and amounts:
            entities['total_amount'] = max(amounts)
        
        if not entities['store_name'] and lines:
            entities['store_name'] = lines[0][:50]
        
        # Calculate confidence
        entities['confidence'] = self._calculate_confidence(entities)
        
        return entities
    
    def _extract_amounts_from_line(self, line):
        """Trích xuất số tiền từ dòng - optimized"""
        amounts = []
        matches = self.patterns['amount'].findall(line)
        
        for match in matches:
            try:
                clean_amount = re.sub(r'[,\.]', '', match)
                if clean_amount.isdigit():
                    amount = float(clean_amount)
                    if 1000 <= amount <= 100000000:
                        amounts.append(amount)
            except:
                continue
        
        return amounts
    
    def _calculate_confidence(self, entities):
        """Tính confidence score nhanh"""
        score = 0
        if entities['total_amount'] > 0: score += 40
        if entities['store_name'] and len(entities['store_name']) > 3: score += 25
        if entities['date']: score += 20
        if entities['phone']: score += 10
        if entities['items']: score += 5
        return min(score, 100)
    
    def _empty_result(self):
        """Return empty result structure"""
        return {
            'store_name': '',
            'total_amount': 0.0,
            'date': '',
            'items': [],
            'phone': '',
            'address': '',
            'confidence': 0
        }
    
    def process_receipt(self, image):
        """Xử lý receipt - main method"""
        text = self.extract_text_ocr(image)
        return self.extract_entities_smart(text)
    
    # Backward compatibility
    def extract_text_ocr_legacy(self, image):
        return self.extract_text_ocr(image)
    
    def extract_entities(self, text):
        return self.extract_entities_smart(text)