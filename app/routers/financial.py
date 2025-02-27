# app/routers/financial.py
from fastapi import APIRouter, HTTPException, Depends
from ..services.quickbooks import QuickBooksService
from fastapi.requests import Request

router = APIRouter(prefix="/api/financial", tags=["financial"])


@router.get("/auth-url")
async def get_auth_url(request: Request, qb_service: QuickBooksService = Depends()):
    try:
        # Get the QuickBooks auth URL
        auth_url = await qb_service.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        # Log the full error details for debugging
        import traceback

        print(f"Error generating auth URL: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error generating QuickBooks auth URL: {str(e)}"
        )


@router.get("/accounts")
async def get_accounts(qb_service: QuickBooksService = Depends()):
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
    qb_service: QuickBooksService = Depends(),
):
    try:
        return await qb_service.get_profit_loss_statement(start_date, end_date)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching profit/loss: {str(e)}"
        )


@router.get("/statements/balance-sheet")
async def get_balance_sheet(
    as_of_date: str = None, qb_service: QuickBooksService = Depends()
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
    qb_service: QuickBooksService = Depends(),
):
    try:
        return await qb_service.get_cash_flow_statement(start_date, end_date)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching cash flow: {str(e)}"
        )
