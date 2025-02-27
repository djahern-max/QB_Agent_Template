from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from .routers.financial import router as financial_router
from fastapi import APIRouter
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute


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

# Add the financial router with the correct prefix
# If your frontend is requesting /api/financial/*, use this:
router = APIRouter(tags=["financial"])

# If you need to keep the financial router's existing prefix (if it already includes '/financial')
# Make sure it's clear what you're doing:
# app.include_router(financial_router)


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


# Move the catch-all route AFTER all other routes
# And make it more specific to avoid catching legitimate routes
@app.get("/api/debug/{full_path:path}", include_in_schema=False)
async def api_debug_catch_all(request: Request, full_path: str):
    """Debug route to catch API requests that don't match any defined routes"""
    logger.debug(f"Received unmatched API request at path: {full_path}")
    logger.debug(f"Full URL: {request.url}")
    logger.debug(f"Query params: {request.query_params}")
    return {"path": full_path, "message": "API route not found"}
