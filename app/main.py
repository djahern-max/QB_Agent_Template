# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from typing import List, Dict

from .routers import financial
from .database import engine, Base
import logging
from fastapi.responses import PlainTextResponse
from fastapi.routing import APIRoute
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RYZE.ai Financial Analysis Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(financial.router)


@app.get("/routes", response_class=JSONResponse)
async def get_routes():
    routes = []
    for route in app.routes:
        if isinstance(route, APIRoute):
            routes.append(
                {"path": route.path, "name": route.name, "methods": list(route.methods)}
            )
    return {"routes": routes}


# Run the application
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
