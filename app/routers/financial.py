# app/routers/financial.py
from fastapi import APIRouter, HTTPException, Depends
from ..services.quickbooks import QuickBooksService
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.params import Query
from ..database import get_db
from sqlalchemy.orm import Session
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financial", tags=["financial"])


# Helper function to get QuickBooksService instance
def get_quickbooks_service(db: Session = Depends(get_db)):
    return QuickBooksService(db)


@router.get("/auth-url")
async def get_auth_url(qb_service: QuickBooksService = Depends(get_quickbooks_service)):
    """Generate QuickBooks auth URL"""
    try:
        # Just return the result directly
        return await qb_service.get_auth_url()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connection-status/{realm_id}")
async def check_connection_status(
    realm_id: str, qb_service: QuickBooksService = Depends(get_quickbooks_service)
):
    """Check if the connection to QuickBooks is active"""
    try:
        status = await qb_service.get_connection_status(realm_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts")
async def get_accounts(qb_service: QuickBooksService = Depends(get_quickbooks_service)):
    try:
        accounts = await qb_service.get_accounts()
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching accounts: {str(e)}"
        )


# Add financial statement endpoints
@router.get("/statements/profit-loss")
async def get_profit_loss(
    start_date: str = None,
    end_date: str = None,
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    try:
        return await qb_service.get_profit_loss_statement(start_date, end_date)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching profit/loss: {str(e)}"
        )


@router.get("/statements/balance-sheet")
async def get_balance_sheet(
    as_of_date: str = None,
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    try:
        return await qb_service.get_balance_sheet(as_of_date)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching balance sheet: {str(e)}"
        )


@router.get("/statements/cash-flow")
async def get_cash_flow(
    start_date: str = None,
    end_date: str = None,
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    try:
        return await qb_service.get_cash_flow_statement(start_date, end_date)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching cash flow: {str(e)}"
        )


@router.get("/callback/quickbooks")
async def quickbooks_callback(
    code: str = Query(None),
    state: str = Query(None),
    realmId: str = Query(None),
    error: str = Query(None),
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    """Handle OAuth callback from QuickBooks"""
    if error:
        # Log the error
        print(f"OAuth error: {error}")
        # Redirect to error page in React app with absolute URL
        return RedirectResponse(url="https://agent1.ryze.ai/oauth-error")

    if not code or not realmId:
        return HTTPException(status_code=400, detail="Missing required parameters")

    try:
        # Exchange authorization code for access token
        tokens = await qb_service.get_tokens(code)

        # Store tokens in your database
        await qb_service.store_tokens(realmId, tokens)

        # Use absolute URL to redirect to React app's callback or dashboard
        return RedirectResponse(
            url=f"https://agent1.ryze.ai/dashboard?realm_id={realmId}"
        )
    except Exception as e:
        print(f"Error in QuickBooks callback: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "detail": f"OAuth error: {str(e)}",
                "headers": None,
            },
        )


@router.get("/company-name/{realm_id}")
async def get_company_name(
    realm_id: str, qb_service: QuickBooksService = Depends(get_quickbooks_service)
):
    """Get the company name for a QuickBooks connection"""
    try:
        # In a real implementation, you would query QuickBooks for the company info
        # For now, return a placeholder
        return {"company_name": "Your Company Name"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{realm_id}")
async def get_accounts_by_realm(
    realm_id: str, qb_service: QuickBooksService = Depends(get_quickbooks_service)
):
    """Get all accounts for a specific QuickBooks realm"""
    try:
        accounts = await qb_service.get_accounts_by_realm(realm_id)
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching accounts: {str(e)}"
        )


@router.get("/statements/trends/{realm_id}")
async def get_financial_trends(
    realm_id: str,
    db: Session = Depends(get_db),
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    """Get financial trends analysis"""
    try:
        # Import the FinancialStatementsService with correct capitalization
        from ..services.financial_statements import FinancialStatementsService

        # Create the financial statements service with the QuickBooksService instance
        fs_service = FinancialStatementsService(qb_service)

        # Generate trends analysis
        trends = await fs_service.analyze_financial_trends(realm_id, db)
        return trends
    except ImportError as e:
        # Handle the case where the import fails
        logger.error(f"Import error in financial trends endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error in financial trends service: {str(e)}"
        )
    except Exception as e:
        # Handle other exceptions
        logger.error(f"Error analyzing financial trends: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error analyzing financial trends: {str(e)}"
        )
