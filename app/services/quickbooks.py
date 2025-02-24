from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
from urllib.parse import urlencode
import requests
from app.database import get_db
from app.models import QuickBooksTokens
from datetime import datetime
from datetime import timedelta

router = APIRouter()

# QuickBooks OAuth configuration
CLIENT_ID = os.getenv("QUICKBOOKS_CLIENT_ID")
CLIENT_SECRET = os.getenv("QUICKBOOKS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("QUICKBOOKS_REDIRECT_URI")

# QuickBooks endpoints
AUTHORIZATION_ENDPOINT = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_ENDPOINT = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"


@router.get("/connect/quickbooks")
async def connect_quickbooks():
    """
    Initiates the QuickBooks OAuth flow
    """
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


@router.get(
    "/callback/quickbooks"
)  # This becomes /api/v1/callback/quickbooks due to the prefix
async def quickbooks_callback(
    code: str = None,
    state: str = None,
    realmId: str = None,
    db: Session = Depends(get_db),
):
    """
    Handles the QuickBooks OAuth callback and exchanges the code for tokens
    """
    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed")

    try:
        # Exchange code for tokens
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

        # Calculate expires_at from expires_in
        expires_at = datetime.utcnow() + timedelta(seconds=tokens["expires_in"])

        # Store tokens in database
        quickbooks_tokens = QuickBooksTokens(
            realm_id=realmId,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_at=expires_at,
        )

        # Check if we already have tokens for this realm
        existing_tokens = (
            db.query(QuickBooksTokens)
            .filter(QuickBooksTokens.realm_id == realmId)
            .first()
        )

        if existing_tokens:
            # Update existing tokens
            existing_tokens.access_token = tokens["access_token"]
            existing_tokens.refresh_token = tokens["refresh_token"]
            existing_tokens.expires_at = expires_at
        else:
            # Add new tokens
            db.add(quickbooks_tokens)

        db.commit()

        return {
            "message": "Authorization successful!",
            "realm_id": realmId,
            "expires_at": expires_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")


@router.get("/debug/quickbooks-config")
async def debug_quickbooks_config():
    """
    Debug endpoint to check QuickBooks configuration
    """
    return {
        "client_id": CLIENT_ID[:5] + "..." if CLIENT_ID else "Not set",
        "client_secret": CLIENT_SECRET[:5] + "..." if CLIENT_SECRET else "Not set",
        "redirect_uri": REDIRECT_URI,
    }
