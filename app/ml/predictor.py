import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class SpendingPredictor:
    """AI model for predicting future spending patterns"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        
    def create_features(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """Create features for spending prediction"""
        df = transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Time-based features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Rolling statistics (7-day and 30-day windows)
        df['rolling_7_mean'] = df['amount'].rolling(window=7, min_periods=1).mean()
        df['rolling_7_std'] = df['amount'].rolling(window=7, min_periods=1).std().fillna(0)
        df['rolling_30_mean'] = df['amount'].rolling(window=30, min_periods=1).mean()
        df['rolling_30_std'] = df['amount'].rolling(window=30, min_periods=1).std().fillna(0)
        
        # Category encoding
        category_dummies = pd.get_dummies(df['category'], prefix='cat')
        df = pd.concat([df, category_dummies], axis=1)
        
        # Lag features
        df['amount_lag_1'] = df['amount'].shift(1).fillna(0)
        df['amount_lag_7'] = df['amount'].shift(7).fillna(0)
        
        return df
    
    def prepare_training_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for model training"""
        feature_cols = [col for col in df.columns if col not in 
                       ['id', 'user_id', 'amount', 'description', 'date', 'category', 
                        'predicted_category', 'is_anomaly', 'confidence_score', 'created_at']]
        
        self.feature_columns = feature_cols
        X = df[feature_cols].fillna(0)
        y = df['amount']
        
        return X.values, y.values
    
    def train_model(self, transactions_df: pd.DataFrame) -> Dict:
        """Train the spending prediction model"""
        # Create features
        df_features = self.create_features(transactions_df)
        
        # Prepare training data
        X, y = self.prepare_training_data(df_features)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_scaled, y)
        
        # Calculate metrics
        y_pred = self.model.predict(X_scaled)
        mae = mean_absolute_error(y, y_pred)
        rmse = np.sqrt(mean_squared_error(y, y_pred))
        
        metrics = {
            'mae': mae,
            'rmse': rmse,
            'r2_score': self.model.score(X_scaled, y)
        }
        
        print(f"Model trained - MAE: {mae:.2f}, RMSE: {rmse:.2f}, R²: {metrics['r2_score']:.3f}")
        return metrics
    
    def predict_future_spending(self, transactions_df: pd.DataFrame, days_ahead: int = 30) -> Dict:
        """Predict spending for the next N days"""
        if not self.model:
            raise ValueError("Model not trained. Call train_model() first.")
        
        # Get recent transactions for context
        df = transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        recent_df = df.tail(100)  # Use last 100 transactions for prediction
        
        # Create features for recent data
        df_features = self.create_features(recent_df)
        
        # Generate predictions for future dates
        last_date = df['date'].max()
        future_dates = [last_date + timedelta(days=i) for i in range(1, days_ahead + 1)]
        
        predictions = []
        total_predicted = 0
        
        for future_date in future_dates:
            # Create feature vector for future date
            future_features = self._create_future_features(df_features, future_date)
            
            if len(future_features) == len(self.feature_columns):
                # Scale and predict
                future_scaled = self.scaler.transform([future_features])
                predicted_amount = self.model.predict(future_scaled)[0]
                
                predictions.append({
                    'date': future_date.strftime('%Y-%m-%d'),
                    'predicted_amount': max(0, predicted_amount)  # Ensure non-negative
                })
                total_predicted += max(0, predicted_amount)
        
        # Category-wise predictions
        category_predictions = self._predict_by_category(transactions_df, days_ahead)
        
        return {
            'daily_predictions': predictions,
            'total_predicted': total_predicted,
            'category_breakdown': category_predictions,
            'prediction_period': f"{days_ahead} days"
        }
    
    def _create_future_features(self, df_features: pd.DataFrame, future_date: datetime) -> List[float]:
        """Create feature vector for a future date"""
        # Basic time features
        features = [
            future_date.weekday(),  # day_of_week
            future_date.day,        # day_of_month
            future_date.month,      # month
            1 if future_date.weekday() >= 5 else 0,  # is_weekend
        ]
        
        # Use recent rolling statistics
        if len(df_features) > 0:
            recent_stats = df_features.tail(30)
            features.extend([
                recent_stats['rolling_7_mean'].iloc[-1],
                recent_stats['rolling_7_std'].iloc[-1],
                recent_stats['rolling_30_mean'].iloc[-1],
                recent_stats['rolling_30_std'].iloc[-1],
            ])
            
            # Category features (use average distribution)
            cat_cols = [col for col in df_features.columns if col.startswith('cat_')]
            for cat_col in cat_cols:
                if cat_col in df_features.columns:
                    features.append(recent_stats[cat_col].mean())
                else:
                    features.append(0)
            
            # Lag features
            features.extend([
                recent_stats['amount'].iloc[-1] if len(recent_stats) > 0 else 0,
                recent_stats['amount'].iloc[-7] if len(recent_stats) > 7 else 0,
            ])
        else:
            # Default values if no historical data
            features.extend([0] * (len(self.feature_columns) - 4))
        
        return features[:len(self.feature_columns)]
    
    def _predict_by_category(self, transactions_df: pd.DataFrame, days_ahead: int) -> Dict:
        """Predict spending by category"""
        df = transactions_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate average daily spending by category
        recent_30_days = df[df['date'] >= (df['date'].max() - timedelta(days=30))]
        
        category_daily_avg = recent_30_days.groupby('category')['amount'].sum() / 30
        category_predictions = {}
        
        for category, daily_avg in category_daily_avg.items():
            category_predictions[category] = {
                'predicted_total': daily_avg * days_ahead,
                'daily_average': daily_avg
            }
        
        return category_predictions
    
    def save_model(self, filepath: str) -> None:
        """Save trained model and scaler"""
        if self.model:
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns
            }, filepath)
    
    def load_model(self, filepath: str) -> None:
        """Load trained model and scaler"""
        data = joblib.load(filepath)
        self.model = data['model']
        self.scaler = data['scaler']
        self.feature_columns = data['feature_columns']