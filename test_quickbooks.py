import requests
from dotenv import load_dotenv
import os
from urllib.parse import quote  # Add this import


def test_quickbooks_connection():
    load_dotenv()

    client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
    client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")
    redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")

    # URL encode the redirect URI
    encoded_redirect_uri = quote(redirect_uri, safe="")

    auth_endpoint = "https://appcenter.intuit.com/connect/oauth2"

    auth_url = (
        f"{auth_endpoint}?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"scope=com.intuit.quickbooks.accounting%20openid%20profile%20email&"
        f"redirect_uri={encoded_redirect_uri}&"  # Use the encoded URI here
        f"state=security_token"
    )

    print("\n=== QuickBooks Connection Test ===")
    print(f"Client ID: {client_id[:5]}..." if client_id else "Client ID: Not set")
    print(
        f"Client Secret: {client_secret[:5]}..."
        if client_secret
        else "Client Secret: Not set"
    )
    print(f"Redirect URI: {redirect_uri}")
    print("\nAuthorization URL:")
    print(auth_url)

    try:
        response = requests.get(auth_endpoint)
        print(f"\nEndpoint Status: {response.status_code}")
    except Exception as e:
        print(f"\nError accessing endpoint: {str(e)}")


if __name__ == "__main__":
    test_quickbooks_connection()
