from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from typing import Dict, Optional

from app.database import get_db
from app.models.transaction import Transaction
from app.ml.predictor import SpendingPredictor
from app.ml.anomaly_detector import AnomalyDetector

router = APIRouter()
predictor = SpendingPredictor()
anomaly_detector = AnomalyDetector()

@router.post("/train/{user_id}")
async def train_prediction_models(user_id: str, db: Session = Depends(get_db)):
    """Train prediction models for a specific user"""
    
    # Get user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if len(transactions) < 10:
        raise HTTPException(
            status_code=400, 
            detail="Need at least 10 transactions to train models"
        )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'id': t.id,
        'user_id': t.user_id,
        'amount': t.amount,
        'description': t.description,
        'category': t.category,
        'date': t.date,
        'is_income': t.is_income
    } for t in transactions])
    
    # Filter out income transactions for spending prediction
    spending_df = df[df['is_income'] == False].copy()
    
    if len(spending_df) < 5:
        raise HTTPException(
            status_code=400,
            detail="Need at least 5 spending transactions to train models"
        )
    
    try:
        # Train spending predictor
        predictor_metrics = predictor.train_model(spending_df)
        
        # Train anomaly detector
        anomaly_metrics = anomaly_detector.train_model(spending_df)
        
        # Convert numpy types to Python types
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            else:
                return obj
        
        return {
            "message": "Models trained successfully",
            "user_id": user_id,
            "transaction_count": len(transactions),
            "spending_transactions": len(spending_df),
            "predictor_metrics": convert_numpy_types(predictor_metrics),
            "anomaly_metrics": convert_numpy_types(anomaly_metrics)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@router.get("/spending/{user_id}")
async def predict_future_spending(
    user_id: str, 
    days_ahead: int = 30, 
    db: Session = Depends(get_db)
):
    """Predict future spending for a user"""
    
    # Get user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == False
    ).all()
    
    if len(transactions) < 10:
        raise HTTPException(
            status_code=400,
            detail="Need at least 10 transactions for predictions"
        )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'amount': t.amount,
        'description': t.description,
        'category': t.category,
        'date': t.date
    } for t in transactions])
    
    try:
        # Train model if not already trained
        if not predictor.model:
            predictor.train_model(df)
        
        # Generate predictions
        predictions = predictor.predict_future_spending(df, days_ahead)
        
        # Convert numpy types to Python types
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            else:
                return obj
        
        return {
            "user_id": user_id,
            "predictions": convert_numpy_types(predictions),
            "based_on_transactions": len(transactions)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.get("/anomalies/{user_id}")
async def detect_spending_anomalies(user_id: str, db: Session = Depends(get_db)):
    """Detect anomalous spending patterns"""
    
    # Get user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if len(transactions) < 20:
        raise HTTPException(
            status_code=400,
            detail="Need at least 20 transactions for anomaly detection"
        )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'id': t.id,
        'amount': t.amount,
        'description': t.description,
        'category': t.category,
        'date': t.date,
        'is_income': t.is_income
    } for t in transactions])
    
    try:
        # Train model if not already trained
        if not anomaly_detector.isolation_forest:
            anomaly_detector.train_model(df)
        
        # Detect anomalies
        anomalies = anomaly_detector.detect_anomalies(df)
        
        # Update database with anomaly flags
        for anomaly in anomalies:
            transaction_id = anomaly['transaction_id']
            db.query(Transaction).filter(Transaction.id == transaction_id).update({
                'is_anomaly': True
            })
        
        db.commit()
        
        # Get spending insights
        insights = anomaly_detector.get_spending_insights(df)
        
        # Convert numpy types to Python types
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            else:
                return obj
        
        return {
            "user_id": user_id,
            "anomalies": convert_numpy_types(anomalies),
            "anomaly_count": len(anomalies),
            "total_transactions": len(transactions),
            "insights": convert_numpy_types(insights)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anomaly detection failed: {str(e)}")

@router.get("/budget-recommendation/{user_id}")
async def get_budget_recommendation(user_id: str, monthly_income: Optional[float] = None, db: Session = Depends(get_db)):
    """Generate AI-powered budget recommendations"""
    
    # Get user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if len(transactions) < 10:
        raise HTTPException(
            status_code=400,
            detail="Need at least 10 transactions for budget recommendations"
        )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'amount': t.amount,
        'category': t.category,
        'date': t.date,
        'is_income': t.is_income
    } for t in transactions])
    
    # Calculate current spending patterns
    spending_df = df[df['is_income'] == False]
    income_df = df[df['is_income'] == True]
    
    # Calculate monthly averages
    monthly_spending = spending_df.groupby(spending_df['date'].dt.to_period('M'))['amount'].sum().mean()
    
    if monthly_income is None:
        monthly_income = income_df.groupby(income_df['date'].dt.to_period('M'))['amount'].sum().mean()
        if pd.isna(monthly_income) or monthly_income <= 0:
            monthly_income = monthly_spending * 1.5  # Estimate if no income data
    
    # Category-wise spending analysis
    category_spending = spending_df.groupby('category')['amount'].sum()
    category_percentages = (category_spending / category_spending.sum() * 100).round(1)
    
    # Generate recommendations using 50/30/20 rule as baseline
    recommendations = {
        "monthly_income": float(monthly_income),
        "current_monthly_spending": float(monthly_spending),
        "savings_rate": float((monthly_income - monthly_spending) / monthly_income * 100) if monthly_income > 0 else 0,
        
        "recommended_budget": {
            "needs": float(monthly_income * 0.50),  # 50% for needs
            "wants": float(monthly_income * 0.30),  # 30% for wants  
            "savings": float(monthly_income * 0.20), # 20% for savings
        },
        
        "category_analysis": {},
        "recommendations": []
    }
    
    # Analyze each category
    need_categories = ['Bills & Utilities', 'Food & Dining', 'Transportation', 'Healthcare']
    want_categories = ['Entertainment', 'Shopping', 'Travel']
    
    current_needs = category_spending[category_spending.index.isin(need_categories)].sum()
    current_wants = category_spending[category_spending.index.isin(want_categories)].sum()
    
    for category, amount in category_spending.items():
        percentage = float(amount / monthly_spending * 100) if monthly_spending > 0 else 0
        
        recommendations["category_analysis"][category] = {
            "current_amount": float(amount),
            "percentage_of_spending": percentage,
            "monthly_average": float(amount),
            "category_type": "need" if category in need_categories else "want"
        }
    
    # Generate specific recommendations
    if current_needs > recommendations["recommended_budget"]["needs"]:
        recommendations["recommendations"].append({
            "type": "reduce_needs",
            "message": f"Consider reducing essential expenses by ${current_needs - recommendations['recommended_budget']['needs']:.0f}",
            "priority": "high"
        })
    
    if current_wants > recommendations["recommended_budget"]["wants"]:
        recommendations["recommendations"].append({
            "type": "reduce_wants", 
            "message": f"Consider reducing discretionary spending by ${current_wants - recommendations['recommended_budget']['wants']:.0f}",
            "priority": "medium"
        })
    
    if recommendations["savings_rate"] < 20:
        recommendations["recommendations"].append({
            "type": "increase_savings",
            "message": f"Try to increase savings rate to 20% (currently {recommendations['savings_rate']:.1f}%)",
            "priority": "high"
        })
    
    return recommendations