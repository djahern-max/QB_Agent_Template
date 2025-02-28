# test_integration.py
import requests
import json
import os
import sys
from datetime import datetime
import time

# Base URL - change as needed
BASE_URL = "https://clarity.ryze.ai"


def log_response(description, response):
    """Log the response details"""
    print(f"\n=== {description} ===")
    print(f"Status Code: {response.status_code}")

    try:
        json_response = response.json()
        print(f"Response: {json.dumps(json_response, indent=2)}")
    except:
        print(f"Response: {response.text[:200]}...")


def test_connection_status():
    """Test connection status to QuickBooks"""
    url = f"{BASE_URL}/api/financial/connection-status"
    response = requests.get(url)
    log_response("Connection Status", response)

    if response.status_code == 200:
        data = response.json()
        if data.get("connected", False):
            print("✅ Successfully connected to QuickBooks")
            return data.get("realm_id")
        else:
            print("❌ Not connected to QuickBooks")
            return None
    else:
        print("❌ Failed to check connection status")
        return None


def get_auth_url():
    """Get QuickBooks authentication URL"""
    url = f"{BASE_URL}/api/financial/auth-url"
    response = requests.get(url)
    log_response("Auth URL", response)

    if response.status_code == 200:
        auth_url = response.json().get("auth_url")
        print(f"✅ Auth URL: {auth_url}")
        print("Please open this URL in your browser to authorize with QuickBooks.")
        print("After authorization, you'll be redirected back to your application.")

        # Wait for authorization to complete
        input("Press Enter after you've completed authorization...")

        # Check connection status again
        return test_connection_status()
    else:
        print("❌ Failed to get auth URL")
        return None


def get_accounts(realm_id):
    """Get chart of accounts from QuickBooks"""
    if not realm_id:
        print("❌ Cannot fetch accounts without realm_id")
        return None

    url = f"{BASE_URL}/clarity.ryze.ai?realm_id={realm_id}"
    response = requests.get(url)
    log_response("Chart of Accounts", response)

    if response.status_code == 200:
        print("✅ Successfully retrieved chart of accounts")
        return response.json()
    else:
        print("❌ Failed to get chart of accounts")
        return None


def analyze_accounts(accounts_data):
    """Analyze chart of accounts with GPT-4"""
    if not accounts_data:
        print("❌ Cannot analyze without accounts data")
        return None

    url = f"{BASE_URL}/api/financial/analyze"
    payload = {"accounts_data": accounts_data}
    response = requests.post(url, json=payload)
    log_response("Financial Analysis", response)

    if response.status_code == 200:
        print("✅ Successfully analyzed accounts")
        return response.json()
    else:
        print("❌ Failed to analyze accounts")
        return None


def ask_question(accounts_data, question):
    """Ask a specific question about the financial data"""
    if not accounts_data:
        print("❌ Cannot ask question without accounts data")
        return None

    url = f"{BASE_URL}/api/financial/ask"
    payload = {"accounts_data": accounts_data, "question": question}
    response = requests.post(url, json=payload)
    log_response(f"Question: {question}", response)

    if response.status_code == 200:
        print("✅ Successfully got answer")
        return response.json()
    else:
        print("❌ Failed to get answer")
        return None


def main():
    """Main test flow"""
    print("=== TESTING QUICKBOOKS INTEGRATION AND GPT-4 ANALYSIS ===")
    print(f"Base URL: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Step 1: Check connection status
    realm_id = test_connection_status()

    # Step 2: If not connected, get auth URL
    if not realm_id:
        realm_id = get_auth_url()

    # Step 3: Get chart of accounts
    accounts_data = get_accounts(realm_id)

    if accounts_data:
        # Step 4: Analyze accounts
        analysis = analyze_accounts(accounts_data)

        # Step 5: Ask specific questions
        questions = [
            "What is my current financial health?",
            "What are my biggest expense categories?",
            "How can I improve my cash flow?",
        ]

        for question in questions:
            answer = ask_question(accounts_data, question)
            time.sleep(1)  # Avoid rate limiting

    print("\n=== TEST COMPLETE ===")


if __name__ == "__main__":
    main()
