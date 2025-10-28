"""
Initial model training script
"""
import pandas as pd
import os
from sklearn.model_selection import train_test_split
from datetime import datetime

from ml.category_classifier import CategoryClassifier
from ml.config import CATEGORIES, MODEL_CONFIG
from monitoring.logging_config import get_logger

logger = get_logger(__name__)


def load_training_data(data_path: str = None) -> pd.DataFrame:
    """
    Load training data from CSV
    
    Args:
        data_path: Path to training data CSV
        
    Returns:
        pd.DataFrame: Training data
    """
    if not data_path:
        data_path = os.path.join(
            os.getenv("TRAINING_DATA_DIR", "./training_data"),
            "base_receipts.csv"
        )
    
    logger.info(f"Loading training data from {data_path}")
    
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} training samples")
        return df
    
    except FileNotFoundError:
        logger.error(f"Training data not found at {data_path}")
        # Create sample data
        return create_sample_training_data()


def create_sample_training_data() -> pd.DataFrame:
    """Create sample training data for initial setup"""
    logger.info("Creating sample training data")
    
    sample_data = []
    
    # Thực Phẩm samples
    sample_data.extend([
        {"text": "Nhà hàng ABC phở bò tái nước ngọt cơm gạo", "category": "Thực Phẩm"},
        {"text": "Siêu thị rau củ thịt cá trứng sữa bánh mì", "category": "Thực Phẩm"},
        {"text": "Quán cafe cappuccino latte bánh ngọt", "category": "Thực Phẩm"},
        {"text": "Restaurant pizza pasta salad wine", "category": "Thực Phẩm"},
        {"text": "Grocery store chicken beef vegetables", "category": "Thực Phẩm"},
    ])
    
    # Điện Tử samples
    sample_data.extend([
        {"text": "Cửa hàng điện thoại iPhone Samsung laptop", "category": "Điện Tử"},
        {"text": "Máy tính bảng iPad tablet tai nghe", "category": "Điện Tử"},
        {"text": "Electronics store smartphone charger cable", "category": "Điện Tử"},
        {"text": "Tivi 55 inch smart TV samsung LG", "category": "Điện Tử"},
        {"text": "Camera máy ảnh lens phụ kiện", "category": "Điện Tử"},
    ])
    
    # Quần Áo samples
    sample_data.extend([
        {"text": "Cửa hàng thời trang áo quần giày dép", "category": "Quần Áo"},
        {"text": "Fashion store shirt pants dress shoes", "category": "Quần Áo"},
        {"text": "Zara áo khoác váy túi xách", "category": "Quần Áo"},
        {"text": "Nike giày thể thao sneakers adidas", "category": "Quần Áo"},
        {"text": "Uniqlo áo thun quần jean", "category": "Quần Áo"},
    ])
    
    # Y Tế samples
    sample_data.extend([
        {"text": "Nhà thuốc vitamin thuốc cảm băng gạc", "category": "Y Tế"},
        {"text": "Bệnh viện khám bệnh xét nghiệm", "category": "Y Tế"},
        {"text": "Pharmacy medicine prescription pills", "category": "Y Tế"},
        {"text": "Phòng khám nha khoa điều trị răng", "category": "Y Tế"},
        {"text": "Medical clinic doctor examination", "category": "Y Tế"},
    ])
    
    # Giải Trí samples
    sample_data.extend([
        {"text": "Rạp chiếu phim vé xem phim bỏng ngô", "category": "Giải Trí"},
        {"text": "Karaoke bar pub club music", "category": "Giải Trí"},
        {"text": "Cinema movie ticket popcorn drinks", "category": "Giải Trí"},
        {"text": "Game center trò chơi vui chơi giải trí", "category": "Giải Trí"},
        {"text": "Concert ticket music event show", "category": "Giải Trí"},
    ])
    
    # Du Lịch samples
    sample_data.extend([
        {"text": "Khách sạn hotel resort nghỉ dưỡng", "category": "Du Lịch"},
        {"text": "Vé máy bay flight ticket Vietnam Airlines", "category": "Du Lịch"},
        {"text": "Tour du lịch travel vacation trip", "category": "Du Lịch"},
        {"text": "Taxi Grab vé xe bus train", "category": "Du Lịch"},
        {"text": "Booking hotel accommodation stay", "category": "Du Lịch"},
    ])
    
    # Gia Dụng samples
    sample_data.extend([
        {"text": "Đồ gia dụng nồi chảo bát đĩa", "category": "Gia Dụng"},
        {"text": "Nội thất bàn ghế tủ giường", "category": "Gia Dụng"},
        {"text": "Household items kitchenware furniture", "category": "Gia Dụng"},
        {"text": "Chổi lau nhà vệ sinh cleaning", "category": "Gia Dụng"},
        {"text": "Home decor lamp fan table chair", "category": "Gia Dụng"},
    ])
    
    # Khác samples
    sample_data.extend([
        {"text": "Hóa đơn tiền điện electricity bill", "category": "Khác"},
        {"text": "Tiền nước water bill utility", "category": "Khác"},
        {"text": "Internet service payment fee", "category": "Khác"},
        {"text": "Dịch vụ service phí lệ phí", "category": "Khác"},
        {"text": "Other miscellaneous payment", "category": "Khác"},
    ])
    
    df = pd.DataFrame(sample_data)
    
    # Save to file
    save_path = os.path.join(
        os.getenv("TRAINING_DATA_DIR", "./training_data"),
        "base_receipts.csv"
    )
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    logger.info(f"Sample training data saved to {save_path}")
    
    return df


def train_initial_model():
    """Train initial model from base training data"""
    logger.info("Starting initial model training")
    
    # Load training data
    df = load_training_data()
    
    # Split data
    X = df['text'].tolist()
    y = df['category'].tolist()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=MODEL_CONFIG["test_size"],
        random_state=MODEL_CONFIG["random_state"],
        stratify=y
    )
    
    logger.info(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    # Initialize and train classifier
    classifier = CategoryClassifier()
    
    # Train
    train_metrics = classifier.train(X_train, y_train)
    
    # Evaluate on test set
    logger.info("Evaluating on test set...")
    test_embeddings = classifier.encoder.encode(X_test)
    y_test_encoded = classifier.label_encoder.transform(y_test)
    test_score = classifier.classifier.score(test_embeddings, y_test_encoded)
    
    logger.info(f"Test accuracy: {test_score:.4f}")
    
    # Save model
    model_path = classifier.save_model()
    
    # Save training data reference
    training_data_path = os.path.join(model_path, "training_data.csv")
    df.to_csv(training_data_path, index=False)
    
    logger.info("Initial model training completed successfully")
    
    return {
        "model_path": model_path,
        "train_accuracy": train_metrics["train_accuracy"],
        "test_accuracy": test_score,
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }


if __name__ == "__main__":
    result = train_initial_model()
    print("\nTraining Results:")
    print(f"Model saved to: {result['model_path']}")
    print(f"Train accuracy: {result['train_accuracy']:.4f}")
    print(f"Test accuracy: {result['test_accuracy']:.4f}")
    print(f"Train samples: {result['train_samples']}")
    print(f"Test samples: {result['test_samples']}")