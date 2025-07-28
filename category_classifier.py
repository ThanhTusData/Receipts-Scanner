import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from config import EXPENSE_CATEGORIES

class CategoryClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
        self.classifier = MultinomialNB(alpha=0.1)
        self.is_trained = False
        self.categories = list(EXPENSE_CATEGORIES.keys())
        self._train_on_init()
    
    def _train_on_init(self):
        """Auto-train on initialization"""
        try:
            self.train()
        except Exception:
            self.is_trained = False
    
    def create_training_data(self):
        """Generate training data from keywords"""
        texts, labels = [], []
        
        for category, keywords in EXPENSE_CATEGORIES.items():
            for keyword in keywords:
                # Create keyword variations
                variations = [
                    keyword,
                    f"{keyword} cửa hàng",
                    f"{keyword} shop",
                    f"mua {keyword}",
                    f"siêu thị {keyword}",
                    f"{keyword} store"
                ]
                texts.extend(variations)
                labels.extend([category] * len(variations))
        
        return texts, labels
    
    def train(self):
        """Train the classifier"""
        texts, labels = self.create_training_data()
        
        if texts:
            X = self.vectorizer.fit_transform(texts)
            self.classifier.fit(X, labels)
            self.is_trained = True
        
        return self.is_trained
    
    def predict_category(self, receipt_data):
        """Predict category for receipt"""
        # Extract relevant text
        text_parts = [
            receipt_data.get('store_name', ''),
            receipt_data.get('address', ''),
            ' '.join([item.get('name', '') for item in receipt_data.get('items', [])[:5]])  # First 5 items
        ]
        
        combined_text = ' '.join(filter(None, text_parts)).lower().strip()
        
        # Rule-based classification (priority)
        rule_category = self._rule_based_classify(combined_text)
        if rule_category != 'Khác':
            return rule_category
        
        # ML-based classification (fallback)
        if self.is_trained and combined_text:
            try:
                X = self.vectorizer.transform([combined_text])
                probabilities = self.classifier.predict_proba(X)[0]
                max_prob_idx = probabilities.argmax()
                
                # Only return if confidence is reasonable
                if probabilities[max_prob_idx] > 0.3:
                    return self.classifier.classes_[max_prob_idx]
            except Exception:
                pass
        
        return 'Khác'
    
    def _rule_based_classify(self, text):
        """Rule-based classification with fuzzy matching"""
        # Direct keyword matching
        for category, keywords in EXPENSE_CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return category
        
        # Pattern matching for common cases
        patterns = {
            'Ăn uống': [
                r'\b(nhà hàng|quán|cafe|coffee|beer|pub|bar)\b',
                r'\b(cơm|phở|bún|bánh|chè)\b',
                r'\b(food|restaurant|kitchen)\b'
            ],
            'Mua sắm': [
                r'\b(siêu thị|convenience|mart|shop)\b',
                r'\b(vinmart|coopmart|minimall)\b',
                r'\b(store|market|mall)\b'
            ],
            'Xăng xe': [
                r'\b(petro|gas|xăng|dầu)\b',
                r'\b(station|fuel)\b'
            ],
            'Y tế': [
                r'\b(pharmac|drug|thuốc|bệnh viện|clinic)\b',
                r'\b(hospital|medical|health)\b'
            ],
            'Giải trí': [
                r'\b(cinema|movie|game|karaoke)\b',
                r'\b(entertainment|fun|play)\b'
            ]
        }
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, text, re.IGNORECASE):
                    return category
        
        return 'Khác'
    
    def get_prediction_confidence(self, receipt_data):
        """Get prediction confidence score"""
        text_parts = [
            receipt_data.get('store_name', ''),
            receipt_data.get('address', ''),
            ' '.join([item.get('name', '') for item in receipt_data.get('items', [])[:3]])
        ]
        
        combined_text = ' '.join(filter(None, text_parts)).lower().strip()
        
        # Rule-based has high confidence
        if self._rule_based_classify(combined_text) != 'Khác':
            return 0.9
        
        # ML-based confidence
        if self.is_trained and combined_text:
            try:
                X = self.vectorizer.transform([combined_text])
                probabilities = self.classifier.predict_proba(X)[0]
                return probabilities.max()
            except Exception:
                pass
        
        return 0.1  # Low confidence for 'Khác'
    
    def get_category_suggestions(self, receipt_data, top_n=3):
        """Get top N category suggestions with probabilities"""
        text_parts = [
            receipt_data.get('store_name', ''),
            receipt_data.get('address', ''),
            ' '.join([item.get('name', '') for item in receipt_data.get('items', [])[:3]])
        ]
        
        combined_text = ' '.join(filter(None, text_parts)).lower().strip()
        suggestions = []
        
        if self.is_trained and combined_text:
            try:
                X = self.vectorizer.transform([combined_text])
                probabilities = self.classifier.predict_proba(X)[0]
                classes = self.classifier.classes_
                
                # Get top predictions
                top_indices = probabilities.argsort()[-top_n:][::-1]
                suggestions = [
                    {
                        'category': classes[i],
                        'confidence': probabilities[i],
                        'percentage': f"{probabilities[i]*100:.1f}%"
                    }
                    for i in top_indices
                    if probabilities[i] > 0.1
                ]
            except Exception:
                pass
        
        # Always include rule-based result if available
        rule_result = self._rule_based_classify(combined_text)
        if rule_result != 'Khác':
            suggestions.insert(0, {
                'category': rule_result,
                'confidence': 0.9,
                'percentage': "90.0%"
            })
        
        return suggestions[:top_n]
    
    def update_model(self, receipt_data, correct_category):
        """Update model with user feedback (online learning simulation)"""
        if not self.is_trained:
            return False
        
        text_parts = [
            receipt_data.get('store_name', ''),
            receipt_data.get('address', ''),
            ' '.join([item.get('name', '') for item in receipt_data.get('items', [])[:3]])
        ]
        
        combined_text = ' '.join(filter(None, text_parts)).lower().strip()
        
        if combined_text and correct_category in self.categories:
            try:
                # Add to training data and retrain (simplified approach)
                current_texts, current_labels = self.create_training_data()
                current_texts.append(combined_text)
                current_labels.append(correct_category)
                
                X = self.vectorizer.fit_transform(current_texts)
                self.classifier.fit(X, current_labels)
                return True
            except Exception:
                pass
        
        return False