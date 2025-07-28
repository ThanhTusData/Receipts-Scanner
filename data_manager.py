import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import time
from config import DATA_DIR

class DataManager:
    def __init__(self):
        # Sử dụng DATA_DIR từ config
        self.data_file = DATA_DIR / "receipts.json"
        self.data = self.load_data()
    
    def load_data(self):
        """Load dữ liệu từ file JSON"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure data is a list
                    return data if isinstance(data, list) else []
            return []
        except Exception as e:
            print(f"Error loading data: {e}")
            return []
    
    def save_data(self):
        """Lưu dữ liệu vào file JSON"""
        try:
            # Ensure data directory exists
            self.data_file.parent.mkdir(exist_ok=True)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    def add_receipt(self, receipt_data):
        """Thêm hóa đơn mới"""
        try:
            # Tạo ID duy nhất nếu chưa có
            if 'id' not in receipt_data:
                receipt_data['id'] = f"receipt_{int(time.time() * 1000)}"
            
            # Thêm processed_date nếu chưa có
            if 'processed_date' not in receipt_data:
                receipt_data['processed_date'] = datetime.now().isoformat()
            
            # Ensure required fields have default values
            defaults = {
                'store_name': '',
                'total_amount': 0,
                'date': datetime.now().strftime('%d/%m/%Y'),
                'category': 'Khác',
                'notes': '',
                'confidence': 0,
                'phone': '',
                'address': '',
                'items': []
            }
            
            for key, default_value in defaults.items():
                if key not in receipt_data:
                    receipt_data[key] = default_value
            
            self.data.append(receipt_data)
            return self.save_data()
        except Exception as e:
            print(f"Error adding receipt: {e}")
            return False
    
    def get_receipts(self):
        """Lấy tất cả hóa đơn, sắp xếp theo ngày mới nhất"""
        try:
            return sorted(self.data, key=lambda x: x.get('processed_date', ''), reverse=True)
        except Exception as e:
            print(f"Error getting receipts: {e}")
            return []
    
    def get_receipts_df(self):
        """Lấy dữ liệu dưới dạng DataFrame để phân tích và export"""
        try:
            if not self.data:
                return pd.DataFrame()
            
            # Chọn các cột cần thiết cho export
            export_data = []
            for receipt in self.data:
                try:
                    export_data.append({
                        'Cửa hàng': receipt.get('store_name', ''),
                        'Số tiền (VNĐ)': receipt.get('total_amount', 0),
                        'Ngày mua': receipt.get('date', ''),
                        'Danh mục': receipt.get('category', 'Khác'),
                        'Ghi chú': receipt.get('notes', ''),
                        'Độ tin cậy (%)': receipt.get('confidence', 0),
                        'Ngày xử lý': receipt.get('processed_date', ''),
                        # Additional fields for analytics
                        'store_name': receipt.get('store_name', ''),
                        'total_amount': receipt.get('total_amount', 0),
                        'date': receipt.get('date', ''),
                        'category': receipt.get('category', 'Khác'),
                        'confidence': receipt.get('confidence', 0)
                    })
                except Exception as e:
                    print(f"Error processing receipt for DataFrame: {e}")
                    continue
            
            return pd.DataFrame(export_data)
        except Exception as e:
            print(f"Error creating DataFrame: {e}")
            return pd.DataFrame()
    
    def delete_receipt(self, receipt_id):
        """Xóa hóa đơn theo ID"""
        try:
            original_length = len(self.data)
            self.data = [r for r in self.data if r.get('id') != receipt_id]
            
            if len(self.data) < original_length:
                return self.save_data()
            return False
        except Exception as e:
            print(f"Error deleting receipt: {e}")
            return False
    
    def get_statistics(self):
        """Lấy thống kê nhanh"""
        try:
            if not self.data:
                return {
                    'total_receipts': 0,
                    'total_amount': 0,
                    'avg_amount': 0,
                    'avg_confidence': 0
                }
            
            total_amount = sum(float(r.get('total_amount', 0)) for r in self.data)
            avg_confidence = sum(float(r.get('confidence', 0)) for r in self.data) / len(self.data)
            
            return {
                'total_receipts': len(self.data),
                'total_amount': total_amount,
                'avg_amount': total_amount / len(self.data) if len(self.data) > 0 else 0,
                'avg_confidence': avg_confidence
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                'total_receipts': 0,
                'total_amount': 0,
                'avg_amount': 0,
                'avg_confidence': 0
            }
    
    def backup_data(self):
        """Backup current data"""
        try:
            backup_file = self.data_file.with_suffix(f'.backup_{int(time.time())}.json')
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return str(backup_file)
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def clear_all_data(self):
        """Clear all data (for reset functionality)"""
        try:
            self.data = []
            return self.save_data()
        except Exception as e:
            print(f"Error clearing data: {e}")
            return False