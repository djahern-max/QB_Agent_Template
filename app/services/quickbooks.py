# app/services/quickbooks.py
import httpx
import os
from datetime import datetime, timedelta
from ..database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from ..models import QuickBooksTokens
from fastapi.exceptions import HTTPException


class QuickBooksService:
    def __init__(self, db: Session = Depends(get_db)):
        self.client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
        self.client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")
        self.redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")
        self.token_endpoint = (
            "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        )
        self.db = db

    async def get_auth_url(self):
        """Generate QuickBooks OAuth URL"""
        if not self.client_id or not self.redirect_uri:
            raise ValueError(
                "Missing QuickBooks credentials. Check environment variables."
            )

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "com.intuit.quickbooks.accounting",
            "state": "random_state",
        }

        auth_url = "https://appcenter.intuit.com/connect/oauth2"
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{auth_url}?{query_string}"

    async def get_tokens(self, code, realm_id):
        """Exchange authorization code for tokens"""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Create basic auth credentials
        auth = httpx.BasicAuth(self.client_id, self.client_secret)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint, data=data, headers=headers, auth=auth
            )

            if response.status_code != 200:
                print(f"Token error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            tokens = response.json()
            return tokens

    async def save_tokens(self, tokens, realm_id):
        """Save tokens to database"""
        # Calculate expiry time
        expires_in = tokens.get("expires_in", 3600)  # Default to 1 hour if not provided
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Check if we already have tokens for this realm
        existing_token = (
            self.db.query(QuickBooksTokens).filter_by(realm_id=realm_id).first()
        )

        if existing_token:
            # Update existing token
            existing_token.access_token = tokens["access_token"]
            existing_token.refresh_token = tokens["refresh_token"]
            existing_token.expires_at = expires_at
            # updated_at will be updated automatically due to onupdate=func.now()
        else:
            # Create new token record
            new_token = QuickBooksTokens(
                realm_id=realm_id,
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_at=expires_at,
            )
            self.db.add(new_token)

        self.db.commit()
        return True

    async def get_connection_status(self, realm_id):
        """Check if the connection to QuickBooks is active"""
        token = self.db.query(QuickBooksTokens).filter_by(realm_id=realm_id).first()

        if not token:
            return {"connected": False, "message": "No connection found"}

        # Check if token is expired and needs refresh
        if token.expires_at <= datetime.now():
            try:
                # Token is expired, try to refresh
                await self.refresh_token(realm_id)
                return {
                    "connected": True,
                    "realm_id": realm_id,
                    "expires_at": token.expires_at.isoformat(),
                }
            except Exception as e:
                return {
                    "connected": False,
                    "message": f"Token refresh failed: {str(e)}",
                }

        return {
            "connected": True,
            "realm_id": realm_id,
            "expires_at": token.expires_at.isoformat(),
        }

    async def refresh_token(self, realm_id):
        """Refresh the access token using the refresh token"""
        token = self.db.query(QuickBooksTokens).filter_by(realm_id=realm_id).first()

        if not token:
            raise ValueError(f"No token found for realm ID: {realm_id}")

        data = {"grant_type": "refresh_token", "refresh_token": token.refresh_token}

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Create basic auth credentials
        auth = httpx.BasicAuth(self.client_id, self.client_secret)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint, data=data, headers=headers, auth=auth
            )

            if response.status_code != 200:
                print(f"Token refresh error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )

            new_tokens = response.json()

            # Update token in database
            token.access_token = new_tokens["access_token"]
            if "refresh_token" in new_tokens:
                token.refresh_token = new_tokens["refresh_token"]

            # Calculate new expiry time
            expires_in = new_tokens.get("expires_in", 3600)
            token.expires_at = datetime.now() + timedelta(seconds=expires_in)

            self.db.commit()
            return new_tokens

    async def get_accounts(self):
        """Get all accounts from QuickBooks"""
        token = (
            self.db.query(QuickBooksTokens).order_by(QuickBooksTokens.id.desc()).first()
        )

        if not token:
            raise HTTPException(
                status_code=401, detail="No valid QuickBooks connection found"
            )

        # Check if token needs refresh
        if token.expires_at <= datetime.now():
            await self.refresh_token(token.realm_id)
        # Refresh the token object
        token = (
            self.db.query(QuickBooksTokens).filter_by(realm_id=token.realm_id).first()
        )

        # Make request to QuickBooks API
        headers = {
            "Authorization": f"Bearer {token.access_token}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://quickbooks.api.intuit.com/v3/company/{token.realm_id}/query",
                params={
                    "query": "SELECT * FROM Account WHERE Active = true ORDER BY Name"
                },
                headers=headers,
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return response.json()
