"""
ML configuration - Categories and keywords for classification
"""

# Category definitions with Vietnamese and English names
CATEGORIES = [
    "Thực Phẩm",      # Food
    "Điện Tử",        # Electronics
    "Quần Áo",        # Clothing
    "Y Tế",           # Healthcare
    "Giải Trí",       # Entertainment
    "Du Lịch",        # Travel
    "Gia Dụng",       # Household
    "Khác"            # Other
]

# Keywords associated with each category (for feature engineering)
CATEGORY_KEYWORDS = {
    "Thực Phẩm": [
        # Vietnamese
        "thực phẩm", "đồ ăn", "thức ăn", "món ăn", "ăn uống",
        "nhà hàng", "quán ăn", "quán cơm", "phở", "cơm",
        "bánh", "nước", "cafe", "cà phê", "trà", "sinh tố",
        "siêu thị", "chợ", "rau", "củ", "quả", "thịt", "cá",
        "gạo", "mì", "bún", "miến", "hủ tiếu", "chè",
        # English
        "food", "restaurant", "meal", "drink", "cafe", "coffee",
        "grocery", "supermarket", "market", "rice", "noodle",
        "breakfast", "lunch", "dinner", "snack", "beverage"
    ],
    
    "Điện Tử": [
        # Vietnamese
        "điện thoại", "máy tính", "laptop", "ipad", "tablet",
        "điện tử", "smartphone", "đồng hồ thông minh", "tai nghe",
        "loa", "tivi", "tủ lạnh", "máy giặt", "điều hòa",
        "camera", "máy ảnh", "phụ kiện", "sạc", "cáp",
        # English
        "phone", "computer", "laptop", "tablet", "electronics",
        "smartphone", "smartwatch", "headphone", "speaker",
        "television", "camera", "charger", "cable", "accessory",
        "samsung", "apple", "iphone", "xiaomi", "oppo", "vivo"
    ],
    
    "Quần Áo": [
        # Vietnamese
        "quần", "áo", "váy", "đầm", "giày", "dép",
        "thời trang", "trang phục", "phụ kiện thời trang",
        "túi xách", "balo", "mũ", "nón", "khăn", "thắt lưng",
        "áo khoác", "áo sơ mi", "áo thun", "quần jean",
        # English
        "clothing", "shirt", "pants", "dress", "shoes", "sandals",
        "fashion", "bag", "backpack", "hat", "cap", "scarf",
        "jacket", "jeans", "t-shirt", "sneakers", "boots",
        "zara", "uniqlo", "h&m", "nike", "adidas"
    ],
    
    "Y Tế": [
        # Vietnamese
        "bệnh viện", "phòng khám", "y tế", "sức khỏe", "khám bệnh",
        "thuốc", "nhà thuốc", "dược", "tiêm", "xét nghiệm",
        "chữa bệnh", "điều trị", "nha khoa", "răng", "mắt",
        "vitamin", "thực phẩm chức năng", "băng", "gạc",
        # English
        "hospital", "clinic", "healthcare", "medical", "medicine",
        "pharmacy", "drug", "doctor", "treatment", "dental",
        "test", "examination", "vitamin", "supplement",
        "bandage", "prescription"
    ],
    
    "Giải Trí": [
        # Vietnamese
        "giải trí", "vui chơi", "rạp phim", "phim", "cinema",
        "karaoke", "bar", "pub", "club", "vé", "ticket",
        "game", "trò chơi", "sách", "nhạc", "concert",
        "sự kiện", "triển lãm", "bảo tàng", "công viên",
        # English
        "entertainment", "movie", "cinema", "film", "theater",
        "karaoke", "bar", "pub", "club", "ticket",
        "game", "book", "music", "concert", "event",
        "exhibition", "museum", "park", "amusement"
    ],
    
    "Du Lịch": [
        # Vietnamese
        "du lịch", "khách sạn", "hotel", "resort", "homestay",
        "vé máy bay", "máy bay", "flight", "vé tàu", "tàu hỏa",
        "xe khách", "taxi", "grab", "vé xe", "tour",
        "đặt phòng", "lưu trú", "nghỉ dưỡng", "kỳ nghỉ",
        # English
        "travel", "hotel", "resort", "hostel", "accommodation",
        "flight", "airplane", "train", "bus", "taxi",
        "booking", "tour", "vacation", "trip", "tourism",
        "airbnb", "agoda", "booking.com"
    ],
    
    "Gia Dụng": [
        # Vietnamese
        "gia dụng", "nhà cửa", "đồ dùng", "nội thất", "đồ gia dụng",
        "chén", "bát", "dĩa", "nồi", "chảo", "dao", "thớt",
        "bàn", "ghế", "tủ", "giường", "đèn", "quạt",
        "chổi", "lau nhà", "giặt giũ", "vệ sinh", "rửa chén",
        # English
        "household", "home", "furniture", "kitchenware",
        "plate", "bowl", "pot", "pan", "knife", "table",
        "chair", "cabinet", "bed", "lamp", "fan",
        "cleaning", "washing", "detergent", "soap"
    ],
    
    "Khác": [
        # Vietnamese
        "khác", "dịch vụ", "thanh toán", "phí", "lệ phí",
        "hóa đơn", "tiện ích", "điện", "nước", "internet",
        # English
        "other", "service", "payment", "fee", "bill",
        "utility", "electricity", "water", "internet"
    ]
}

# Model configuration
MODEL_CONFIG = {
    "encoder_model": "paraphrase-multilingual-mpnet-base-v2",
    "classifier_type": "logistic_regression",
    "random_state": 42,
    "test_size": 0.2,
    "max_iter": 1000,
    "min_confidence_threshold": 0.6
}

# Retraining configuration
RETRAIN_CONFIG = {
    "threshold": 50,  # Minimum corrections needed
    "auto_retrain": True,
    "schedule_hours": 24
}