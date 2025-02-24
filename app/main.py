from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.financial import router as financial_router
from typing import List, Dict

app = FastAPI(
    title="agent_1 RYZE.ai",
    description="AI-powered financial analysis with QuickBooks integration",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single router mount
app.include_router(financial_router, prefix="/api/v1", tags=["financial"])


@app.get("/")
async def root():
    return {"name": "RYZE.ai API", "version": "1.0.0", "status": "operational"}


@app.get("/routes")
async def get_routes() -> List[Dict]:
    routes = []
    for route in app.routes:
        routes.append(
            {
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if route.methods else [],
            }
        )
    return routes
