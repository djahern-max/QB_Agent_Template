#!/bin/bash

# Set your realm ID and access token from your database
REALM_ID="9341454149171335"
ACCESS_TOKEN="eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..HyIRiuRWhk38DjUpgsxVtg.CBy99kjb9znMvSCac6_L2bUu5mzffaESMjlCyRe2T7IpvXvY-Ii7oT0_lkRvia1BWc7_yewI3tUZ5BYLgg4rjtk6M4P8RzFW11xNtViBpTpmOY40e-Jl-sb2LRRcnb4mCMetK5GP1DSogzple3LoWhA2qYDzaBKAOaCQxN43ZOD0p2ZXe9niy8v6vwtCR7M8aEzSx2r1hCrdByqsaQ6dYcNFrAh2gyNbhs9ru4QNGAD0KodMOlNG_yGB4ZXLKX80JOypzoGFv2qhyyxmLm5xPvqDs3x8z9KnZ-wW3DgWaxMUvjywKA5HasWCu4qQn-5sYaZmMQU29ZFdz-vk45n8Xo11P4Rzb3BIdiFhEK8ApotmDJTQDJvD4pk5XPeRQ6iX5wS3CYS5oqC5pwBSeaDHviWz-ddlbkBUpZ9AwNuo0wNv7owVjICBXeO9fKZpA0jr56pbliSpVZRPXFhfL037_AaLL3vgi57aTzPgy_76yqM9Z8KJvtAf4VlMYiRZ32hBcwtPuFfEb6Z1mvSQDq-QeBTTu5v1yEqPYQfMqhhFAyWKeunRGd0ykhSsTTmsMVHPqk4q6im08JPMTDU7XpgDavxpnKZ7cQ7rd4y9-zJ9hUBHPRtcfRsBJOXIX0ZBR2FkGoWqg41ZO6YVK9ZNF-Wyy1f4tcVKHUC93LgeaGYpnr-JoM8ZxaumDY39kf8NbjfH2hOls0H9vsJZgJ7QqwL4jMXA2s9fxgoCBday0ck8SeV1CnQ9LyyFbTmL68XOf6M1.IJTfFPvWDs6Ypr3xMCsT0Q"

# Base URL for your API
BASE_URL="https://agent1.ryze.ai/api"

# Test the accounts endpoint (adjust the path if needed)
echo "Testing QuickBooks Accounts endpoint..."
curl -v -X GET "$BASE_URL/quickbooks/accounts?realm_id=$REALM_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -o accounts_response.json

# Check if the response was successful
if [ $? -eq 0 ]; then
  echo "Request completed. Checking response..."
  
  # Check if the response contains error messages
  if grep -q "error\\|detail" accounts_response.json; then
    echo "ERROR detected in response:"
    grep -o "\"detail\":\"[^\"]*\"\\|\"error\":\"[^\"]*\"" accounts_response.json
  else
    echo "Success! Response looks good."
    echo "First few lines of the response:"
    head -n 20 accounts_response.json
  fi
else
  echo "Request failed with error code: $?"
fi

# Try alternative endpoint paths if the first one fails
if grep -q "error\\|detail" accounts_response.json; then
  echo -e "\nTrying alternative account endpoints..."
  
  # Try some common variations of the accounts endpoint
  for endpoint in "quickbooks/account" "accounting/accounts" "financial/accounts" "accounts"; do
    echo "Trying $endpoint endpoint..."
    curl -s -X GET "$BASE_URL/$endpoint?realm_id=$REALM_ID" \
      -H "accept: application/json" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -o "${endpoint//\//_}_response.json"
    
    if ! grep -q "error\\|detail" "${endpoint//\//_}_response.json"; then
      echo "Success with $endpoint!"
      echo "First few lines of the response:"
      head -n 20 "${endpoint//\//_}_response.json"
      break
    else
      echo "Failed with $endpoint"
    fi
  done
fi