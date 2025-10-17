import requests
import json
from datetime import datetime, timedelta
import random

# Sample transaction data for testing
SAMPLE_TRANSACTIONS = [
    # Food & Dining
    {"amount": 45.67, "description": "Whole Foods Market", "category": "Food & Dining", "is_income": False},
    {"amount": 12.50, "description": "Starbucks Coffee", "category": "Food & Dining", "is_income": False},
    {"amount": 89.23, "description": "Restaurant Dinner", "category": "Food & Dining", "is_income": False},
    {"amount": 156.78, "description": "Grocery Shopping Safeway", "category": "Food & Dining", "is_income": False},
    {"amount": 23.45, "description": "McDonald's Drive Thru", "category": "Food & Dining", "is_income": False},
    
    # Transportation
    {"amount": 67.89, "description": "Shell Gas Station", "category": "Transportation", "is_income": False},
    {"amount": 15.00, "description": "Uber Ride Downtown", "category": "Transportation", "is_income": False},
    {"amount": 8.50, "description": "Metro Transit Pass", "category": "Transportation", "is_income": False},
    {"amount": 25.00, "description": "Airport Parking Fee", "category": "Transportation", "is_income": False},
    
    # Shopping
    {"amount": 234.56, "description": "Amazon Online Purchase", "category": "Shopping", "is_income": False},
    {"amount": 78.90, "description": "Target Store", "category": "Shopping", "is_income": False},
    {"amount": 145.67, "description": "Clothing Store H&M", "category": "Shopping", "is_income": False},
    {"amount": 56.78, "description": "Best Buy Electronics", "category": "Shopping", "is_income": False},
    
    # Bills & Utilities
    {"amount": 1250.00, "description": "Monthly Rent Payment", "category": "Bills & Utilities", "is_income": False},
    {"amount": 89.45, "description": "Electric Bill PG&E", "category": "Bills & Utilities", "is_income": False},
    {"amount": 65.00, "description": "Internet Service Comcast", "category": "Bills & Utilities", "is_income": False},
    {"amount": 45.99, "description": "Phone Bill Verizon", "category": "Bills & Utilities", "is_income": False},
    {"amount": 34.56, "description": "Water Utility Bill", "category": "Bills & Utilities", "is_income": False},
    
    # Entertainment
    {"amount": 15.99, "description": "Netflix Subscription", "category": "Entertainment", "is_income": False},
    {"amount": 9.99, "description": "Spotify Premium", "category": "Entertainment", "is_income": False},
    {"amount": 45.00, "description": "Movie Theater Tickets", "category": "Entertainment", "is_income": False},
    {"amount": 67.89, "description": "Concert Ticket", "category": "Entertainment", "is_income": False},
    
    # Healthcare
    {"amount": 25.00, "description": "Pharmacy CVS Prescription", "category": "Healthcare", "is_income": False},
    {"amount": 150.00, "description": "Doctor Visit Copay", "category": "Healthcare", "is_income": False},
    {"amount": 89.99, "description": "Dental Cleaning", "category": "Healthcare", "is_income": False},
    
    # Income
    {"amount": 4500.00, "description": "Salary Deposit", "category": "Income", "is_income": True},
    {"amount": 750.00, "description": "Freelance Payment", "category": "Income", "is_income": True},
    {"amount": 125.00, "description": "Investment Dividend", "category": "Income", "is_income": True},
    {"amount": 50.00, "description": "Cashback Reward", "category": "Income", "is_income": True},
]

def generate_sample_data(user_id: str = "demo_user", days_back: int = 90):
    """Generate sample transaction data for the last N days"""
    
    transactions = []
    base_date = datetime.now()
    
    for i in range(days_back):
        # Generate 1-5 transactions per day
        num_transactions = random.randint(1, 5)
        current_date = base_date - timedelta(days=i)
        
        for _ in range(num_transactions):
            # Pick a random sample transaction
            sample = random.choice(SAMPLE_TRANSACTIONS)
            
            # Add some variation to amounts
            amount_variation = random.uniform(0.8, 1.2)
            varied_amount = sample["amount"] * amount_variation
            
            # Add some time variation within the day
            time_variation = timedelta(
                hours=random.randint(6, 22),
                minutes=random.randint(0, 59)
            )
            transaction_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0) + time_variation
            
            transaction = {
                "user_id": user_id,
                "amount": round(varied_amount, 2),
                "description": sample["description"],
                "category": sample.get("category"),
                "date": transaction_date.isoformat(),
                "is_income": sample["is_income"]
            }
            
            transactions.append(transaction)
    
    return transactions

def upload_sample_data(base_url: str = "http://localhost:8000", user_id: str = "demo_user"):
    """Upload sample data to the API"""
    
    print(f"Generating sample data for user: {user_id}")
    transactions = generate_sample_data(user_id)
    
    print(f"Generated {len(transactions)} sample transactions")
    
    # Upload in batches
    batch_size = 50
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i + batch_size]
        
        try:
            response = requests.post(
                f"{base_url}/api/transactions/bulk",
                json=batch,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"Uploaded batch {i//batch_size + 1}/{(len(transactions)-1)//batch_size + 1}")
            else:
                print(f"Error uploading batch: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error uploading batch: {e}")
    
    print("Sample data upload complete!")
    
    # Train the models
    try:
        print("Training prediction models...")
        response = requests.post(f"{base_url}/api/predictions/train/{user_id}")
        if response.status_code == 200:
            print("Models trained successfully!")
        else:
            print(f"Error training models: {response.status_code}")
    except Exception as e:
        print(f"Error training models: {e}")

if __name__ == "__main__":
    # Run this script to populate the database with sample data
    upload_sample_data()