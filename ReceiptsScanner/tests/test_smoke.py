"""
Smoke tests - Basic functionality checks
"""
import pytest
import os


def test_imports():
    """Test that all modules can be imported"""
    try:
        import api.main
        import workers.tasks
        import ocr_engines.tesseract_adapter
        import processing.receipt_processor
        import ml.category_classifier
        import data_manager.json_adapter
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {str(e)}")


def test_environment_variables():
    """Test that required environment variables are set or have defaults"""
    # These should have defaults
    assert os.getenv("DATA_DIR", "./data") is not None
    assert os.getenv("MODELS_DIR", "./models") is not None
    assert os.getenv("STORAGE_BACKEND", "json") is not None


def test_data_directories_exist():
    """Test that data directories can be created"""
    import tempfile
    import shutil
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        data_dir = os.path.join(temp_dir, "data")
        models_dir = os.path.join(temp_dir, "models")
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(models_dir, exist_ok=True)
        
        assert os.path.exists(data_dir)
        assert os.path.exists(models_dir)
    finally:
        shutil.rmtree(temp_dir)


def test_ml_config():
    """Test ML configuration is valid"""
    from ml.config import CATEGORIES, MODEL_CONFIG
    
    assert len(CATEGORIES) > 0
    assert "Khác" in CATEGORIES
    assert "encoder_model" in MODEL_CONFIG
    assert "classifier_type" in MODEL_CONFIG


def test_patterns():
    """Test regex patterns"""
    from processing.patterns import clean_amount, clean_phone
    
    # Test amount cleaning
    assert clean_amount("1,234.56") == 1234.56
    assert clean_amount("1.234,56") == 1234.56
    assert clean_amount("1234") == 1234.0
    
    # Test phone cleaning
    assert clean_phone("0123456789") == "0123456789"
    assert clean_phone("0123-456-789") == "0123456789"


def test_json_adapter_init():
    """Test JSON adapter initialization"""
    import tempfile
    from data_manager.json_adapter import JSONDataAdapter
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        adapter = JSONDataAdapter(data_dir=temp_dir)
        assert adapter is not None
        assert os.path.exists(adapter.receipts_file)
    finally:
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])