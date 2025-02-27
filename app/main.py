from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from .routers.financial import router as financial_router
from fastapi.responses import JSONResponse, PlainTextResponse


from .database import engine, Base

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RYZE.ai Financial Analysis Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Print financial router routes for debugging
print(
    "Financial router routes:",
    [f"{list(route.methods)} {route.path}" for route in financial_router.routes],
)

# Include financial router with /api prefix
app.include_router(financial_router, prefix="/api")

# Debug after including the router
all_routes = []
for route in app.routes:
    if isinstance(route, APIRoute):
        all_routes.append(f"{list(route.methods)} {route.path}")
print("All routes after including financial_router:", all_routes)


@app.get("/")
async def root():
    """Root endpoint that redirects to dashboard"""
    return {"message": "API is working. For dashboard, go to /dashboard"}


@app.get("/api/routes", response_class=JSONResponse)
async def get_routes():
    """Get all API routes"""
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(
                {"path": route.path, "name": route.name, "methods": list(route.methods)}
            )
    return {"routes": routes}


@app.get("/api/routes-simple", response_class=PlainTextResponse)
async def get_routes_simple_with_prefix():
    """
    Returns a concise list of all routes with their paths and methods (with API prefix).
    """
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            methods = ", ".join(route.methods)
            routes.append(f"{methods}: {route.path}")

    return "\n".join(routes)
