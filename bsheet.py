import requests
import json
from datetime import datetime, timedelta

# QuickBooks API credentials
CLIENT_ID = "AB6XZ3ij6GDYmJYhs72RBrn93eHXJ3jdLNjpc6nb66IAlyzc3a"
CLIENT_SECRET = "LDpXGTz0cw19bma34ivSkKeNkRkSTEOQijEzx2eM"
REDIRECT_URI = "https://agent1.ryze.ai/api/financial/callback/quickbooks"

# Company information
REALM_ID = "9341454160706034"

# Auth token from your database
ACCESS_TOKEN = "eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..kn5tbou6Mt-Zr9u2LDkaLw.TMS2KAMzQRnYsm1_nVXCNGyF1sy0fhY8bObHZM-X-EUaHWvLZtCKC-1PgrPOeQQm4yIV08GMUM3w6iOVYs416WPbc6vDiF5-QPOY5BXZFEFvbv5XNrE4KF0xGLGO2CAnqVW0VI8FENwc_5CBHdietqDhhulS3FFWbSYGDDYe3MNpU1Sto_bppbBohUwVpMmMJk97x_FABKQBFkl5wcAToxr7D03eQACgkx9b2c88aAMxi5fANKS-f3EVr7SKAdJzkaEN70WcSD13wUe5PqqFyb7WMkRCtz0VzvAOY2oVxK4mM1ZZSnn1LOACv8nEU3aJno29vWwkeZPzfdR5r35bLaypHuBzQjU9AfXWRxoDKd4ZcdjUAsKVU_ihzdaCVwuCz86B4D7NHNsIPrut7_XfkFCGw1CjvgL25KFoczve4qT_Ec_lpbnCl7BOTCUsUqCmzCnFeDQ1Ry2CjIZrhAXctKJ7-EDcFRnpmx9bjZFWyZwlfVOxfF8TO2jTRX53tJVE3LIMojIRZdStBAhcZefqPChxfyDP6qujWR78xMgLivOn4WJge4BemVxvimdb1QGsNCYg_FBxtLS2oN9XMQtTl03ZKHpwu4BaJDZQNBaZCCJxA2eMrFlsZZgYn_HjteKSm9kcUIvylzgxq0rd9hecO27QvyViejoCmA8nBBbNNZPZlipC3XNXb-rTHJXvNjL79x4aTUe0X1CSXCLzRqkKYBZsuQCk-nyu1vsBuNiQ3uZu4r-g5k4BCybl1ny1430v.gLzLibOVijJOhzWEZJD3jg"
REFRESH_TOKEN = "AB11749575306XNI3wqsdysWbsaVCflTL5yKEX22YIpPYQRTsl"
EXPIRES_AT = "2025-03-01 18:08:26.638017"


def check_token_expiry():
    """Check if the access token has expired and refresh if needed"""
    expires_at = datetime.strptime(EXPIRES_AT, "%Y-%m-%d %H:%M:%S.%f")
    if datetime.now() >= expires_at:
        print("Token expired, refreshing...")
        refresh_access_token()
    else:
        print("Token is still valid")


def refresh_access_token():
    """Refresh the access token using the refresh token"""
    # Declare globals at the beginning of the function
    global ACCESS_TOKEN, REFRESH_TOKEN, EXPIRES_AT

    url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }

    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        data = response.json()
        # In a real application, you would update these values in your database
        print("Token refreshed successfully")
        print(f"New access token: {data.get('access_token')}")
        print(f"New refresh token: {data.get('refresh_token')}")
        print(f"Expires in: {data.get('expires_in')} seconds")

        # Update global variables for this session
        ACCESS_TOKEN = data.get("access_token")
        REFRESH_TOKEN = data.get("refresh_token")
        EXPIRES_AT = (
            datetime.now() + timedelta(seconds=data.get("expires_in"))
        ).strftime("%Y-%m-%d %H:%M:%S.%f")
    else:
        print(f"Failed to refresh token: {response.status_code}")
        print(response.text)


def get_balance_sheet(params=None):
    """Fetch the balance sheet report from QuickBooks API"""

    # Base URL for QuickBooks API
    base_url = "https://quickbooks.api.intuit.com"

    # Default parameters if none provided
    if params is None:
        params = {
            "accounting_method": "Accrual",
            "date_macro": "this fiscal year-to-date",
            "qzurl": "true",
        }

    # Endpoint for Balance Sheet report
    endpoint = f"/v3/company/{REALM_ID}/reports/BalanceSheet"

    # Headers required for the API call
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # Make the API request
    url = f"{base_url}{endpoint}"
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def save_response_to_file(data, filename="balance_sheet_response.json"):
    """Save the API response to a JSON file for inspection"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Response saved to {filename}")


def main():
    # Check if token needs refreshing
    check_token_expiry()

    # Define parameters for the Balance Sheet report
    params = {
        "accounting_method": "Accrual",  # Can be "Cash" or "Accrual"
        "date_macro": "last calendar year",  # Predefined date range for last year
        # Alternatively, you can specify explicit dates:
        # "start_date": "2024-01-01",
        # "end_date": "2024-12-31",
        "qzurl": "true",  # Include Quick Zoom URLs
    }

    # Get the Balance Sheet report
    print("Fetching Balance Sheet report...")
    balance_sheet = get_balance_sheet(params)

    if balance_sheet:
        print("Successfully retrieved Balance Sheet report")
        # Save the response to a file for inspection
        save_response_to_file(balance_sheet)

        # Display some basic information from the report
        if "Header" in balance_sheet and "ReportName" in balance_sheet["Header"]:
            print(f"Report: {balance_sheet['Header']['ReportName']}")

        # Check if the report has rows (which contain the actual data)
        if "Rows" in balance_sheet and "Row" in balance_sheet["Rows"]:
            row_count = len(balance_sheet["Rows"]["Row"])
            print(f"Report contains {row_count} rows of data")
    else:
        print("Failed to retrieve Balance Sheet report")


if __name__ == "__main__":
    main()
