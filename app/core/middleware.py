# app/core/middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import re


class SubdomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract host from the request
        host = request.headers.get("host", "")

        # Extract the subdomain (if any)
        subdomain = None
        domain_pattern = r"(?:(.+)\.)?ryze\.ai"
        match = re.match(domain_pattern, host)

        if match and match.group(1):
            subdomain = match.group(1)

        # Add subdomain to request state for use in routers
        request.state.subdomain = subdomain

        # Continue processing the request
        response = await call_next(request)
        return response
