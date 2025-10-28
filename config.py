import os
from pathlib import Path

BASE_DIR = Path(os.getcwd())
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = BASE_DIR / "uploads"

DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

APP_CONFIG = {
    'page_title': 'ReceiptsScanner',
    'page_icon': '🧾',
    'layout': 'wide',
    'version': '2.0'
}

OCR_CONFIG = {
    'tesseract_config': '--oem 3 --psm 6',
    'min_confidence': 30,
    'max_file_size_mb': 10
}

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
