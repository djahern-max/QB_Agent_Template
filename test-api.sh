#!/bin/bash

# Export the correct realm ID from your database
export TEST_REALM_ID="9341454149171335"

# Use the access token from your database
export ACCESS_TOKEN="eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..HyIRiuRWhk38DjUpgsxVtg.CBy99kjb9znMvSCac6_L2bUu5mzffaESMjlCyRe2T7IpvXvY-Ii7oT0_lkRvia1BWc7_yewI3tUZ5BYLgg4rjtk6M4P8RzFW11xNtViBpTpmOY40e-Jl-sb2LRRcnb4mCMetK5GP1DSogzple3LoWhA2qYDzaBKAOaCQxN43ZOD0p2ZXe9niy8v6vwtCR7M8aEzSx2r1hCrdByqsaQ6dYcNFrAh2gyNbhs9ru4QNGAD0KodMOlNG_yGB4ZXLKX80JOypzoGFv2qhyyxmLm5xPvqDs3x8z9KnZ-wW3DgWaxMUvjywKA5HasWCu4qQn-5sYaZmMQU29ZFdz-vk45n8Xo11P4Rzb3BIdiFhEK8ApotmDJTQDJvD4pk5XPeRQ6iX5wS3CYS5oqC5pwBSeaDHviWz-ddlbkBUpZ9AwNuo0wNv7owVjICBXeO9fKZpA0jr56pbliSpVZRPXFhfL037_AaLL3vgi57aTzPgy_76yqM9Z8KJvtAf4VlMYiRZ32hBcwtPuFfEb6Z1mvSQDq-QeBTTu5v1yEqPYQfMqhhFAyWKeunRGd0ykhSsTTmsMVHPqk4q6im08JPMTDU7XpgDavxpnKZ7cQ7rd4y9-zJ9hUBHPRtcfRsBJOXIX0ZBR2FkGoWqg41ZO6YVK9ZNF-Wyy1f4tcVKHUC93LgeaGYpnr-JoM8ZxaumDY39kf8NbjfH2hOls0H9vsJZgJ7QqwL4jMXA2s9fxgoCBday0ck8SeV1CnQ9LyyFbTmL68XOf6M1.IJTfFPvWDs6Ypr3xMCsT0Q"

# Test profit and loss endpoint
echo "Testing Profit & Loss endpoint..."
curl -X GET "https://clarity.ryze.ai/api/financial/statements/profit-loss?realm_id=$TEST_REALM_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

echo -e "\n\n"

# Test balance sheet endpoint
echo "Testing Balance Sheet endpoint..."
curl -X GET "https://clarity.ryze.ai/api/financial/statements/balance-sheet?realm_id=$TEST_REALM_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

echo -e "\n\n"

# Test cash flow endpoint
echo "Testing Cash Flow endpoint..."
curl -X GET "https://clarity.ryze.ai/api/financial/statements/cash-flow?realm_id=$TEST_REALM_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

echo -e "\n\n"

# Test trends endpoint
echo "Testing Trends endpoint..."
curl -X GET "https://clarity.ryze.ai/api/financial/statements/trends/$TEST_REALM_ID" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN"