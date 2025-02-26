# app/agents/financial_agent/agent.py
import os
import json
from typing import Dict, Any, List
import requests
import datetime
from openai import OpenAI
from fastapi import Depends
from sqlalchemy.orm import Session


from ...database import get_db


def get_cash_accounts(self, realm_id: str) -> Dict:
    """Get cash and bank accounts from QuickBooks"""
    tokens = self._get_tokens(realm_id)

    url = f"{self.base_url}/{realm_id}/query"
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }

    # Query only cash/bank accounts
    query = "SELECT * FROM Account WHERE AccountType IN ('Bank', 'Other Current Asset') AND Active = true"
    params = {"query": query}

    # Similar error handling as in get_accounts
    response = requests.get(url, headers=headers, params=params)
    # handle errors and refresh token if needed

    return response.json()


def get_transaction_history(self, realm_id: str, days: int = 90) -> Dict:
    """Get recent transaction history"""
    tokens = self._get_tokens(realm_id)

    url = f"{self.base_url}/{realm_id}/query"
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }

    # Calculate date range
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=days)

    # Query for recent transactions
    query = f"SELECT * FROM Transaction WHERE TxnDate >= '{start_date.strftime('%Y-%m-%d')}' AND TxnDate <= '{end_date.strftime('%Y-%m-%d')}' ORDER BY TxnDate DESC"
    params = {"query": query}

    response = requests.get(url, headers=headers, params=params)
    # handle errors and refresh token if needed

    return response.json()
