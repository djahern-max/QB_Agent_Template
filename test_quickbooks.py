import requests
from dotenv import load_dotenv
import os


def test_quickbooks_connection():
    # Load environment variables from .env file
    load_dotenv()

    # Get credentials from environment variables
    client_id = os.getenv("QUICKBOOKS_CLIENT_ID")
    client_secret = os.getenv("QUICKBOOKS_CLIENT_SECRET")
    redirect_uri = os.getenv("QUICKBOOKS_REDIRECT_URI")

    # Verify all required credentials are present
    if not all([client_id, client_secret, redirect_uri]):
        print("\nError: Missing required environment variables!")
        print("Please check your .env file contains:")
        print("- QUICKBOOKS_CLIENT_ID")
        print("- QUICKBOOKS_CLIENT_SECRET")
        print("- QUICKBOOKS_REDIRECT_URI")
        return

    # QuickBooks OAuth endpoint
    auth_endpoint = "https://appcenter.intuit.com/connect/oauth2"

    # Create authorization URL
    auth_url = (
        f"{auth_endpoint}?"
        f"client_id={client_id}&"
        f"response_type=code&"
        f"scope=com.intuit.quickbooks.accounting%20openid%20profile%20email&"
        f"redirect_uri={redirect_uri}&"
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

    # Test if the URL is accessible
    try:
        response = requests.get(auth_endpoint)
        print(f"\nEndpoint Status: {response.status_code}")
    except Exception as e:
        print(f"\nError accessing endpoint: {str(e)}")


if __name__ == "__main__":
    test_quickbooks_connection()
