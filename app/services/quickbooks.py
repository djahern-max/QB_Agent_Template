# app/services/quickbooks.py
import os
import random
from typing import Dict, List, Any, Optional
import logging
import aiohttp
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Import existing models and utilities as needed
from ..models import QuickBooksTokens

logger = logging.getLogger(__name__)


class QuickBooksService:
    def __init__(self, db: Session):
        self.db = db
        # Existing initialization code...

    async def get_tokens(self, auth_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            Dict containing access_token, refresh_token, and expiry information
        """
        try:
            # Get environment variables
            client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
            client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")
            redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")

            if not client_id or not client_secret or not redirect_uri:
                raise Exception(
                    "Missing QuickBooks API credentials in environment variables"
                )

            # Set up token exchange request
            token_endpoint = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
            payload = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": redirect_uri,
            }

            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }

            # Make the token request
            async with aiohttp.ClientSession() as session:
                # Create Basic auth header
                auth = aiohttp.BasicAuth(client_id, client_secret)

                async with session.post(
                    token_endpoint, data=payload, headers=headers, auth=auth
                ) as response:
                    if response.status == 200:
                        token_data = await response.json()

                        # Calculate expiry time
                        expires_in = token_data.get(
                            "expires_in", 3600
                        )  # Default to 1 hour if not specified
                        expiry_time = datetime.now().timestamp() + expires_in

                        return {
                            "access_token": token_data.get("access_token"),
                            "refresh_token": token_data.get("refresh_token"),
                            "expires_at": datetime.fromtimestamp(expiry_time),
                            "x_refresh_token_expires_in": token_data.get(
                                "x_refresh_token_expires_in"
                            ),
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get tokens: {error_text}")
                        raise Exception(
                            f"Token exchange failed: HTTP {response.status} - {error_text}"
                        )

        except Exception as e:
            logger.error(f"Error getting tokens: {str(e)}")
            raise Exception(f"Could not get tokens: {str(e)}")

    async def store_tokens(self, realm_id: str, tokens: Dict[str, Any]):
        """
        Store QuickBooks OAuth tokens in the database.

        Args:
            realm_id: QuickBooks company ID
            tokens: Token data from get_tokens method
        """
        try:
            # Check if a record already exists for this realm
            existing_record = (
                self.db.query(QuickBooksTokens)
                .filter(QuickBooksTokens.realm_id == realm_id)
                .first()
            )

            if existing_record:
                # Update existing record
                existing_record.access_token = tokens["access_token"]
                existing_record.refresh_token = tokens["refresh_token"]
                existing_record.expires_at = tokens["expires_at"]
                existing_record.updated_at = datetime.now()
            else:
                # Create new record
                new_record = QuickBooksTokens(
                    realm_id=realm_id,
                    access_token=tokens["access_token"],
                    refresh_token=tokens["refresh_token"],
                    expires_at=tokens["expires_at"],
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                self.db.add(new_record)

            # Commit the changes
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing tokens: {str(e)}")
            raise Exception(f"Could not store tokens: {str(e)}")

    async def get_report(
        self, realm_id: str, report_type: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get a report from the QuickBooks Online API.
        """
        try:
            # Get access token from database or refresh if needed
            auth_token = await self._get_access_token(realm_id)

            # Check if we're in sandbox or production
            is_sandbox = (
                os.getenv("QUICKBOOKS_ENVIRONMENT", "production").lower() == "sandbox"
            )

            # Prepare URL and headers based on environment
            if is_sandbox:
                base_url = "https://sandbox-quickbooks.api.intuit.com"
            else:
                base_url = "https://quickbooks.api.intuit.com"

            url = f"{base_url}/v3/company/{realm_id}/reports/{report_type}"

            # Prepare headers with proper Accept format
            headers = {
                "Authorization": f"Bearer {auth_token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            # Ensure params dictionary exists
            if params is None:
                params = {}

            # Add minorversion parameter if not present
            if "minorversion" not in params:
                params["minorversion"] = "65"  # Use the latest minor version

            # Log the request details for debugging
            logger.debug(f"Making report request to {url} with params {params}")

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    # Log the response status and headers for debugging
                    logger.debug(f"Report response status: {response.status}")
                    logger.debug(f"Report response headers: {response.headers}")

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

        # Check if token is expired
        current_time = datetime.now()

        # If token is expired or about to expire in the next 5 minutes, refresh it
        if token_record.expires_at <= current_time + timedelta(minutes=5):
            try:
                # Get refresh token
                refresh_token = token_record.refresh_token

                # Get environment variables
                client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
                client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")

                if not client_id or not client_secret:
                    raise Exception(
                        "Missing QuickBooks API credentials in environment variables"
                    )

                # Set up token refresh request
                token_endpoint = (
                    "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
                )
                payload = {
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }

                headers = {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                }

                # Make the token request
                async with aiohttp.ClientSession() as session:
                    # Create Basic auth header
                    auth = aiohttp.BasicAuth(client_id, client_secret)

                    async with session.post(
                        token_endpoint, data=payload, headers=headers, auth=auth
                    ) as response:
                        if response.status == 200:
                            token_data = await response.json()

                            # Calculate expiry time
                            expires_in = token_data.get(
                                "expires_in", 3600
                            )  # Default to 1 hour if not specified
                            expiry_time = datetime.now() + timedelta(seconds=expires_in)

                            # Update the token in the database
                            token_record.access_token = token_data.get("access_token")

                            # The refresh token might be updated too
                            if "refresh_token" in token_data:
                                token_record.refresh_token = token_data.get(
                                    "refresh_token"
                                )

                            token_record.expires_at = expiry_time
                            token_record.updated_at = datetime.now()

                            # Commit the changes
                            self.db.commit()

                            return token_record.access_token
                        else:
                            error_text = await response.text()
                            logger.error(f"Failed to refresh token: {error_text}")
                            raise Exception(
                                f"Token refresh failed: HTTP {response.status} - {error_text}"
                            )

            except Exception as e:
                logger.error(f"Error refreshing token: {str(e)}")
                # If refresh fails, we might need to force reauthentication
                raise Exception(
                    f"Authentication expired. Please reconnect to QuickBooks: {str(e)}"
                )

        # Return the token if it's still valid
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
        realm_id = os.getenv("QUICKBOOKS_REALM_ID")
        if not realm_id:
            logger.error("No QuickBooks realm ID available")
            raise ValueError(
                "No QuickBooks realm ID available. Please connect to QuickBooks first."
            )

        return realm_id

    async def get_connection_status(self, realm_id: str):
        try:
            # Check if we have valid tokens for this realm
            token_record = (
                self.db.query(QuickBooksTokens)
                .filter(QuickBooksTokens.realm_id == realm_id)
                .first()
            )

            if not token_record:
                return {"connected": False, "reason": "No tokens found"}

            # Check if tokens are expired
            current_time = datetime.now()
            if token_record.expires_at < current_time:
                # Token refresh logic here
                return {"connected": False, "reason": "Tokens expired"}

            # If we have valid tokens, try to get the company info
            try:
                # Get the auth token
                auth_token = token_record.access_token

                # Prepare URL and headers
                base_url = "https://quickbooks.api.intuit.com"
                url = f"{base_url}/v3/company/{realm_id}/companyinfo/{realm_id}"

                headers = {
                    "Authorization": f"Bearer {auth_token}",
                    "Accept": "application/json",
                }

                # Make the API request
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            company_data = await response.json()
                            company_name = company_data.get("CompanyInfo", {}).get(
                                "CompanyName", "Your Company"
                            )
                            return {"connected": True, "company_name": company_name}
                        else:
                            # If we can't get the company info but have valid tokens, still return connected
                            return {"connected": True, "company_name": "Your Company"}
            except Exception as e:
                logger.error(f"Error getting company info: {str(e)}")
                # If we can't get the company info but have valid tokens, still return connected
                return {"connected": True, "company_name": "Your Company"}

        except Exception as e:
            logger.error(f"Error checking connection status: {str(e)}")
            return {"connected": False, "reason": str(e)}

    async def get_auth_url(self):
        """
        Generate an OAuth authorization URL for QuickBooks Online.
        """
        try:
            # Get environment variables
            client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
            redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")

            if not client_id or not redirect_uri:
                raise Exception(
                    "Missing QuickBooks API credentials in environment variables"
                )

            # Generate a random state parameter for security
            state = "".join(
                random.choice("0123456789abcdefghijklmnopqrstuvwxyz") for _ in range(32)
            )

            # Create authorization URL
            auth_endpoint = "https://appcenter.intuit.com/connect/oauth2"
            scope = "com.intuit.quickbooks.accounting"

            auth_url = (
                f"{auth_endpoint}?"
                f"client_id={client_id}&"
                f"response_type=code&"
                f"scope={scope}&"
                f"redirect_uri={redirect_uri}&"
                f"state={state}"
            )

            return {"auth_url": auth_url}

        except Exception as e:
            logger.error(f"Error generating auth URL: {str(e)}")
            raise Exception(f"Could not generate authorization URL: {str(e)}")
