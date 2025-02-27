# app/services/quickbooks.py
# Assuming this file already exists, we'll add the get_report method
import os
from typing import Dict, List, Any, Optional
import logging
import aiohttp
from sqlalchemy.orm import Session
from datetime import datetime


# Import existing models and utilities as needed
from ..models import QuickBooksTokens

logger = logging.getLogger(__name__)


class QuickBooksService:
    def __init__(self, db: Session):
        self.db = db
        # Existing initialization code...

    # Existing methods...

    async def get_report(
        self, realm_id: str, report_type: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get a report from the QuickBooks Online API.

        Args:
            realm_id: QuickBooks realm ID
            report_type: Type of report (e.g., "ProfitAndLoss", "BalanceSheet", "CashFlow")
            params: Additional parameters for the report query

        Returns:
            Dict containing the report data
        """
        try:
            # Get access token from database or refresh if needed
            auth_token = await self._get_access_token(realm_id)

            # Prepare URL and headers
            base_url = "https://sandbox-quickbooks.api.intuit.com"  # Use the appropriate environment URL
            url = f"{base_url}/v3/company/{realm_id}/reports/{report_type}"

            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Accept": "application/json",
            }

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Error fetching {report_type} report: {error_text}"
                        )
                        raise Exception(
                            f"Failed to fetch {report_type} report: HTTP {response.status}"
                        )

        except Exception as e:
            logger.error(f"Error getting {report_type} report: {str(e)}")
            raise

    # Add helper method to get or refresh tokens if not already present
    async def _get_access_token(self, realm_id: str) -> str:
        """
        Get a valid access token for the QuickBooks API.
        Refreshes the token if it has expired.
        """
        # Retrieve token from database
        token_record = (
            self.db.query(QuickBooksTokens)
            .filter(QuickBooksTokens.realm_id == realm_id)
            .first()
        )

        if not token_record:
            raise Exception(f"No OAuth tokens found for realm ID {realm_id}")

        # TODO: Check if token is expired and refresh if needed
        # This depends on your token management implementation

        return token_record.access_token

    async def get_profit_loss_statement(self, start_date=None, end_date=None):
        """Get profit and loss statement from QuickBooks"""
        # Use default dates if not provided
        if not start_date:
            # Default to beginning of current month
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            # Default to today
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Get the realm ID from your active connection
        realm_id = self._get_active_realm_id()

        # Call the report API
        return await self.get_report(
            realm_id=realm_id,
            report_type="ProfitAndLoss",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    async def get_balance_sheet(self, as_of_date=None):
        """Get balance sheet from QuickBooks"""
        # Use today's date if not provided
        if not as_of_date:
            as_of_date = datetime.now().strftime("%Y-%m-%d")
        # Get the realm ID from your active connection
        realm_id = self._get_active_realm_id()
        # Call the report API
        return await self.get_report(
            realm_id=realm_id,
            report_type="BalanceSheet",
            params={
                "as_of": as_of_date,
            },
        )

    async def get_cash_flow_statement(self, start_date=None, end_date=None):
        """Get cash flow statement from QuickBooks"""
        # Use default dates if not provided
        if not start_date:
            # Default to beginning of current month
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        if not end_date:
            # Default to today
            end_date = datetime.now().strftime("%Y-%m-%d")
        # Get the realm ID from your active connection
        realm_id = self._get_active_realm_id()
        # Call the report API
        return await self.get_report(
            realm_id=realm_id,
            report_type="CashFlow",
            params={
                "start_date": start_date,
                "end_date": end_date,
            },
        )

    def _get_active_realm_id(self):
        """Get the active realm ID for the current user"""
        # In a real implementation, you would get this from your user session
        # For development/testing with your Skynet account, you should use your test account's realm ID

        # Query the database for any valid token
        token_record = self.db.query(QuickBooksTokens).first()
        if token_record:
            return token_record.realm_id

        # If no token found, use a fallback for development
        return os.getenv("QUICKBOOKS_TEST_REALM_ID", "your_skynet_realm_id_here")
