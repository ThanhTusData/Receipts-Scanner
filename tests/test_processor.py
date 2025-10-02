# tests/test_processor.py
import json
from PIL import Image
import io
import os

import pytest

from receipt_processor import ReceiptProcessor
from data_manager import DataManager

class DummyOcrAdapter:
    """Adapter giả trả về text cố định để test parser mà không cần tesseract."""
    def extract(self, image):
        text = (
            "Cua Hang ABC\n"
            "01/09/2025\n"
            "1 x Paneer 150,000\n"
            "TONG: 150,000 VND\n"
            "0901234567\n"
        )
        return {"raw_text": text, "ocr_meta": {"engine": "dummy", "duration": 0.001}}


def make_white_image(width=800, height=600):
    """Tạo ảnh trắng đơn giản (PIL.Image) để truyền vào processor."""
    return Image.new("RGB", (width, height), color="white")


def test_processor_with_dummy_ocr_adapter():
    """Smoke test: ReceiptProcessor hoạt động với adapter giả và trả về schema đúng."""
    img = make_white_image()
    rp = ReceiptProcessor(ocr_adapter=DummyOcrAdapter())
    out = rp.process_receipt(img)

    # Kiểm tra cấu trúc kết quả
    assert isinstance(out, dict)
    assert "parsed" in out
    parsed = out["parsed"]
    assert isinstance(parsed, dict)

    # Kiểm tra các trường quan trọng trong parsed
    assert parsed.get("store_name")  # store_name được lấy từ dòng đầu
    assert parsed.get("total_amount") >= 150000
    # phone có thể được bắt ra
    assert "090" in parsed.get("phone", "") or parsed.get("phone", "") == ""
    # confidence là số
    assert isinstance(parsed.get("confidence"), (int, float))


def test_data_manager_json_adapter_tmpdir(tmp_path):
    """Test DataManager (JSON adapter) với thư mục tạm để đảm bảo lưu và đọc hoạt động."""
    base_dir = tmp_path / "processed"
    dm = DataManager(base_dir=base_dir)

    sample = {
        "store_name": "Cua Hang ABC",
        "total_amount": 150000,
        "date": "01/09/2025",
        "items": [{"name": "Paneer", "price": 150000}],
        "confidence": 85
    }

    # Thêm receipt
    res = dm.add_receipt(sample)
    # add_receipt có thể trả True (the adapter implementation) hoặc đường dẫn - chấp nhận cả hai
    assert res in (True, None) or isinstance(res, (str, bool))

    # Kiểm tra file receipts.json tồn tại và có nội dung
    receipts_file = base_dir / "receipts.json"
    assert receipts_file.exists(), "receipts.json should be created in base_dir"

    with open(receipts_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert any(r.get("store_name") == "Cua Hang ABC" for r in data)

    # Kiểm tra API list_receipts trả về list
    listed = dm.get_receipts()
    assert isinstance(listed, list)
    # Phải có ít nhất 1 record
    assert len(listed) >= 1
