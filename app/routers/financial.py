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
import aiohttp
from ..database import get_db
from ..models import QuickBooksTokens
from ..services.quickbooks import QuickBooksService
from typing import Dict, Any
from ..agents.financial_agent.agent import FinancialAnalysisAgent
import json
import os
import logging
import traceback
import aiohttp
from datetime import datetime


logger = logging.getLogger(__name__)


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
    realm_id: str = Query(...),  # Make this required
    start_date: str = None,
    end_date: str = None,
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    try:
        return await qb_service.get_report(
            realm_id=realm_id,
            report_type="ProfitAndLoss",
            params={
                "start_date": start_date
                or datetime.now().replace(day=1).strftime("%Y-%m-%d"),
                "end_date": end_date or datetime.now().strftime("%Y-%m-%d"),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching profit/loss: {str(e)}"
        )


@router.get("/statements/balance-sheet")
async def get_balance_sheet(
    realm_id: str = Query(...),
    as_of_date: str = None,  # Changed from start_date/end_date to as_of_date
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    try:
        # Log the request parameters
        logger.debug(
            f"Balance Sheet request: realm_id={realm_id}, as_of_date={as_of_date}"
        )

        return await qb_service.get_report(
            realm_id=realm_id,
            report_type="BalanceSheet",
            params={
                "as_of": as_of_date or datetime.now().strftime("%Y-%m-%d"),
                "minorversion": "75",
            },
        )
    except Exception as e:
        logger.error(f"Error fetching balance sheet: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching balance sheet: {str(e)}"
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
        return RedirectResponse(url="https://clarity.ryze.ai/oauth-error")

    if not code or not realmId:
        return HTTPException(status_code=400, detail="Missing required parameters")

    try:
        # Exchange authorization code for access token
        tokens = await qb_service.get_tokens(code)

        # Store tokens in your database
        await qb_service.store_tokens(realmId, tokens)

        # Use absolute URL to redirect to React app's callback or dashboard
        return RedirectResponse(
            url=f"https://clarity.ryze.ai/dashboard?realm_id={realmId}"
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


@router.get("/financial/accounts/{realm_id}", response_model=dict)
async def get_quickbooks_accounts(realm_id: str, db: Session = Depends(get_db)):
    """
    Retrieve all accounts for a given QuickBooks realm ID.
    """
    try:
        quickbooks_service = QuickBooksService(db)
        accounts = await quickbooks_service.get_accounts_by_realm(realm_id)
        return accounts
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching accounts: {str(e)}"
        )


@router.post("/disconnect/{realm_id}")
async def disconnect_quickbooks(
    realm_id: str,
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
    db: Session = Depends(get_db),
):
    """Disconnect from a QuickBooks company"""
    try:
        # Delete the tokens for this realm
        token_record = (
            db.query(QuickBooksTokens)
            .filter(QuickBooksTokens.realm_id == realm_id)
            .first()
        )

        if token_record:
            db.delete(token_record)
            db.commit()
            return {
                "success": True,
                "message": f"Disconnected from company with realm_id {realm_id}",
            }
        else:
            return {"success": False, "message": "No connection found for this company"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error disconnecting: {str(e)}")


@router.get("/trends/{realm_id}")
async def get_financial_trends(
    realm_id: str,
    months: int = Query(6, ge=1, le=12),
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    """Get financial trend analysis"""
    try:
        # Import the FinancialTrendsService
        from ..services.financial_trends import FinancialTrendsService

        # Create the service with the QuickBooks service
        trends_service = FinancialTrendsService(qb_service)

        # Get trends data
        trend_data = await trends_service.get_monthly_profit_loss_trend(
            realm_id, months
        )

        return trend_data
    except Exception as e:
        logger.error(f"Error analyzing financial trends: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error analyzing financial trends: {str(e)}"
        )


# app/routers/financial.py - Update the analyze_financial_data function


# Update this in app/routers/financial.py


@router.post("/analyze/{report_type}")
async def analyze_financial_data(
    report_type: str, data: Dict[str, Any], db: Session = Depends(get_db)
):
    """Analyze financial data with AI"""
    if report_type not in ["profit-loss", "balance-sheet", "cash-flow"]:
        raise HTTPException(status_code=400, detail="Invalid report type")

    try:
        # Create the financial analysis agent
        agent = FinancialAnalysisAgent(db)

        # Log the data being sent for analysis
        logger.debug(f"Analyzing {report_type} data: {data.keys()}")

        # Validate the data structure
        if "data" not in data:
            logger.warning(f"Invalid request format: 'data' field is missing")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid request format: 'data' field is missing",
                    "summary": "The request did not contain the expected data structure.",
                    "insights": [
                        "Please check the API documentation for the correct request format."
                    ],
                    "recommendations": [
                        "Ensure the API request includes the financial data in the expected format."
                    ],
                },
            )

        # Use data.get('data') which handles the case when 'data' might be None
        financial_data = data.get("data", {})

        if not financial_data or not isinstance(financial_data, dict):
            logger.warning(f"Empty or invalid financial data received")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Empty or invalid financial data",
                    "summary": "No financial data was provided for analysis.",
                    "insights": [
                        "The provided data appears to be empty or in an invalid format."
                    ],
                    "recommendations": [
                        "Please provide valid financial data for analysis."
                    ],
                },
            )

        # Format the prompt based on report type
        logger.debug(f"Calling analysis for {report_type}")

        try:
            if report_type == "profit-loss":
                analysis = await agent.analyze_profit_loss(financial_data)
            elif report_type == "balance-sheet":
                analysis = await agent.analyze_balance_sheet(financial_data)
            elif report_type == "cash-flow":
                analysis = await agent.analyze_cash_flow(financial_data)
            else:
                # This should never happen due to the earlier check, but just in case
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": f"Unsupported report type: {report_type}",
                        "summary": "The requested analysis type is not supported.",
                        "insights": [],
                        "recommendations": [
                            "Please use one of the supported report types: profit-loss, balance-sheet, or cash-flow."
                        ],
                    },
                )

            # Log the analysis result
            logger.debug(f"Analysis result: {analysis}")

            # Check if the analysis contains an error
            if "error" in analysis:
                logger.error(f"Analysis error: {analysis['error']}")
                return JSONResponse(
                    status_code=200,  # Return 200 even for analysis errors to maintain consistent client behavior
                    content={
                        "error": analysis["error"],
                        "summary": analysis.get(
                            "summary", "Analysis encountered an error."
                        ),
                        "insights": analysis.get("insights", []),
                        "recommendations": analysis.get("recommendations", []),
                    },
                )

            # If the response doesn't have the expected structure, add default values
            if "summary" not in analysis:
                analysis["summary"] = "Analysis completed successfully."
            if "insights" not in analysis:
                analysis["insights"] = []
            if "recommendations" not in analysis:
                analysis["recommendations"] = []

            return analysis

        except Exception as inner_error:
            logger.exception(f"Error in analysis method: {str(inner_error)}")
            return JSONResponse(
                status_code=200,  # Return 200 to maintain frontend compatibility
                content={
                    "error": f"Analysis method error: {str(inner_error)}",
                    "summary": "An error occurred while analyzing the financial data.",
                    "insights": [
                        "The analysis process encountered an unexpected error."
                    ],
                    "recommendations": [
                        "Please try again later or contact support if the issue persists."
                    ],
                },
            )

    except Exception as e:
        logger.exception(f"Unhandled exception in analyze_financial_data: {str(e)}")
        # Return a structured error response
        return JSONResponse(
            status_code=200,  # Return 200 so the frontend can handle it gracefully
            content={
                "error": f"Analysis failed: {str(e)}",
                "summary": "Analysis could not be completed due to an error.",
                "insights": ["The analysis service encountered an unexpected issue."],
                "recommendations": [
                    "Please try again later or contact support if the issue persists."
                ],
            },
        )


@router.get("/statements/cash-flow")
async def get_cash_flow(
    realm_id: str = Query(...),
    start_date: str = None,
    end_date: str = None,
    qb_service: QuickBooksService = Depends(get_quickbooks_service),
):
    try:
        # Log the request parameters
        logger.debug(
            f"Cash Flow request: realm_id={realm_id}, start_date={start_date}, end_date={end_date}"
        )

        # Try "StatementOfCashFlows" instead of "CashFlow"
        return await qb_service.get_report(
            realm_id=realm_id,
            report_type="StatementOfCashFlows",  # Changed from "CashFlow"
            params={
                "start_date": start_date
                or datetime.now().replace(day=1).strftime("%Y-%m-%d"),
                "end_date": end_date or datetime.now().strftime("%Y-%m-%d"),
                "minorversion": "75",
            },
        )
    except Exception as e:
        logger.error(
            f"Error fetching cash flow: {str(e)}, traceback: {traceback.format_exc()}"
        )

        # If the first attempt fails, try with the original "CashFlow" name
        try:
            return await qb_service.get_report(
                realm_id=realm_id,
                report_type="CashFlow",
                params={
                    "start_date": start_date
                    or datetime.now().replace(day=1).strftime("%Y-%m-%d"),
                    "end_date": end_date or datetime.now().strftime("%Y-%m-%d"),
                    "minorversion": "75",
                },
            )
        except Exception as inner_e:
            logger.error(f"Error with fallback CashFlow: {str(inner_e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching cash flow: {str(e)} -> {str(inner_e)}",
            )


@router.get("/connection-status")
async def check_current_connection(db: Session = Depends(get_db)):
    """Check if any active QuickBooks connection exists"""
    try:
        # Get the most recent active token from the database
        token_record = (
            db.query(QuickBooksTokens).order_by(QuickBooksTokens.id.desc()).first()
        )

        if token_record:
            return {"connected": True, "realmId": token_record.realm_id}
        else:
            return {"connected": False, "realmId": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/company-name/{realm_id}")
async def get_company_name(
    realm_id: str, qb_service: QuickBooksService = Depends(get_quickbooks_service)
):
    """Get the company name for a QuickBooks connection"""
    try:
        # Get access token
        auth_token = await qb_service._get_access_token(realm_id)

        # Set API URL
        url = f"https://quickbooks.api.intuit.com/v3/company/{realm_id}/companyinfo/{realm_id}"

        # API request
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={
                    "Authorization": f"Bearer {auth_token}",
                    "Accept": "application/json",
                },
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "company_name": data.get("CompanyInfo", {}).get(
                            "CompanyName", "Name Not Found"
                        )
                    }
                else:
                    return {
                        "company_name": f"API Error: {response.status}",
                        "error": await response.text(),
                    }
    except Exception as e:
        return {"company_name": f"Exception: {type(e).__name__}", "error": str(e)}
