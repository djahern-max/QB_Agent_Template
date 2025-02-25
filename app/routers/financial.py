# app/routers/financial.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from typing import Dict, Optional
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse
import datetime

from ..database import get_db
from ..agents.financial_agent.agent import FinancialAnalysisAgent
from ..services.quickbooks import (
    QuickBooksService,
    QuickBooksTokens,
)  # Assuming you already have this service


router = APIRouter(tags=["financial"])


@router.get("/api/financial/auth-url")
async def get_auth_url(request: Request, qb_service: QuickBooksService = Depends()):
    """Get QuickBooks authorization URL"""
    try:
        auth_url = qb_service.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get auth URL: {str(e)}")


# Update in routers/financial.py
@router.get("/api/financial/accounts/{realm_id}")
async def get_accounts(realm_id: str, qb_service: QuickBooksService = Depends()):
    """Get chart of accounts from QuickBooks"""
    print(f"DEBUG: Account request received for realm_id: {realm_id}")
    try:
        accounts = qb_service.get_accounts(realm_id)
        print(f"DEBUG: Successfully retrieved accounts")
        return accounts
    except Exception as e:
        print(f"DEBUG: ERROR getting accounts: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        import traceback

        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to get accounts: {str(e)}")


@router.post("/api/financial/analyze")
async def analyze_accounts(
    request: Request,
    db: Session = Depends(get_db),
    agent: FinancialAnalysisAgent = Depends(),
):
    """Analyze chart of accounts with GPT-4"""
    try:
        # Get the accounts data from the request body
        data = await request.json()
        accounts_data = data.get("accounts_data")

        if not accounts_data:
            raise HTTPException(status_code=400, detail="Accounts data is required")

        # Analyze with GPT-4
        analysis = await agent.analyze_accounts(accounts_data)

        return analysis
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/api/financial/ask")
async def ask_question(
    request: Request,
    db: Session = Depends(get_db),
    agent: FinancialAnalysisAgent = Depends(),
):
    """Answer a financial question about the accounts"""
    try:
        # Get the data from the request body
        data = await request.json()
        accounts_data = data.get("accounts_data")
        question = data.get("question")

        if not accounts_data:
            raise HTTPException(status_code=400, detail="Accounts data is required")

        if not question:
            raise HTTPException(status_code=400, detail="Question is required")

        # Get answer from GPT-4
        answer = await agent.ask_question(accounts_data, question)

        return answer
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to answer question: {str(e)}"
        )


@router.get("/api/financial/suggested-questions")
async def get_suggested_questions():
    """Get suggested financial questions"""
    return {
        "questions": [
            "What is my current financial health?",
            "How can I improve my cash flow?",
            "What are my biggest expense categories?",
            "Is my debt-to-equity ratio healthy?",
            "What tax strategies should I consider?",
            "Are there any concerning financial trends?",
            "How can I reduce my operational costs?",
            "Should I be concerned about my current liabilities?",
        ]
    }


@router.get("/financial")
async def financial_dashboard(request: Request):
    """Return financial dashboard API status"""
    return {"message": "Financial dashboard API is working"}


@router.get("/api/financial/callback/quickbooks")
async def quickbooks_callback_alt(
    request: Request,
    code: str,
    state: str = None,
    realmId: str = None,
    qb_service: QuickBooksService = Depends(),
):
    """Handle QuickBooks OAuth callback"""
    print(f"Callback received - code: {code[:10]}..., realmId: {realmId}")
    try:
        # Save tokens to database
        tokens = qb_service.handle_callback(code, realmId)
        print(f"Tokens saved successfully for realm: {realmId}")

        # Redirect URL
        frontend_url = "https://agent1.ryze.ai/dashboard"
        redirect_url = f"{frontend_url}?realm_id={realmId}"
        print(f"Redirecting to: {redirect_url}")

        return RedirectResponse(url=redirect_url)
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        error_url = "https://agent1.ryze.ai/oauth-error"
        return RedirectResponse(url=f"{error_url}?error={str(e)}")


@router.get("/{full_path:path}")
async def catch_all_route(request: Request, full_path: str):
    """Debug route to catch all requests and print the path"""
    print(f"Received request at path: {full_path}")
    print(f"Full URL: {request.url}")
    print(f"Query params: {request.query_params}")

    # Check if it's a QuickBooks callback
    if "callback/quickbooks" in full_path and "code" in request.query_params:
        code = request.query_params.get("code")
        realmId = request.query_params.get("realmId")

        # Create QBService and handle callback
        qb_service = QuickBooksService(next(get_db()))
        try:
            tokens = qb_service.handle_callback(code, realmId)

            # Add redirection here
            frontend_url = "https://agent1.ryze.ai/dashboard"
            redirect_url = f"{frontend_url}?realm_id={realmId}"
            return RedirectResponse(url=redirect_url)
        except Exception as e:
            error_url = "https://agent1.ryze.ai/oauth-error"
            return RedirectResponse(url=f"{error_url}?error={str(e)}")

    return {"path": full_path, "message": "Route not found"}


@router.get("/api/financial/connection-status")
async def check_connection_status(
    request: Request, realm_id: str = None, db: Session = Depends(get_db)
):
    """Check if user is connected to QuickBooks"""
    try:
        if realm_id:
            # Query for tokens for the specific realm_id
            tokens = db.query(QuickBooksTokens).filter_by(realm_id=realm_id).first()
        else:
            # Fallback to most recent tokens if no realm_id provided
            tokens = (
                db.query(QuickBooksTokens).order_by(QuickBooksTokens.id.desc()).first()
            )

        if tokens:
            # Check if token is expired
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


@router.get("/api/financial/debug-tokens")
async def debug_tokens(db: Session = Depends(get_db)):
    """Debug endpoint to check saved tokens"""
    tokens = db.query(QuickBooksTokens).order_by(QuickBooksTokens.id.desc()).first()
    if tokens:
        return {
            "realm_id": tokens.realm_id,
            "has_access_token": bool(tokens.access_token),
            "has_refresh_token": bool(tokens.refresh_token),
            "expires_at": tokens.expires_at.isoformat() if tokens.expires_at else None,
        }
    else:
        return {"error": "No tokens found"}
