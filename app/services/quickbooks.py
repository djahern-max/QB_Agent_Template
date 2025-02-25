# app/services/quickbooks.py
import os
import requests
import datetime
from typing import Dict, Any
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    QuickBooksTokens,
)  # Make sure you have this model defined in your database models


class QuickBooksService:
    def __init__(self, db: Session = Depends(get_db)):
        self.client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
        self.client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")
        self.redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")
        # Change from sandbox to production URL
        self.base_url = "https://quickbooks.api.intuit.com/v3/company"
        self.db = db

    def get_auth_url(self) -> str:
        """Generate authorization URL for QuickBooks OAuth"""
        auth_url = "https://appcenter.intuit.com/connect/oauth2"
        scope = "com.intuit.quickbooks.accounting"
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "scope": scope,
            "redirect_uri": self.redirect_uri,
            "state": "state",  # You might want to generate a random state
        }
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{query_string}"

    def handle_callback(self, code: str, realm_id: str) -> Dict:
        """Handle OAuth callback and exchange code for tokens"""
        tokens = self._exchange_code_for_tokens(code)

        # Save tokens to database with realm_id
        self._save_tokens(tokens, realm_id)

        return tokens

    def _exchange_code_for_tokens(self, code: str) -> Dict:
        """Exchange authorization code for access and refresh tokens"""
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code != 200:
            print(f"DEBUG: Token exchange failed with response: {response.text}")
            raise HTTPException(
                status_code=400, detail="Failed to exchange code for tokens"
            )

        return response.json()

    def _refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh the access token using refresh token"""
        token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code != 200:
            print(f"DEBUG: Token refresh failed with response: {response.text}")
            raise HTTPException(
                status_code=400, detail="Failed to refresh access token"
            )

        return response.json()

    def _save_tokens(self, tokens: Dict, realm_id: str) -> None:
        """Save QuickBooks tokens to database"""
        # Calculate expires_at datetime from expires_in seconds
        expires_at = datetime.datetime.now() + datetime.timedelta(
            seconds=int(tokens["expires_in"])
        )

        token_record = (
            self.db.query(QuickBooksTokens).filter_by(realm_id=realm_id).first()
        )

        if token_record:
            token_record.access_token = tokens["access_token"]
            token_record.refresh_token = tokens["refresh_token"]
            token_record.expires_at = (
                expires_at  # Using expires_at instead of expires_in
            )
        else:
            token_record = QuickBooksTokens(
                realm_id=realm_id,
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_at=expires_at,  # Using expires_at instead of expires_in
            )
            self.db.add(token_record)

        self.db.commit()

    def _get_tokens(self, realm_id: str) -> Dict:
        """Get tokens from database and refresh if needed"""
        token_record = (
            self.db.query(QuickBooksTokens).filter_by(realm_id=realm_id).first()
        )

        if not token_record:
            raise HTTPException(
                status_code=401, detail="Not authenticated with QuickBooks"
            )

        return {
            "access_token": token_record.access_token,
            "refresh_token": token_record.refresh_token,
            "realm_id": token_record.realm_id,
        }


def get_accounts(self, realm_id: str) -> Dict:
    """Get chart of accounts from QuickBooks"""
    print(f"DEBUG: Getting accounts for realm_id: {realm_id}")
    tokens = self._get_tokens(realm_id)
    print(f"DEBUG: Got tokens with access_token length: {len(tokens['access_token'])}")

    url = f"{self.base_url}/{realm_id}/query"
    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
        "Accept": "application/json",
    }

    # Query to get all accounts
    query = "SELECT * FROM Account WHERE Active = true ORDER BY Name"
    params = {"query": query}

    print(f"DEBUG: Making request to: {url}")
    print(f"DEBUG: Headers: {headers}")
    print(f"DEBUG: Params: {params}")

    response = requests.get(url, headers=headers, params=params)
    print(f"DEBUG: Response status: {response.status_code}")

    if response.status_code != 200:
        print(f"DEBUG: Response body: {response.text[:500]}")

        # Try refreshing token if unauthorized
        if response.status_code == 401:
            print("DEBUG: Attempting to refresh token")
            refreshed_tokens = self._refresh_access_token(tokens["refresh_token"])
            self._save_tokens(refreshed_tokens, realm_id)

            # Retry with new token
            headers["Authorization"] = f"Bearer {refreshed_tokens['access_token']}"
            print(
                f"DEBUG: Retrying with new token, length: {len(refreshed_tokens['access_token'])}"
            )
            response = requests.get(url, headers=headers, params=params)
            print(f"DEBUG: Retry response status: {response.status_code}")

            if response.status_code != 200:
                print(f"DEBUG: Retry response body: {response.text[:500]}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Failed to fetch accounts after token refresh: {response.text[:200]}",
                )
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to fetch accounts: {response.text[:200]}",
            )

    return response.json()
