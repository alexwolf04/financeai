from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import numpy as np

from app.database import get_db
from app.models.transaction import Transaction

router = APIRouter()

@router.get("/investment/{user_id}")
async def get_investment_recommendations(
    user_id: str, 
    risk_tolerance: str = "moderate",  # conservative, moderate, aggressive
    db: Session = Depends(get_db)
):
    """Generate personalized investment recommendations based on spending patterns"""
    
    # Get user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if len(transactions) < 10:
        raise HTTPException(
            status_code=400,
            detail="Need at least 10 transactions for investment recommendations"
        )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'amount': t.amount,
        'category': t.category,
        'date': t.date,
        'is_income': t.is_income
    } for t in transactions])
    
    # Calculate financial metrics
    spending_df = df[df['is_income'] == False]
    income_df = df[df['is_income'] == True]
    
    monthly_spending = spending_df.groupby(spending_df['date'].dt.to_period('M'))['amount'].sum().mean()
    monthly_income = income_df.groupby(income_df['date'].dt.to_period('M'))['amount'].sum().mean()
    
    if pd.isna(monthly_income) or monthly_income <= 0:
        monthly_income = monthly_spending * 1.3  # Conservative estimate
    
    # Calculate available investment amount
    monthly_surplus = monthly_income - monthly_spending
    emergency_fund_needed = monthly_spending * 6  # 6 months of expenses
    
    # Risk profiles
    risk_profiles = {
        "conservative": {
            "stocks": 30,
            "bonds": 60,
            "cash": 10,
            "expected_return": 0.06,
            "volatility": 0.08
        },
        "moderate": {
            "stocks": 60,
            "bonds": 30,
            "cash": 10,
            "expected_return": 0.08,
            "volatility": 0.12
        },
        "aggressive": {
            "stocks": 80,
            "bonds": 15,
            "cash": 5,
            "expected_return": 0.10,
            "volatility": 0.16
        }
    }
    
    profile = risk_profiles.get(risk_tolerance, risk_profiles["moderate"])
    
    # Generate recommendations
    recommendations = {
        "user_profile": {
            "monthly_income": float(monthly_income),
            "monthly_spending": float(monthly_spending),
            "monthly_surplus": float(monthly_surplus),
            "risk_tolerance": risk_tolerance
        },
        
        "emergency_fund": {
            "recommended_amount": float(emergency_fund_needed),
            "priority": "high" if monthly_surplus > 0 else "critical",
            "timeline": "3-6 months"
        },
        
        "investment_allocation": profile,
        
        "specific_recommendations": [],
        
        "projected_growth": {}
    }
    
    # Specific investment recommendations
    if monthly_surplus > 0:
        # Emergency fund first
        if monthly_surplus < emergency_fund_needed / 6:  # Less than 6 months to build emergency fund
            recommendations["specific_recommendations"].append({
                "type": "emergency_fund",
                "allocation": min(monthly_surplus * 0.8, emergency_fund_needed / 6),
                "description": "Build emergency fund first (high-yield savings account)",
                "priority": 1
            })
        
        # Investment recommendations
        investment_amount = max(0, monthly_surplus * 0.2 if monthly_surplus < emergency_fund_needed / 6 else monthly_surplus * 0.8)
        
        if investment_amount > 0:
            recommendations["specific_recommendations"].extend([
                {
                    "type": "index_funds",
                    "allocation": investment_amount * (profile["stocks"] / 100),
                    "description": f"Low-cost index funds (S&P 500, Total Market) - {profile['stocks']}%",
                    "priority": 2,
                    "examples": ["VTSAX", "FZROX", "SWTSX"]
                },
                {
                    "type": "bonds",
                    "allocation": investment_amount * (profile["bonds"] / 100),
                    "description": f"Bond funds for stability - {profile['bonds']}%",
                    "priority": 3,
                    "examples": ["VBTLX", "FXNAX", "SWAGX"]
                }
            ])
    
    else:
        recommendations["specific_recommendations"].append({
            "type": "budget_optimization",
            "description": "Focus on reducing expenses before investing",
            "priority": 1,
            "suggested_actions": [
                "Review and cut unnecessary subscriptions",
                "Optimize food and entertainment spending",
                "Consider increasing income through side work"
            ]
        })
    
    # Project growth over time
    if monthly_surplus > 0:
        investment_monthly = max(0, monthly_surplus * 0.8)
        years = [1, 5, 10, 20, 30]
        
        for year in years:
            # Compound growth calculation
            months = year * 12
            future_value = investment_monthly * (((1 + profile["expected_return"]/12) ** months - 1) / (profile["expected_return"]/12))
            
            recommendations["projected_growth"][f"{year}_years"] = {
                "total_invested": float(investment_monthly * months),
                "projected_value": float(future_value),
                "growth": float(future_value - investment_monthly * months)
            }
    
    return recommendations

@router.get("/savings-goals/{user_id}")
async def get_savings_goals_recommendations(user_id: str, db: Session = Depends(get_db)):
    """Generate personalized savings goals based on spending patterns"""
    
    # Get user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if len(transactions) < 5:
        raise HTTPException(
            status_code=400,
            detail="Need at least 5 transactions for savings recommendations"
        )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'amount': t.amount,
        'category': t.category,
        'date': t.date,
        'is_income': t.is_income
    } for t in transactions])
    
    # Calculate spending patterns
    spending_df = df[df['is_income'] == False]
    income_df = df[df['is_income'] == True]
    
    monthly_spending = spending_df.groupby(spending_df['date'].dt.to_period('M'))['amount'].sum().mean()
    monthly_income = income_df.groupby(income_df['date'].dt.to_period('M'))['amount'].sum().mean()
    
    if pd.isna(monthly_income) or monthly_income <= 0:
        monthly_income = monthly_spending * 1.2
    
    monthly_surplus = monthly_income - monthly_spending
    
    # Common savings goals with personalized amounts
    goals = {
        "emergency_fund": {
            "name": "Emergency Fund",
            "target_amount": monthly_spending * 6,
            "priority": 1,
            "timeline_months": 12,
            "description": "6 months of expenses for financial security"
        },
        "vacation": {
            "name": "Vacation Fund", 
            "target_amount": monthly_spending * 0.5,  # Half a month's spending
            "priority": 3,
            "timeline_months": 6,
            "description": "Annual vacation or travel fund"
        },
        "home_down_payment": {
            "name": "Home Down Payment",
            "target_amount": monthly_income * 24,  # 2 years of income (rough estimate)
            "priority": 2,
            "timeline_months": 60,
            "description": "20% down payment for home purchase"
        },
        "car_replacement": {
            "name": "Car Replacement",
            "target_amount": monthly_income * 6,  # 6 months of income
            "priority": 4,
            "timeline_months": 36,
            "description": "Replace vehicle when needed"
        },
        "retirement_boost": {
            "name": "Retirement Boost",
            "target_amount": monthly_income * 12,  # 1 year of income
            "priority": 2,
            "timeline_months": 24,
            "description": "Additional retirement savings beyond regular contributions"
        }
    }
    
    # Calculate monthly savings needed for each goal
    recommendations = {
        "user_profile": {
            "monthly_income": float(monthly_income),
            "monthly_spending": float(monthly_spending),
            "monthly_surplus": float(monthly_surplus),
            "savings_capacity": "good" if monthly_surplus > monthly_income * 0.2 else "limited" if monthly_surplus > 0 else "deficit"
        },
        "savings_goals": [],
        "recommended_strategy": {}
    }
    
    # Prioritize goals based on surplus
    total_monthly_needed = 0
    
    for goal_key, goal in sorted(goals.items(), key=lambda x: x[1]["priority"]):
        monthly_needed = goal["target_amount"] / goal["timeline_months"]
        
        goal_recommendation = {
            "name": goal["name"],
            "target_amount": float(goal["target_amount"]),
            "monthly_needed": float(monthly_needed),
            "timeline_months": goal["timeline_months"],
            "priority": goal["priority"],
            "description": goal["description"],
            "feasible": monthly_needed <= monthly_surplus - total_monthly_needed if monthly_surplus > 0 else False
        }
        
        if goal_recommendation["feasible"]:
            total_monthly_needed += monthly_needed
            goal_recommendation["status"] = "recommended"
        else:
            goal_recommendation["status"] = "stretch_goal"
            # Suggest longer timeline
            if monthly_surplus > 0:
                adjusted_timeline = goal["target_amount"] / (monthly_surplus - total_monthly_needed)
                goal_recommendation["adjusted_timeline_months"] = max(goal["timeline_months"], adjusted_timeline)
        
        recommendations["savings_goals"].append(goal_recommendation)
    
    # Overall strategy
    if monthly_surplus > 0:
        recommendations["recommended_strategy"] = {
            "total_monthly_allocation": float(min(total_monthly_needed, monthly_surplus)),
            "allocation_percentage": float(min(total_monthly_needed, monthly_surplus) / monthly_income * 100),
            "strategy": "automated_savings",
            "tips": [
                "Set up automatic transfers on payday",
                "Use separate savings accounts for each goal",
                "Review and adjust monthly based on spending changes",
                "Consider high-yield savings accounts for better returns"
            ]
        }
    else:
        recommendations["recommended_strategy"] = {
            "strategy": "expense_reduction_first",
            "deficit_amount": float(abs(monthly_surplus)),
            "tips": [
                "Focus on reducing expenses before setting savings goals",
                "Track spending for 30 days to identify areas to cut",
                "Consider increasing income through side work",
                "Start with a small emergency fund ($500-1000) first"
            ]
        }
    
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
    
    return convert_numpy_types(recommendations)

@router.get("/spending-optimization/{user_id}")
async def get_spending_optimization(user_id: str, db: Session = Depends(get_db)):
    """Analyze spending patterns and suggest optimizations"""
    
    # Get user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.is_income == False
    ).all()
    
    if len(transactions) < 10:
        raise HTTPException(
            status_code=400,
            detail="Need at least 10 spending transactions for optimization analysis"
        )
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'amount': t.amount,
        'category': t.category,
        'date': t.date,
        'description': t.description
    } for t in transactions])
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Analyze spending patterns
    total_spending = df['amount'].sum()
    category_spending = df.groupby('category')['amount'].sum().sort_values(ascending=False)
    category_counts = df.groupby('category').size()
    
    # Recent vs historical comparison (last 30 days vs previous period)
    recent_date = df['date'].max()
    last_30_days = df[df['date'] >= (recent_date - timedelta(days=30))]
    previous_30_days = df[(df['date'] >= (recent_date - timedelta(days=60))) & 
                         (df['date'] < (recent_date - timedelta(days=30)))]
    
    optimizations = {
        "spending_analysis": {
            "total_spending": float(total_spending),
            "average_transaction": float(df['amount'].mean()),
            "transaction_count": len(df),
            "top_categories": {cat: float(amount) for cat, amount in category_spending.head(5).items()}
        },
        
        "category_insights": {},
        "optimization_opportunities": [],
        "trend_analysis": {}
    }
    
    # Analyze each category
    for category, total_amount in category_spending.items():
        category_data = df[df['category'] == category]
        
        optimizations["category_insights"][category] = {
            "total_spent": float(total_amount),
            "percentage_of_total": float(total_amount / total_spending * 100),
            "transaction_count": int(category_counts[category]),
            "average_per_transaction": float(category_data['amount'].mean()),
            "frequency": "high" if category_counts[category] > len(df) * 0.2 else "medium" if category_counts[category] > len(df) * 0.1 else "low"
        }
        
        # Identify optimization opportunities
        if total_amount > total_spending * 0.15:  # Categories over 15% of spending
            if category in ['Food & Dining', 'Entertainment', 'Shopping']:
                optimizations["optimization_opportunities"].append({
                    "category": category,
                    "type": "high_spending",
                    "current_amount": float(total_amount),
                    "suggested_reduction": float(total_amount * 0.1),  # 10% reduction
                    "potential_monthly_savings": float(total_amount * 0.1),
                    "tips": get_category_optimization_tips(category)
                })
    
    # Trend analysis
    if len(last_30_days) > 0 and len(previous_30_days) > 0:
        recent_total = last_30_days['amount'].sum()
        previous_total = previous_30_days['amount'].sum()
        
        change_percent = ((recent_total - previous_total) / previous_total * 100) if previous_total > 0 else 0
        
        optimizations["trend_analysis"] = {
            "recent_30_days": float(recent_total),
            "previous_30_days": float(previous_total),
            "change_percent": float(change_percent),
            "trend": "increasing" if change_percent > 5 else "decreasing" if change_percent < -5 else "stable"
        }
        
        if change_percent > 10:
            optimizations["optimization_opportunities"].append({
                "type": "spending_increase",
                "message": f"Spending increased by {change_percent:.1f}% in the last 30 days",
                "suggested_action": "Review recent purchases and identify causes of increase",
                "priority": "high"
            })
    
    # Subscription detection (recurring similar amounts)
    potential_subscriptions = detect_subscriptions(df)
    if potential_subscriptions:
        optimizations["optimization_opportunities"].append({
            "type": "subscription_review",
            "subscriptions": potential_subscriptions,
            "suggested_action": "Review and cancel unused subscriptions",
            "potential_savings": sum(sub["monthly_cost"] for sub in potential_subscriptions)
        })
    
    return optimizations

def get_category_optimization_tips(category: str) -> List[str]:
    """Get specific optimization tips for each category"""
    tips = {
        "Food & Dining": [
            "Cook more meals at home",
            "Use grocery store loyalty programs",
            "Plan meals and make shopping lists",
            "Limit restaurant visits to special occasions"
        ],
        "Entertainment": [
            "Look for free local events",
            "Share streaming subscriptions with family",
            "Take advantage of happy hour pricing",
            "Consider library resources for books/movies"
        ],
        "Shopping": [
            "Wait 24 hours before non-essential purchases",
            "Use price comparison apps",
            "Shop with a list and stick to it",
            "Look for sales and use coupons"
        ],
        "Transportation": [
            "Use public transportation when possible",
            "Combine errands into single trips",
            "Consider carpooling or ride-sharing",
            "Keep up with vehicle maintenance"
        ]
    }
    
    return tips.get(category, ["Review spending in this category for potential savings"])

def detect_subscriptions(df: pd.DataFrame) -> List[Dict]:
    """Detect potential recurring subscriptions"""
    subscriptions = []
    
    # Group by similar amounts (within $5) and check for regularity
    df['amount_rounded'] = (df['amount'] / 5).round() * 5
    
    for amount in df['amount_rounded'].unique():
        similar_transactions = df[df['amount_rounded'] == amount]
        
        if len(similar_transactions) >= 3:  # At least 3 similar transactions
            # Check if they're roughly monthly
            dates = similar_transactions['date'].sort_values()
            intervals = dates.diff().dt.days.dropna()
            
            if len(intervals) > 0 and 25 <= intervals.mean() <= 35:  # Roughly monthly
                subscriptions.append({
                    "description": similar_transactions['description'].iloc[0],
                    "monthly_cost": float(amount),
                    "frequency": len(similar_transactions),
                    "category": similar_transactions['category'].iloc[0]
                })
    
    return subscriptions