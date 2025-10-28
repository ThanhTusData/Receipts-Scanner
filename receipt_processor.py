import time
import uuid
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np

from preprocessing import preprocess_image
from ocr_engines.tesseract_adapter import TesseractAdapter

# Keep patterns similar to original for robust extraction
patterns = {
    'amount': re.compile(r'([0-9]{1,3}(?:[,\.][0-9]{3})+|[0-9]+[,\.][0-9]{3}|[0-9]{4,})'),
    'date': re.compile(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|\d{1,2}\.\d{1,2}\.\d{2,4})'),
    'phone': re.compile(r'(\+?84[\s\-]?[0-9]{8,12}|[0-9]{3,4}[\s\-]?[0-9]{3,4}[\s\-]?[0-9]{3,4})'),
    'total_keywords': re.compile(r'(tổng|total|thành tiền|sum|total:|final total|final|subtotal)', re.IGNORECASE),
    'currency': re.compile(r'(VND|VNĐ|đ|dong)', re.IGNORECASE)
}

class ReceiptProcessorRefactor:
    def __init__(self, ocr_adapter: Optional[Any] = None):
        """
        ocr_adapter: object có method extract(image) -> {'raw_text': str, 'ocr_meta': {...}}
        """
        self.ocr = ocr_adapter or TesseractAdapter()

    def _normalize_number(self, s: str) -> Optional[float]:
        """Remove separators and parse to float. Return None if fail."""
        try:
            cleaned = re.sub(r'[^\d]', '', s)  # giữ chữ số
            if cleaned == '':
                return None
            return float(cleaned)
        except Exception:
            return None

    def _extract_amounts(self, line: str) -> List[float]:
        """
        Tìm tất cả pattern số trong 1 dòng, trả về danh sách số hợp lệ (float).
        Giữ lại những số lớn hơn 1000 (có khả năng là tiền) và < 1e12 để tránh số vô lý.
        """
        amounts: List[float] = []
        for m in patterns['amount'].findall(line):
            try:
                match_text = m if isinstance(m, str) else m[0]
                val = self._normalize_number(match_text)
                if val is None:
                    continue
                if 1000 <= val <= 1e12:
                    amounts.append(val)
            except Exception:
                continue
        return amounts

    def _extract_dates(self, line: str) -> List[str]:
        """Trả về list các date string match."""
        return [m if isinstance(m, str) else m[0] for m in patterns['date'].findall(line)]

    def _extract_phones(self, line: str) -> List[str]:
        return [m if isinstance(m, str) else m[0] for m in patterns['phone'].findall(line)]

    def _calc_confidence(self, entities: Dict[str, Any]) -> int:
        """
        Tính điểm tin cậy đơn giản dựa trên các entity tìm được.
        Trọng số (ví dụ):
            - total_amount: 50 điểm
            - date: 15 điểm
            - phone: 10 điểm
            - currency: 10 điểm
            - store_name: 15 điểm
        Tổng tối đa 100.
        """
        score = 0
        if entities.get('total_amount', 0) and entities['total_amount'] > 0:
            score += 50
        if entities.get('date'):
            score += 15
        if entities.get('phone'):
            score += 10
        if entities.get('currency'):
            score += 10
        if entities.get('store_name'):
            score += 15

        # cap 0-100
        return max(0, min(100, int(score)))

    def extract_entities(self, raw_text: str) -> Dict[str, Any]:
        """
        Từ raw_text (chuỗi lớn), tách thành lines, scan để tìm amounts, date, phone, currency, store_name.
        Quy tắc chọn total_amount:
          - Nếu có dòng chứa keyword 'total' hoặc 'tổng' => chọn số lớn nhất trên dòng đó (nếu có)
          - Nếu không, chọn giá trị lớn nhất trong toàn hoá đơn
        """
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
        found_amounts = []
        candidate_totals = []
        found_dates = []
        found_phones = []
        found_currency = None
        store_name = None

        # heuristic: first non-numeric long text line (<= 40 chars and contains letters) may be store name
        for ln in lines[:6]:
            if re.search(r'[A-Za-zÀ-ỹ]', ln) and not any(ch.isdigit() for ch in ln) and 3 < len(ln) < 80:
                store_name = ln
                break

        for ln in lines:
            amounts = self._extract_amounts(ln)
            if amounts:
                found_amounts.extend(amounts)
            dates = self._extract_dates(ln)
            if dates:
                found_dates.extend(dates)
            phones = self._extract_phones(ln)
            if phones:
                found_phones.extend(phones)
            if not found_currency and patterns['currency'].search(ln):
                found_currency = patterns['currency'].search(ln).group(0)
            if patterns['total_keywords'].search(ln):
                if amounts:
                    candidate_totals.extend(amounts)

        # decide total_amount
        total_amount = 0.0
        if candidate_totals:
            total_amount = max(candidate_totals)
        elif found_amounts:
            total_amount = max(found_amounts)

        entities = {
            'store_name': store_name or '',
            'total_amount': float(total_amount) if total_amount else 0.0,
            'date': found_dates[0] if found_dates else '',
            'phone': found_phones[0] if found_phones else '',
            'currency': found_currency or '',
            'raw_amounts': found_amounts,
            'raw_dates': found_dates,
            'lines_scanned': len(lines),
        }

        entities['confidence'] = self._calc_confidence(entities)
        return entities

    def process(self, image_input: Any) -> Dict[str, Any]:
        """
        Toàn bộ pipeline: preprocess -> ocr -> extract_entities -> return result dict.
        Trả về:
          {
            'id': str,
            'processed_date': ISO str,
            'raw_text': str,
            'ocr_meta': {...},
            'entities': {...},
            'duration': float,
          }
        """
        start = time.time()
        pre = preprocess_image(image_input)
        if pre is None:
            return {
                'id': str(uuid.uuid4()),
                'processed_date': datetime.utcnow().isoformat() + 'Z',
                'raw_text': '',
                'ocr_meta': {'engine': getattr(self.ocr, '__class__', type(self.ocr)).__name__, 'duration': 0.0},
                'entities': {},
                'duration': time.time() - start,
            }

        # OCR
        try:
            ocr_result = self.ocr.extract(pre)
            raw_text = ocr_result.get('raw_text', '') if isinstance(ocr_result, dict) else str(ocr_result)
            ocr_meta = ocr_result.get('ocr_meta', {}) if isinstance(ocr_result, dict) else {}
        except Exception:
            raw_text = ''
            ocr_meta = {}

        entities = self.extract_entities(raw_text)

        result = {
            'id': str(uuid.uuid4()),
            'processed_date': datetime.utcnow().isoformat() + 'Z',
            'raw_text': raw_text,
            'ocr_meta': ocr_meta,
            'entities': entities,
            'duration': time.time() - start,
        }
        return result
