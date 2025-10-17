from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
from typing import Dict, List
from datetime import datetime, timedelta
import calendar

from app.database import get_db
from app.models.transaction import Transaction

router = APIRouter()

@router.get("/overview/{user_id}")
async def get_dashboard_overview(user_id: str, db: Session = Depends(get_db)):
    """Get comprehensive dashboard overview for a user"""
    
    # Get all user transactions
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if not transactions:
        return {
            "message": "No transactions found",
            "user_id": user_id,
            "overview": {},
            "charts": {},
            "insights": []
        }
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'id': t.id,
        'amount': t.amount,
        'category': t.category,
        'date': t.date,
        'is_income': t.is_income,
        'is_anomaly': t.is_anomaly,
        'description': t.description
    } for t in transactions])
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Separate income and expenses
    expenses_df = df[df['is_income'] == False]
    income_df = df[df['is_income'] == True]
    
    # Calculate key metrics
    total_income = income_df['amount'].sum() if len(income_df) > 0 else 0
    total_expenses = expenses_df['amount'].sum() if len(expenses_df) > 0 else 0
    net_worth_change = total_income - total_expenses
    
    # Recent activity (last 30 days)
    recent_date = df['date'].max()
    last_30_days = df[df['date'] >= (recent_date - timedelta(days=30))]
    recent_expenses = last_30_days[last_30_days['is_income'] == False]['amount'].sum()
    recent_income = last_30_days[last_30_days['is_income'] == True]['amount'].sum()
    
    # Monthly trends
    monthly_data = get_monthly_trends(df)
    
    # Category breakdown
    category_data = get_category_breakdown(expenses_df)
    
    # Anomalies
    anomalies = df[df['is_anomaly'] == True]
    
    overview = {
        "user_id": user_id,
        "overview": {
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net_worth_change": float(net_worth_change),
            "savings_rate": float((net_worth_change / total_income * 100) if total_income > 0 else 0),
            "recent_30_days": {
                "income": float(recent_income),
                "expenses": float(recent_expenses),
                "net": float(recent_income - recent_expenses)
            },
            "transaction_count": len(df),
            "anomaly_count": len(anomalies)
        },
        
        "charts": {
            "monthly_trends": monthly_data,
            "category_breakdown": category_data,
            "spending_timeline": get_spending_timeline(expenses_df)
        },
        
        "insights": generate_insights(df, expenses_df, income_df)
    }
    
    return overview

def get_monthly_trends(df: pd.DataFrame) -> Dict:
    """Calculate monthly income/expense trends"""
    df_monthly = df.copy()
    df_monthly['month'] = df_monthly['date'].dt.to_period('M')
    
    monthly_summary = df_monthly.groupby(['month', 'is_income'])['amount'].sum().unstack(fill_value=0)
    
    trends = []
    for month in monthly_summary.index:
        month_data = {
            "month": str(month),
            "income": float(monthly_summary.loc[month, True] if True in monthly_summary.columns else 0),
            "expenses": float(monthly_summary.loc[month, False] if False in monthly_summary.columns else 0)
        }
        month_data["net"] = month_data["income"] - month_data["expenses"]
        trends.append(month_data)
    
    return {"data": trends}

def get_category_breakdown(expenses_df: pd.DataFrame) -> Dict:
    """Get spending breakdown by category"""
    if len(expenses_df) == 0:
        return {"data": []}
    
    category_totals = expenses_df.groupby('category')['amount'].sum().sort_values(ascending=False)
    total_spending = category_totals.sum()
    
    breakdown = []
    for category, amount in category_totals.items():
        breakdown.append({
            "category": category,
            "amount": float(amount),
            "percentage": float(amount / total_spending * 100) if total_spending > 0 else 0,
            "transaction_count": int(len(expenses_df[expenses_df['category'] == category]))
        })
    
    return {"data": breakdown}

def get_spending_timeline(expenses_df: pd.DataFrame) -> Dict:
    """Get daily spending timeline for the last 30 days"""
    if len(expenses_df) == 0:
        return {"data": []}
    
    # Get last 30 days
    recent_date = expenses_df['date'].max()
    last_30_days = expenses_df[expenses_df['date'] >= (recent_date - timedelta(days=30))]
    
    # Group by date
    daily_spending = last_30_days.groupby(last_30_days['date'].dt.date)['amount'].sum()
    
    timeline = []
    for date, amount in daily_spending.items():
        timeline.append({
            "date": date.strftime('%Y-%m-%d'),
            "amount": float(amount)
        })
    
    return {"data": sorted(timeline, key=lambda x: x['date'])}

def generate_insights(df: pd.DataFrame, expenses_df: pd.DataFrame, income_df: pd.DataFrame) -> List[Dict]:
    """Generate AI-powered financial insights"""
    insights = []
    
    if len(expenses_df) == 0:
        return insights
    
    # Insight 1: Top spending category
    category_sums = expenses_df.groupby('category')['amount'].sum()
    top_category = category_sums.idxmax()
    top_amount = category_sums.max()
    total_expenses = expenses_df['amount'].sum()
    
    insights.append({
        "type": "top_category",
        "title": "Highest Spending Category",
        "message": f"You spend the most on {top_category} (${float(top_amount):.0f}, {float(top_amount)/float(total_expenses)*100:.1f}% of total)",
        "category": str(top_category),
        "amount": float(top_amount),
        "actionable": True,
        "suggestion": f"Consider reviewing your {top_category} expenses for potential savings"
    })
    
    # Insight 2: Savings rate
    total_income = float(income_df['amount'].sum()) if len(income_df) > 0 else 0
    total_expenses_float = float(total_expenses)
    
    if total_income > 0:
        savings_rate = (total_income - total_expenses_float) / total_income * 100
        
        if savings_rate < 10:
            insights.append({
                "type": "low_savings",
                "title": "Low Savings Rate",
                "message": f"Your savings rate is {savings_rate:.1f}%. Aim for at least 20%",
                "savings_rate": float(savings_rate),
                "actionable": True,
                "suggestion": "Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings"
            })
        elif savings_rate > 30:
            insights.append({
                "type": "high_savings",
                "title": "Excellent Savings Rate",
                "message": f"Great job! Your savings rate is {savings_rate:.1f}%",
                "savings_rate": float(savings_rate),
                "actionable": False,
                "suggestion": "Consider investing your surplus for long-term growth"
            })
    
    # Insight 3: Spending trends
    recent_date = df['date'].max()
    last_30_days = expenses_df[expenses_df['date'] >= (recent_date - timedelta(days=30))]
    previous_30_days = expenses_df[(expenses_df['date'] >= (recent_date - timedelta(days=60))) & 
                                  (expenses_df['date'] < (recent_date - timedelta(days=30)))]
    
    if len(last_30_days) > 0 and len(previous_30_days) > 0:
        recent_spending = float(last_30_days['amount'].sum())
        previous_spending = float(previous_30_days['amount'].sum())
        
        if previous_spending > 0:
            change_percent = (recent_spending - previous_spending) / previous_spending * 100
            
            if abs(change_percent) > 10:
                trend = "increased" if change_percent > 0 else "decreased"
                insights.append({
                    "type": "spending_trend",
                    "title": f"Spending {trend.title()}",
                    "message": f"Your spending has {trend} by {abs(change_percent):.1f}% in the last 30 days",
                    "change_percent": float(change_percent),
                    "actionable": bool(change_percent > 0),
                    "suggestion": "Review recent purchases to understand the change" if change_percent > 0 else "Keep up the good work on reducing expenses!"
                })
    
    # Insight 4: Anomalies detected
    anomalies = df[df['is_anomaly'] == True]
    if len(anomalies) > 0:
        insights.append({
            "type": "anomalies",
            "title": "Unusual Transactions Detected",
            "message": f"Found {len(anomalies)} unusual transactions worth reviewing",
            "anomaly_count": len(anomalies),
            "actionable": True,
            "suggestion": "Review flagged transactions for potential fraud or errors"
        })
    
    # Insight 5: Weekend vs weekday spending
    expenses_df_copy = expenses_df.copy()
    expenses_df_copy['is_weekend'] = expenses_df_copy['date'].dt.dayofweek >= 5
    weekend_avg = expenses_df_copy[expenses_df_copy['is_weekend']]['amount'].mean()
    weekday_avg = expenses_df_copy[~expenses_df_copy['is_weekend']]['amount'].mean()
    
    if not pd.isna(weekend_avg) and not pd.isna(weekday_avg) and weekend_avg > weekday_avg * 1.5:
        weekend_avg_float = float(weekend_avg)
        weekday_avg_float = float(weekday_avg)
        
        insights.append({
            "type": "weekend_spending",
            "title": "Higher Weekend Spending",
            "message": f"You spend {weekend_avg_float/weekday_avg_float:.1f}x more on weekends (${weekend_avg_float:.0f} vs ${weekday_avg_float:.0f})",
            "weekend_avg": weekend_avg_float,
            "weekday_avg": weekday_avg_float,
            "actionable": True,
            "suggestion": "Plan weekend activities with a budget to control spending"
        })
    
    return insights

@router.get("/charts/{user_id}")
async def get_chart_data(user_id: str, chart_type: str, db: Session = Depends(get_db)):
    """Get specific chart data for dashboard visualizations"""
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if not transactions:
        return {"data": [], "message": "No data available"}
    
    df = pd.DataFrame([{
        'amount': t.amount,
        'category': t.category,
        'date': t.date,
        'is_income': t.is_income
    } for t in transactions])
    
    df['date'] = pd.to_datetime(df['date'])
    
    if chart_type == "spending_by_day_of_week":
        expenses_df = df[df['is_income'] == False]
        expenses_df['day_name'] = expenses_df['date'].dt.day_name()
        
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_spending = expenses_df.groupby('day_name')['amount'].mean().reindex(day_order, fill_value=0)
        
        return {
            "data": [{"day": day, "amount": float(amount)} for day, amount in daily_spending.items()],
            "chart_type": chart_type
        }
    
    elif chart_type == "monthly_comparison":
        monthly_data = df.groupby([df['date'].dt.to_period('M'), 'is_income'])['amount'].sum().unstack(fill_value=0)
        
        comparison_data = []
        for month in monthly_data.index:
            comparison_data.append({
                "month": str(month),
                "income": float(monthly_data.loc[month, True] if True in monthly_data.columns else 0),
                "expenses": float(monthly_data.loc[month, False] if False in monthly_data.columns else 0)
            })
        
        return {"data": comparison_data, "chart_type": chart_type}
    
    elif chart_type == "category_trends":
        expenses_df = df[df['is_income'] == False]
        
        # Get top 5 categories
        top_categories = expenses_df.groupby('category')['amount'].sum().nlargest(5).index
        
        category_trends = []
        for category in top_categories:
            cat_data = expenses_df[expenses_df['category'] == category]
            monthly_amounts = cat_data.groupby(cat_data['date'].dt.to_period('M'))['amount'].sum()
            
            trend_data = []
            for month, amount in monthly_amounts.items():
                trend_data.append({"month": str(month), "amount": float(amount)})
            
            category_trends.append({
                "category": category,
                "data": trend_data
            })
        
        return {"data": category_trends, "chart_type": chart_type}
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown chart type: {chart_type}")

@router.get("/export/{user_id}")
async def export_financial_data(user_id: str, format: str = "json", db: Session = Depends(get_db)):
    """Export user's financial data in various formats"""
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id
    ).all()
    
    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")
    
    # Convert to exportable format
    export_data = []
    for t in transactions:
        export_data.append({
            "id": t.id,
            "date": t.date.isoformat(),
            "amount": t.amount,
            "description": t.description,
            "category": t.category,
            "predicted_category": t.predicted_category,
            "is_income": t.is_income,
            "is_anomaly": t.is_anomaly,
            "confidence_score": t.confidence_score
        })
    
    if format.lower() == "csv":
        # Convert to CSV format (return as structured data for frontend to handle)
        return {
            "format": "csv",
            "data": export_data,
            "filename": f"financeai_export_{user_id}_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    
    else:  # Default to JSON
        return {
            "format": "json",
            "data": export_data,
            "export_date": datetime.now().isoformat(),
            "user_id": user_id,
            "transaction_count": len(export_data)
        }