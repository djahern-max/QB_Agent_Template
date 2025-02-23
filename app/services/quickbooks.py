from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import os
from urllib.parse import urlencode

router = APIRouter()

# QuickBooks OAuth configuration
CLIENT_ID = os.getenv("QUICKBOOKS_CLIENT_ID")
CLIENT_SECRET = os.getenv("QUICKBOOKS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("QUICKBOOKS_REDIRECT_URI")

# QuickBooks authorization URL
AUTHORIZATION_ENDPOINT = "https://appcenter.intuit.com/connect/oauth2"


@router.get("/connect/quickbooks")
async def connect_quickbooks():
    """
    Initiates the QuickBooks OAuth flow
    """
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting openid profile email phone address",  # Updated scopes
        "redirect_uri": REDIRECT_URI,
        "state": "randomstate",  # In production, use a secure random string
    }

    authorization_url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
    print(f"Redirecting to: {authorization_url}")  # Add this for debugging
    return RedirectResponse(authorization_url)


@router.get("/callback/quickbooks")
async def quickbooks_callback(code: str = None, state: str = None, realmId: str = None):
    """
    Handles the QuickBooks OAuth callback
    """
    if code:
        return {
            "code": code,
            "realmId": realmId,
            "state": state,
            "message": "Authorization successful! You can now use this code to get access tokens.",
        }
    else:
        raise HTTPException(status_code=400, detail="Authorization failed")


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
