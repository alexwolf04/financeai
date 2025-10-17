import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import re
from typing import Tuple, List

class TransactionCategorizer:
    """AI model for automatically categorizing financial transactions"""
    
    def __init__(self):
        self.model = None
        self.categories = [
            'Food & Dining', 'Shopping', 'Transportation', 'Bills & Utilities',
            'Entertainment', 'Healthcare', 'Travel', 'Education', 'Investment',
            'Income', 'Transfer', 'Other'
        ]
        
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess transaction descriptions"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', 'NUM', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def create_training_data(self) -> pd.DataFrame:
        """Generate synthetic training data for the model"""
        training_data = [
            # Food & Dining
            ("mcdonalds restaurant", "Food & Dining"),
            ("starbucks coffee", "Food & Dining"),
            ("pizza hut delivery", "Food & Dining"),
            ("grocery store walmart", "Food & Dining"),
            ("restaurant dinner", "Food & Dining"),
            
            # Shopping
            ("amazon purchase", "Shopping"),
            ("target store", "Shopping"),
            ("clothing store", "Shopping"),
            ("online shopping", "Shopping"),
            ("retail purchase", "Shopping"),
            
            # Transportation
            ("uber ride", "Transportation"),
            ("gas station fuel", "Transportation"),
            ("parking fee", "Transportation"),
            ("public transport", "Transportation"),
            ("car maintenance", "Transportation"),
            
            # Bills & Utilities
            ("electric bill", "Bills & Utilities"),
            ("internet service", "Bills & Utilities"),
            ("phone bill", "Bills & Utilities"),
            ("water utility", "Bills & Utilities"),
            ("rent payment", "Bills & Utilities"),
            
            # Entertainment
            ("netflix subscription", "Entertainment"),
            ("movie theater", "Entertainment"),
            ("spotify premium", "Entertainment"),
            ("gaming purchase", "Entertainment"),
            ("concert ticket", "Entertainment"),
            
            # Healthcare
            ("pharmacy cvs", "Healthcare"),
            ("doctor visit", "Healthcare"),
            ("dental care", "Healthcare"),
            ("hospital bill", "Healthcare"),
            ("insurance premium", "Healthcare"),
            
            # Income
            ("salary deposit", "Income"),
            ("freelance payment", "Income"),
            ("bonus payment", "Income"),
            ("investment return", "Income"),
            ("refund received", "Income"),
        ]
        
        return pd.DataFrame(training_data, columns=['description', 'category'])
    
    def train_model(self) -> None:
        """Train the categorization model"""
        # Create training data
        df = self.create_training_data()
        
        # Preprocess descriptions
        df['processed_description'] = df['description'].apply(self.preprocess_text)
        
        # Create pipeline
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000, ngram_range=(1, 2))),
            ('classifier', MultinomialNB(alpha=0.1))
        ])
        
        # Train model
        X = df['processed_description']
        y = df['category']
        
        self.model.fit(X, y)
        
        print("Model trained successfully!")
        
    def predict_category(self, description: str) -> Tuple[str, float]:
        """Predict category for a transaction description"""
        if not self.model:
            self.train_model()
            
        processed_desc = self.preprocess_text(description)
        prediction = self.model.predict([processed_desc])[0]
        confidence = max(self.model.predict_proba([processed_desc])[0])
        
        return prediction, confidence
    
    def save_model(self, filepath: str) -> None:
        """Save trained model to disk"""
        if self.model:
            joblib.dump(self.model, filepath)
            
    def load_model(self, filepath: str) -> None:
        """Load trained model from disk"""
        self.model = joblib.load(filepath)