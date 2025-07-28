import os
from pathlib import Path

# Đường dẫn cơ bản

BASE_DIR = Path(os.getcwd())  # luôn trả đúng thư mục chạy app.py
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"

# Tạo thư mục nếu chưa tồn tại
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

# Cấu hình ứng dụng
APP_CONFIG = {
    'page_title': 'ReceiptsScanner',
    'page_icon': '🧾',
    'layout': 'wide',
    'version': '2.0'
}

# Cấu hình OCR/AI
OCR_CONFIG = {
    'tesseract_config': '--oem 3 --psm 6',
    'min_confidence': 30,
    'max_file_size_mb': 10
}

# Danh mục chi tiêu với keywords - FIXED FORMAT
EXPENSE_CATEGORIES = {
    'Ăn uống': ['restaurant', 'food', 'coffee', 'cafe', 'nhà hàng', 'quán', 'ăn', 'thức ăn', 'cà phê', 'phở', 'bún', 'cơm'],
    'Mua sắm': ['store', 'shop', 'market', 'siêu thị', 'cửa hàng', 'mua', 'shopping', 'mart', 'plaza'],
    'Xăng dầu': ['gas', 'petrol', 'fuel', 'xăng', 'dầu', 'nhiên liệu', 'petrolimex'],
    'Y tế': ['pharmacy', 'hospital', 'clinic', 'bệnh viện', 'phòng khám', 'thuốc', 'dược phẩm'],
    'Giải trí': ['cinema', 'movie', 'entertainment', 'rạp phim', 'giải trí', 'vui chơi', 'karaoke'],
    'Giao thông': ['taxi', 'grab', 'uber', 'xe ôm', 'bus', 'xe buýt', 'giao thông'],
    'Học tập': ['school', 'book', 'education', 'trường', 'sách', 'học phí', 'văn phòng phẩm'],
    'Khác': []
}

# Category icons for display - separate mapping
CATEGORY_ICONS = {
    'Ăn uống': '🍽️',
    'Mua sắm': '🛒', 
    'Xăng dầu': '⛽',
    'Y tế': '🏥',
    'Giải trí': '🎬',
    'Giao thông': '🚗',
    'Học tập': '📚',
    'Khác': '📋'
}

# Từ khóa nhận diện
DETECTION_KEYWORDS = {
    'currency': ['VND', 'VNĐ', 'đ', '$', 'USD', 'total', 'tổng', 'thành tiền', 'cộng', 'sum'],
    'date': ['date', 'ngày', 'time', 'thời gian', 'bill date', 'hóa đơn'],
    'store': ['store', 'shop', 'company', 'cửa hàng', 'công ty', 'doanh nghiệp'],
    'phone': ['tel', 'phone', 'sdt', 'điện thoại', 'hotline'],
    'address': ['address', 'địa chỉ', 'add', 'street', 'đường']
}

# Cấu hình validation
VALIDATION_RULES = {
    'min_store_name_length': 2,
    'max_store_name_length': 100,
    'min_amount': 0,
    'max_amount': 100_000_000,  # 100 triệu VNĐ
    'date_format': '%d/%m/%Y'
}

# Tin nhắn hệ thống
MESSAGES = {
    'success': {
        'receipt_saved': '✅ Đã lưu hóa đơn thành công!',
        'receipt_deleted': '✅ Đã xóa hóa đơn!',
        'data_exported': '✅ Đã xuất dữ liệu!'
    },
    'error': {
        'ocr_failed': '❌ Không thể đọc được nội dung từ ảnh!',
        'save_failed': '❌ Có lỗi khi lưu dữ liệu!',
        'validation_failed': '⚠️ Vui lòng sửa các lỗi sau:'
    },
    'info': {
        'no_receipts': '📝 Chưa có hóa đơn nào!',
        'processing': '🔄 Đang xử lý ảnh...',
        'saving': '💾 Đang lưu...'
    }
}

# Cấu hình hiển thị
DISPLAY_CONFIG = {
    'items_preview_limit': 10,
    'receipts_per_page': 20,
    'max_search_results': 100,
    'currency_format': '{:,.0f} VNĐ'
}

# Cấu hình xuất dữ liệu
EXPORT_CONFIG = {
    'csv_columns': [
        'Cửa hàng', 'Số tiền (VNĐ)', 'Ngày mua', 'Danh mục', 
        'Ghi chú', 'Độ tin cậy (%)', 'Ngày xử lý'
    ],
    'filename_format': 'receipts_{timestamp}.csv'
}