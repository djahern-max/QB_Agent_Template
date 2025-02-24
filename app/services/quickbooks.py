from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
from urllib.parse import urlencode
import requests
from app.database import get_db
from app.models import QuickBooksTokens
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

router = APIRouter()

# QuickBooks OAuth configuration
CLIENT_ID = os.getenv("QUICKBOOKS_CLIENT_ID")
CLIENT_SECRET = os.getenv("QUICKBOOKS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("QUICKBOOKS_REDIRECT_URI")

# QuickBooks endpoints
AUTHORIZATION_ENDPOINT = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_ENDPOINT = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"


class QuickBooksService:
    BASE_URL = "https://sandbox-quickbooks.api.intuit.com"
    API_VERSION = "v3"

    def __init__(self, db: Session):
        self.db = db

    def _get_tokens(self, realm_id: str) -> Optional[QuickBooksTokens]:
        tokens = (
            self.db.query(QuickBooksTokens)
            .filter(QuickBooksTokens.realm_id == realm_id)
            .first()
        )
        if not tokens:
            raise HTTPException(
                status_code=404, detail="No tokens found for this realm"
            )
        return tokens

    def _refresh_tokens_if_needed(self, tokens: QuickBooksTokens) -> QuickBooksTokens:
        if datetime.utcnow() >= tokens.expires_at:
            token_data = {
                "grant_type": "refresh_token",
                "refresh_token": tokens.refresh_token,
            }

            response = requests.post(
                TOKEN_ENDPOINT, data=token_data, auth=(CLIENT_ID, CLIENT_SECRET)
            )
            new_tokens = response.json()

            tokens.access_token = new_tokens["access_token"]
            tokens.refresh_token = new_tokens.get("refresh_token", tokens.refresh_token)
            tokens.expires_at = datetime.utcnow() + timedelta(
                seconds=new_tokens["expires_in"]
            )

            self.db.commit()

        return tokens

    def _make_api_request(
        self,
        realm_id: str,
        endpoint: str,
        method: str = "GET",
        params: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        tokens = self._get_tokens(realm_id)
        tokens = self._refresh_tokens_if_needed(tokens)

        url = f"{self.BASE_URL}/{self.API_VERSION}/company/{realm_id}/{endpoint}"

        headers = {
            "Authorization": f"Bearer {tokens.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.request(
            method=method, url=url, headers=headers, params=params, json=data
        )

        if response.status_code == 401:
            # Token might have expired during the request
            tokens = self._refresh_tokens_if_needed(tokens)
            headers["Authorization"] = f"Bearer {tokens.access_token}"
            response = requests.request(
                method=method, url=url, headers=headers, params=params, json=data
            )

        response.raise_for_status()
        return response.json()

    # Company Info
    def get_company_info(self, realm_id: str) -> Dict[str, Any]:
        """Get basic company information"""
        return self._make_api_request(realm_id, f"companyinfo/{realm_id}")

    # Account Methods
    def get_accounts(
        self, realm_id: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get list of accounts"""
        return self._make_api_request(
            realm_id, "query", params={"query": "select * from Account"}
        )

    def get_account(self, realm_id: str, account_id: str) -> Dict[str, Any]:
        """Get specific account details"""
        return self._make_api_request(realm_id, f"account/{account_id}")

    # Customer Methods
    def get_customers(
        self, realm_id: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get list of customers"""
        return self._make_api_request(
            realm_id, "query", params={"query": "select * from Customer"}
        )

    def get_customer(self, realm_id: str, customer_id: str) -> Dict[str, Any]:
        """Get specific customer details"""
        return self._make_api_request(realm_id, f"customer/{customer_id}")

    # Invoice Methods
    def get_invoices(
        self, realm_id: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get list of invoices"""
        return self._make_api_request(
            realm_id, "query", params={"query": "select * from Invoice"}
        )

    def get_invoice(self, realm_id: str, invoice_id: str) -> Dict[str, Any]:
        """Get specific invoice details"""
        return self._make_api_request(realm_id, f"invoice/{invoice_id}")


# OAuth Flow Routes
@router.get("/connect/quickbooks")
async def connect_quickbooks():
    """Initiates the QuickBooks OAuth flow"""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting openid profile email phone address",
        "redirect_uri": REDIRECT_URI,
        "state": "randomstate",  # In production, use a secure random string
    }

    authorization_url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
    print(f"Redirecting to: {authorization_url}")
    return RedirectResponse(authorization_url)


@router.get("/callback/quickbooks")
async def quickbooks_callback(
    code: str = None,
    state: str = None,
    realmId: str = None,
    db: Session = Depends(get_db),
):
    """Handles the QuickBooks OAuth callback and exchanges the code for tokens"""
    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed")

    try:
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }

        token_response = requests.post(
            TOKEN_ENDPOINT, data=token_data, auth=(CLIENT_ID, CLIENT_SECRET)
        )

        tokens = token_response.json()

        if "error" in tokens:
            raise HTTPException(status_code=400, detail=tokens["error_description"])

        expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])

        quickbooks_tokens = QuickBooksTokens(
            realm_id=realmId,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_at=expires_at,
        )

        existing_tokens = (
            db.query(QuickBooksTokens)
            .filter(QuickBooksTokens.realm_id == realmId)
            .first()
        )

        if existing_tokens:
            existing_tokens.access_token = tokens["access_token"]
            existing_tokens.refresh_token = tokens["refresh_token"]
            existing_tokens.expires_at = expires_at
        else:
            db.add(quickbooks_tokens)

        db.commit()

        return {
            "message": "Authorization successful!",
            "realm_id": realmId,
            "expires_at": expires_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")


# Data Access Routes
@router.get("/company/{realm_id}")
async def get_company_info(
    realm_id: str, db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get company information from QuickBooks"""
    qb_service = QuickBooksService(db)
    return qb_service.get_company_info(realm_id)


@router.get("/accounts/{realm_id}")
async def get_accounts(realm_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all accounts from QuickBooks"""
    qb_service = QuickBooksService(db)
    return qb_service.get_accounts(realm_id)


@router.get("/customers/{realm_id}")
async def get_customers(realm_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all customers from QuickBooks"""
    qb_service = QuickBooksService(db)
    return qb_service.get_customers(realm_id)


@router.get("/invoices/{realm_id}")
async def get_invoices(realm_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get all invoices from QuickBooks"""
    qb_service = QuickBooksService(db)
    return qb_service.get_invoices(realm_id)


@router.get("/debug/quickbooks-config")
async def debug_quickbooks_config():
    """Debug endpoint to check QuickBooks configuration"""
    return {
        "client_id": CLIENT_ID[:5] + "..." if CLIENT_ID else "Not set",
        "client_secret": CLIENT_SECRET[:5] + "..." if CLIENT_SECRET else "Not set",
        "redirect_uri": REDIRECT_URI,
    }
