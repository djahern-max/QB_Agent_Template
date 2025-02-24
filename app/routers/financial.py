from fastapi import APIRouter, HTTPException, Header, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
from urllib.parse import urlencode
import requests
from datetime import timedelta

from app.database import get_db
from app.services.quickbooks import QuickBooksService
from app.agents.financial_agent.agent import FinancialAnalysisAgent
from app.models import QuickBooksTokens
from app.core.errors import (
    log_api_call,
)

router = APIRouter(
    tags=["financial-analysis"],
    responses={
        404: {"description": "Not found"},
        401: {"description": "Invalid API key"},
        500: {"description": "QuickBooks API error"},
    },
)

# QuickBooks OAuth configuration options
CLIENT_ID = os.getenv("QUICKBOOKS_CLIENT_ID")
CLIENT_SECRET = os.getenv("QUICKBOOKS_CLIENT_SECRET")
REDIRECT_URI = os.getenv("QUICKBOOKS_REDIRECT_URI")
AUTHORIZATION_ENDPOINT = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_ENDPOINT = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"


def verify_api_key(api_key: str = Header(..., convert_underscores=False)) -> str:
    if not api_key.startswith("ryze_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    return api_key


# Add QuickBooks Routes
@router.get("/connect/quickbooks")
async def connect_quickbooks():
    """Initiates the QuickBooks OAuth flow"""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting openid profile email phone address",
        "redirect_uri": REDIRECT_URI,
        "state": "randomstate",
    }
    authorization_url = f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
    return RedirectResponse(authorization_url)


@router.get("/callback/quickbooks")
async def quickbooks_callback(
    code: str = None,
    state: str = None,
    realmId: str = None,
    db: Session = Depends(get_db),
):
    """Handles the QuickBooks OAuth callback"""
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

        # Store or update tokens
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
            quickbooks_tokens = QuickBooksTokens(
                realm_id=realmId,
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                expires_at=expires_at,
            )
            db.add(quickbooks_tokens)

        db.commit()

        return {
            "message": "Authorization successful!",
            "realm_id": realmId,
            "expires_at": expires_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {str(e)}")


# Add QuickBooks Data Routes
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


@router.get("/analysis/{realm_id}")
async def get_financial_analysis(
    realm_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    metrics: Optional[List[str]] = Query(None),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get comprehensive financial analysis from QuickBooks data

    Parameters:
    - realm_id: QuickBooks realm ID
    - start_date: Optional start date for analysis period
    - end_date: Optional end date for analysis period
    - metrics: Optional list of specific metrics to calculate
    """
    start_time = datetime.utcnow()
    log_api_call(
        "get_financial_analysis",
        realm_id,
        start_date=start_date,
        end_date=end_date,
        metrics=metrics,
    )

    try:
        qb_service = QuickBooksService(db)
        agent = FinancialAnalysisAgent(api_key=api_key, qb_service=qb_service)

        input_data = {
            "realm_id": realm_id,
            "date_range": {"start": start_date, "end": end_date},
            "requested_metrics": metrics,
        }

        processed_data = agent.process_input(input_data)
        analysis_result = agent.generate_response(processed_data)

        return analysis_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/metrics/{realm_id}")
async def get_financial_metrics(
    realm_id: str,
    metric_type: Optional[str] = Query(
        None, description="Specific metric category to retrieve"
    ),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get specific financial metrics from QuickBooks data

    Parameters:
    - realm_id: QuickBooks realm ID
    - metric_type: Optional specific metric category (profit_loss, cash_flow, revenue, customer)
    """
    try:
        qb_service = QuickBooksService(db)
        agent = FinancialAnalysisAgent(api_key=api_key, qb_service=qb_service)

        input_data = {"realm_id": realm_id, "metric_type": metric_type}

        processed_data = agent.process_input(input_data)

        if metric_type:
            # Return specific metric category if requested
            return {"metrics": processed_data.get(metric_type, {})}
        else:
            # Return all metrics
            return {"metrics": processed_data}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Metrics calculation failed: {str(e)}"
        )


@router.get("/trends/{realm_id}")
async def get_financial_trends(
    realm_id: str,
    trend_type: str = Query(
        ..., description="Type of trend to analyze (revenue, profit, cash_flow)"
    ),
    months: int = Query(12, description="Number of months to analyze"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get trend analysis for specified financial metrics

    Parameters:
    - realm_id: QuickBooks realm ID
    - trend_type: Type of trend to analyze
    - months: Number of months for trend analysis
    """
    try:
        qb_service = QuickBooksService(db)
        agent = FinancialAnalysisAgent(api_key=api_key, qb_service=qb_service)

        input_data = {"realm_id": realm_id, "trend_type": trend_type, "months": months}

        processed_data = agent.process_input(input_data)

        return {
            "trend_analysis": (
                processed_data.get("revenue_metrics", {})
                if trend_type == "revenue"
                else processed_data.get(f"{trend_type}_trend", {})
            )
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/recommendations/{realm_id}")
async def get_financial_recommendations(
    realm_id: str,
    priority: Optional[str] = Query(
        None, description="Filter by priority (high, medium, low)"
    ),
    category: Optional[str] = Query(None, description="Filter by category"),
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get AI-generated financial recommendations

    Parameters:
    - realm_id: QuickBooks realm ID
    - priority: Optional priority filter
    - category: Optional category filter
    """
    try:
        qb_service = QuickBooksService(db)
        agent = FinancialAnalysisAgent(api_key=api_key, qb_service=qb_service)

        input_data = {"realm_id": realm_id}

        processed_data = agent.process_input(input_data)
        recommendations = agent.generate_response(processed_data)["recommendations"]

        # Filter recommendations if requested
        if priority:
            recommendations = [
                r for r in recommendations if r["priority"].lower() == priority.lower()
            ]
        if category:
            recommendations = [
                r for r in recommendations if r["category"].lower() == category.lower()
            ]

        return {"recommendations": recommendations}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Recommendation generation failed: {str(e)}"
        )


@router.get("/health-check/{realm_id}")
async def get_financial_health_check(
    realm_id: str, api_key: str = Depends(verify_api_key), db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a quick financial health check with key metrics and alerts

    Parameters:
    - realm_id: QuickBooks realm ID
    """
    try:
        qb_service = QuickBooksService(db)
        agent = FinancialAnalysisAgent(api_key=api_key, qb_service=qb_service)

        input_data = {"realm_id": realm_id}

        processed_data = agent.process_input(input_data)

        return {
            "cash_flow_status": processed_data["cash_flow"]["cash_flow_status"],
            "profit_margin": processed_data["profit_loss"]["profit_margin"],
            "revenue_trend": processed_data["revenue_metrics"]["revenue_trend"],
            "alerts": [
                alert
                for alert in agent._generate_recommendations(processed_data)
                if alert["priority"] == "High"
            ],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
