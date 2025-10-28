"""
Category classifier using Sentence-BERT + Logistic Regression
"""
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
import numpy as np
import pickle
import os
from typing import Dict, Any, List
from datetime import datetime

from ml.config import CATEGORIES, CATEGORY_KEYWORDS, MODEL_CONFIG
from monitoring.logging_config import get_logger

logger = get_logger(__name__)


class CategoryClassifier:
    """Category classification using sentence embeddings"""
    
    def __init__(self, model_dir: str = None):
        """
        Initialize category classifier
        
        Args:
            model_dir: Directory containing model artifacts
        """
        self.models_dir = os.getenv("MODELS_DIR", "./models")
        self.model_dir = model_dir
        
        # Initialize components
        self.encoder = None
        self.classifier = None
        self.label_encoder = None
        
        # Load model if directory specified
        if model_dir and os.path.exists(model_dir):
            self.load_model(model_dir)
        else:
            self._load_latest_model()
    
    def _load_latest_model(self):
        """Load the latest trained model"""
        try:
            # Find latest model directory
            model_dirs = [
                d for d in os.listdir(self.models_dir)
                if d.startswith("category_clf_v") and 
                os.path.isdir(os.path.join(self.models_dir, d))
            ]
            
            if not model_dirs:
                logger.warning("No trained model found. Initializing new model.")
                self._initialize_new_model()
                return
            
            # Sort by timestamp and get latest
            latest_dir = sorted(model_dirs)[-1]
            model_path = os.path.join(self.models_dir, latest_dir)
            
            logger.info(f"Loading model from {model_path}")
            self.load_model(model_path)
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self._initialize_new_model()
    
    def _initialize_new_model(self):
        """Initialize new untrained model"""
        logger.info("Initializing new model components")
        
        # Load Sentence-BERT encoder
        self.encoder = SentenceTransformer(MODEL_CONFIG["encoder_model"])
        
        # Initialize classifier (will be trained later)
        self.classifier = LogisticRegression(
            max_iter=MODEL_CONFIG["max_iter"],
            random_state=MODEL_CONFIG["random_state"]
        )
        
        # Initialize label encoder
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(CATEGORIES)
        
        logger.info("Model components initialized")
    
    def load_model(self, model_dir: str):
        """
        Load trained model from directory
        
        Args:
            model_dir: Path to model directory
        """
        try:
            logger.info(f"Loading model from {model_dir}")
            
            # Load encoder
            encoder_path = os.path.join(model_dir, "encoder_model")
            if os.path.exists(encoder_path):
                self.encoder = SentenceTransformer(encoder_path)
            else:
                self.encoder = SentenceTransformer(MODEL_CONFIG["encoder_model"])
            
            # Load classifier
            classifier_path = os.path.join(model_dir, "classifier.pkl")
            with open(classifier_path, "rb") as f:
                self.classifier = pickle.load(f)
            
            # Load label encoder
            label_encoder_path = os.path.join(model_dir, "label_encoder.pkl")
            with open(label_encoder_path, "rb") as f:
                self.label_encoder = pickle.load(f)
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def save_model(self, version: str = None) -> str:
        """
        Save model to disk
        
        Args:
            version: Optional version string
            
        Returns:
            str: Path to saved model
        """
        try:
            # Create version string
            if not version:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                version = f"category_clf_v{timestamp}"
            
            # Create model directory
            model_path = os.path.join(self.models_dir, version)
            os.makedirs(model_path, exist_ok=True)
            
            # Save encoder
            encoder_path = os.path.join(model_path, "encoder_model")
            self.encoder.save(encoder_path)
            
            # Save classifier
            classifier_path = os.path.join(model_path, "classifier.pkl")
            with open(classifier_path, "wb") as f:
                pickle.dump(self.classifier, f)
            
            # Save label encoder
            label_encoder_path = os.path.join(model_path, "label_encoder.pkl")
            with open(label_encoder_path, "wb") as f:
                pickle.dump(self.label_encoder, f)
            
            logger.info(f"Model saved to {model_path}")
            
            return model_path
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
    
    def predict(self, text: str, entities: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Predict category for receipt text
        
        Args:
            text: Receipt text
            entities: Optional extracted entities
            
        Returns:
            dict: Prediction result with category and confidence
        """
        try:
            # Prepare text for encoding
            combined_text = self._prepare_text(text, entities)
            
            # Generate embedding
            embedding = self.encoder.encode([combined_text])[0]
            
            # Predict
            prediction = self.classifier.predict([embedding])[0]
            probabilities = self.classifier.predict_proba([embedding])[0]
            
            # Get category and confidence
            category = self.label_encoder.inverse_transform([prediction])[0]
            confidence = float(max(probabilities))
            
            # If confidence is low, default to "Khác"
            min_confidence = MODEL_CONFIG["min_confidence_threshold"]
            if confidence < min_confidence:
                logger.warning(f"Low confidence ({confidence:.2%}), defaulting to 'Khác'")
                category = "Khác"
            
            logger.info(f"Predicted category: {category} (confidence: {confidence:.2%})")
            
            return {
                "category": category,
                "confidence": confidence,
                "all_probabilities": {
                    cat: float(prob)
                    for cat, prob in zip(self.label_encoder.classes_, probabilities)
                }
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                "category": "Khác",
                "confidence": 0.0,
                "all_probabilities": {}
            }
    
    def _prepare_text(self, text: str, entities: Dict[str, Any] = None) -> str:
        """
        Prepare text for encoding by combining text and entities
        
        Args:
            text: Raw receipt text
            entities: Extracted entities
            
        Returns:
            str: Combined text for classification
        """
        parts = [text]
        
        if entities:
            # Add merchant name with higher weight
            if entities.get("merchant_name"):
                parts.append(entities["merchant_name"] * 2)
            
            # Add items
            if entities.get("items"):
                items_text = " ".join(entities["items"])
                parts.append(items_text)
        
        return " ".join(parts)
    
    def train(self, X_train: List[str], y_train: List[str]) -> Dict[str, Any]:
        """
        Train the classifier
        
        Args:
            X_train: Training texts
            y_train: Training labels
            
        Returns:
            dict: Training metrics
        """
        try:
            logger.info(f"Training classifier with {len(X_train)} samples")
            
            # Encode texts
            logger.info("Encoding training texts...")
            X_embeddings = self.encoder.encode(X_train, show_progress_bar=True)
            
            # Encode labels
            y_encoded = self.label_encoder.transform(y_train)
            
            # Train classifier
            logger.info("Training logistic regression...")
            self.classifier.fit(X_embeddings, y_encoded)
            
            # Calculate training accuracy
            train_score = self.classifier.score(X_embeddings, y_encoded)
            
            logger.info(f"Training completed. Accuracy: {train_score:.4f}")
            
            return {
                "train_samples": len(X_train),
                "train_accuracy": train_score,
                "categories": list(self.label_encoder.classes_)
            }
            
        except Exception as e:
            logger.error(f"Training error: {str(e)}")
            raise