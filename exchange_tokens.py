import requests
import json


def exchange_code_for_tokens(auth_code):
    # Your QuickBooks credentials
    client_id = "AB6XZ3ij6GDYmJYhs72RBrn93eHXJ3jdLNjpc6nb66IAlyzc3a"
    client_secret = "C8IlL62M7di98joDpxUPsKfTeVXtvF5D0IzCc9Ba"
    redirect_uri = "https://f0a5-205-209-24-211.ngrok-free.app/callback"

    # Token endpoint
    token_endpoint = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

    # Request headers and data
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        response = requests.post(token_endpoint, headers=headers, data=data)
        print("\nToken Exchange Response Status:", response.status_code)

        if response.status_code == 200:
            tokens = response.json()
            print("\nAccess Token (Keep secure!):", tokens.get("access_token"))
            print("Refresh Token (Keep secure!):", tokens.get("refresh_token"))
            print("\nToken exchange successful! Save these tokens securely.")
            return tokens
        else:
            print("Error Response:", response.text)
            return None

    except Exception as e:
        print(f"Error exchanging code for tokens: {str(e)}")
        return None


# Use your actual authorization code here
auth_code = "AB11740324986J0EacU5QpEbjEoytOIQN7Vrv1q3J8xWh5UcNx"
tokens = exchange_code_for_tokens(auth_code)
