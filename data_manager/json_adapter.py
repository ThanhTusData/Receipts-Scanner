# imports cần thiết (đặt ở đầu file)
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# --- Các phương thức (đặt bên trong class của bạn) ---
def insert_receipt(self, receipt_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Thêm 1 hóa đơn vào self._data rồi lưu bằng self._save().
    Trả về True nếu lưu thành công, False nếu có lỗi.
    """
    if receipt_data is None:
        receipt_data = {}

    # defaults phải là 1 dict (bạn dán thiếu phần khai báo)
    defaults = {
        'id': str(int(time.time() * 1000)),  # nếu bạn không có id, tạo id đơn giản
        'store_name': '',
        'total_amount': 0,
        'processed_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'date': datetime.now().strftime('%d/%m/%Y'),
        'category': 'Khác',
        'notes': '',
        'confidence': 0,
        'phone': '',
        'address': '',
        'items': []
    }

    for k, v in defaults.items():
        receipt_data.setdefault(k, v)

    self._data.append(receipt_data)
    try:
        return self._save()  # giả sử _save() trả về True/False
    except Exception:
        return False

def list_receipts(self) -> List[Dict[str, Any]]:
    try:
        return sorted(
            self._data,
            key=lambda x: x.get('processed_date', ''),
            reverse=True
        )
    except Exception:
        return list(self._data)

def to_dataframe(self) -> pd.DataFrame:
    try:
        if not self._data:
            return pd.DataFrame()
        export_data = []
        for r in self._data:
            export_data.append({
                'Cửa hàng': r.get('store_name', ''),
                'Số tiền (VNĐ)': float(r.get('total_amount', 0)) if r.get('total_amount', None) is not None else 0,
                'Ngày mua': r.get('date', ''),
                'Danh mục': r.get('category', 'Khác'),
                'Ghi chú': r.get('notes', ''),
                'Độ tin cậy (%)': float(r.get('confidence', 0)) if r.get('confidence', None) is not None else 0,
                'Ngày xử lý': r.get('processed_date', ''),
            })
        return pd.DataFrame(export_data)
    except Exception:
        return pd.DataFrame()

# ... delete_receipt, get_statistics, backup_data, clear_all_data (see file)
def delete_receipt(self, receipt_id: str) -> bool:
    """
    Xóa hóa đơn theo id. Nếu có thay đổi số lượng phần tử thì lưu và trả về kết quả của _save().
    Nếu không có thay đổi, trả về False.
    """
    original = len(self._data)
    self._data = [r for r in self._data if r.get('id') != receipt_id]
    if len(self._data) < original:
        try:
            return self._save()
        except Exception:
            return False
    return False


def get_statistics(self) -> Dict[str, Any]:
    """
    Trả về các thống kê đơn giản: tổng số hóa đơn, tổng tiền, trung bình tiền, trung bình độ tin cậy.
    """
    if not self._data:
        return {'total_receipts': 0, 'total_amount': 0, 'avg_amount': 0, 'avg_confidence': 0}

    # Chuyển các giá trị về float/catch lỗi
    total_amount = 0.0
    total_conf = 0.0
    count = 0
    for r in self._data:
        try:
            total_amount += float(r.get('total_amount', 0) or 0)
            total_conf += float(r.get('confidence', 0) or 0)
            count += 1
        except (TypeError, ValueError):
            # bỏ record không chuyển được
            continue

    avg_confidence = (total_conf / count) if count > 0 else 0.0
    avg_amount = (total_amount / count) if count > 0 else 0.0

    return {
        'total_receipts': count,
        'total_amount': total_amount,
        'avg_amount': avg_amount,
        'avg_confidence': avg_confidence
    }


def backup_data(self) -> Optional[str]:
    """
    Tạo bản sao dữ liệu ra file .backup_<timestamp>.json và trả về path string, ngược lại trả về None.
    """
    try:
        # self.data_file phải là Path
        suffix = f'.backup_{int(time.time())}.json'
        if isinstance(self.data_file, Path):
            backup_file = self.data_file.with_suffix(suffix)
        else:
            backup_file = Path(str(self.data_file) + suffix)
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        return str(backup_file)
    except Exception:
        return None


def clear_all_data(self) -> bool:
    """
    Xóa toàn bộ dữ liệu trong memory và lưu file (gọi self._save()).
    """
    self._data = []
    try:
        return self._save()
    except Exception:
        return False
