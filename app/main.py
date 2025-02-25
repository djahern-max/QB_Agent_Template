# app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
from typing import List, Dict

from .routers import financial
from .database import engine, Base

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Set up templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(financial.router)


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/routes")
async def get_routes() -> List[Dict]:
    routes = []
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = list(route.methods) if route.methods else []
        else:
            methods = []

        routes.append(
            {
                "Path": route.path,
                "Name": route.name or "Unnamed Route",
                "Methods": ", ".join(methods),  # Join methods into a single string
            }
        )
    return {"Available Routes": routes}


# Run the application
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
