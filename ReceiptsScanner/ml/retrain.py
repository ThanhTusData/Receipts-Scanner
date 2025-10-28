"""
Incremental model retraining with human corrections
"""
import pandas as pd
import os
from datetime import datetime
from typing import List, Dict

from ml.category_classifier import CategoryClassifier
from ml.config import MODEL_CONFIG, RETRAIN_CONFIG
from monitoring.logging_config import get_logger

logger = get_logger(__name__)


def load_corrections(corrections_data: List[Dict] = None) -> pd.DataFrame:
    """
    Load correction data from JSON or list
    
    Args:
        corrections_data: List of correction dictionaries
        
    Returns:
        pd.DataFrame: Corrections data
    """
    if corrections_data:
        df = pd.DataFrame(corrections_data)
    else:
        # Load from file
        from data_manager.json_adapter import JSONDataAdapter
        adapter = JSONDataAdapter()
        corrections = adapter.load_corrections()
        df = pd.DataFrame(corrections)
    
    if df.empty:
        logger.warning("No corrections found")
        return df
    
    logger.info(f"Loaded {len(df)} corrections")
    
    return df


def prepare_retraining_data(corrections_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare retraining data by combining corrections with original training data
    
    Args:
        corrections_df: Corrections dataframe
        
    Returns:
        pd.DataFrame: Combined training data
    """
    # Load original training data
    training_path = os.path.join(
        os.getenv("TRAINING_DATA_DIR", "./training_data"),
        "base_receipts.csv"
    )
    
    if os.path.exists(training_path):
        base_df = pd.read_csv(training_path)
        logger.info(f"Loaded {len(base_df)} base training samples")
    else:
        base_df = pd.DataFrame()
        logger.warning("No base training data found")
    
    # Prepare corrections for training
    corrections_training = pd.DataFrame({
        'text': corrections_df.apply(
            lambda row: f"{row.get('text', '')} {row.get('merchant_name', '')} {' '.join(row.get('items', []))}",
            axis=1
        ),
        'category': corrections_df['corrected_category']
    })
    
    # Combine data
    combined_df = pd.concat([base_df, corrections_training], ignore_index=True)
    
    # Remove duplicates
    combined_df = combined_df.drop_duplicates(subset=['text'])
    
    logger.info(f"Combined training data: {len(combined_df)} samples")
    
    # Save augmented data
    augmented_path = os.path.join(
        os.getenv("TRAINING_DATA_DIR", "./training_data"),
        "augmented_data.csv"
    )
    combined_df.to_csv(augmented_path, index=False)
    logger.info(f"Augmented data saved to {augmented_path}")
    
    return combined_df


def retrain_model(corrections_data: List[Dict] = None) -> Dict:
    """
    Retrain model with corrections
    
    Args:
        corrections_data: List of correction dictionaries
        
    Returns:
        dict: Retraining results
    """
    logger.info("Starting model retraining with corrections")
    
    # Load corrections
    corrections_df = load_corrections(corrections_data)
    
    if len(corrections_df) < RETRAIN_CONFIG["threshold"]:
        logger.warning(
            f"Not enough corrections ({len(corrections_df)}) "
            f"to retrain (minimum: {RETRAIN_CONFIG['threshold']})"
        )
        return {
            "status": "skipped",
            "reason": "insufficient_corrections",
            "corrections_count": len(corrections_df)
        }
    
    # Prepare training data
    training_df = prepare_retraining_data(corrections_df)
    
    # Split data
    from sklearn.model_selection import train_test_split
    
    X = training_df['text'].tolist()
    y = training_df['category'].tolist()
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=MODEL_CONFIG["test_size"],
        random_state=MODEL_CONFIG["random_state"],
        stratify=y
    )
    
    # Initialize classifier with current model
    classifier = CategoryClassifier()
    
    # Train on combined data
    logger.info(f"Retraining with {len(X_train)} samples")
    train_metrics = classifier.train(X_train, y_train)
    
    # Evaluate on test set
    test_embeddings = classifier.encoder.encode(X_test)
    y_test_encoded = classifier.label_encoder.transform(y_test)
    test_accuracy = classifier.classifier.score(test_embeddings, y_test_encoded)
    
    logger.info(f"Retrained model test accuracy: {test_accuracy:.4f}")
    
    # Save retrained model
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_version = f"category_clf_v{timestamp}_retrained"
    model_path = classifier.save_model(version=model_version)
    
    # Save training data with model
    training_data_path = os.path.join(model_path, "training_data.csv")
    training_df.to_csv(training_data_path, index=False)
    
    # Update metadata
    metadata = {
        "version": model_version,
        "created_at": datetime.now().isoformat(),
        "train_accuracy": train_metrics["train_accuracy"],
        "test_accuracy": test_accuracy,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "corrections_used": len(corrections_df),
        "type": "retrained"
    }
    
    # Save metadata
    import json
    metadata_path = os.path.join(
        os.getenv("MODELS_DIR", "./models"),
        "models_metadata.json"
    )
    
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            all_metadata = json.load(f)
    else:
        all_metadata = []
    
    all_metadata.append(metadata)
    
    with open(metadata_path, 'w') as f:
        json.dump(all_metadata, f, indent=2)
    
    logger.info("Model retraining completed successfully")
    
    return {
        "status": "success",
        "model_version": model_version,
        "model_path": model_path,
        "accuracy": test_accuracy,
        "train_samples": len(X_train),
        "corrections_used": len(corrections_df)
    }


if __name__ == "__main__":
    result = retrain_model()
    print("\nRetraining Results:")
    print(f"Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        print(f"Model version: {result['model_version']}")
        print(f"Accuracy: {result['accuracy']:.4f}")
        print(f"Train samples: {result['train_samples']}")
        print(f"Corrections used: {result['corrections_used']}")
    else:
        print(f"Reason: {result.get('reason')}")