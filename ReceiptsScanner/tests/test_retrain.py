"""
Tests for model retraining workflow
"""
import pytest
import tempfile
import shutil
import os
import pandas as pd

from ml.retrain import retrain_model, load_corrections, prepare_retraining_data
from ml.category_classifier import CategoryClassifier


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing"""
    data_dir = tempfile.mkdtemp()
    models_dir = tempfile.mkdtemp()
    training_dir = tempfile.mkdtemp()
    
    os.environ["DATA_DIR"] = data_dir
    os.environ["MODELS_DIR"] = models_dir
    os.environ["TRAINING_DATA_DIR"] = training_dir
    
    yield {
        "data_dir": data_dir,
        "models_dir": models_dir,
        "training_dir": training_dir
    }
    
    # Cleanup
    shutil.rmtree(data_dir, ignore_errors=True)
    shutil.rmtree(models_dir, ignore_errors=True)
    shutil.rmtree(training_dir, ignore_errors=True)


def test_load_corrections_empty(temp_dirs):
    """Test loading corrections when none exist"""
    corrections_df = load_corrections([])
    
    assert corrections_df.empty


def test_load_corrections_with_data(temp_dirs):
    """Test loading corrections with data"""
    corrections_data = [
        {
            "receipt_id": "123",
            "original_category": "Khác",
            "corrected_category": "Thực Phẩm",
            "text": "siêu thị rau củ",
            "merchant_name": "Siêu Thị ABC",
            "items": ["rau", "thịt"],
            "corrected_at": "2024-10-19"
        },
        {
            "receipt_id": "456",
            "original_category": "Khác",
            "corrected_category": "Điện Tử",
            "text": "cửa hàng điện thoại",
            "merchant_name": "Mobile Store",
            "items": ["iPhone"],
            "corrected_at": "2024-10-19"
        }
    ]
    
    corrections_df = load_corrections(corrections_data)
    
    assert len(corrections_df) == 2
    assert "corrected_category" in corrections_df.columns
    assert "text" in corrections_df.columns


def test_prepare_retraining_data(temp_dirs):
    """Test preparing retraining data"""
    # Create base training data
    base_data = pd.DataFrame({
        "text": ["thực phẩm siêu thị", "điện tử máy tính"],
        "category": ["Thực Phẩm", "Điện Tử"]
    })
    
    base_path = os.path.join(temp_dirs["training_dir"], "base_receipts.csv")
    base_data.to_csv(base_path, index=False)
    
    # Create corrections
    corrections_df = pd.DataFrame({
        "text": ["rau củ quả"],
        "corrected_category": ["Thực Phẩm"],
        "merchant_name": ["Siêu Thị"],
        "items": [["rau", "củ"]]
    })
    
    combined_df = prepare_retraining_data(corrections_df)
    
    assert len(combined_df) >= 3  # Base + corrections
    assert "text" in combined_df.columns
    assert "category" in combined_df.columns


def test_retrain_insufficient_corrections(temp_dirs):
    """Test retraining with insufficient corrections"""
    os.environ["RETRAIN_THRESHOLD"] = "50"
    
    # Only 2 corrections (less than threshold)
    corrections_data = [
        {
            "receipt_id": "1",
            "original_category": "Khác",
            "corrected_category": "Thực Phẩm",
            "text": "siêu thị",
            "merchant_name": "ABC",
            "items": [],
            "corrected_at": "2024-10-19"
        },
        {
            "receipt_id": "2",
            "original_category": "Khác",
            "corrected_category": "Điện Tử",
            "text": "điện thoại",
            "merchant_name": "XYZ",
            "items": [],
            "corrected_at": "2024-10-19"
        }
    ]
    
    result = retrain_model(corrections_data)
    
    assert result["status"] == "skipped"
    assert result["reason"] == "insufficient_corrections"
    assert result["corrections_count"] == 2


def test_retrain_with_sufficient_corrections(temp_dirs):
    """Test retraining with sufficient corrections"""
    os.environ["RETRAIN_THRESHOLD"] = "5"  # Lower threshold for testing
    
    # Create base training data
    base_data = pd.DataFrame({
        "text": [
            "thực phẩm siêu thị rau củ",
            "điện tử máy tính laptop",
            "quần áo thời trang giày dép",
            "y tế bệnh viện thuốc men",
            "giải trí phim ảnh rạp chiếu"
        ],
        "category": ["Thực Phẩm", "Điện Tử", "Quần Áo", "Y Tế", "Giải Trí"]
    })
    
    base_path = os.path.join(temp_dirs["training_dir"], "base_receipts.csv")
    base_data.to_csv(base_path, index=False)
    
    # Create corrections (more than threshold)
    corrections_data = []
    for i in range(10):
        corrections_data.append({
            "receipt_id": f"receipt_{i}",
            "original_category": "Khác",
            "corrected_category": "Thực Phẩm" if i % 2 == 0 else "Điện Tử",
            "text": f"sample text {i}",
            "merchant_name": f"Store {i}",
            "items": [f"item_{i}"],
            "corrected_at": "2024-10-19"
        })
    
    result = retrain_model(corrections_data)
    
    assert result["status"] == "success"
    assert "model_version" in result
    assert "accuracy" in result
    assert result["corrections_used"] == 10
    assert os.path.exists(result["model_path"])


def test_retrain_model_versioning(temp_dirs):
    """Test that retraining creates new model versions"""
    os.environ["RETRAIN_THRESHOLD"] = "3"
    
    # Create base data
    base_data = pd.DataFrame({
        "text": ["thực phẩm", "điện tử", "quần áo"],
        "category": ["Thực Phẩm", "Điện Tử", "Quần Áo"]
    })
    
    base_path = os.path.join(temp_dirs["training_dir"], "base_receipts.csv")
    base_data.to_csv(base_path, index=False)
    
    # First retrain
    corrections_1 = [
        {"receipt_id": f"{i}", "corrected_category": "Thực Phẩm", 
         "text": f"text{i}", "merchant_name": "A", "items": [], "corrected_at": "2024-10-19"}
        for i in range(5)
    ]
    
    result_1 = retrain_model(corrections_1)
    
    assert result_1["status"] == "success"
    model_version_1 = result_1["model_version"]
    
    # Models directory should contain the new model
    models_in_dir = os.listdir(temp_dirs["models_dir"])
    assert any(model_version_1 in m for m in models_in_dir)


def test_retrain_updates_metadata(temp_dirs):
    """Test that retraining updates metadata file"""
    os.environ["RETRAIN_THRESHOLD"] = "3"
    
    # Create base data
    base_data = pd.DataFrame({
        "text": ["thực phẩm", "điện tử"],
        "category": ["Thực Phẩm", "Điện Tử"]
    })
    
    base_path = os.path.join(temp_dirs["training_dir"], "base_receipts.csv")
    base_data.to_csv(base_path, index=False)
    
    # Retrain
    corrections = [
        {"receipt_id": f"{i}", "corrected_category": "Thực Phẩm",
         "text": f"text{i}", "merchant_name": "A", "items": [], "corrected_at": "2024-10-19"}
        for i in range(5)
    ]
    
    result = retrain_model(corrections)
    
    # Check metadata file exists
    metadata_path = os.path.join(temp_dirs["models_dir"], "models_metadata.json")
    assert os.path.exists(metadata_path)
    
    # Check metadata content
    import json
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert len(metadata) > 0
    assert metadata[-1]["version"] == result["model_version"]
    assert metadata[-1]["type"] == "retrained"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])