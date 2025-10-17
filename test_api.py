#!/usr/bin/env python3
"""
Test script to verify all FinanceAI API endpoints are working
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
USER_ID = "demo_user"

def test_endpoint(method, endpoint, description, expected_status=200):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "POST":
            response = requests.post(url)
        else:
            response = requests.get(url)
        
        if response.status_code == expected_status:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description} - Status: {response.status_code}")
            print(f"   Response: {response.text[:100]}...")
            return False
            
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def main():
    print("🧪 Testing FinanceAI API Endpoints")
    print("=" * 50)
    
    tests = [
        ("GET", "/health", "Health Check"),
        ("GET", f"/api/transactions/?user_id={USER_ID}&limit=5", "Get Transactions"),
        ("GET", f"/api/transactions/categories/stats?user_id={USER_ID}", "Category Statistics"),
        ("GET", f"/api/dashboard/overview/{USER_ID}", "Dashboard Overview"),
        ("POST", f"/api/predictions/train/{USER_ID}", "Train ML Models"),
        ("GET", f"/api/predictions/spending/{USER_ID}?days_ahead=30", "Spending Predictions"),
        ("GET", f"/api/predictions/anomalies/{USER_ID}", "Anomaly Detection"),
        ("GET", f"/api/recommendations/investment/{USER_ID}?risk_tolerance=moderate", "Investment Recommendations"),
        ("GET", f"/api/recommendations/savings-goals/{USER_ID}", "Savings Goals"),
    ]
    
    passed = 0
    total = len(tests)
    
    for method, endpoint, description in tests:
        if test_endpoint(method, endpoint, description):
            passed += 1
        time.sleep(0.5)  # Small delay between requests
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your FinanceAI API is working perfectly!")
        print("\n🚀 Next Steps:")
        print("1. Open frontend/index.html in your browser")
        print("2. Click 'Load Sample Data' if you haven't already")
        print("3. Explore the AI-powered financial insights!")
        print("4. Check out the API docs at http://localhost:8000/docs")
    else:
        print(f"⚠️  {total - passed} tests failed. Check the server logs for details.")
    
    return passed == total

if __name__ == "__main__":
    main()