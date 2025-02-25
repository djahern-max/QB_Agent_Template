# app/routers/financial.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..agents.financial_agent.agent import FinancialAnalysisAgent
from ..services.quickbooks import (
    QuickBooksService,
)  # Assuming you already have this service

# Set up templates
templates = Jinja2Templates(directory="templates")

router = APIRouter(tags=["financial"])


@router.get("/api/financial/auth-url")
async def get_auth_url(request: Request, qb_service: QuickBooksService = Depends()):
    """Get QuickBooks authorization URL"""
    try:
        auth_url = qb_service.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get auth URL: {str(e)}")


@router.get("/api/financial/callback")
async def quickbooks_callback(
    request: Request, code: str, realmId: str, qb_service: QuickBooksService = Depends()
):
    """Handle QuickBooks OAuth callback"""
    try:
        # This should save the tokens to your database
        tokens = qb_service.handle_callback(code, realmId)
        return {
            "success": True,
            "message": "Successfully authenticated with QuickBooks",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth callback failed: {str(e)}")


@router.get("/api/financial/accounts")
async def get_accounts(
    request: Request, realm_id: str, qb_service: QuickBooksService = Depends()
):
    """Get chart of accounts from QuickBooks"""
    try:
        accounts = qb_service.get_accounts(realm_id)
        return accounts
    except Exception as e:
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
    """Render the financial dashboard"""
    return templates.TemplateResponse("financial_dashboard.html", {"request": request})
