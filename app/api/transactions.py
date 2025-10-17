from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import pandas as pd

from app.database import get_db
from app.models.transaction import Transaction, TransactionCreate, TransactionResponse
from app.ml.categorizer import TransactionCategorizer
from app.security import validate_user_id, sanitize_input, validate_amount, verify_rate_limit

router = APIRouter()
categorizer = TransactionCategorizer()

@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate, 
    request: Request,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_rate_limit)
):
    """Create a new transaction with AI-powered categorization"""
    
    # Validate inputs
    if not validate_user_id(transaction.user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    if not validate_amount(transaction.amount):
        raise HTTPException(status_code=400, detail="Invalid transaction amount")
    
    # Sanitize description
    clean_description = sanitize_input(transaction.description, 200)
    if not clean_description:
        raise HTTPException(status_code=400, detail="Transaction description is required")
    
    # Predict category if not provided
    predicted_category = None
    confidence_score = None
    
    if not transaction.category:
        try:
            predicted_category, confidence_score = categorizer.predict_category(clean_description)
        except Exception as e:
            print(f"Categorization error: {e}")
            predicted_category = "Other"
            confidence_score = 0.5
    
    # Create transaction record
    db_transaction = Transaction(
        user_id=transaction.user_id,
        amount=transaction.amount,
        description=clean_description,
        category=transaction.category or predicted_category,
        predicted_category=predicted_category,
        date=transaction.date,
        is_income=transaction.is_income,
        confidence_score=confidence_score
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    return db_transaction

@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(user_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """Get transactions for a user"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).order_by(Transaction.date.desc()).limit(limit).all()
    
    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    """Get a specific transaction"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction

@router.post("/bulk")
async def create_bulk_transactions(transactions: List[TransactionCreate], db: Session = Depends(get_db)):
    """Create multiple transactions at once"""
    created_transactions = []
    
    for transaction_data in transactions:
        # Predict category
        predicted_category = None
        confidence_score = None
        
        if not transaction_data.category:
            try:
                predicted_category, confidence_score = categorizer.predict_category(transaction_data.description)
            except Exception:
                predicted_category = "Other"
                confidence_score = 0.5
        
        db_transaction = Transaction(
            user_id=transaction_data.user_id,
            amount=transaction_data.amount,
            description=transaction_data.description,
            category=transaction_data.category or predicted_category,
            predicted_category=predicted_category,
            date=transaction_data.date,
            is_income=transaction_data.is_income,
            confidence_score=confidence_score
        )
        
        db.add(db_transaction)
        created_transactions.append(db_transaction)
    
    db.commit()
    
    return {"message": f"Created {len(created_transactions)} transactions", "count": len(created_transactions)}

@router.get("/categories/stats")
async def get_category_stats(user_id: str, db: Session = Depends(get_db)):
    """Get spending statistics by category"""
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == False
    ).all()
    
    if not transactions:
        return {"categories": {}, "total_spending": 0}
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame([{
        'category': t.category,
        'amount': t.amount,
        'date': t.date
    } for t in transactions])
    
    # Calculate category statistics
    category_stats = df.groupby('category').agg({
        'amount': ['sum', 'mean', 'count']
    }).round(2)
    
    category_data = {}
    for category in category_stats.index:
        total_sum = category_stats.loc[category, ('amount', 'sum')]
        total_mean = category_stats.loc[category, ('amount', 'mean')]
        total_count = category_stats.loc[category, ('amount', 'count')]
        
        category_data[category] = {
            'total': float(total_sum),
            'average': float(total_mean),
            'count': int(total_count),
            'percentage': float(total_sum / df['amount'].sum() * 100)
        }
    
    return {
        "categories": category_data,
        "total_spending": float(df['amount'].sum()),
        "transaction_count": len(transactions)
    }