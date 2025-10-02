"""
CategoryClassifier MVP for Day 3
- uses sentence-transformers for embeddings
- trains a scikit-learn LogisticRegression classifier over embeddings
- exposes fit / predict / save / load / update_from_feedback
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import joblib

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

# Optional import; user must install sentence-transformers in environment to use encode
try:
    from sentence_transformers import SentenceTransformer
except Exception as e:
    SentenceTransformer = None  # handled at runtime

class CategoryClassifier:
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2", model_dir: str = "models/category_clf_v001"):
        self.embedding_model_name = embedding_model_name
        self.model_dir = Path(model_dir)
        self.encoder: Optional[LabelEncoder] = None
        self.classifier: Optional[LogisticRegression] = None
        self.model_metadata: Dict[str, Any] = {}
        self._encoder_model = None  # SentenceTransformer instance cached during runtime
        self.is_trained = False

    def _ensure_encoder(self):
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is required to compute embeddings. Install via `pip install sentence-transformers`.")
        if self._encoder_model is None:
            self._encoder_model = SentenceTransformer(self.embedding_model_name)

    def _encode(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """Encode a list of texts into embeddings (numpy array)."""
        self._ensure_encoder()
        # sentence-transformers does batching internally
        embeddings = self._encoder_model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        return np.asarray(embeddings, dtype=np.float32)

    def fit(self, texts: List[str], labels: List[str], save_training: bool = True, **clf_kwargs) -> Dict[str, Any]:
        """
        Fit classifier on texts and labels.
        - texts: list of strings
        - labels: list of category labels (strings)
        Returns metadata dict with metrics placeholders.
        """
        # basic checks
        if len(texts) != len(labels):
            raise ValueError("texts and labels must be same length")
        if not texts:
            raise ValueError("Empty training data")

        # encode texts
        X = self._encode(texts)
        y = np.asarray(labels, dtype=object)

        # label encode
        self.encoder = LabelEncoder()
        y_enc = self.encoder.fit_transform(y)

        # classifier
        self.classifier = LogisticRegression(max_iter=1000, **clf_kwargs)
        self.classifier.fit(X, y_enc)

        self.is_trained = True
        self.model_metadata = {
            "embedding_model": self.embedding_model_name,
            "n_classes": int(len(self.encoder.classes_)),
            "classes": self.encoder.classes_.tolist(),
            "num_examples": int(len(y)),
        }

        # create model dir and save training arrays for possible future incremental training / feedback
        if save_training:
            self.model_dir.mkdir(parents=True, exist_ok=True)
            # save original texts and labels so update_from_feedback can retrain on combined set
            joblib.dump(texts, self.model_dir / "training_texts.joblib")
            joblib.dump(labels, self.model_dir / "training_labels.joblib")

        return self.model_metadata

    def predict(self, texts: List[str], top_k: int = 1) -> List[Dict[str, Any]]:
        """
        Predict labels+confidence for each text. Returns list of dicts:
         {'text': str, 'predicted_label': str, 'confidence': float, 'topk': [(label, prob), ...]}
        """
        if not self.is_trained:
            raise RuntimeError("Model is not trained. Call fit() or load().")

        X = self._encode(texts)
        probs = self.classifier.predict_proba(X)
        results = []
        for i, p in enumerate(probs):
            # get top k indices
            idxs = p.argsort()[-top_k:][::-1]
            topk = [(self.encoder.inverse_transform([int(j)])[0], float(p[int(j)])) for j in idxs]
            predicted_label = topk[0][0]
            confidence = float(topk[0][1])
            results.append({
                "text": texts[i],
                "predicted_label": predicted_label,
                "confidence": confidence,
                "topk": topk,
            })
        return results

    def save(self, dir_path: Optional[str] = None) -> None:
        """Save classifier, encoder and metadata to dir_path (or self.model_dir)."""
        dir_path = Path(dir_path) if dir_path is not None else self.model_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        # save sklearn classifier and label encoder via joblib
        if self.classifier is not None:
            joblib.dump(self.classifier, dir_path / "classifier.joblib")
        if self.encoder is not None:
            joblib.dump(self.encoder, dir_path / "label_encoder.joblib")
        # save metadata
        meta = {
            "embedding_model_name": self.embedding_model_name,
            "is_trained": bool(self.is_trained),
            **self.model_metadata
        }
        with open(dir_path / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def load(self, dir_path: Optional[str] = None) -> None:
        """Load classifier, encoder and metadata from dir_path (or self.model_dir)."""
        dir_path = Path(dir_path) if dir_path is not None else self.model_dir
        if not dir_path.exists():
            raise FileNotFoundError(f"Model dir not found: {dir_path}")
        # load metadata
        meta_path = dir_path / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                self.model_metadata = json.load(f)
                self.embedding_model_name = self.model_metadata.get("embedding_model_name", self.embedding_model_name)
        # load model objects
        le_path = dir_path / "label_encoder.joblib"
        clf_path = dir_path / "classifier.joblib"
        if le_path.exists():
            self.encoder = joblib.load(le_path)
        if clf_path.exists():
            self.classifier = joblib.load(clf_path)
        # mark trained if classifier loaded
        self.is_trained = self.classifier is not None and self.encoder is not None

    def update_from_feedback(self, corrections_texts: List[str], corrections_labels: List[str], save: bool = True) -> Dict[str, Any]:
        """
        Accept corrections (texts + correct labels) and retrain the classifier by combining with saved training set.
        This is a simple retrain (not incremental online learning).
        """
        # load existing training set if available
        existing_texts = []
        existing_labels = []
        texts_path = self.model_dir / "training_texts.joblib"
        labels_path = self.model_dir / "training_labels.joblib"
        if texts_path.exists() and labels_path.exists():
            existing_texts = joblib.load(texts_path)
            existing_labels = joblib.load(labels_path)

        combined_texts = existing_texts + corrections_texts
        combined_labels = existing_labels + corrections_labels

        # re-fit on combined set
        meta = self.fit(combined_texts, combined_labels, save_training=save)
        # save classifier objects
        self.save(self.model_dir)
        return meta
