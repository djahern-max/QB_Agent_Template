from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from .routers.financial import router as financial_router


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


app.include_router(financial_router)


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


# Catch-all route to see what paths are being requested
@app.get("/api/{full_path:path}", include_in_schema=False)
async def api_catch_all(request: Request, full_path: str):
    """Debug route to catch all API requests and print the path"""
    logger.debug(f"Received API request at path: {full_path}")
    logger.debug(f"Full URL: {request.url}")
    logger.debug(f"Query params: {request.query_params}")
    return {"path": full_path, "message": "API route not found"}


# Run the application
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
