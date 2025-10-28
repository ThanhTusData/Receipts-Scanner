# Receipt Scanner - ML Pipeline Documentation

## Overview

The Receipt Scanner uses a machine learning pipeline to automatically categorize receipts into 8 predefined categories. The pipeline combines modern NLP embeddings (Sentence-BERT) with traditional classification (Logistic Regression) for accurate and efficient categorization.

## Architecture

```
Receipt Text → Preprocessing → Sentence-BERT → Logistic Regression → Category
     ↓                                                                    ↓
  Entities                                                          Confidence
     ↓                                                                    ↓
Feature Engineering                                            User Correction
     ↓                                                                    ↓
Combined Features                                              Feedback Loop
                                                                         ↓
                                                                  Model Retrain
```

## Categories

The system classifies receipts into 8 Vietnamese categories:

| Category | Vietnamese | Description | Keywords |
|----------|-----------|-------------|----------|
| 1 | Thực Phẩm | Food & Groceries | siêu thị, nhà hàng, cafe, thực phẩm |
| 2 | Điện Tử | Electronics | điện thoại, laptop, máy tính, camera |
| 3 | Quần Áo | Clothing & Fashion | áo, quần, giày, thời trang |
| 4 | Y Tế | Healthcare | bệnh viện, thuốc, y tế, khám bệnh |
| 5 | Giải Trí | Entertainment | phim, game, karaoke, vui chơi |
| 6 | Du Lịch | Travel | khách sạn, máy bay, tour, du lịch |
| 7 | Gia Dụng | Household | đồ gia dụng, nội thất, chén bát |
| 8 | Khác | Other | Fallback category |

## Model Components

### 1. Text Encoder: Sentence-BERT

**Model**: `paraphrase-multilingual-mpnet-base-v2`

**Why Sentence-BERT?**
- Multilingual support (Vietnamese + English)
- High-quality sentence embeddings
- Pre-trained on diverse data
- Fast inference (<1s per receipt)
- Captures semantic meaning

**Embedding Process**:

```python
from sentence_transformers import SentenceTransformer

encoder = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
text = "Siêu thị ABC - Rau củ thịt cá"
embedding = encoder.encode(text)  # Returns 768-dimensional vector
```

**Output**: 768-dimensional dense vector representing text semantics

### 2. Classifier: Logistic Regression

**Why Logistic Regression?**
- Fast training and inference
- Interpretable coefficients
- Works well with high-quality embeddings
- Low memory footprint
- Supports incremental learning

**Configuration**:
```python
LogisticRegression(
    max_iter=1000,
    random_state=42,
    solver='lbfgs',
    multi_class='multinomial'
)
```

### 3. Feature Engineering

The system combines multiple signals:

**Input Features**:
1. **Raw Text Embedding** - Sentence-BERT encoding of full OCR text
2. **Merchant Name** (weighted 2x) - Store name often indicates category
3. **Items List** - Purchased items provide strong signals

**Text Preparation**:
```python
def prepare_text(text, entities):
    parts = [text]
    
    # Add merchant name (higher weight)
    if entities.get("merchant_name"):
        parts.append(entities["merchant_name"] * 2)
    
    # Add items
    if entities.get("items"):
        items_text = " ".join(entities["items"])
        parts.append(items_text)
    
    return " ".join(parts)
```

## Training Pipeline

### Initial Training

**Data Sources**:
1. Base training data (`training_data/base_receipts.csv`)
2. Sample data generated programmatically
3. Synthetic data with category keywords

**Training Process**:

```bash
# Run initial training
python -m ml.train
```

**Steps**:
1. Load base training data (or create samples)
2. Split into train/test (80/20)
3. Initialize Sentence-BERT encoder
4. Generate embeddings for all texts
5. Train Logistic Regression classifier
6. Evaluate on test set
7. Save model artifacts

**Output**:
```
models/category_clf_v20241019_103000/
├── encoder_model/          # Sentence-BERT model
├── classifier.pkl          # Trained LogisticRegression
├── label_encoder.pkl       # Category label encoder
└── training_data.csv       # Training data snapshot
```

### Model Evaluation

```bash
# Evaluate model performance
python -m ml.eval
```

**Metrics Reported**:
- Overall accuracy
- Per-category precision, recall, F1-score
- Confusion matrix
- Average confidence

**Example Output**:
```
Model Evaluation Results
========================
Overall Accuracy: 0.9200
Average Confidence: 0.8750

Per-Category Performance:
--------------------------
Thực Phẩm:
  Precision: 0.9500
  Recall:    0.9200
  F1-Score:  0.9350
  Support:   45

Điện Tử:
  Precision: 0.9000
  Recall:    0.9100
  F1-Score:  0.9050
  Support:   32
```

## Inference Pipeline

### Prediction Flow

```python
# 1. Preprocess image
preprocessed = preprocess_image(image_path)

# 2. OCR extraction
ocr_result = ocr_adapter.extract_text(preprocessed)
text = ocr_result["text"]

# 3. Entity extraction
entities = receipt_processor.extract_entities(text)

# 4. Classification
result = classifier.predict(text, entities)

# Output
{
    "category": "Thực Phẩm",
    "confidence": 0.95,
    "all_probabilities": {
        "Thực Phẩm": 0.95,
        "Điện Tử": 0.02,
        "Quần Áo": 0.01,
        ...
    }
}
```

### Confidence Thresholding

**Minimum Confidence**: 0.6 (configurable)

```python
if confidence < 0.6:
    category = "Khác"  # Default to "Other"
```

**Rationale**:
- Prevents incorrect high-confidence predictions
- Reduces user correction burden
- Maintains accuracy > precision trade-off

## Continuous Learning (Feedback Loop)

### Correction Collection

When users correct categories:

```python
correction = {
    "receipt_id": "receipt-123",
    "original_category": "Khác",
    "corrected_category": "Thực Phẩm",
    "text": "Siêu thị XYZ rau củ...",
    "merchant_name": "Siêu Thị XYZ",
    "items": ["rau", "củ", "thịt"],
    "corrected_at": "2024-10-19T10:30:00Z"
}
```

Saved to `data/corrections.json`

### Retraining Trigger

**Automatic Retraining** when:
- Corrections count ≥ 50 (configurable)
- Manual trigger via API: `POST /admin/retrain`

**Retraining Process**:

```bash
# Manual retrain
python -m ml.retrain

# Or via API
curl -X POST http://localhost:8000/admin/retrain
```

**Steps**:
1. Load accumulated corrections
2. Check threshold (minimum 50 corrections)
3. Merge corrections with base training data
4. Remove duplicates
5. Split train/test
6. Train new model version
7. Evaluate and save
8. Update model metadata

**Output**:
```json
{
    "status": "success",
    "model_version": "category_clf_v20241019_140000_retrained",
    "accuracy": 0.9350,
    "train_samples": 350,
    "corrections_used": 75
}
```

### Model Versioning

All models are versioned with timestamps:

```
category_clf_v20241019_103000        # Initial model
category_clf_v20241019_140000_retrained  # First retrain
category_clf_v20241020_090000_retrained  # Second retrain
```

**Metadata Tracking**:

```json
[
  {
    "version": "category_clf_v20241019_103000",
    "created_at": "2024-10-19T10:30:00Z",
    "train_accuracy": 0.9200,
    "test_accuracy": 0.9000,
    "train_samples": 275,
    "test_samples": 70,
    "type": "initial"
  },
  {
    "version": "category_clf_v20241019_140000_retrained",
    "created_at": "2024-10-19T14:00:00Z",
    "train_accuracy": 0.9350,
    "test_accuracy": 0.9250,
    "train_samples": 350,
    "corrections_used": 75,
    "type": "retrained"
  }
]
```

## Performance Optimization

### Inference Speed

**Target**: < 1 second per receipt

**Optimizations**:
1. **Model Caching**: Load model once, reuse for all predictions
2. **Batch Processing**: Process multiple receipts together
3. **Embedding Cache**: Cache embeddings for repeated texts
4. **Lightweight Classifier**: LogisticRegression has O(n) inference

**Measured Performance**:
- Text encoding: ~0.3s
- Classification: ~0.05s
- Total: ~0.35s per receipt

### Training Speed

**Initial Training**: ~2-5 minutes (depending on data size)

**Retraining**: ~3-7 minutes (with corrections)

**Factors**:
- Number of training samples
- Sentence-BERT encoding (dominant factor)
- Hardware (CPU vs GPU)

## Model Monitoring

### Metrics Tracked

**Prometheus Metrics**:

```python
# Classification confidence
classification_confidence_score.observe(0.95)

# Model predictions by category
model_predictions_total.labels(category="Thực Phẩm").inc()

# Model accuracy
model_accuracy.set(0.92)

# Retraining runs
model_retraining_total.labels(status="success").inc()
```

### Performance Alerts

**Alert Rules** (`prometheus/alerts.yml`):

```yaml
- alert: ModelAccuracyDegraded
  expr: model_accuracy < 0.7
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "Model accuracy has degraded"
    description: "Current accuracy is {{ $value }}, consider retraining"
```

## Best Practices

### For Training

1. **Balance Dataset**: Ensure each category has sufficient examples
2. **Quality over Quantity**: 50 high-quality examples > 500 noisy examples
3. **Regular Evaluation**: Monitor test accuracy after each retrain
4. **Keep Training Data**: Store all training snapshots with models

### For Inference

1. **Confidence Thresholding**: Use minimum confidence of 0.6
2. **Fallback Strategy**: Default to "Khác" for low confidence
3. **Feature Engineering**: Include merchant name and items when available
4. **Error Handling**: Handle OCR failures gracefully

### For Retraining

1. **Correction Quality**: Verify corrections before retraining
2. **Threshold Setting**: Require ≥50 corrections to avoid overfitting
3. **A/B Testing**: Compare new model with old before deploying
4. **Rollback Strategy**: Keep previous model versions for rollback

## Troubleshooting

### Low Classification Accuracy

**Symptoms**: Accuracy < 80%

**Solutions**:
1. Check training data quality and balance
2. Increase training samples (especially underrepresented categories)
3. Verify category definitions are clear and distinct
4. Review and update keyword lists in `ml/config.py`

### Poor Vietnamese Text Handling

**Symptoms**: Low confidence for Vietnamese receipts

**Solutions**:
1. Verify Tesseract has Vietnamese language pack installed
2. Check text preprocessing (accents, diacritics)
3. Add more Vietnamese training examples
4. Update Vietnamese keywords in category definitions

### Model Not Loading

**Symptoms**: `Model not found` errors

**Solutions**:
1. Run initial training: `python -m ml.train`
2. Check `MODELS_DIR` environment variable
3. Verify model files exist and have correct permissions
4. Check for corrupted `.pkl` files

### Slow Inference

**Symptoms**: Predictions taking >2 seconds

**Solutions**:
1. Ensure model is loaded once and cached
2. Use batch processing for multiple receipts
3. Consider using GPU for Sentence-BERT encoding
4. Profile code to identify bottlenecks

## Future Improvements

### Planned Features

1. **Active Learning**: Intelligently select uncertain predictions for human review
2. **Category Hierarchies**: Nested categories (e.g., Food → Restaurants → Vietnamese)
3. **Multi-label Classification**: Receipts with multiple categories
4. **Fine-tuning**: Fine-tune Sentence-BERT on receipt-specific data
5. **Explainability**: Show which words contributed to classification
6. **AutoML**: Automated hyperparameter tuning

### Research Directions

1. **Better Embeddings**: Experiment with domain-specific encoders
2. **Ensemble Methods**: Combine multiple classifiers
3. **Deep Learning**: End-to-end neural models
4. **Few-shot Learning**: Learn new categories with minimal examples
5. **Transfer Learning**: Leverage models trained on similar tasks

## References

- **Sentence-BERT**: [https://www.sbert.net/](https://www.sbert.net/)
- **Scikit-learn**: [https://scikit-learn.org/](https://scikit-learn.org/)
- **Multilingual Models**: [https://huggingface.co/sentence-transformers](https://huggingface.co/sentence-transformers)

---

For implementation details, see:
- `ml/category_classifier.py` - Classifier implementation
- `ml/train.py` - Initial training script
- `ml/retrain.py` - Retraining logic
- `ml/config.py` - Categories and configuration