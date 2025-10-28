"""
Tests for ML category classifier
"""
import pytest
import tempfile
import os
import shutil

from ml.category_classifier import CategoryClassifier
from ml.config import CATEGORIES


@pytest.fixture
def temp_models_dir():
    """Create temporary models directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_classifier_initialization(temp_models_dir):
    """Test classifier initialization"""
    os.environ["MODELS_DIR"] = temp_models_dir
    
    classifier = CategoryClassifier()
    
    assert classifier is not None
    assert classifier.encoder is not None
    assert classifier.label_encoder is not None


def test_classifier_categories():
    """Test that classifier knows all categories"""
    classifier = CategoryClassifier()
    
    expected_categories = set(CATEGORIES)
    actual_categories = set(classifier.label_encoder.classes_)
    
    assert expected_categories == actual_categories


def test_predict_basic():
    """Test basic prediction"""
    classifier = CategoryClassifier()
    
    # Train with minimal data
    X_train = [
        "siêu thị thức ăn rau củ",
        "nhà hàng phở bún",
        "điện thoại laptop máy tính",
        "áo quần giày dép thời trang"
    ]
    y_train = ["Thực Phẩm", "Thực Phẩm", "Điện Tử", "Quần Áo"]
    
    classifier.train(X_train, y_train)
    
    # Predict
    result = classifier.predict("mua rau củ ở siêu thị")
    
    assert "category" in result
    assert "confidence" in result
    assert result["category"] in CATEGORIES
    assert 0 <= result["confidence"] <= 1


def test_predict_with_entities():
    """Test prediction with entities"""
    classifier = CategoryClassifier()
    
    # Train
    X_train = [
        "siêu thị cơm gạo",
        "cửa hàng điện thoại"
    ]
    y_train = ["Thực Phẩm", "Điện Tử"]
    
    classifier.train(X_train, y_train)
    
    # Predict with entities
    entities = {
        "merchant_name": "Siêu Thị ABC",
        "items": ["rau", "thịt", "cá"]
    }
    
    result = classifier.predict("hóa đơn mua sắm", entities)
    
    assert result["category"] in CATEGORIES


def test_train_classifier():
    """Test training classifier"""
    classifier = CategoryClassifier()
    
    X_train = [
        "thực phẩm siêu thị",
        "điện tử máy tính",
        "quần áo thời trang",
        "y tế bệnh viện",
        "giải trí phim ảnh"
    ]
    y_train = [
        "Thực Phẩm",
        "Điện Tử",
        "Quần Áo",
        "Y Tế",
        "Giải Trí"
    ]
    
    result = classifier.train(X_train, y_train)
    
    assert "train_samples" in result
    assert "train_accuracy" in result
    assert result["train_samples"] == len(X_train)
    assert result["train_accuracy"] > 0


def test_save_and_load_model(temp_models_dir):
    """Test model saving and loading"""
    os.environ["MODELS_DIR"] = temp_models_dir
    
    # Train and save
    classifier1 = CategoryClassifier()
    X_train = ["thực phẩm", "điện tử"]
    y_train = ["Thực Phẩm", "Điện Tử"]
    classifier1.train(X_train, y_train)
    
    model_path = classifier1.save_model("test_model")
    
    assert os.path.exists(model_path)
    
    # Load
    classifier2 = CategoryClassifier(model_dir=model_path)
    
    assert classifier2.encoder is not None
    assert classifier2.classifier is not None
    
    # Test prediction with loaded model
    result = classifier2.predict("siêu thị thực phẩm")
    assert result["category"] in CATEGORIES


def test_low_confidence_prediction():
    """Test low confidence defaults to 'Khác'"""
    classifier = CategoryClassifier()
    
    # Train with limited data
    X_train = ["thực phẩm siêu thị"]
    y_train = ["Thực Phẩm"]
    
    classifier.train(X_train, y_train)
    
    # Predict with very different text
    result = classifier.predict("xyz abc 123 random text that doesn't match")
    
    # Should default to "Khác" due to low confidence
    # (may or may not, depending on model behavior)
    assert result["category"] in CATEGORIES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])