from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from typing import Dict, Optional
from sqlalchemy.orm import Session
import datetime

from ..database import get_db
from ..services.quickbooks import QuickBooksService, QuickBooksTokens

router = APIRouter()


# OAuth routes - Keep these since they're being used
@router.get("/api/financial/auth-url")
async def get_auth_url(request: Request, qb_service: QuickBooksService = Depends()):
    """Get QuickBooks authorization URL"""
    try:
        auth_url = qb_service.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get auth URL: {str(e)}")


@router.get("/api/financial/callback/quickbooks")
async def quickbooks_callback(
    request: Request,
    code: str,
    state: str = None,
    realmId: str = None,
    qb_service: QuickBooksService = Depends(),
):
    """Handle QuickBooks OAuth callback"""
    try:
        # Save tokens to database
        tokens = qb_service.handle_callback(code, realmId)

        # Redirect URL with realm_id parameter
        frontend_url = "https://agent1.ryze.ai/dashboard"
        redirect_url = f"{frontend_url}?realm_id={realmId}"

        return RedirectResponse(url=redirect_url)
    except Exception as e:
        error_url = "https://agent1.ryze.ai/oauth-error"
        return RedirectResponse(url=f"{error_url}?error={str(e)}")


# Accounts route - Keep because it's used by dashboard
@router.get("/api/financial/accounts/{realm_id}")
async def get_accounts(realm_id: str, qb_service: QuickBooksService = Depends()):
    """Get chart of accounts from QuickBooks"""
    try:
        accounts = qb_service.get_accounts(realm_id)
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get accounts: {str(e)}")


# Add a test endpoint
@router.get("/api/financial/test")
async def test_endpoint():
    """Test endpoint to verify routing"""
    return {"status": "ok", "message": "Test endpoint is working"}


# Add the company name endpoint
@router.get("/api/financial/company-name/{realm_id}")
async def get_company_name(realm_id: str, qb_service: QuickBooksService = Depends()):
    """Get company name from QuickBooks"""
    try:
        company_info = qb_service.get_company_info(realm_id)
        company_name = company_info.get("CompanyInfo", {}).get(
            "CompanyName", "Unknown Company"
        )
        return {"company_name": company_name}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching company name: {str(e)}"
        )


# Add a detailed company info endpoint
@router.get("/api/financial/company-info/{realm_id}")
async def get_company_info(realm_id: str, qb_service: QuickBooksService = Depends()):
    """Get detailed company information from QuickBooks"""
    try:
        company_info = qb_service.get_company_info(realm_id)
        return {"status": "success", "data": company_info}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching company info: {str(e)}"
        )


# Add a connection status endpoint
@router.get("/api/financial/connection-status/{realm_id}")
async def check_connection_status(realm_id: str, db: Session = Depends(get_db)):
    """Check if user is connected to QuickBooks"""
    try:
        tokens = db.query(QuickBooksTokens).filter_by(realm_id=realm_id).first()

        if tokens:
            is_expired = (
                tokens.expires_at and tokens.expires_at < datetime.datetime.now()
            )
            return {
                "connected": not is_expired,
                "realm_id": tokens.realm_id,
                "expires_at": (
                    tokens.expires_at.isoformat() if tokens.expires_at else None
                ),
            }
        else:
            return {"connected": False}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to check connection status: {str(e)}"
        )


@router.post("/api/financial/disconnect")
async def disconnect_quickbooks(request: Request, db: Session = Depends(get_db)):
    """Disconnect from QuickBooks by removing the saved tokens"""
    try:
        # Get the data from the request body
        data = await request.json()
        realm_id = data.get("realm_id")

        print(f"Disconnect request received for realm_id: {realm_id}")

        if not realm_id:
            raise HTTPException(status_code=400, detail="realm_id is required")

        # Find and delete the tokens for this realm
        token = db.query(QuickBooksTokens).filter_by(realm_id=realm_id).first()

        if not token:
            print(f"No token found for realm_id: {realm_id}")
            raise HTTPException(
                status_code=404, detail="No connection found for this realm"
            )

        # Delete the token
        print(f"Deleting token for realm_id: {realm_id}")
        db.delete(token)
        db.commit()
        print(f"Token deleted successfully for realm_id: {realm_id}")

        return {"success": True, "message": "Successfully disconnected from QuickBooks"}
    except Exception as e:
        print(f"Error in disconnect: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")
