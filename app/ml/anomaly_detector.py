import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

class AnomalyDetector:
    """AI model for detecting unusual spending patterns and potential fraud"""
    
    def __init__(self):
        self.isolation_forest = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def create_features(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """Create features for anomaly detection"""
        df = transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Amount-based features
        df['amount_log'] = np.log1p(df['amount'])
        df['amount_zscore'] = (df['amount'] - df['amount'].mean()) / df['amount'].std()
        
        # Time-based features
        df['hour'] = df['date'].dt.hour
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_night'] = ((df['hour'] >= 22) | (df['hour'] <= 6)).astype(int)
        
        # Rolling statistics
        df['rolling_7_mean'] = df['amount'].rolling(window=7, min_periods=1).mean()
        df['rolling_7_std'] = df['amount'].rolling(window=7, min_periods=1).std().fillna(0)
        df['rolling_30_mean'] = df['amount'].rolling(window=30, min_periods=1).mean()
        
        # Deviation from personal patterns
        df['amount_vs_7day_mean'] = df['amount'] / (df['rolling_7_mean'] + 1e-6)
        df['amount_vs_30day_mean'] = df['amount'] / (df['rolling_30_mean'] + 1e-6)
        
        # Category frequency (how often user spends in this category)
        category_counts = df['category'].value_counts()
        df['category_frequency'] = df['category'].map(category_counts)
        df['category_frequency_norm'] = df['category_frequency'] / len(df)
        
        # Transaction frequency patterns
        df['transactions_per_day'] = df.groupby(df['date'].dt.date).transform('size')
        
        # Spending velocity (change in spending pattern)
        df['amount_diff'] = df['amount'].diff().fillna(0)
        df['spending_acceleration'] = df['amount_diff'].diff().fillna(0)
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Prepare feature matrix for anomaly detection"""
        # Only use features that are guaranteed to exist
        available_cols = df.columns.tolist()
        
        feature_cols = [
            'amount_log', 'amount_zscore', 'hour', 'day_of_week', 
            'is_weekend', 'is_night', 'amount_vs_7day_mean', 
            'amount_vs_30day_mean', 'category_frequency_norm'
        ]
        
        # Only include columns that actually exist
        feature_cols = [col for col in feature_cols if col in available_cols]
        
        self.feature_columns = feature_cols
        X = df[feature_cols].fillna(0)
        
        # Handle infinite values
        X = X.replace([np.inf, -np.inf], 0)
        
        return X.values
    
    def train_model(self, transactions_df: pd.DataFrame) -> Dict:
        """Train the anomaly detection model"""
        # Create features
        df_features = self.create_features(transactions_df)
        
        # Prepare feature matrix
        X = self.prepare_features(df_features)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.isolation_forest = IsolationForest(
            contamination=0.1,  # Expect 10% anomalies
            random_state=42,
            n_estimators=100
        )
        
        anomaly_scores = self.isolation_forest.fit_predict(X_scaled)
        anomaly_proba = self.isolation_forest.score_samples(X_scaled)
        
        # Calculate statistics
        n_anomalies = np.sum(anomaly_scores == -1)
        anomaly_rate = n_anomalies / len(anomaly_scores)
        
        metrics = {
            'total_transactions': len(transactions_df),
            'detected_anomalies': n_anomalies,
            'anomaly_rate': anomaly_rate,
            'avg_anomaly_score': np.mean(anomaly_proba[anomaly_scores == -1]) if n_anomalies > 0 else 0
        }
        
        print(f"Anomaly detection model trained - {n_anomalies} anomalies detected ({anomaly_rate:.2%})")
        return metrics
    
    def detect_anomalies(self, transactions_df: pd.DataFrame) -> List[Dict]:
        """Detect anomalies in transaction data"""
        if not self.isolation_forest:
            raise ValueError("Model not trained. Call train_model() first.")
        
        # Create features
        df_features = self.create_features(transactions_df)
        
        # Prepare features
        X = self.prepare_features(df_features)
        X_scaled = self.scaler.transform(X)
        
        # Predict anomalies
        anomaly_predictions = self.isolation_forest.predict(X_scaled)
        anomaly_scores = self.isolation_forest.score_samples(X_scaled)
        
        # Identify anomalous transactions
        anomalies = []
        for idx, (prediction, score) in enumerate(zip(anomaly_predictions, anomaly_scores)):
            if prediction == -1:  # Anomaly detected
                transaction = transactions_df.iloc[idx]
                
                # Determine anomaly reasons
                reasons = self._analyze_anomaly_reasons(df_features.iloc[idx], transactions_df)
                
                anomalies.append({
                    'transaction_id': transaction.get('id', idx),
                    'amount': transaction['amount'],
                    'description': transaction['description'],
                    'category': transaction['category'],
                    'date': transaction['date'],
                    'anomaly_score': score,
                    'severity': self._get_severity(score),
                    'reasons': reasons,
                    'risk_level': self._assess_risk_level(transaction, reasons)
                })
        
        return sorted(anomalies, key=lambda x: x['anomaly_score'])
    
    def _analyze_anomaly_reasons(self, transaction_features: pd.Series, full_df: pd.DataFrame) -> List[str]:
        """Analyze why a transaction was flagged as anomalous"""
        reasons = []
        
        # Check amount anomalies
        if transaction_features['amount_vs_30day_mean'] > 3:
            reasons.append("Amount significantly higher than usual spending")
        
        if transaction_features['is_night'] == 1:
            reasons.append("Transaction occurred during unusual hours (night)")
        
        if transaction_features['category_frequency_norm'] < 0.05:
            reasons.append("Spending in rarely used category")
        
        # Skip transactions_per_day check if not available
        if 'transactions_per_day' in transaction_features.index and 'transactions_per_day' in full_df.columns:
            if transaction_features['transactions_per_day'] > full_df['transactions_per_day'].quantile(0.95):
                reasons.append("Unusually high number of transactions in one day")
        
        # Skip spending_acceleration check if not available
        if 'spending_acceleration' in transaction_features.index and 'spending_acceleration' in full_df.columns:
            if abs(transaction_features['spending_acceleration']) > full_df['spending_acceleration'].quantile(0.95):
                reasons.append("Sudden change in spending pattern")
        
        return reasons if reasons else ["General spending pattern deviation"]
    
    def _get_severity(self, anomaly_score: float) -> str:
        """Determine severity level based on anomaly score"""
        if anomaly_score < -0.5:
            return "High"
        elif anomaly_score < -0.3:
            return "Medium"
        else:
            return "Low"
    
    def _assess_risk_level(self, transaction: pd.Series, reasons: List[str]) -> str:
        """Assess fraud risk level"""
        risk_factors = 0
        
        # High amount
        if transaction['amount'] > 1000:
            risk_factors += 2
        elif transaction['amount'] > 500:
            risk_factors += 1
        
        # Multiple risk reasons
        risk_factors += len(reasons)
        
        # Night transactions are riskier
        if "night" in str(reasons).lower():
            risk_factors += 1
        
        if risk_factors >= 4:
            return "High Risk"
        elif risk_factors >= 2:
            return "Medium Risk"
        else:
            return "Low Risk"
    
    def get_spending_insights(self, transactions_df: pd.DataFrame) -> Dict:
        """Generate insights about spending patterns"""
        df = transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # Recent vs historical comparison
        recent_30 = df[df['date'] >= (df['date'].max() - timedelta(days=30))]
        historical = df[df['date'] < (df['date'].max() - timedelta(days=30))]
        
        insights = {
            'spending_trend': {
                'recent_avg_daily': recent_30['amount'].sum() / 30 if len(recent_30) > 0 else 0,
                'historical_avg_daily': historical['amount'].sum() / max(1, len(historical.groupby(historical['date'].dt.date))) if len(historical) > 0 else 0,
            },
            'category_changes': {},
            'unusual_patterns': []
        }
        
        # Category spending changes
        if len(historical) > 0 and len(recent_30) > 0:
            recent_by_cat = recent_30.groupby('category')['amount'].sum()
            historical_by_cat = historical.groupby('category')['amount'].sum()
            
            for category in recent_by_cat.index:
                recent_amt = recent_by_cat[category]
                historical_amt = historical_by_cat.get(category, 0)
                
                if historical_amt > 0:
                    change_pct = ((recent_amt - historical_amt) / historical_amt) * 100
                    insights['category_changes'][category] = {
                        'change_percent': change_pct,
                        'recent_amount': recent_amt,
                        'historical_amount': historical_amt
                    }
        
        return insights
    
    def save_model(self, filepath: str) -> None:
        """Save trained model and scaler"""
        if self.isolation_forest:
            joblib.dump({
                'model': self.isolation_forest,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns
            }, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load trained model and scaler"""
        data = joblib.load(filepath)
        self.isolation_forest = data['model']
        self.scaler = data['scaler']
        self.feature_columns = data['feature_columns']