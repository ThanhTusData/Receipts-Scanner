"""
Model evaluation script
"""
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
import os

from ml.category_classifier import CategoryClassifier
from ml.config import CATEGORIES, MODEL_CONFIG
from monitoring.logging_config import get_logger

logger = get_logger(__name__)


def evaluate_model(model_dir: str = None, test_data_path: str = None):
    """
    Evaluate model performance
    
    Args:
        model_dir: Path to model directory
        test_data_path: Path to test data CSV
        
    Returns:
        dict: Evaluation metrics
    """
    logger.info("Starting model evaluation")
    
    # Load model
    classifier = CategoryClassifier(model_dir=model_dir)
    
    # Load test data
    if test_data_path and os.path.exists(test_data_path):
        df = pd.read_csv(test_data_path)
    else:
        # Use training data and split
        training_path = os.path.join(
            os.getenv("TRAINING_DATA_DIR", "./training_data"),
            "base_receipts.csv"
        )
        df = pd.read_csv(training_path)
        
        # Split to get test set
        _, df = train_test_split(
            df,
            test_size=MODEL_CONFIG["test_size"],
            random_state=MODEL_CONFIG["random_state"],
            stratify=df['category']
        )
    
    logger.info(f"Evaluating on {len(df)} samples")
    
    # Prepare data
    X_test = df['text'].tolist()
    y_true = df['category'].tolist()
    
    # Make predictions
    y_pred = []
    confidences = []
    
    for text in X_test:
        result = classifier.predict(text)
        y_pred.append(result['category'])
        confidences.append(result['confidence'])
    
    # Calculate metrics
    accuracy = accuracy_score(y_true, y_pred)
    
    # Classification report
    report = classification_report(
        y_true,
        y_pred,
        target_names=CATEGORIES,
        output_dict=True
    )
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=CATEGORIES)
    
    # Average confidence
    avg_confidence = np.mean(confidences)
    
    logger.info(f"Evaluation completed. Accuracy: {accuracy:.4f}")
    
    # Print results
    print("\n" + "="*60)
    print("MODEL EVALUATION RESULTS")
    print("="*60)
    print(f"\nOverall Accuracy: {accuracy:.4f}")
    print(f"Average Confidence: {avg_confidence:.4f}")
    print("\n" + "-"*60)
    print("Per-Category Performance:")
    print("-"*60)
    
    for category in CATEGORIES:
        if category in report:
            print(f"\n{category}:")
            print(f"  Precision: {report[category]['precision']:.4f}")
            print(f"  Recall:    {report[category]['recall']:.4f}")
            print(f"  F1-Score:  {report[category]['f1-score']:.4f}")
            print(f"  Support:   {report[category]['support']}")
    
    print("\n" + "="*60)
    
    return {
        "accuracy": accuracy,
        "avg_confidence": avg_confidence,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "test_samples": len(X_test)
    }


if __name__ == "__main__":
    metrics = evaluate_model()